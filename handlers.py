import psutil, re, config
from aiogram import types
from dispatcher import dp
from stats import Stats
from aiohttp import request
from datetime import datetime


@dp.message_handler(commands=("start", "about", "help"))
async def help(message: types.Message) -> None:

    reply =  "Привет, я Розефитта, увОжаемая личность в Малибу между прочим.\n"
    reply += "Но... Кажется меня превратили в бота, вот так сюрприз.\n\n"
    reply += "Доступные команды:\n"
    reply += "/about или /help - Выведет это сообщение\n"
    reply += "/ping - Выведет сообщение о текущей системе\n"
    reply += "/topNwords - Выведет топ N слов в чате (Информация с GRStats)\n"
    reply += "/random_anime - Выдаёт случайное аниме с ShikiMori\n"
    reply += "/ztauth {ID} - Автроизует ID в сети ZeroTier\n"
    reply += "/ztname {ID} {NAME} - Устанавливает имя {ID} в сети ZeroTier\n"
    reply += "/ztmembers - Выводит информацию об участниках сети ZeroTier\n\n"
    reply += "GitHub link - https://github.com/RozeFound/tg-rozelmao-bot"

    await message.answer(reply, disable_web_page_preview=True)

@dp.message_handler(commands="ping")
async def ping(message: types.Message) -> None:

    reply =  "Да-да, живая я. Вот вам краткая инфа по железу:\n"
    reply += f"*CPU*: *{psutil.cpu_count()} cores* (*{psutil.cpu_freq().max:0.0f}MHz*) with *{psutil.cpu_percent()}%* current usage\n"
    reply += f"*RAM*: *{psutil.virtual_memory().used >> 20}MB* / *{psutil.virtual_memory().total >> 20}MB*"

    await message.answer(reply, parse_mode="markdown")

@dp.message_handler(regexp=r"\/top\d+words")
async def get_topNwords(message: types.Message) -> None:

    if match := re.search(r"\/top(\d+)words", message.text):

        words_count, words_amount = 0, int(match.group(1))

        if words_amount <= 0 or words_amount > 100:
            await message.reply("Слышь инвалид, используй пжалста цифру от 1 до 100.")
            return

        top_words = Stats.get_top_words(config.GROUP_ID)

        reply = f"Топ слов в этом канале:\n\n"
        async for word, usage_count in top_words:
            words_count += 1
            reply += f"*{words_count}.* *{word}* - *{usage_count}* раз\n" 
            if words_count >= words_amount: break

        await message.answer(reply, parse_mode="markdown")

@dp.message_handler(commands="random_anime")
async def random_anime(message: types.Message) -> None:

    payload = {
        "order": "random", "kind": "tv",
        "status": "released", "score": 7,
        "rating": ("g", "pg", "pg_13", "r", "r_plus"),
        "censored": "true"
    } 

    headers = {"User-Agent": "TG-RozeLMAO-BOT"}

    async with request('GET', "https://shikimori.me/api/animes", params=payload, headers=headers) as response:
        await message.answer(f"https://shikimori.me{(await response.json())[0]['url']}")

def clamp_delta(duration) -> str:

    days, seconds = duration.days, duration.seconds
    hours = days * 24 + seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = (seconds % 60)
    weeks = days // 7

    if weeks: time = f"{weeks}w"
    elif days: time = f"{days}d"
    elif hours: time = f"{hours}h"
    elif minutes: time = f"{minutes}m"
    elif seconds: time = f"{seconds}s"

    return time

@dp.message_handler(commands="ztmembers")
async def zt_members(message: types.Message) -> None:

    headers = {"Authorization": f"token {config.ZT_TOKEN}"}
    url = f"https://api.zerotier.com/api/v1/network/{config.ZT_NETWORK_ID}/member"
    async with request("GET", url, headers=headers) as response:

        reply = f"Список участников в сети ZT {config.ZT_NETWORK_ID}:\n\n"

        for member in await response.json():

            if member['hidden']: continue

            name = member.get("name", "Unknown")
            ips = member['config']['ipAssignments']
            last_seen = member.get("lastSeen", 0)

            delta = datetime.now() - datetime.fromtimestamp(last_seen/1000.0)

            reply += f"\[*{clamp_delta(delta)}*] {name} - *{', '.join(ips)}*\n"

    await message.answer(reply, parse_mode="markdown")

@dp.message_handler(commands="ztauth")
async def zt_auth(message: types.Message) -> None:

    if not (member_id := message.get_args()): 
        return await message.answer(f"Укажите ID пользователя.")

    headers = {"Authorization": f"token {config.ZT_TOKEN}"}
    url = f"https://api.zerotier.com/api/v1/network/{config.ZT_NETWORK_ID}/member/{member_id}"
    async with request("GET", url, headers=headers) as response:
        if response.status == 404: reply = f"Пользователь с ID *{member_id}* не найден."
        else:
            async with request("POST", url, headers=headers, json={"config":{"authorized":True}}) as response:
                if response.status == 200: reply = f"ID *{member_id}* успешно авторизован"
                else: reply = f"Произошла неизвестная ошибка во время авторизации."

    await message.answer(reply, parse_mode="markdown")

@dp.message_handler(commands="ztname")
async def zt_name(message: types.Message) -> None:

    args = message.get_args().split()

    if not args: 
        return await message.reply("usage: /ztname {id} {name}")

    if not (member_id := args[0]): 
        return await message.answer(f"Укажите ID пользователя.")

    if not (name := " ".join(args[1:])): 
        return await message.answer(f"Укажите желаемое имя.")

    headers = {"Authorization": f"token {config.ZT_TOKEN}"}
    url = f"https://api.zerotier.com/api/v1/network/{config.ZT_NETWORK_ID}/member/{member_id}"
    async with request("GET", url, headers=headers) as response:
        if response.status == 404: reply = f"Пользователь с ID *{member_id}* не найден."
        else:
            async with request("POST", url, headers=headers, json={"name":name}) as response:
                if response.status == 200: reply = f"*{member_id}* успешно переименован в *{name}*"
                else: reply = f"Произошла неизвестная ошибка."

    await message.answer(reply, parse_mode="markdown")