from playwright.sync_api import sync_playwright
from .Utils.Session import BrowserSession

class ManagedTab:
    """Represents a specific Tab inside a Profile, identified by a unique ID."""
    def __init__(self, tab_id: str, page):
        self.tab_id = tab_id
        self.page = page

class ManagedProfile:
    """Represents a Profile session containing multiple isolated tabs."""
    def __init__(self, profile_id: str, session: BrowserSession, playwright_instance):
        self.profile_id = profile_id
        self.session = session
        self.p = playwright_instance
        self.tabs = {}
        
        # Initialize default main tab
        main_page = self.session.get_playwright_page(self.p)
        self.tabs["main"] = ManagedTab("main", main_page)
        
    def new_tab(self, tab_id: str) -> ManagedTab:
        """Creates a new isolated tab within this profile with a given ID."""
        if tab_id in self.tabs:
            raise ValueError(f"Tab ID '{tab_id}' already exists in profile '{self.profile_id}'.")
        page = self.session.create_new_tab(self.p)
        tab = ManagedTab(tab_id, page)
        self.tabs[tab_id] = tab
        return tab

    def get_tab(self, tab_id: str = "main") -> ManagedTab:
        """Retrieves a tab by its ID."""
        if tab_id not in self.tabs:
            raise KeyError(f"Tab '{tab_id}' not found in profile '{self.profile_id}'.")
        return self.tabs[tab_id]

    def close(self):
        """Closes all tabs belonging to this profile and detaches the session."""
        self.session.stop()
        self.tabs.clear()

class ProfileManager:
    """
    High-level Facade API for managing multiple profiles and tabs.
    Provides a simple Interface for developers.
    NOTE: Playwright is strictly thread-bound. For multi-threading, instantiate one ProfileManager per thread.
    """
    def __init__(self):
        self.playwright_context = None
        self.p = None
        self.profiles = {}
        
    def __enter__(self):
        self.playwright_context = sync_playwright()
        self.p = self.playwright_context.__enter__()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.close_all()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Error in close_all: %s", e)
        finally:
            if self.playwright_context:
                try:
                    self.playwright_context.__exit__(exc_type, exc_val, exc_tb)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning("Error exiting playwright: %s", e)
            
    def get_profile(self, profile_id: str, browser_name: str = "Chrome") -> ManagedProfile:
        """
        Retrieves or launches a profile by its ID (Profile Name).
        """
        if profile_id not in self.profiles:
            session = BrowserSession(profile_id, browser_name=browser_name, kill_existing=False)
            session.start()
            self.profiles[profile_id] = ManagedProfile(profile_id, session, self.p)
        return self.profiles[profile_id]
        
    def close_all(self):
        """Closes all active profiles managed by this instance."""
        for profile in self.profiles.values():
            try:
                profile.close()
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning("Error closing profile: %s", e)
        self.profiles.clear()
