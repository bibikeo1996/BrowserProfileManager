import time
import logging

logger = logging.getLogger(__name__)

class PlaywrightHelper:
    """Helper utilities for interacting with Playwright in multi-profile environments."""
    
    @staticmethod
    def get_context(browser, session, timeout: int = 15):
        """
        Finds the exact BrowserContext belonging to the physical profile of the given BrowserSession.
        In a Shared Master Process environment, browser.contexts contains multiple profiles.
        This helper opens a temporary blank tab to check chrome://version and verify the profile path.
        """
        profile_id = session.launcher.profile_id
        start_time = time.time()
        
        logger.info("Searching for Playwright context matching profile '%s'...", profile_id)
        
        while time.time() - start_time < timeout:
            for context in browser.contexts:
                page = None
                try:
                    # Create a temporary page to inspect the context's identity
                    page = context.new_page()
                    page.goto("chrome://version/")
                    
                    # Read the Profile Path directly from Chrome's internal engine
                    path_text = page.locator("#profile_path").inner_text()
                    
                    # Close the temp page immediately so the user doesn't notice it
                    page.close()
                    
                    if profile_id in path_text:
                        logger.info("Found exact matching context for '%s'", profile_id)
                        return context
                except Exception as e:
                    if page and not page.is_closed():
                        page.close()
            
            # Context might not have spawned yet due to IPC delay, sleep and retry
            time.sleep(1)
            
        raise RuntimeError(f"Could not find a Playwright context for profile '{profile_id}' within {timeout}s.")
