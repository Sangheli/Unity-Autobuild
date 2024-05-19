import os
import shutil
import requests
from datetime import datetime

now = datetime.now()
date_time = now.strftime("_%Y_%m_%d_%H_%M_%S")
print("date and time:", date_time)

BASE_UNIT_PATH = ''
UNITY = 'Unity.exe'
projectPath = ''
projectPathAndroid = ''
buildpath = ''
name = ''

tg_token = ''
tg_chatid = ''


def clean():
    contents = [os.path.join(buildpath, i) for i in os.listdir(buildpath)]
    [shutil.rmtree(i) if os.path.isdir(i) and not os.path.islink(i) else os.remove(i) for i in contents]


def create_folder():
    newpath = f'{buildpath}\\Windows'
    if not os.path.exists(newpath):
        os.makedirs(newpath)


def build_win(app_name):
    os.chdir(BASE_UNIT_PATH)
    os.system(
        f'{UNITY} -quit -batchmode -nographics -projectpath {projectPath} -buildWindowsPlayer "{buildpath}\\Windows\\{app_name}.exe"')


def build_android(app_name):
    os.chdir(BASE_UNIT_PATH)
    os.system(
        f'{UNITY} -quit -batchmode -nographics -projectPath {projectPathAndroid} -executeMethod BuildScript.PerformBuild "{buildpath}\\{app_name}{date_time}.apk"')


def zipdir():
    shutil.make_archive(f'{buildpath}\\build', 'zip', f'{buildpath}\\Windows')


def upload_tg():
    url = f'https://api.telegram.org/bot{tg_token}/sendDocument'

    for filename in os.listdir(buildpath):
        full_path = os.path.join(buildpath, filename)
        if not os.path.isfile(full_path):
            continue

        # Open the file in binary mode
        with open(full_path, 'rb') as file:
            files = {'document': file}
            params = {'chat_id': tg_chatid}

            # Send the document to the Telegram Bot API
            response = requests.post(url, params=params, files=files)
            print(f'[{filename}]', response.json())


clean()
create_folder()
build_win(name)
build_android(name)
zipdir()
os.chdir(buildpath)
os.system('dir')
upload_tg()
print('\n[Build done]')
