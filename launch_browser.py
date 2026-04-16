import subprocess
import sys
import os
import time
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHROME_PROFILE_DIR = os.path.join(SCRIPT_DIR, "chrome_profile")
REMOTE_DEBUG_PORT = 9222
CREDS_FILE = os.path.join(SCRIPT_DIR, "../creds.txt")

os.makedirs(CHROME_PROFILE_DIR, exist_ok=True)

# ---- find Chrome executable ----
if sys.platform == "win32":
    candidate_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    chrome_exe = next((p for p in candidate_paths if os.path.exists(p)), None)
    if not chrome_exe:
        print("ERROR: Chrome not found. Add your Chrome path to candidate_paths in launch_browser.py.")
        sys.exit(1)
else:
    chrome_exe = "google-chrome"

# ---- read credentials ----
if not os.path.isfile(CREDS_FILE):
    print(f"ERROR: Credentials file not found at {CREDS_FILE}")
    sys.exit(1)

with open(CREDS_FILE, encoding="utf8") as f:
    lines = [l.strip() for l in f.readlines()]

if len(lines) < 2:
    print("ERROR: creds.txt must have username on line 1 and password on line 2.")
    sys.exit(1)

usr, pwd = lines[0], lines[1]

# ---- check if bot Chrome is already running ----
already_running = False
try:
    urllib.request.urlopen(f"http://127.0.0.1:{REMOTE_DEBUG_PORT}/json/version", timeout=1)
    already_running = True
except Exception:
    pass

if already_running:
    print(f"Bot Chrome is already running on port {REMOTE_DEBUG_PORT} — skipping launch.")
else:
    # ---- launch Chrome with remote debugging ----
    cmd = [
        chrome_exe,
        f"--user-data-dir={CHROME_PROFILE_DIR}",
        f"--remote-debugging-port={REMOTE_DEBUG_PORT}",
        "--no-first-run",
        "--no-default-browser-check",
        "about:blank",
    ]

    print(f"Launching Chrome on port {REMOTE_DEBUG_PORT}...")
    subprocess.Popen(cmd)

    # wait for Chrome to be ready
    print("Waiting for Chrome to start...", end="", flush=True)
    for _ in range(20):
        time.sleep(1)
        print(".", end="", flush=True)
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{REMOTE_DEBUG_PORT}/json/version", timeout=1)
            break
        except Exception:
            pass
    else:
        print("\nERROR: Chrome did not start in time. Try running manually.")
        sys.exit(1)

    print(" ready.")

# ---- connect Selenium and log in ----
import os.path as _osp
if os.name == 'nt':
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium import webdriver

    options = Options()
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{REMOTE_DEBUG_PORT}")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
else:
    from selenium.webdriver.chrome.service import Service
    from selenium import webdriver

    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{REMOTE_DEBUG_PORT}")
    service = Service(executable_path=_osp.join(SCRIPT_DIR, "chromedriver"))
    driver = webdriver.Chrome(service=service, options=options)

# check if already logged in
driver.get("https://www.linkedin.com/feed")
time.sleep(4)

if "/feed" in driver.current_url or "/mynetwork" in driver.current_url:
    print("Already logged in — session was saved from a previous run.")
else:
    print("Logging in to LinkedIn...")
    import sys as _sys
    _sys.path.insert(0, SCRIPT_DIR)
    import utils
    utils.loginToLinkedin(driver, usr, pwd)
    print("Login complete.")

print()
print("Browser is ready. Keep this window open and run your bot scripts.")
