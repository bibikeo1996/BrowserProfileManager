from ..Config.Settings import DEFAULT_BROWSER, BROWSER_PATHS, SYSTEM_DEFAULT_PATHS
from ..Scanners.BrowserScanner import BrowserScanner
from .BrowserLauncher import BrowserLauncher
import time
import socket
import logging

logger = logging.getLogger(__name__)

class BrowserSession:
    """
    A high-level context manager to easily launch and manage a browser profile session.
    Yields the CDP endpoint URL to be used with Playwright.
    """
    def __init__(self, profile_name: str, browser_name: str = DEFAULT_BROWSER, 
                 port: int = 0, kill_existing: bool = True, extra_args: list = None):
        self.profile_name = profile_name
        self.browser_name = browser_name
        self.port = port
        self.kill_existing = kill_existing
        self.extra_args = extra_args or []
        self.launcher = None
        self.endpoint_url = None

    def _wait_for_port(self, host: str, port: int, timeout: float = 15.0) -> bool:
        """Poll TCP port until it's open or timeout is reached."""
        start = time.time()
        while time.time() - start < timeout:
            try:
                with socket.create_connection((host, port), timeout=1):
                    return True
            except (ConnectionRefusedError, OSError):
                time.sleep(0.5)
        return False

    def start(self) -> str:
        """Starts the browser session and returns the CDP endpoint URL."""
        user_data_dir = BROWSER_PATHS.get(self.browser_name)
        default_user_data_dir = SYSTEM_DEFAULT_PATHS.get(self.browser_name) or user_data_dir
        if not user_data_dir:
            raise ValueError(
                f"Unknown browser: {self.browser_name}. "
                f"Supported: {list(BROWSER_PATHS.keys())}"
            )

        # First scan the default system path to find the target profile metadata
        scanner = BrowserScanner(browser_name=self.browser_name, user_data_dir=default_user_data_dir)
        result = scanner.scan()
        
        target_profile = None
        if result.is_success:
            target_profile = next((p for p in result.profiles if p.name == self.profile_name), None)
            
        # Fallback to scanning the automation directory if not found in the default directory
        if not target_profile and user_data_dir != default_user_data_dir:
            scanner = BrowserScanner(browser_name=self.browser_name, user_data_dir=user_data_dir)
            result = scanner.scan()
            if result.is_success:
                target_profile = next((p for p in result.profiles if p.name == self.profile_name), None)

        if not target_profile:
            # Gather all profiles we could find for a helpful error message
            all_profiles = []
            for path in set([default_user_data_dir, user_data_dir]):
                sc = BrowserScanner(browser_name=self.browser_name, user_data_dir=path)
                res = sc.scan()
                if res.is_success:
                    all_profiles.extend([p.name for p in res.profiles])
            raise ValueError(
                f"Profile '{self.profile_name}' not found for {self.browser_name}. "
                f"Available profiles: {list(set(all_profiles))}"
            )

        self.launcher = BrowserLauncher(
            browser_name=self.browser_name,
            profile_id=target_profile.profile_id,
            user_data_dir=user_data_dir,
            port=self.port,
            extra_args=self.extra_args
        )
        self.endpoint_url = self.launcher.launch(kill_existing=self.kill_existing)
        
        # BrowserLauncher already polls CDP endpoint internally via HTTP
        self.port = self.launcher.port # Sync the port back just in case
        
        logger.info("Browser session ready at %s", self.endpoint_url)
        return self.endpoint_url

    def stop(self):
        """Kills the browser process or cleans up the session's isolated tabs."""
        if self.launcher:
            self.launcher.kill()

    def get_playwright_page(self, playwright_instance, session_tag: str = None):
        """
        Connects Playwright to the CDP endpoint and extracts the isolated tab.
        If session_tag is not provided, extracts the main tab of the session.
        Returns a Playwright Page object.
        """
        if session_tag is None:
            if not self.launcher or not hasattr(self.launcher, 'session_tag'):
                raise RuntimeError("Session has not been started yet.")
            session_tag = self.launcher.session_tag
            
        browser = playwright_instance.chromium.connect_over_cdp(self.endpoint_url)
        context = browser.contexts[0]
        
        target_page = None
        for _ in range(20):
            for page in context.pages:
                if session_tag in page.url:
                    target_page = page
                    break
            if target_page:
                break
            time.sleep(0.5)
            
        if not target_page:
            raise RuntimeError(f"Playwright could not find tab with tag: {session_tag}")
            
        return target_page

    def create_new_tab(self, playwright_instance):
        """
        Spawns a new fully isolated tab within the same Profile Window 
        and returns its Playwright Page object.
        """
        if not self.launcher:
            raise RuntimeError("Session has not been started yet.")
            
        new_tag = self.launcher.spawn_tab()
        return self.get_playwright_page(playwright_instance, session_tag=new_tag)

    def __enter__(self) -> 'BrowserSession':
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
