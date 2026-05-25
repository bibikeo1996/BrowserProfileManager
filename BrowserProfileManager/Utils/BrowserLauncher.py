import os
import subprocess
import time
import logging
import socket
import urllib.request
import urllib.error
import sys
import threading
from typing import Optional
from pathlib import Path
import shutil
from BrowserProfileManager.Config.Settings import EXECUTABLE_PATHS

logger = logging.getLogger(__name__)

def ForceKillBrowser(browser_name: str):
    """Utility to forcefully kill all running instances of a browser."""
    logger.info("Force killing all %s processes...", browser_name)
    try:
        if browser_name.lower() == "chrome":
            app_pattern = "chrome.exe" if sys.platform == "win32" else "Google Chrome"
        elif browser_name.lower() == "brave":
            app_pattern = "brave.exe" if sys.platform == "win32" else "Brave Browser"
        elif browser_name.lower() == "firefox":
            app_pattern = "firefox.exe" if sys.platform == "win32" else "firefox"
        else:
            app_pattern = browser_name
            
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/IM", app_pattern], capture_output=True)
        else:
            # Also gracefully try osascript on macOS before pkill
            if sys.platform == "darwin":
                if browser_name.lower() == "chrome":
                    subprocess.run(["osascript", "-e", 'quit app "Google Chrome"'], capture_output=True)
                elif browser_name.lower() == "brave":
                    subprocess.run(["osascript", "-e", 'quit app "Brave Browser"'], capture_output=True)
            subprocess.run(["pkill", "-9", "-f", app_pattern], capture_output=True)
        time.sleep(1.5)
        
        # Clean up our custom port file so we don't read stale ports
        import os
        from BrowserProfileManager.Config.Settings import BROWSER_PATHS
        user_data_dir = BROWSER_PATHS.get(browser_name)
        if user_data_dir:
            bpm_file = Path(user_data_dir) / ".bpm_port"
            if bpm_file.exists():
                try:
                    bpm_file.unlink()
                except Exception:
                    pass
    except Exception as e:
        logger.warning("Error force killing browser: %s", e)

