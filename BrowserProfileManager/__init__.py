from .Config.Settings import DEFAULT_BROWSER, BROWSER_PATHS, DEFAULT_PROFILE_NAME
from .Scanners.BrowserScanner import BrowserScanner
from .Utils.BrowserLauncher import BrowserLauncher, ForceKillBrowser
from .Utils.Session import BrowserSession
from .Utils.CDPEmulator import CDPEmulator
from .Models.ProfileModel import ProfileInfo, BrowserScanResult

__version__ = "0.3.0"

def GetAllProfiles(browser_name: str = DEFAULT_BROWSER) -> list:
    """Helper API to quickly scan and return all available profiles for a browser."""
    user_data_dir = BROWSER_PATHS.get(browser_name)
    if not user_data_dir:
        raise ValueError(f"Unknown browser: {browser_name}. Supported: {list(BROWSER_PATHS.keys())}")
    scanner = BrowserScanner(browser_name, user_data_dir)
    result = scanner.scan()
    if not result.is_success:
        raise RuntimeError(f"Failed to scan {browser_name} profiles: {result.error_message}")
    return result.profiles

__all__ = [
    'DEFAULT_BROWSER', 'BROWSER_PATHS', 'DEFAULT_PROFILE_NAME',
    'BrowserScanner', 'BrowserLauncher', 'BrowserSession', 'ProfileInfo', 'BrowserScanResult',
    'GetAllProfiles', 'CDPEmulator', 'ForceKillBrowser',
    'ProfileManager', 'ManagedProfile', 'ManagedTab'
]

from .Manager import ProfileManager, ManagedProfile, ManagedTab
