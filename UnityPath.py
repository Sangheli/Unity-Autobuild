import platform
import os

def get_unity_path(env):
    PLATFORM = platform.system()

    if PLATFORM == "Windows":
        path = os.path.join(env["UNITY_EXECUTABLE_WINDOWS"], "Editor", env["UNITY_VERSION"], "Editor", "Unity.exe")
    elif PLATFORM == "Linux":
        path = os.path.join(env["UNITY_EXECUTABLE_LINUX"], "Editor", env["UNITY_VERSION"], "Editor", "Unity")
    elif PLATFORM == "Darwin":  # macOS
        path = os.path.join(env["UNITY_EXECUTABLE_MAC"], "Editor", env["UNITY_VERSION"], "Editor", "Unity.app")
    else:
        raise Exception(f"Unknown platform: {PLATFORM}")

    return f'"{path}"'
