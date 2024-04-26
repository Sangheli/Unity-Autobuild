import asyncio
from telegram import Bot

TOKEN =
CHAT_ID =

bot = Bot(token=TOKEN)
file_path = 'buildWin.bat'
document = open(file_path, 'rb')


async def send_telegram_message():
    await bot.send_document(CHAT_ID, document)


asyncio.run(send_telegram_message())
