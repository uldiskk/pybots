"""Quick headless smoke-test: logs into LinkedIn, checks one search page for Connect buttons.
No connection requests are sent."""
import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import utils

credsFile = "../creds.txt"
usr = utils.getUser(credsFile, 0, 0)
pwd = utils.getPwd(credsFile, 1, 0)

options = Options()
options.add_argument("--headless=new")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--window-size=1920,1080")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                     "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})

print("Logging in...")
utils.loginToLinkedin(driver, usr, pwd)
print("Post-login URL:", driver.current_url)
print("Post-login title:", driver.title)

test_url = (
    "https://www.linkedin.com/search/results/people/"
    "?geoUrn=%5B%22106491660%22%5D"
    "&keywords=speaker%20OR%20intelligence"
    "&network=%5B%22S%22%2C%22O%22%5D"
    "&origin=FACETED_SEARCH&spellCorrectionEnabled=false&page=1"
)
print("\nNavigating to search page...")
driver.get(test_url)
time.sleep(7)

print("Page title:", driver.title)
print("Page URL :", driver.current_url)

connect_buttons = driver.find_elements(
    By.XPATH,
    "//a[starts-with(@aria-label,'Invite') and contains(@aria-label,'connect')]"
)
print(f"\nFound Connect buttons: {len(connect_buttons)}")
for btn in connect_buttons[:5]:
    print(" -", btn.get_attribute("aria-label"))

if len(connect_buttons) == 0:
    # Dump a slice of page source to help diagnose what LinkedIn actually served
    src = driver.page_source
    print("\n--- page source excerpt (first 2000 chars) ---")
    print(src[:2000])

driver.quit()
print("\nTest complete.")
