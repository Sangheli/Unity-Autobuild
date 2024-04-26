import asyncio
from telegram import Bot
import argparse
import os

parser = argparse.ArgumentParser()

parser.add_argument('-folderpath', type=str)
parser.add_argument('-token', type=str)
parser.add_argument('-chatid', type=str)

args = parser.parse_args()

folder_path = args.folderpath
TOKEN = args.token
CHAT_ID = args.chatid

file_names = [os.path.join(folder_path, f) for f in os.listdir(folder_path)
              if os.path.isfile(os.path.join(folder_path, f))]


async def send_telegram_message():
    bot = Bot(token=TOKEN)
    for filename in file_names:
        with open(filename, 'rb') as file:
            content = file.read().decode('utf-8', errors='ignore')
            await bot.send_document(CHAT_ID, content)


asyncio.run(send_telegram_message())
