# BrowserProfileManager

A robust, multi-threaded Automation Framework for connecting Playwright to existing Chrome/Brave Profiles using a Shared Master Process architecture. 

It handles all OS-level processes, CDP connection, Port polling, Tab isolation, and garbage collection automatically.

---

## 📦 Installation

```bash
pip install -e ./BrowserProfileManager
```

---

## 🚀 Quick Start (Facade API)

Use the high-level `ProfileManager` to control multiple Profiles and Tabs without worrying about Playwright Context or IPC conflicts.

```python
from BrowserProfileManager import ProfileManager

with ProfileManager() as manager:
    
    # 1. Fetch a Profile (Launches Browser if not running)
    my_chrome = manager.get_profile("Your Chrome", browser_name="Chrome")
    
    # 2. Control the default Main Tab
    main_tab = my_chrome.get_tab("main")
    main_tab.page.goto("https://vi.wikipedia.org/")
    print(main_tab.page.title())
    
    # 3. Spawn a New Tab inside the SAME Profile
    # The new tab will open strictly in the "Your Chrome" profile window!
    sub_tab = my_chrome.new_tab("github")
    sub_tab.page.goto("https://github.com")
    
    # 4. Fetch the tab anywhere by its ID
    manager.get_profile("Your Chrome").get_tab("github").page.fill('input', 'Playwright')

# Once the 'with' block ends, ProfileManager automatically:
# 1. Stops Playwright.
# 2. Closes ALL isolated tabs created during the session.
# 3. Kills the Master Process if no other threads are using it.
```

---

## 🧵 Threading & Concurrency

Playwright's `sync_playwright` is strictly bound to the thread that creates it. 
**Do NOT pass `ProfileManager` across Python threads.** Instead, instantiate a new `ProfileManager` **inside** each worker thread. 

The library automatically uses **Reference Counting** to ensure threads do not kill the Master Process while others are using it!

```python
import threading
from BrowserProfileManager import ProfileManager

def worker(profile_name, url):
    # Instantiate Manager INSIDE the thread
    with ProfileManager() as manager:
        profile = manager.get_profile(profile_name)
        tab = profile.get_tab("main")
        tab.page.goto(url)
        # Tab automatically closes when Thread finishes!

t1 = threading.Thread(target=worker, args=("Your Chrome", "https://github.com"))
t2 = threading.Thread(target=worker, args=("GoogleFlow", "https://stackoverflow.com"))

t1.start()
t2.start()

t1.join()
t2.join()
```

---

## 📖 Core API Reference

### `ProfileManager`
The unified Context Manager that wraps Playwright and BrowserSessions.

* **`get_profile(profile_id: str, browser_name: str = "Chrome") -> ManagedProfile`**
  Returns a `ManagedProfile` instance. Triggers Chrome/Brave OS-level boot if the Master Process isn't running.
  * `profile_id`: Name of the profile (e.g. `"GoogleFlow"`, `"Profile 1"`).
  * `browser_name`: `"Chrome"` or `"Brave"`.

* **`close_all()`**
  Forcefully closes all tabs tracked by this manager and drops connections.

### `ManagedProfile`
A specific Profile Instance.

* **`get_tab(tab_id: str = "main") -> ManagedTab`**
  Fetches an active tab by its ID. Every profile has a default `"main"` tab upon creation.

* **`new_tab(tab_id: str) -> ManagedTab`**
  Injects a new fully isolated child tab directly into this profile's OS Window using IPC.

### `ManagedTab`
The active tab object.
* **`tab.id`**: The string ID of the tab.
* **`tab.page`**: The standard **Playwright Page object** (`playwright.sync_api.Page`). You use this to interact with the DOM (`goto`, `fill`, `click`).

---

## 🧹 Utilities

### `ForceKillBrowser(browser_name: str)`
Manually nuke all system browser processes if the environment becomes corrupted.
```python
from BrowserProfileManager import ForceKillBrowser

ForceKillBrowser("Chrome")
```
