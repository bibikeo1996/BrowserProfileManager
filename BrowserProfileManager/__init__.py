from .Config.Settings import DEFAULT_BROWSER, DEFAULT_PROFILE_NAME, AUTOMATION_PROFILES_DIR
from .Utils.BrowserLauncher import BrowserLauncher, ForceKillBrowser
from .Utils.Session import BrowserSession
from .Utils.CDPEmulator import CDPEmulator
from .Setup import setup_automation_profile

__version__ = "0.4.0"

__all__ = [
    'DEFAULT_BROWSER', 'DEFAULT_PROFILE_NAME', 'AUTOMATION_PROFILES_DIR',
    'setup_automation_profile', 'BrowserLauncher', 'BrowserSession',
    'CDPEmulator', 'ForceKillBrowser',
    'ProfileManager', 'ManagedProfile', 'ManagedTab'
]

from .Manager import ProfileManager, ManagedProfile, ManagedTab
