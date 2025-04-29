# builds unity webgl build and uploads it to itch
# you'll need an itch.io butler for this
# https://itch.io/docs/butler/login.html
  
import os
import subprocess
import time
import logging
from logging import handlers
import colorlog
from git import Repo
from git.exc import InvalidGitRepositoryError
from io import StringIO

log_buffers = {}  # repo_path -> StringIO

BUTLER_EXECUTABLE = './butler'  # Path to the butler executable (assuming you're running the script from the butler directory)
                                # you can read about butler here https://itch.io/docs/butler/login.html

CHECK_INTERVAL = 60  # Time in seconds to wait before checking for new commits

# List of project configurations
CONFIGS = [
    {
        "BRANCH": 'origin/main',
        "REPO_PATH": 'C:\\_Work\\RedBall',
        "UNITY_EXECUTABLE": '"C:\\Program Files\\Unity\\Hub\\Editor\\6000.1.0f1\\Editor\\Unity.exe"',
        "BUILD_PATH": 'C:\\_Work\\RedBall\\androidBuild',
        "UNITY_BUILD_METHOD": "AndroidBuilder.Build",
        "BUILD_TARGET": "Android",
        "FORCE": True,
        "UPLOAD":False,
    },
    {
        "BRANCH": 'origin/main',
        "REPO_PATH": 'C:\\_Work\\PaperShooter',
        "ITCH_PROJECT": 'sangheli/papershooter:webgl',
        "UNITY_EXECUTABLE": '"C:\\Program Files\\Unity\\Hub\\Editor\\6000.1.0f1\\Editor\\Unity.exe"',
        "BUILD_PATH": 'C:\\_Work\\PaperShooter\\webgl_build',
        "UNITY_BUILD_METHOD": "WebGLBuilder.Build",
        "BUILD_TARGET": "WebGL",
        "FORCE": True,
    },
    {
        "BRANCH": 'origin/update3',
        "REPO_PATH": 'C:\\_Work\\HellDigger-Web',
        "ITCH_PROJECT": 'sangheli/ld57helldiggeridle:webgl',
        "UNITY_EXECUTABLE": '"C:\\Program Files\\Unity\\Hub\\Editor\\6000.1.0f1\\Editor\\Unity.exe"',
        "BUILD_PATH": 'C:\\_Work\\HellDigger-Web\\webgl_build',
        "UNITY_BUILD_METHOD": "WebGLBuilder.Build",
        "BUILD_TARGET": "WebGL",
        "FORCE": True,
    },
    {
        "BRANCH": 'origin/stachka2025',
        "REPO_PATH": 'C:\\_Work\\minitank-web',
        "ITCH_PROJECT": 'sangheli/minitankdesertstrikedemo1:webgl',
        "UNITY_EXECUTABLE": '"C:\\Program Files\\Unity\\Hub\\Editor\\6000.1.0f1\\Editor\\Unity.exe"',
        "BUILD_PATH": 'C:\\_Work\\minitank-web\\webgl_build',
        "UNITY_BUILD_METHOD": "WebGLBuilder.Build",
        "BUILD_TARGET": "WebGL",
        "FORCE": False,
    },
    {
        "BRANCH": 'origin/main',
        "REPO_PATH": 'C:\\_Work\\sibjam2025-web',
        "ITCH_PROJECT": 'sangheli/sibjam2025:webgl',
        "UNITY_EXECUTABLE": '"C:\\Program Files\\Unity\\Hub\\Editor\\6000.1.0f1\\Editor\\Unity.exe"',
        "BUILD_PATH": 'C:\\_Work\\sibjam2025-web\\webgl_build',
        "UNITY_BUILD_METHOD": "WebGLBuilder.Build",
        "BUILD_TARGET": "WebGL",
        "FORCE": False,
    },
]

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

def build_unity_project(config, log):
    """Triggers a headless WebGL build for the Unity project."""
    try:
        # Build the single command string as you would run it in the terminal
        unity_command = (
        # f'sudo '
            f'{config["UNITY_EXECUTABLE"]} -batchmode -nographics -quit '
            f'-projectPath "{config["REPO_PATH"]}" '
            f'-executeMethod {config["UNITY_BUILD_METHOD"]} '
            f'-buildTarget "{config["BUILD_TARGET"]}" '
            f'-output "{config["BUILD_PATH"]}"'
        )
        log.info(f"'{config["REPO_PATH"]}' Starting Unity build...")
        subprocess.run(unity_command, shell=True, check=True)
        log.info(f"'{config["REPO_PATH"]}' Unity build completed successfully.")

        # # Upload build to Itch.io using Butler
        if config.get("UPLOAD", False):
            log.info(f"'{config["REPO_PATH"]}' Uploading build to Itch.io...")
            subprocess.run([
                BUTLER_EXECUTABLE,
                'push',
                config["BUILD_PATH"],
                config["ITCH_PROJECT"]
            ], check=True)
            log.info(f"'{config["REPO_PATH"]}' Build uploaded to Itch.io successfully.")

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

def main():
    last_commit_hashes = {}

    loggers = {}
    for config in CONFIGS:
        log = setup_logger(config["REPO_PATH"])
        loggers[config["REPO_PATH"]] = log
        initial_hash = record_init_commit_hash(config, log)
        if initial_hash is None:
            log.warning(f"'{config["REPO_PATH"]}' Skipping project due to invalid git repository.")
            continue
        last_commit_hashes[config["REPO_PATH"]] = initial_hash

    forced_built = set()

    while True:
        for config in CONFIGS:
            log = loggers[config["REPO_PATH"]]
            if config["REPO_PATH"] not in last_commit_hashes:
                continue

            log.info(f"'{config["REPO_PATH"]}' Checking for new commits...")

            try:
                pull_latest_changes(config["REPO_PATH"], config["BRANCH"], log)
                current_commit_hash = get_latest_commit_hash(config["REPO_PATH"], log)
                if current_commit_hash is None:
                    log.warning(f"'{config["REPO_PATH"]}' Skipping project due to invalid git repository.")
                    continue

                should_force = config.get("FORCE", False) and config["REPO_PATH"] not in forced_built

                if should_force:
                    log.info(f"'{config["REPO_PATH"]}' Forced build triggered.")
                    build_unity_project(config, log)
                    last_commit_hashes[config["REPO_PATH"]] = current_commit_hash
                    forced_built.add(config["REPO_PATH"])
                elif current_commit_hash != last_commit_hashes[config["REPO_PATH"]]:
                    log.info(f"'{config["REPO_PATH"]}' New commit detected: {current_commit_hash}")
                    last_commit_hashes[config["REPO_PATH"]] = current_commit_hash
                    build_unity_project(config, log)
                else:
                    log.info(f"'{config["REPO_PATH"]}' No new commits found.")

            except Exception as e:
                log.error(f"Error while processing project: {e}")

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
