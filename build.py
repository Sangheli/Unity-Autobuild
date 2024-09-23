import os
import shutil
import requests
from datetime import datetime
import subprocess as sp

path_7z = 'C:\\Program Files\\7-Zip\\'

now = datetime.now()
date_time = now.strftime("%Y_%m_%d_%H_%M_%S")
print("date and time:", date_time)

BASE_UNIT_PATH = 'C:\\Program Files\\Unity\\Hub\\Editor\\2023.2.10f1\\Editor\\'
UNITY = 'Unity.exe'
projectPath = 'C:\\_Work\\Trem\\Unity-PotatoZeldaForBuild'
projectPathMac = 'C:\\_Work\\Trem\\Unity-PotatoZeldaForBuild'
projectPathAndroid = 'C:\\_Work\\Trem\\Unity-PotatoZeldaAndroid'
projectPathWindowsRender = 'C:\\_Work\\Trem\\Unity-PotatoZeldaForRender'
projectPathWeb = 'C:\\_Work\\Trem\\Unity-PotatoZeldaWebgl'
buildpath = 'C:\\_Work\\Trem\\build'
dropboxpath = 'C:\\Dropbox\\Public'
name = 'MiniTank'

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


def git_reset(projectPath):
    os.chdir(f'{projectPath}\\')
    os.system(f'git reset --hard HEAD')


def build_win(app_name, build_folder, project_path):
    create_folder(f'{buildpath}\\{build_folder}')
    os.chdir(BASE_UNIT_PATH)
    os.system(
        f'{UNITY} -quit -batchmode -nographics -projectpath {project_path} -buildWindowsPlayer "{buildpath}\\{build_folder}\\{app_name}.exe"')


def build_android(app_name, project_path):
    create_folder(f'{buildpath}')
    os.chdir(BASE_UNIT_PATH)
    os.system(
        f'{UNITY} -quit -batchmode -nographics -projectPath {project_path} -executeMethod BuildScript.PerformBuild "{buildpath}\\{app_name}_{date_time}.apk"')


def build_mac(app_name,build_folder, project_path):
    create_folder(f'{buildpath}')
    os.chdir(BASE_UNIT_PATH)
    os.system(
        f'{UNITY} -quit -batchmode -nographics -projectPath {project_path} -executeMethod BuildScriptMac.PerformBuild "{buildpath}\\{build_folder}\\{app_name}_{date_time}"')


def build_android_map_editor(app_name, project_path):
    create_folder(f'{buildpath}')
    os.chdir(BASE_UNIT_PATH)
    os.system(
        f'{UNITY} -quit -batchmode -nographics -projectPath {project_path} -executeMethod BuildScriptMapEditor.PerformBuild "{buildpath}\\{app_name}MapEditor_{date_time}.apk"')

def build_web(app_name, project_path):
    create_folder(f'{buildpath}')
    os.chdir(BASE_UNIT_PATH)
    os.system(
        f'{UNITY} -quit -batchmode -nographics -projectPath {project_path} -executeMethod BuildScriptWeb.PerformBuild "{buildpath}\\{app_name}_{date_time}_web"')

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


def get_current_hash(projectPath):
    os.chdir(f'{projectPath}\\')
    output = sp.getoutput('git rev-parse HEAD')
    return output[:8]


def get_log(projectPath):
    os.chdir(f'{projectPath}\\')
    result = sp.getoutput('git log --oneline HEAD')
    return result.split('\n')


def extract_history(log, hash):
    result = []

    for x in log:
        result.append("* "+x[9:])
        if hash in x:
            result.append("\n[Old history]\n")

    return result


def save_to_folder(log, output_path,date_time):
    with open(f'{output_path}', "w") as file:
        file.write("["+date_time+"]"+"\n\n")

        for x in log:
            file.write(x + "\n")


def build_render():
    git_reset(projectPathWindowsRender)
    git_update(projectPathWindowsRender)
    build_win(name, 'Windows', projectPathWindowsRender)


def build_windows_full():
    git_reset(projectPath)
    hash = get_current_hash(projectPath)

    git_update(projectPath)
    log = get_log(projectPath)
    log_extracted = extract_history(log, hash)

    build_win(name, 'WindowsCompressed', projectPath)
    save_to_folder(log_extracted, f'{buildpath}\\patchnote_{date_time}.txt', date_time)
    zipdir_orig(f'{buildpath}\\WindowsCompressed', f'{buildpath}\\{name}_{date_time}_WindowsCompressed')


def build_android_full():
    git_reset(projectPathAndroid)
    git_update(projectPathAndroid)
    build_android(name, projectPathAndroid)


def build_mac_full():
    git_reset(projectPathMac)
    git_update(projectPathMac)
    build_mac(name, "MacOS" ,projectPathMac)


def build_web_full():
    git_reset(projectPathWeb)
    git_update(projectPathWeb)
    build_web(name, projectPathWeb)
    zipdir_orig(f'{buildpath}\\{name}_{date_time}_web', f'{buildpath}\\{name}_{date_time}_web')

def upload():
    os.chdir(buildpath)
    os.system('dir')
    upload_tg()


def copy_dropbox():
    for filename in os.listdir(buildpath):
        full_path = os.path.join(buildpath, filename)
        if os.path.isfile(full_path):
            shutil.copy(full_path, dropboxpath)


clean()
build_render()
build_windows_full()
build_android_full()
build_mac_full()
# build_web_full()
upload()
copy_dropbox()
print('\n[Build done]')
