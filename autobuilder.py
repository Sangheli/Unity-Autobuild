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
from Configs import ConfigPayOrDie as Config
import UnityPath
import ButlerPath

log_buffers = {}  # repo_path -> StringIO

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
        seven = shutil.which('7z') or shutil.which('7za') or r'C:\Program Files\7-Zip\7z.exe'
        if not seven or not os.path.exists(seven):
            raise FileNotFoundError("7z executable not found. Install 7-Zip or put 7z in PATH.")
        cmd = [seven, 'a', zip_path, build_folder, '-mx9', '-v49m']
        subprocess.run(cmd, check=True)

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
def setup_logger(repo_path, build_target):
    project_name = os.path.basename(repo_path.strip("\\/"))
    logger = logging.getLogger(f"{project_name}_{build_target}")
    logger.setLevel(logging.INFO)

    # Добавляем фильтр, который вставляет платформу в каждое сообщение
    class PlatformFilter(logging.Filter):
        def filter(self, record):
            record.msg = f"[{build_target}] {record.msg}"
            return True

    logger.addFilter(PlatformFilter())

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
    log_file = os.path.join("log", f'{project_name}_{build_target}.log')
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

def get_build_path_to_push(config, env, log):
    build_path_to_push = os.path.join(str(env["REPO_PATH"]), str(config["BUILD_PATH"]))

    if config["BUILD_TARGET"].lower() == "android":
        apk_files = [f for f in os.listdir(build_path_to_push) if f.endswith(".apk")]
        if not apk_files:
            log.warning(f"'{env['REPO_PATH']}' No APK files found in build path: {build_path_to_push}")
            return
        # Для простоты выгружаем первый найденный APK (или можно все перебрать в цикле)
        build_path_to_push = os.path.join(build_path_to_push, apk_files[0])
        log.info(f"'{env['REPO_PATH']}' Found APK to upload: {build_path_to_push}")

    return build_path_to_push

def upload_itch(config, env,log, build_path_to_push):
    if not env.get("UPLOAD_TO_ITCH", False):
        log.info("UPLOAD flag is False, skipping itch upload.")
        return

    log.info(f"'{env['REPO_PATH']}' Uploading build to Itch.io...")
    subprocess.run([
        ButlerPath.get(),
        'push',
        build_path_to_push,
        f"{env['ITCH_PROJECT']}:{config['ITCH_TARGET']}"
    ], check=True)
    log.info(f"'{env['REPO_PATH']}' Build uploaded to Itch.io successfully.")

def upload_tg(config,env,log, build_path_to_push, history_file):
    if config.get("UPLOAD_TELEGRAM", False):
        upload_to_telegram(build_path_to_push, env.get("TELEGRAM_BOT_TOKEN", ""), env.get("TELEGRAM_CHAT_ID", ""), log)
        if history_file:
            upload_to_telegram(history_file, env.get("TELEGRAM_BOT_TOKEN", ""), env.get("TELEGRAM_CHAT_ID", ""), log)

def upload_dropbox(config,env, log, build_path_to_push, history_file):
    if config.get("UPLOAD_DROPBOX", False):
        copy_to_dropbox(build_path_to_push, env.get("DROPBOX_PATH", ""), log)
        if history_file:
            copy_to_dropbox(history_file, env.get("DROPBOX_PATH", ""), log)

def try_zip(config,env, log):
    build_path_to_push = get_build_path_to_push(config, env, log)
    if config.get("ZIP_BEFORE_UPLOAD", False):
        try:
            method = config.get("ZIP_METHOD", "zip")
            build_path_to_push = zip_build_folder(build_path_to_push, log, method)
        except Exception as e:
            log.error(f"Failed to create archive: {e}")
            return None

    return build_path_to_push

def get_history_file(config,env, log):
    if config.get("NO_GIT", False):
        return None

    hash = get_latest_commit_hash(env["REPO_PATH"], log)
    return extract_git_history(env["REPO_PATH"], hash, log)

def get_unity_build_command(config, env, ENV_UNITY):
    # Build the single command string as you would run it in the terminal

    unity_path = UnityPath.get(ENV_UNITY)
    return (
        # f'sudo '
        f'{unity_path} -batchmode -nographics -quit '
        f'-projectPath "{env["REPO_PATH"]}" '
        f'-executeMethod Builder.Build '
        f'-buildTarget {config["BUILD_TARGET"]} '
        f'-output "{f"{os.path.join(str(env["REPO_PATH"]), str(config["BUILD_PATH"]))}"}"'
    )


# Глобальный список для сбора всех ошибок
ALL_ERRORS = []

