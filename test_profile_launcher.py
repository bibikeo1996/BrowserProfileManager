import logging
import sys
import time
from BrowserProfileManager import ProfileManager, GetAllProfiles

# Configure logging to see steps clearly in terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("GoogleFlowTester")

class GoogleFlowProfileTester:
    """Helper class to orchestrate the profile launch and navigation verification."""
    
    def __init__(self, profile_name: str = "GoogleFlow", browser_name: str = "Chrome"):
        self.profile_name = profile_name
        self.browser_name = browser_name

    def verifyProfileExists(self) -> bool:
        """Checks if the target profile exists in the scanned profiles list."""
        logger.info("Scanning for available %s profiles...", self.browser_name)
        try:
            profiles = GetAllProfiles(self.browser_name)
            available_names = [p.name for p in profiles]
            logger.info("Available profiles detected: %s", available_names)
            
            target_profile = next((p for p in profiles if p.name == self.profile_name), None)
            if target_profile:
                logger.info("Found target profile: name='%s', folder='%s'", target_profile.name, target_profile.profile_id)
                return True
            else:
                logger.error("Target profile '%s' not found!", self.profile_name)
                return False
        except Exception as e:
            logger.exception("Error scanning profiles: %s", e)
            return False

    def launchAndNavigate(self) -> None:
        """Launches the profile using ProfileManager, performs sequential navigations, and pauses."""
        logger.info("Launching profile '%s' on %s...", self.profile_name, self.browser_name)
        with ProfileManager() as manager:
            # 1. Fetch the profile (this will boot Chrome if not running)
            profile = manager.get_profile(self.profile_name, browser_name=self.browser_name)
            
            # 2. Get the default main tab
            main_tab = profile.get_tab("main")
            logger.info("Successfully connected to main tab. Current URL: %s", main_tab.page.url)
            
            # 3. Navigate to Google first
            logger.info("Navigating to: https://www.google.com")
            main_tab.page.goto("https://www.google.com")
            logger.info("Current page title: '%s'", main_tab.page.title())
            
            # 4. Wait for 5 seconds
            logger.info("Waiting for 5 seconds...")
            time.sleep(5)
            
            # 5. Navigate to the Google Labs Flow project
            target_url = "https://labs.google/fx/vi/tools/flow/project/46df67e3-d5c5-410f-8326-7d5cfb09ab8a"
            logger.info("Navigating to: %s", target_url)
            main_tab.page.goto(target_url)
            logger.info("Successfully navigated. Current title: '%s'", main_tab.page.title())
            
            # 6. Pause/sleep here for 1 minute (60 seconds)
            logger.info("Pausing here for 60 seconds (1 minute)...")
            time.sleep(60)
            
            logger.info("Closing manager context...")

    def run(self) -> None:
        """Orchestrates validation and launching steps."""
        logger.info("Starting GoogleFlow Profile Test...")
        if not self.verifyProfileExists():
            logger.error("Test aborted: Target profile does not exist.")
            sys.exit(1)
            
        try:
            self.launchAndNavigate()
            logger.info("Test COMPLETED SUCCESSFULY!")
        except Exception as e:
            logger.exception("Test FAILED with exception: %s", e)
            sys.exit(1)

if __name__ == "__main__":
    tester = GoogleFlowProfileTester()
    tester.run()
