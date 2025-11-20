import platform

# Path to the butler executable (assuming you're running the script from the butler directory)
# you can read about butler here https://itch.io/docs/butler/login.html

def get():
    PLATFORM = platform.system()

    if PLATFORM == "Windows":
       return './butler.exe'
    elif PLATFORM == "Linux":
        return './butler'
    elif PLATFORM == "Darwin":  # macOS
        return './butler'
    else:
        raise Exception(f"Unknown platform: {PLATFORM}")