class BrowserLauncher:
    """Class to launch a real browser via OS subprocess and connect Playwright."""
    
    _active_sessions = 0
    _master_process = None
    _lock = threading.Lock()
    
    def __init__(self, browser_name: str, user_data_dir, port: int = 0, extra_args: list = None):
        self._killed = False
        with BrowserLauncher._lock:
            BrowserLauncher._active_sessions += 1
            
        self.browser_name = browser_name
        self.user_data_dir = str(user_data_dir)
        self.extra_args = extra_args or []
        self.port = port if port != 0 else self._get_free_port()
        self.target_ids = []
        
    def _get_free_port(self) -> int:
        """Find an available port dynamically in the 8000-8999 range."""
        import random
        return random.randint(8000, 8999)
        
    def _get_executable_path(self) -> str:
        exec_path = EXECUTABLE_PATHS.get(self.browser_name)
        if not exec_path:
            raise ValueError(f"Unsupported browser: {self.browser_name}")
        return exec_path

    def _kill_existing_instances(self):
        """Force kill existing browser instances to ensure CDP port can be bound."""
        ForceKillBrowser(self.browser_name)

    def _wait_for_cdp(self, timeout: int = 15) -> bool:
        """Actively poll the CDP endpoint until it becomes available."""
        start_time = time.time()
        url = f"http://127.0.0.1:{self.port}/json/version"
        while time.time() - start_time < timeout:
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=1) as response:
                    if response.status == 200:
                        return True
            except (urllib.error.URLError, ConnectionResetError):
                time.sleep(0.2)
        return False

    def _read_devtools_active_port(self) -> Optional[int]:
        # Try Chrome's native file first (if it was created)
        target_dir = self.user_data_dir
        port_file = Path(target_dir) / "DevToolsActivePort"
        if port_file.exists():
            try:
                with open(port_file, "r") as f:
                    lines = f.readlines()
                    if lines:
                        return int(lines[0].strip())
            except Exception as e:
                logger.warning("Failed to read DevToolsActivePort: %s", e)
                
        # Try our custom state file
        bpm_file = Path(target_dir) / ".bpm_port"
        if bpm_file.exists():
            try:
                with open(bpm_file, "r") as f:
                    content = f.read().strip()
                    if content:
                        return int(content)
            except Exception as e:
                logger.warning("Failed to read .bpm_port: %s", e)
        return None

    def _write_bpm_port(self):
        try:
            target_dir = self.user_data_dir
            bpm_file = Path(target_dir) / ".bpm_port"
            with open(bpm_file, "w") as f:
                f.write(str(self.port))
        except Exception as e:
            logger.warning("Failed to write .bpm_port: %s", e)

    def _find_target_ws_url(self, port: int, session_tag: str, timeout: int = 15) -> str:
        """Polls CDP /json/list to find the specific tab opened for this session."""
        import json
        import urllib.request
        start_time = time.time()
        url = f"http://127.0.0.1:{port}/json/list"
        target_url_fragment = f"bpm-tag-{session_tag}"
        
        while time.time() - start_time < timeout:
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=1) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode('utf-8'))
                        for target in data:
                            if target_url_fragment in target.get("url", ""):
                                ws_url = target.get("webSocketDebuggerUrl")
                                if ws_url:
                                    if not hasattr(self, 'target_ids'):
                                        self.target_ids = []
                                    t_id = target.get("id")
                                    if t_id not in self.target_ids:
                                        self.target_ids.append(t_id)
                                    return ws_url
            except Exception:
                pass
            time.sleep(0.5)
            
        raise RuntimeError(f"Could not find CDP target for tag '{session_tag}' on port {port}. Chrome might have failed to open the tab.")

    def spawn_tab(self) -> str:
        """
        Spawns a new tab in the active profile via OS command and returns its session tag.
        This ensures the tab opens in the exact correct profile window.
        """
        import uuid
        import subprocess
        new_tag = str(uuid.uuid4())
        tag_url = f"data:text/html,<title>bpm-tag-{new_tag}</title>"
        
        exec_path = self._get_executable_path()
        if self.browser_name.lower() == "firefox":
            args = [
                exec_path,
                f"-profile",
                f"{self.user_data_dir}",
                f"-remote-debugging-port", str(self.port),
                "-no-remote",
                tag_url
            ]
        else:
            args = [
                exec_path,
                f"--remote-debugging-port={self.port}",
                f"--user-data-dir={self.user_data_dir}",
                "--no-first-run",
                "--no-default-browser-check",
                "--remote-allow-origins=*",
                "--password-store=basic",
                "--disable-blink-features=AutomationControlled",
                "--test-type",
                tag_url
            ]
            
        if self.extra_args:
            args.extend(self.extra_args)
            
        subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for tab to appear in CDP and register its ID internally
        self._find_target_ws_url(self.port, new_tag)
        return new_tag

    def checkAndHandleFirstLogin(self, exec_path: str, user_data_dir: str, default_user_data_dir: str, profile_id: str):
        """
        Ensures the automation profile directory is properly set up.
        On Windows, if it's the first run, opens Chrome interactively for the user to log in.
        On macOS, automatically creates a symlink of the profile directory to load cookies instantly.
        """
        if user_data_dir == default_user_data_dir:
            return

        target_profile_dir = Path(user_data_dir) / profile_id
        default_profile_dir = Path(default_user_data_dir) / profile_id

        # 1. Windows: First-time login wizard
        if sys.platform == "win32":
            if not target_profile_dir.exists():
                logger.info("Profile '%s' is being run for the first time in automation.", profile_id)
                # Ensure user_data_dir parent exists
                os.makedirs(user_data_dir, exist_ok=True)
                
                # Copy Local State from default path to preserve profile metadata / keys
                default_local_state = Path(default_user_data_dir) / "Local State"
                target_local_state = Path(user_data_dir) / "Local State"
                if default_local_state.exists() and not target_local_state.exists():
                    try:
                        shutil.copy2(default_local_state, target_local_state)
                        logger.info("Copied Local State from default profile path to preserve metadata.")
                    except Exception as e:
                        logger.warning("Could not copy Local State: %s", e)
                
                # Prompt the user with ASCII block
                print("\n" + "=" * 80)
                print(" " * 4 + "[ACTION REQUIRED: FIRST-TIME LOGIN]")
                print(" " * 4 + f"An interactive browser window will open for profile directory: {profile_id}")
                print(" " * 4 + "Please log in to your account inside the opened window.")
                print(" " * 4 + "Once you have successfully logged in, CLOSE the browser window")
                print(" " * 4 + "to automatically proceed with the automation flow.")
                print(" " * 4 + "----------------------------------------------------------------")
                print(" " * 4 + f"Tip: If you close the window early, delete this folder to retry:")
                print(" " * 4 + f"     {target_profile_dir}")
                print("=" * 80 + "\n")
                
                # Run browser interactively (blocking call)
                args = [
                    exec_path,
                    f"--user-data-dir={user_data_dir}",
                    f"--profile-directory={profile_id}",
                    "--no-first-run",
                    "--no-default-browser-check"
                ]
                try:
                    subprocess.run(args, check=False)
                except Exception as e:
                    logger.error("Failed to run interactive browser session: %s", e)
                
                logger.info("Interactive login window closed. Continuing to automation...")

        # 2. macOS: Symlink creation
        elif sys.platform == "darwin":
            if default_profile_dir.exists():
                os.makedirs(user_data_dir, exist_ok=True)
                
                # Copy Local State
                default_local_state = Path(default_user_data_dir) / "Local State"
                target_local_state = Path(user_data_dir) / "Local State"
                if default_local_state.exists() and not target_local_state.exists():
                    try:
                        shutil.copy2(default_local_state, target_local_state)
                        logger.info("Copied Local State to automation folder.")
                    except Exception as e:
                        logger.warning("Could not copy Local State on macOS: %s", e)
                
                # Symlink target profile dir if it doesn't exist
                if not target_profile_dir.exists() and not target_profile_dir.is_symlink():
                    try:
                        os.symlink(str(default_profile_dir), str(target_profile_dir))
                        logger.info("Created profile symlink on macOS: %s -> %s", target_profile_dir, default_profile_dir)
                    except Exception as e:
                        logger.warning("Failed to create symlink: %s", e)

    def launch(self, kill_existing: bool = True) -> str:
        """Launches the browser with a resilient retry mechanism."""
        max_retries = 1
        for attempt in range(max_retries + 1):
            try:
                return self._launch_internal(kill_existing=(kill_existing or attempt > 0))
            except Exception as e:
                if attempt < max_retries:
                    logger.warning("Launch attempt %d failed: %s. Force killing and retrying...", attempt + 1, e)
                    ForceKillBrowser(self.browser_name)
                    time.sleep(2)
                else:
                    raise e

    def _launch_internal(self, kill_existing: bool = True) -> str:
        """Launches the browser and returns the HTTP endpoint URL. Wait for specific tab to be ready."""
        if kill_existing:
            self._kill_existing_instances()
        
        exec_path = self._get_executable_path()
        if not os.path.exists(exec_path):
            raise FileNotFoundError(f"{self.browser_name} executable not found at: {exec_path}.")
            
        from BrowserProfileManager.Config.Settings import SYSTEM_DEFAULT_PATHS
        default_user_data_dir = SYSTEM_DEFAULT_PATHS.get(self.browser_name, self.user_data_dir)
        
        # Ensure first-time login or symlinks are handled before running the browser with CDP
        self.checkAndHandleFirstLogin(exec_path, self.user_data_dir, default_user_data_dir, self.profile_id)
        
        import uuid
        import sys
        self.session_tag = str(uuid.uuid4())
        tag_url = f"data:text/html,<title>bpm-tag-{self.session_tag}</title>"
        
        if self.browser_name.lower() == "firefox":
            args = [
                exec_path,
                f"-profile",
                f"{self.user_data_dir}",
                f"-remote-debugging-port", str(self.port),
                "-no-remote",
                tag_url
            ]
        else:
            args = [
                exec_path,
                f"--remote-debugging-port={self.port}",
                f"--user-data-dir={self.user_data_dir}",
                "--no-first-run",
                "--no-default-browser-check",
                "--remote-allow-origins=*",
                "--password-store=basic",
                "--disable-blink-features=AutomationControlled",
                "--test-type",
                tag_url
            ]
        
        if self.extra_args:
            args.extend(self.extra_args)
        
        logger.info("Launching %s on port %d with isolated profile at '%s'", self.browser_name, self.port, self.user_data_dir)
        
        try:
            process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError as e:
            raise RuntimeError(f"Failed to launch {self.browser_name}: {e}")
        
        time.sleep(1.0)
        if process.poll() is not None:
            exit_code = process.returncode
            if exit_code == 0:
                # Retry reading the port file for up to 5 seconds to handle race conditions 
                # where the Master Process is still starting up and hasn't written the file yet.
                port = None
                for _ in range(15):
                    port = self._read_devtools_active_port()
                    if port:
                        break
                    time.sleep(0.5)
                    
                if port:
                    logger.info("Attached to Master Process on port %d", port)
                    self.port = port
                    # Chờ tab của chúng ta được tạo ra
                    self._find_target_ws_url(self.port, self.session_tag)
                    return f"http://localhost:{self.port}"
                else:
                    raise RuntimeError("Chrome master process is running but CDP is not enabled or port file missing. Please fully close Chrome first.")
            else:
                raise RuntimeError(f"{self.browser_name} process exited immediately with code {exit_code}.")
        else:
            with BrowserLauncher._lock:
                BrowserLauncher._master_process = process
        
        logger.info("Waiting for CDP port %d to open...", self.port)
        if not self._wait_for_cdp(timeout=15):
            self.kill()
            raise RuntimeError(f"CDP port {self.port} did not respond in time.")
        
        self._write_bpm_port()
        
        try:
            self._find_target_ws_url(self.port, self.session_tag)
        except Exception as e:
            self.kill() # Prevent zombie Master process if tab fails to open
            raise e
            
        return f"http://localhost:{self.port}"
        
    def kill(self):
        """Gracefully kills the browser process or closes the isolated tabs."""
        if self._killed:
            return
        self._killed = True
            
        # 1. Luôn luôn dọn dẹp các tab mà session này đã tạo ra (bao gồm tab chính và tab con)
        for t_id in getattr(self, 'target_ids', []):
            try:
                import urllib.request
                url = f"http://127.0.0.1:{self.port}/json/close/{t_id}"
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=2) as _:
                    logger.info("Closed isolated session tab %s", t_id)
            except Exception as e:
                logger.debug("Failed to close session tab %s (might already be closed): %s", t_id, e)
                
        if hasattr(self, 'target_ids'):
            self.target_ids.clear()
                
        # 2. Xử lý tắt Master Process dựa vào Reference Counter
        with BrowserLauncher._lock:
            BrowserLauncher._active_sessions -= 1
            if BrowserLauncher._active_sessions <= 0:
                BrowserLauncher._active_sessions = 0
                if BrowserLauncher._master_process:
                    try:
                        BrowserLauncher._master_process.terminate()
                        try:
                            BrowserLauncher._master_process.wait(timeout=3)
                        except subprocess.TimeoutExpired:
                            logger.warning("%s did not exit after SIGTERM, sending SIGKILL...", self.browser_name)
                            BrowserLauncher._master_process.kill()
                            BrowserLauncher._master_process.wait(timeout=2)
                    except Exception as e:
                        logger.warning("Error during browser cleanup: %s", e)
                    finally:
                        BrowserLauncher._master_process = None
                        logger.info("Browser master process terminated.")

                pass