def build_unity_project(config, env, ENV_UNITY, log):
    try:
        log.info(f"'{env['REPO_PATH']}' Starting Unity build...")
        cmd = get_unity_build_command(config, env, ENV_UNITY)
        subprocess.run(cmd, shell=True, check=True)
        log.info(f"'{env['REPO_PATH']}' Unity build completed successfully.")

        history_file = get_history_file(config, env, log)
        build_path_to_push = try_zip(config, env, log)
        if not build_path_to_push:
            log.warning(f"'{env['REPO_PATH']}' Nothing to upload after build.")
            return

        upload_itch(config, env, log, build_path_to_push)
        upload_tg(config, env, log, build_path_to_push, history_file)
        upload_dropbox(config, env, log, build_path_to_push, history_file)
        log.info(f"'{env['REPO_PATH']}' Build done.")

    except subprocess.CalledProcessError as e:
        msg = f"'{env['REPO_PATH']}' Unity build or upload failed: {e}"
        log.error(msg)
        ALL_ERRORS.append(msg)
    except Exception as e:
        msg = f"Unexpected error during build for '{env['REPO_PATH']}': {e}"
        log.exception(msg)
        ALL_ERRORS.append(msg)


def ensure_build_path_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

def record_init_commit_hash(config,env, log):
    build_path = os.path.join(env['REPO_PATH'], config['BUILD_PATH'])
    ensure_build_path_exists(build_path)
    commit_hash = get_latest_commit_hash(env["REPO_PATH"], log)
    if commit_hash:
        log.info(f"'{env['REPO_PATH']}' Initial commit hash: {commit_hash}")
    return commit_hash

def check_butler_login():
    try:
        subprocess.run([ButlerPath.get(), 'whoami'], check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("Butler is not logged in. Run `butler login` manually.")
        exit(1)


def build_project_always(config, env, ENV_UNITY, log):
    log.info(f"'{env['REPO_PATH']}' NO_GIT flag is set. Building project directly.")
    build_unity_project(config, env, ENV_UNITY, log)


def build_project_on_commit_change(config,env, ENV_UNITY, log, last_commit_hashes, forced_built):
    repo_path = env["REPO_PATH"]

    log.info(f"'{repo_path}' Checking for new commits...")

    try:
        pull_latest_changes(repo_path, env["BRANCH"], log)
        current_commit_hash = get_latest_commit_hash(repo_path, log)
        if current_commit_hash is None:
            log.warning(f"'{repo_path}' Skipping project due to invalid git repository.")
            return

        should_force = env.get("FORCE_BUILD_GIT", False) and repo_path not in forced_built

        if should_force:
            log.info(f"'{repo_path}' Forced build triggered.")
            build_unity_project(config,env, ENV_UNITY, log)
            last_commit_hashes[repo_path] = current_commit_hash
            forced_built.add(repo_path)
        elif current_commit_hash != last_commit_hashes[repo_path]:
            log.info(f"'{repo_path}' New commit detected: {current_commit_hash}")
            last_commit_hashes[repo_path] = current_commit_hash
            build_unity_project(config,env, ENV_UNITY, log)
        else:
            log.info(f"'{repo_path}' No new commits found.")

    except Exception as e:
        log.error(f"Error while processing project: {e}")


def init_loggers_and_hashes():
    loggers = {}
    last_commit_hashes = {}

    for config in Config.CONFIGS:
        repo_path = Config.ENV["REPO_PATH"]
        build_target = config.get("BUILD_TARGET", "Unknown")
        log = setup_logger(repo_path, build_target)
        loggers[repo_path] = log

        if config.get("NO_GIT", False):
            log.info(f"'{repo_path}' NO_GIT flag is enabled. Will only build, skipping git.")
            continue

        initial_hash = record_init_commit_hash(config, Config.ENV, log)
        if initial_hash is None:
            log.warning(f"'{repo_path}' Skipping project due to invalid git repository.")
            continue

        last_commit_hashes[repo_path] = initial_hash

    return loggers, last_commit_hashes


def execute_no_git(loggers):
    # Отдельно собрать NO_GIT-конфиги и удалить их из общего списка
    no_git_configs = [config for config in Config.CONFIGS if config.get("NO_GIT", False)]

    # Сначала выполнить билд для NO_GIT-конфигов
    for config in no_git_configs:
        repo_path = Config.ENV["REPO_PATH"]
        log = loggers[repo_path]
        build_project_always(config, Config.ENV, Config.ENV_UNITY, log)

    if no_git_configs:
        # После завершения всех NO_GIT сборок
        for config in no_git_configs:
            repo_path = Config.ENV["REPO_PATH"]
            log = loggers[repo_path]
            log.info(f"All NO_GIT builds completed successfully.")


def main():
    ensure_build_path_exists("log")
    loggers, last_commit_hashes = init_loggers_and_hashes()
    forced_built = set()

    execute_no_git(loggers)

    # После выполнения всех no_git билдов вывести общий лог
    if ALL_ERRORS:
        print("\n========== ⚠️ BUILD ERRORS SUMMARY ⚠️ ==========")
        for err in ALL_ERRORS:
            print(err)
        print("===============================================\n")
    else:
        print("\n✅ All NO_GIT builds completed without errors.\n")

    git_configs = [config for config in Config.CONFIGS if not config.get("NO_GIT", False)]
    # Теперь работать только с git-конфигами в цикле
    while True:
        for config in git_configs:
            repo_path = Config.ENV["REPO_PATH"]
            log = loggers[repo_path]
            if repo_path not in last_commit_hashes:
                continue
            build_project_on_commit_change(config, Config.ENV, Config.ENV_UNITY, log, last_commit_hashes, forced_built)

        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    main()