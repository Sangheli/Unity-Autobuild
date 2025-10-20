# List of project configurations

ENV = {
    "ITCH_PROJECT": 'sangheli/pay-or-die',
    "BRANCH": 'origin/main',
    "REPO_PATH": 'C:\\_Work\\PayOrDie',
    "UNITY_EXECUTABLE": '"C:\\Program Files\\Unity\\Hub\\Editor\\6000.2.6f2\\Editor\\Unity.exe"',
    "FORCE_BUILD_GIT": True, # skip git listen on first build
    "UPLOAD_TO_ITCH": True,
    "TELEGRAM_BOT_TOKEN": "",
    "TELEGRAM_CHAT_ID": "",
    "DROPBOX_PATH": "C:\\Dropbox\\Public",
}

CONFIGS = [
    {
        "BUILD_PATH": 'webgl_build',
        "ITCH_TARGET": 'webgl',
        "BUILD_TARGET": "WebGL",
        "NO_GIT": True,
    },
    {
        "BUILD_PATH": 'pc_build',
        "ITCH_TARGET": 'win',
        "BUILD_TARGET": "Win64",
        "NO_GIT": True,
        "ZIP_BEFORE_UPLOAD": True,
    },
    {
        "BUILD_PATH": 'mac_build',
        "ITCH_TARGET": 'mac',
        "BUILD_TARGET": "OSX",
        "NO_GIT": True,
        "ZIP_BEFORE_UPLOAD": True,
    },
    {
        "BUILD_PATH": 'androidBuild',
        "ITCH_TARGET": 'android',
        "BUILD_TARGET": "Android",
        "NO_GIT": True,
    },
    {
        "BUILD_PATH": 'linux_build',
        "ITCH_TARGET": 'linux',
        "BUILD_TARGET": "Linux64",
        "NO_GIT": True,
        "ZIP_BEFORE_UPLOAD": True,
    },
    # {
    #     "BUILD_PATH": 'androidBuild', # sub path inside unity project folder
    #     "ITCH_PROJECT": 'android',  # itch prefix for build
    #     "BUILD_TARGET": "Android", # unity build target
    #     "NO_GIT": True, # build once, didnt listen git pushes
    #     "ZIP_BEFORE_UPLOAD": False,
    #     "ZIP_METHOD": "zip",  # zip или 7z
    #     "UPLOAD_TELEGRAM": False,
    #     "UPLOAD_DROPBOX": False,
    # },
]