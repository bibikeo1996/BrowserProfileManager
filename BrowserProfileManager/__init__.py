from .Config.Settings import DEFAULT_BROWSER, BROWSER_PATHS, DEFAULT_PROFILE_NAME
from .Scanners.BrowserScanner import BrowserScanner
from .Utils.BrowserLauncher import BrowserLauncher, ForceKillBrowser
from .Utils.Session import BrowserSession
from .Utils.CDPEmulator import CDPEmulator
from .Models.ProfileModel import ProfileInfo, BrowserScanResult

__version__ = "0.3.0"

def GetAllProfiles(browser_name: str = DEFAULT_BROWSER) -> list:
    """Helper API to quickly scan and return all available profiles for a browser."""
    from .Config.Settings import SYSTEM_DEFAULT_PATHS
    default_dir = SYSTEM_DEFAULT_PATHS.get(browser_name)
    user_data_dir = BROWSER_PATHS.get(browser_name)
    
    # Try default directory first to get original profiles
    if default_dir:
        scanner = BrowserScanner(browser_name, default_dir)
        result = scanner.scan()
        if result.is_success and result.profiles:
            return result.profiles
            
    # Fallback to scanning the automation directory
    if user_data_dir:
        scanner = BrowserScanner(browser_name, user_data_dir)
        result = scanner.scan()
        if result.is_success:
            return result.profiles
            
    raise RuntimeError(f"Failed to scan {browser_name} profiles.")

__all__ = [
    'DEFAULT_BROWSER', 'BROWSER_PATHS', 'DEFAULT_PROFILE_NAME',
    'BrowserScanner', 'BrowserLauncher', 'BrowserSession', 'ProfileInfo', 'BrowserScanResult',
    'GetAllProfiles', 'CDPEmulator', 'ForceKillBrowser',
    'ProfileManager', 'ManagedProfile', 'ManagedTab'
]

from .Manager import ProfileManager, ManagedProfile, ManagedTab
