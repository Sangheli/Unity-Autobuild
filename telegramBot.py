import requests
import argparse
import os

parser = argparse.ArgumentParser()

parser.add_argument('-folderpath', type=str)
parser.add_argument('-token', type=str)
parser.add_argument('-chatid', type=str)

args = parser.parse_args()
folder_path = args.folderpath

if not os.path.exists(folder_path):
    print(f"[{folder_path}] Folder not exist")
    exit(0)

# Set the Telegram Bot API URL
url = f'https://api.telegram.org/bot{args.token}/sendDocument'

for filename in os.listdir(folder_path):
    full_path = os.path.join(folder_path, filename)
    if not os.path.isfile(full_path):
        continue

    # Open the file in binary mode
    with open(full_path, 'rb') as file:
        files = {'document': file}
        params = {'chat_id': args.chatid}

        # Send the document to the Telegram Bot API
        response = requests.post(url, params=params, files=files)
        print(f'[{filename}]', response.json())
