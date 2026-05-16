from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ProfileInfo:
    """Class representing a single browser profile."""
    profile_id: str             # e.g., 'Default', 'Profile 1'
    name: str                   # e.g., 'Personal', 'Work'
    path: str                   # Absolute path to the profile directory
    avatar_url: Optional[str] = None
    is_default: bool = False

@dataclass
class BrowserScanResult:
    """Class representing the result of scanning a browser."""
    browser_name: str
    user_data_dir: str
    profiles: List[ProfileInfo]
    is_success: bool = True
    error_message: Optional[str] = None
