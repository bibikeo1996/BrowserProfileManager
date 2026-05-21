import os
import sys

DEFAULT_BROWSER = "Chrome"
DEFAULT_PROFILE_NAME = "GoogleFlow"

def _find_windows_executable(subpaths: list) -> str:
    prefixes = [
        os.environ.get("ProgramFiles", r"C:\Program Files"),
        os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
        os.environ.get("LOCALAPPDATA", os.path.expanduser(r"~\AppData\Local"))
    ]
    for prefix in prefixes:
        for subpath in subpaths:
            full_path = os.path.join(prefix, subpath)
            if os.path.exists(full_path):
                return full_path
    return os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), subpaths[0])

if sys.platform == "win32":
    BROWSER_PATHS = {
        "Chrome": os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data Automation"),
        "Brave": os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data"),
        "Firefox": os.path.expandvars(r"%APPDATA%\Mozilla\Firefox\Profiles")
    }
    SYSTEM_DEFAULT_PATHS = {
        "Chrome": os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data"),
        "Brave": os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data"),
        "Firefox": os.path.expandvars(r"%APPDATA%\Mozilla\Firefox\Profiles")
    }
    EXECUTABLE_PATHS = {
        "Chrome": _find_windows_executable([r"Google\Chrome\Application\chrome.exe"]),
        "Brave": _find_windows_executable([r"BraveSoftware\Brave-Browser\Application\brave.exe"]),
        "Firefox": _find_windows_executable([r"Mozilla Firefox\firefox.exe"])
    }
else:
    # Default to macOS
    BROWSER_PATHS = {
        "Brave": os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser Automation"),
        "Chrome": os.path.expanduser("~/Library/Application Support/Google/Chrome Automation"),
        "Firefox": os.path.expanduser("~/Library/Application Support/Firefox")
    }
    SYSTEM_DEFAULT_PATHS = {
        "Brave": os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser"),
        "Chrome": os.path.expanduser("~/Library/Application Support/Google/Chrome"),
        "Firefox": os.path.expanduser("~/Library/Application Support/Firefox")
    }
    EXECUTABLE_PATHS = {
        "Brave": "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        "Chrome": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "Firefox": "/Applications/Firefox.app/Contents/MacOS/firefox"
    }
