import logging, config
from aiogram import Bot, Dispatcher

logging.basicConfig(level=logging.INFO)

if not config.TOKEN: exit("TOKEN NOT FOUND")

bot = Bot(config.TOKEN)
dp = Dispatcher(bot)
