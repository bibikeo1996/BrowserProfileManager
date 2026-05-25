import os
import sys

DEFAULT_BROWSER = "Chrome"
DEFAULT_PROFILE_NAME = "GoogleFlow"
AUTOMATION_PROFILES_DIR = os.path.join(os.getcwd(), ".automation_profiles")

if sys.platform == "win32":
    BROWSER_PATHS = {
        "Chrome": os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data"),
        "Brave": os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data"),
        "Firefox": os.path.expandvars(r"%APPDATA%\Mozilla\Firefox\Profiles")
    }
    EXECUTABLE_PATHS = {
        "Chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "Brave": r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        "Firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe"
    }
else:
    # Default to macOS
    BROWSER_PATHS = {
        "Brave": os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser"),
        "Chrome": os.path.expanduser("~/Library/Application Support/Google/Chrome"),
        "Firefox": os.path.expanduser("~/Library/Application Support/Firefox")
    }
    EXECUTABLE_PATHS = {
        "Brave": "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        "Chrome": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "Firefox": "/Applications/Firefox.app/Contents/MacOS/firefox"
    }
