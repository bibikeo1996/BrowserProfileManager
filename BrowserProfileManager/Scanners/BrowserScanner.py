import json
import os
import configparser
import logging
from pathlib import Path
from typing import List, Optional

from BrowserProfileManager.Models.ProfileModel import ProfileInfo, BrowserScanResult

logger = logging.getLogger(__name__)

class BrowserScanner:
    """Scanner to find and parse browser profiles."""

    def __init__(self, browser_name: str, user_data_dir):
        self.browser_name = browser_name
        self.user_data_dir = Path(user_data_dir)

    def scan(self) -> BrowserScanResult:
        """Scan the user data directory for browser profiles."""
        try:
            if not self.user_data_dir.exists() or not self.user_data_dir.is_dir():
                return BrowserScanResult(
                    browser_name=self.browser_name,
                    user_data_dir=str(self.user_data_dir),
                    profiles=[],
                    is_success=False,
                    error_message=f"Directory not found: {self.user_data_dir}"
                )
        except PermissionError:
            return BrowserScanResult(
                browser_name=self.browser_name,
                user_data_dir=str(self.user_data_dir),
                profiles=[],
                is_success=False,
                error_message=f"Permission denied accessing {self.user_data_dir}. You may need to grant Full Disk Access to your Terminal."
            )
        except Exception as e:
            return BrowserScanResult(
                browser_name=self.browser_name,
                user_data_dir=str(self.user_data_dir),
                profiles=[],
                is_success=False,
                error_message=f"Error accessing {self.user_data_dir}: {e}"
            )

        profiles: List[ProfileInfo] = []
        
        if self.browser_name.lower() == "firefox":
            profiles = self._parse_firefox_profiles()
        else:
            # Chromium-based logic (Chrome, Brave, etc.)
            local_state_path = self.user_data_dir / "Local State"
            if local_state_path.exists():
                profiles = self._parse_local_state(local_state_path)
                
            if not profiles:
                profiles = self._scan_directories()

        return BrowserScanResult(
            browser_name=self.browser_name,
            user_data_dir=str(self.user_data_dir),
            profiles=profiles,
            is_success=True
        )

    def _parse_firefox_profiles(self) -> List[ProfileInfo]:
        """Parse profiles from Firefox profiles.ini."""
        profiles = []
        ini_path = self.user_data_dir / "profiles.ini"
        if not ini_path.exists():
            return profiles
            
        try:
            config = configparser.ConfigParser()
            config.read(ini_path)
            
            for section in config.sections():
                if section.startswith("Profile"):
                    name = config[section].get("Name", section)
                    path = config[section].get("Path", "")
                    is_default = config[section].get("Default", "0") == "1"
                    
                    if path:
                        profile_path = self.user_data_dir / path
                        profiles.append(ProfileInfo(
                            profile_id=path,
                            name=name,
                            path=str(profile_path),
                            is_default=is_default
                        ))
        except (configparser.Error, PermissionError, OSError) as e:
            logger.warning("Error parsing Firefox profiles.ini: %s", e)
            
        return profiles

    def _parse_local_state(self, local_state_path: Path) -> List[ProfileInfo]:
        """Parse profiles from Local State JSON file."""
        profiles = []
        try:
            with open(local_state_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            info_cache = data.get("profile", {}).get("info_cache", {})
            for profile_id, info in info_cache.items():
                profile_path = self.user_data_dir / profile_id
                
                name = info.get("name", profile_id)
                avatar_url = info.get("avatar_icon")
                is_default = (profile_id == "Default")
                
                profiles.append(ProfileInfo(
                    profile_id=profile_id,
                    name=name,
                    path=str(profile_path),
                    avatar_url=avatar_url,
                    is_default=is_default
                ))
        except (json.JSONDecodeError, PermissionError, OSError) as e:
            logger.warning("Error parsing Local State: %s", e)
            
        return profiles

    def _scan_directories(self) -> List[ProfileInfo]:
        """Fallback: Scan directories like 'Default', 'Profile 1', etc."""
        profiles = []
        
        try:
            for item in self.user_data_dir.iterdir():
                if item.is_dir():
                    dirname = item.name
                    if dirname == "Default" or dirname.startswith("Profile "):
                        profiles.append(ProfileInfo(
                            profile_id=dirname,
                            name=dirname,
                            path=str(item),
                            is_default=(dirname == "Default")
                        ))
        except (PermissionError, OSError) as e:
            logger.warning("Error scanning profile directories: %s", e)
                    
        return profiles
