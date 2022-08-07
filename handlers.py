import psutil, re, config
from aiogram import types
from dispatcher import dp
from stats import Stats
from aiohttp import request

@dp.message_handler(commands=("start", "about", "help"))
async def help(message: types.Message) -> None:

    reply =  "Привет, я Розефитта, увОжаемая личность в Малибу между прочим.\n"
    reply += "Но... Кажется меня превратили в бота, вот так сюрприз.\n\n"
    reply += "Доступные команды:\n"
    reply += "/about или /help - Выведет это сообщение\n"
    reply += "/ping - Выведет сообщение о текущей системе\n"
    reply += "/topNwords - Выведет топ N слов в чате (Информация с GRStats)\n"
    reply += "/random_anime - Выдаёт случайное аниме с ShikiMori\n\n"
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

    async with request('GET', "https://shikimori.one/api/animes", params=payload, headers=headers) as response:
        await message.answer(f"https://shikimori.one{(await response.json())[0]['url']}")