# builds unity webgl build and uploads it to itch
# you'll need an itch.io butler for this
# https://itch.io/docs/butler/login.html
  
import os
import subprocess
import time
import logging
from logging import handlers
import colorlog
import requests
from git import Repo
from git.exc import InvalidGitRepositoryError
from io import StringIO
import shutil
import Config

log_buffers = {}  # repo_path -> StringIO

BUTLER_EXECUTABLE = './butler'  # Path to the butler executable (assuming you're running the script from the butler directory)
                                # you can read about butler here https://itch.io/docs/butler/login.html

CHECK_INTERVAL = 60  # Time in seconds to wait before checking for new commits


def zip_build_folder(build_folder, log, method="zip"):
    zip_path = f"{build_folder}.{'7z' if method == '7z' else 'zip'}"
    log.info(f"Creating {method} archive: {zip_path}")

    # Удаляем старый архив, если он уже есть
    if os.path.exists(zip_path):
        os.remove(zip_path)

    # Архивируем (make_archive возвращает путь к архиву)
    if method == "zip":
        shutil.make_archive(build_folder, 'zip', build_folder)
    else:
        # Используем 7z (требуется установленный 7z)
        path_7z = 'C:\\Program Files\\7-Zip\\'
        current_dir = os.getcwd()
        os.chdir(path_7z)
        os.system(f'7z.exe a {zip_path} {build_folder} -mx9 -v49m')
        os.chdir(current_dir)

    log.info(f"{method.upper()} archive created: {zip_path}")
    return zip_path


def upload_to_telegram(file_path, token, chat_id, log):
    url = f'https://api.telegram.org/bot{token}/sendDocument'
    with open(file_path, 'rb') as file:
        files = {'document': file}
        params = {'chat_id': chat_id}
        response = requests.post(url, params=params, files=files)
        log.info(f"Uploaded to Telegram: {file_path} | Response: {response.json()}")


def copy_to_dropbox(file_path, dropbox_path, log):
    if not os.path.exists(dropbox_path):
        os.makedirs(dropbox_path)
    shutil.copy(file_path, dropbox_path)
    log.info(f"Copied to Dropbox: {file_path}")


def extract_git_history(repo_path, hash, log):
    os.chdir(repo_path)
    full_log = subprocess.getoutput('git log --oneline HEAD').split('\n')
    extracted = []
    for x in full_log:
        extracted.append("* " + x[9:])
        if hash in x:
            extracted.append("\n[Old history]\n")
    log_file = os.path.join(repo_path, f'patchnote_{time.strftime("%Y_%m_%d_%H_%M_%S")}.txt')
    with open(log_file, 'w') as f:
        f.write("\n".join(extracted))
    log.info(f"Git history saved: {log_file}")
    return log_file


# Setup per-project loggers
def setup_logger(repo_path):
    project_name = os.path.basename(repo_path.strip("\\/"))
    logger = logging.getLogger(project_name)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    color_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    )

    # File handler
    log_file = f'{project_name}.log'
    fh = handlers.RotatingFileHandler(log_file, maxBytes=5_000_000, backupCount=2)
    fh.setFormatter(formatter)

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(color_formatter)

    # Avoid duplicate handlers
    buffer = StringIO()
    bh = logging.StreamHandler(buffer)
    bh.setFormatter(formatter)
    log_buffers[repo_path] = buffer

    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)
        logger.addHandler(bh)

    return logger

def get_latest_commit_hash(repo_path, log):
    try:
        repo = Repo(repo_path)
        return repo.head.commit.hexsha
    except InvalidGitRepositoryError:
        log.error(f"'{repo_path}' is not a valid Git repository. Skipping.")
        return None

def pull_latest_changes(repo_path, branch, log):
    try:
        repo = Repo(repo_path)
        repo.git.checkout(branch.split('/')[-1])
        origin = repo.remotes.origin
        origin.pull()
    except Exception as e:
        log.warning(f"'{repo_path}' Failed to pull latest changes: {e}")

def get_build_path_to_push(config, log):
    build_path_to_push = config["BUILD_PATH"]
    if config["BUILD_TARGET"].lower() == "android":
        apk_files = [f for f in os.listdir(build_path_to_push) if f.endswith(".apk")]
        if not apk_files:
            log.warning(f"'{config["REPO_PATH"]}' No APK files found in build path: {build_path_to_push}")
            return
        # Для простоты выгружаем первый найденный APK (или можно все перебрать в цикле)
        build_path_to_push = os.path.join(build_path_to_push, apk_files[0])
        log.info(f"'{config["REPO_PATH"]}' Found APK to upload: {build_path_to_push}")

    return build_path_to_push

