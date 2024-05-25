import os
import shutil
import requests
from datetime import datetime

path_7z = 'C:\\Program Files\\7-Zip\\'

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


def create_folder(string_path):
    if not os.path.exists(string_path):
        os.makedirs(string_path)


def git_update(projectPath):
    os.chdir(f'{projectPath}\\')
    os.system(f'git pull')


def build_win(app_name):
    create_folder(f'{buildpath}\\Windows')
    os.chdir(BASE_UNIT_PATH)
    os.system(
        f'{UNITY} -quit -batchmode -nographics -projectpath {projectPath} -buildWindowsPlayer "{buildpath}\\Windows\\{app_name}.exe"')


def build_android(app_name):
    create_folder(f'{buildpath}')
    os.chdir(BASE_UNIT_PATH)
    os.system(
        f'{UNITY} -quit -batchmode -nographics -projectPath {projectPathAndroid} -executeMethod BuildScript.PerformBuild "{buildpath}\\{app_name}{date_time}.apk"')


def zipdir(to_archive_path, output_path):
    os.chdir(f'{path_7z}')
    os.system(f'7z.exe a {output_path}.7z {to_archive_path} -mx9 -v49m')


def zipdir_orig(to_archive_path, output_path):
    shutil.make_archive(output_path, 'zip', to_archive_path)


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

git_update(projectPath)
build_win(name)
zipdir_orig(f'{buildpath}\\Windows', f'{buildpath}\\{name}{date_time}_windows')

git_update(projectPathAndroid)
build_android(name)
# zipdir(f'{buildpath}\\*.apk', f'{buildpath}\\{name}{date_time}_apk.7z')

os.chdir(buildpath)
os.system('dir')
upload_tg()
print('\n[Build done]')