def build_unity_project(config, log):
    """Triggers a headless WebGL build for the Unity project."""
    try:
        # Build the single command string as you would run it in the terminal
        unity_command = (
        # f'sudo '
            f'{config["UNITY_EXECUTABLE"]} -batchmode -nographics -quit '
            f'-projectPath "{config["REPO_PATH"]}" '
            f'-executeMethod {config["UNITY_BUILD_METHOD"]} '
            f'-buildTarget {config["BUILD_TARGET"]} '
            f'-output "{config["BUILD_PATH"]}"'
        )
        log.info(f"'{config["REPO_PATH"]}' Starting Unity build...")
        subprocess.run(unity_command, shell=True, check=True)
        log.info(f"'{config["REPO_PATH"]}' Unity build completed successfully.")

        # # Upload build to Itch.io using Butler
        if not config.get("NO_GIT", False):
            hash = get_latest_commit_hash(config["REPO_PATH"], log)
            history_file = extract_git_history(config["REPO_PATH"], hash, log)
        else:
            history_file = None

        build_path_to_push = get_build_path_to_push(config, log)
        if config.get("ZIP_BEFORE_UPLOAD", False):
            build_path_to_push = zip_build_folder(build_path_to_push, log, config.get("ZIP_METHOD", "zip"))

        if config.get("UPLOAD", False):
            log.info(f"'{config["REPO_PATH"]}' Uploading build to Itch.io...")
            subprocess.run([
                BUTLER_EXECUTABLE,
                'push',
                build_path_to_push,
                config["ITCH_PROJECT"]
            ], check=True)
            log.info(f"'{config["REPO_PATH"]}' Build uploaded to Itch.io successfully.")

        if config.get("UPLOAD_TELEGRAM", False):
            upload_to_telegram(build_path_to_push, config["TELEGRAM_BOT_TOKEN"], config["TELEGRAM_CHAT_ID"], log)
            if history_file:
                upload_to_telegram(history_file, config["TELEGRAM_BOT_TOKEN"], config["TELEGRAM_CHAT_ID"], log)

        if config.get("UPLOAD_DROPBOX", False):
            copy_to_dropbox(build_path_to_push, config["DROPBOX_PATH"], log)
            if history_file:
                copy_to_dropbox(history_file, config["DROPBOX_PATH"], log)

        log.info(f"'{config["REPO_PATH"]}' Build done.")

    except subprocess.CalledProcessError as e:
        log.error(f"'{config["REPO_PATH"]}' Unity build or upload failed: {e}")

def ensure_build_path_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

def record_init_commit_hash(config, log):
    ensure_build_path_exists(config["BUILD_PATH"])
    commit_hash = get_latest_commit_hash(config["REPO_PATH"], log)
    if commit_hash:
        log.info(f"'{config["REPO_PATH"]}' Initial commit hash: {commit_hash}")
    return commit_hash

def check_butler_login():
    try:
        subprocess.run([BUTLER_EXECUTABLE, 'whoami'], check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("Butler is not logged in. Run `butler login` manually.")
        exit(1)


def build_project_always(config, log):
    log.info(f"'{config['REPO_PATH']}' NO_GIT flag is set. Building project directly.")
    build_unity_project(config, log)


def build_project_on_commit_change(config, log, last_commit_hashes, forced_built):
    repo_path = config["REPO_PATH"]

    log.info(f"'{repo_path}' Checking for new commits...")

    try:
        pull_latest_changes(repo_path, config["BRANCH"], log)
        current_commit_hash = get_latest_commit_hash(repo_path, log)
        if current_commit_hash is None:
            log.warning(f"'{repo_path}' Skipping project due to invalid git repository.")
            return

        should_force = config.get("FORCE", False) and repo_path not in forced_built

        if should_force:
            log.info(f"'{repo_path}' Forced build triggered.")
            build_unity_project(config, log)
            last_commit_hashes[repo_path] = current_commit_hash
            forced_built.add(repo_path)
        elif current_commit_hash != last_commit_hashes[repo_path]:
            log.info(f"'{repo_path}' New commit detected: {current_commit_hash}")
            last_commit_hashes[repo_path] = current_commit_hash
            build_unity_project(config, log)
        else:
            log.info(f"'{repo_path}' No new commits found.")

    except Exception as e:
        log.error(f"Error while processing project: {e}")


def init_loggers_and_hashes():
    loggers = {}
    last_commit_hashes = {}

    for config in Config.CONFIGS:
        repo_path = config["REPO_PATH"]
        log = setup_logger(repo_path)
        loggers[repo_path] = log

        if config.get("NO_GIT", False):
            log.info(f"'{repo_path}' NO_GIT flag is enabled. Will only build, skipping git.")
            continue

        initial_hash = record_init_commit_hash(config, log)
        if initial_hash is None:
            log.warning(f"'{repo_path}' Skipping project due to invalid git repository.")
            continue

        last_commit_hashes[repo_path] = initial_hash

    return loggers, last_commit_hashes


def main():
    loggers, last_commit_hashes = init_loggers_and_hashes()
    forced_built = set()

    # Отдельно собрать NO_GIT-конфиги и удалить их из общего списка
    no_git_configs = [config for config in Config.CONFIGS if config.get("NO_GIT", False)]
    git_configs = [config for config in Config.CONFIGS if not config.get("NO_GIT", False)]

    # Сначала выполнить билд для NO_GIT-конфигов
    for config in no_git_configs:
        repo_path = config["REPO_PATH"]
        log = loggers[repo_path]
        build_project_always(config, log)

    # Теперь работать только с git-конфигами в цикле
    while True:
        for config in git_configs:
            repo_path = config["REPO_PATH"]
            log = loggers[repo_path]
            if repo_path not in last_commit_hashes:
                continue
            build_project_on_commit_change(config, log, last_commit_hashes, forced_built)

        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    main()

#
# you will also need to implement a build script inside of unity, you can start with this one
#
# public class WebGLBuilder
# {
#    [MenuItem("Build/Build WebGL")]
#    public static void Build()
#    {
#        string[] scenes =
#        {
#            "Assets/main.unity",
#        };
#
#        PlayerSettings.defaultWebScreenWidth = 1340;
#        PlayerSettings.defaultWebScreenHeight = 710;
#
#        BuildPlayerOptions buildPlayerOptions = new BuildPlayerOptions();
#        buildPlayerOptions.scenes = scenes;
#        buildPlayerOptions.locationPathName = "webgl_build";
#        buildPlayerOptions.target = BuildTarget.WebGL;
#        buildPlayerOptions.options = BuildOptions.None;
#
#        BuildPipeline.BuildPlayer(scenes, "webgl_build", BuildTarget.WebGL, BuildOptions.None);
#    }
# }
