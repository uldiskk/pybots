import string
import re
import os
import urllib.request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from random import randint
import time
import os.path
import sys
import utils

if len(sys.argv) < 2:
    print("Please specify the configuration file as a cmd parameter")
    exit(1)
else:
    configFile = sys.argv[1]

# ***************** CONSTANTS ***********************
pagesToScan = 250
invitesInOneRound = 70
roundsToRepeat = 10
verboseOn = 0
fileOfExcludedNames = "../exclude.txt"
credsFile = "../creds.txt"
REMOTE_DEBUG_PORT = 9222

# ********** BROWSER SETUP *************
# Try connecting to an already-running Chrome (launched via launch_browser.py).
# If not available, fall back to launching a fresh browser and logging in.

def _get_chromedriver_service():
    if os.name == 'nt':
        return Service(ChromeDriverManager().install())
    else:
        return Service(ChromeDriverManager().install())

def try_connect_existing_browser():
    """Connect to Chrome already running with --remote-debugging-port."""
    try:
        urllib.request.urlopen(
            f"http://127.0.0.1:{REMOTE_DEBUG_PORT}/json/version", timeout=2
        )
        options = Options()
        options.binary_location = "/usr/bin/google-chrome" #don't forget to run 'pip install -r requirements.txt' in venv
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{REMOTE_DEBUG_PORT}")
        drv = webdriver.Chrome(service=_get_chromedriver_service(), options=options)
        print(f"Connected to existing Chrome on port {REMOTE_DEBUG_PORT} — session reused, no login needed.")
        return drv
    except Exception:
        return None

driver = try_connect_existing_browser()
needs_login = driver is None

if driver is None:
    print("No persistent browser found. Launching a new Chrome instance...")
    adPrinted = 0
    usr = utils.getUser(credsFile, adPrinted, verboseOn)
    adPrinted = 1
    pwd = utils.getPwd(credsFile, adPrinted, verboseOn)

    if os.name == 'nt':
        options = Options()
        options.add_experimental_option('detach', True)
        driver = webdriver.Chrome(service=_get_chromedriver_service(), options=options)
    else:
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        # options.add_argument("--disable-gpu")
        driver = webdriver.Chrome(service=_get_chromedriver_service(), options=options)

    driver.set_window_size(1000, 650)
    utils.loginToLinkedin(driver, usr, pwd)
else:
    # Still need to read creds path for exclude list etc., but don't log in
    adPrinted = 0
    usr = utils.getUser(credsFile, adPrinted, verboseOn)
    adPrinted = 1


# EVENT FLOW
def open_event_invite_dialog(driver, people_list_url):
    if "/events/" not in people_list_url and "/event/manage/" not in people_list_url:
        return

    print("Opening event invite picker...")
    time.sleep(3)

    # Check if invite picker already open
    already_open = driver.execute_script("""
        const host = document.querySelector('#interop-outlet');
        if (!host || !host.shadowRoot) return false;
        return host.shadowRoot.querySelectorAll('.invitee-picker__result-item').length > 0;
    """)
    if already_open:
        print("Invite picker already open, skipping navigation.")
        return

    # Step 1: find Share element and click it with Selenium native click
    # (JS el.click() doesn't fire React synthetic events — native click does)
    share_el = None
    candidates = driver.find_elements(By.XPATH, "//*[@role='button']")
    for el in candidates:
        try:
            if el.text.strip() == 'Share':
                share_el = el
                break
        except Exception:
            pass

    if not share_el:
        print("WARNING: Share button not found. Cannot open invite picker.")
        return

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", share_el)
    time.sleep(0.5)
    share_el.click()
    print("Clicked Share (native).")

    # Step 2: wait for Invite to appear, then click it
    invite_el = None
    for _ in range(12):
        time.sleep(0.5)
        candidates = driver.find_elements(By.XPATH, "//*[@role='button' or @role='menuitem' or self::a or self::button or self::li]")
        for el in candidates:
            try:
                t = el.text.strip().lower()
                if t.startswith('invite') and len(t) < 30 and el.is_displayed():
                    invite_el = el
                    break
            except Exception:
                pass
        if invite_el:
            break
    else:
        print("WARNING: Invite item never appeared after clicking Share.")
        return

    invite_el.click()
    print("Clicked Invite:", invite_el.text.strip())
    time.sleep(3)


def scroll_event_modal(driver, search_keywords, needed_count, max_rounds=200):

    for _ in range(max_rounds):

        matching_count = driver.execute_script("""
            const host = document.querySelector('#interop-outlet');
            if (!host || !host.shadowRoot) return 0;

            const shadow = host.shadowRoot;
            const cards = shadow.querySelectorAll('.invitee-picker__result-item');

            let count = 0;

            const rawKeywords = arguments[0];

            let keywords = [];

            if (Array.isArray(rawKeywords)) {
                keywords = rawKeywords.map(k => String(k).toLowerCase());
            } else if (typeof rawKeywords === "string") {
                keywords = rawKeywords.toLowerCase().split(",");
            }

            for (let card of cards) {

                const checkbox = card.querySelector('input[type="checkbox"]');
                const invitedLabel = card.innerText.includes("Invited");

                if (!checkbox || checkbox.checked || invitedLabel) continue;

                const text = card.innerText.toLowerCase();
                if (!text) continue;

                let match = false;

                for (let kw of keywords) {
                    if (text.includes(kw.trim())) {
                        match = true;
                        break;
                    }
                }

                if (match) count++;

                if (count >= arguments[1]) break;
            }

            return count;
        """, search_keywords, needed_count)

        if matching_count >= needed_count:
            time.sleep(0.5)
            return

        clicked = driver.execute_script("""
            const host = document.querySelector('#interop-outlet');
            if (!host || !host.shadowRoot) return false;

            const shadow = host.shadowRoot;
            const btn = shadow.querySelector('.scaffold-finite-scroll__load-button');

            if (!btn) return false;

            btn.click();
            return true;
        """)

        if not clicked:
            return

        time.sleep(1.5)
        time.sleep(0.5)


# ***************** LOGIC ***********************
totalConnectRequests = 0

excludeList = utils.getExcludeList(fileOfExcludedNames, adPrinted, verboseOn)
people_list_url = utils.getUrl(configFile)
search_keywords = utils.getKeywords(configFile)
filterByFirstLocation = utils.getBoolFirstLocation(configFile)
f2 = utils.getBool2ndLocation(configFile)
f3 = utils.getBool3rdLocation(configFile)
f4 = utils.getBool4thLocation(configFile)
f5 = utils.getBool5thLocation(configFile)
f6 = utils.getBool6thLocation(configFile)
testMode = utils.getTestMode(configFile)
if testMode is None:
    print("WARNING: testMode not found in config. Defaulting to test mode for safety.")
    testMode = 1

if testMode:
    print("*** TEST MODE ON — no invites will be sent ***")

already_selected = set()

round = 0

if "/events/" in people_list_url:
    driver.get(people_list_url)
    time.sleep(randint(3, 7))

while round < roundsToRepeat:

    if "/events/" not in people_list_url:

        driver.get(people_list_url)
        time.sleep(randint(3, 6))

        utils.clickFilterByLocation(driver, verboseOn, filterByFirstLocation, f2, f3, f4, f5, f6)
        utils.loadContactsToInvite(driver, pagesToScan, verboseOn)

        all_checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
        print("Found " + str(len(all_checkboxes)) + " contacts. Selecting:")

        invitesSelected = 0

        for btn in all_checkboxes:
            if testMode:
                div_parent = btn.find_element(By.XPATH, "..")
                for kw in search_keywords:
                    if kw.lower() in div_parent.text.lower():
                        print("TEST — would invite:", div_parent.text)
                        invitesSelected += 1
                        break
            else:
                nameSelected = utils.selectContactToInvite(
                    driver, btn, search_keywords, excludeList, verboseOn
                )
                if len(nameSelected) > 0:
                    invitesSelected += 1

            if invitesSelected >= invitesInOneRound:
                break

        if invitesSelected == 0:
            print("No people match the search criteria.")
            break

        if testMode:
            print("TEST — would click Invite for", invitesSelected, "people. Skipping.")
        else:
            print("------Inviting--------")
            invite = driver.find_element(By.CSS_SELECTOR, "button.artdeco-button--primary")
            invite.click()

        totalConnectRequests += invitesSelected
        time.sleep(4)

    else:

        open_event_invite_dialog(driver, people_list_url)

        scroll_event_modal(driver, search_keywords, invitesInOneRound)

        card_elements = driver.execute_script("""
            const host = document.querySelector('#interop-outlet');
            if (!host || !host.shadowRoot) return [];

            const shadow = host.shadowRoot;
            const cards = shadow.querySelectorAll('.invitee-picker__result-item');

            let result = [];

            for (let card of cards) {

                const checkbox = card.querySelector('input[type="checkbox"]');
                const invitedLabel = card.innerText.includes("Invited");

                if (checkbox && !checkbox.checked && !invitedLabel) {

                    const text = card.innerText.toLowerCase();
                    if (!text) continue;

                    const rawKeywords = arguments[1];

                    let keywords = [];

                    if (Array.isArray(rawKeywords)) {
                        keywords = rawKeywords.map(k => String(k).toLowerCase());
                    } else if (typeof rawKeywords === "string") {
                        keywords = rawKeywords.toLowerCase().split(",");
                    } else {
                        keywords = [];
                    }

                    let match = false;

                    for (let kw of keywords) {
                        if (text.includes(kw.trim())) {
                            match = true;
                            break;
                        }
                    }

                    if (match) {
                        result.push(card);
                    }
                }

                if (result.length >= arguments[0]) break;
            }

            return result;
        """, invitesInOneRound, search_keywords)

        selected_count = 0

        for card in card_elements:
            try:
                name = driver.execute_script("""
                    const el = arguments[0].querySelector('span');
                    return el ? el.innerText : arguments[0].innerText;
                """, card)

                if name in already_selected:
                    continue

                already_selected.add(name)

                name_clean = re.sub(r"[\n\t\s]*", "", name.lower())
                excluded = any(e.strip().lower() in name_clean for e in excludeList)
                if excluded:
                    print("!!!Excluding:", name)
                    continue

                if testMode:
                    print("TEST — would invite:", name)
                    selected_count += 1
                else:
                    driver.execute_script("""
                        const checkbox = arguments[0].querySelector('input[type="checkbox"]');
                        if (checkbox && !checkbox.checked) {
                            checkbox.click();
                        }
                    """, card)

                    time.sleep(0.8 + randint(0, 7) / 10)

                    # verify it actually got checked
                    is_checked = driver.execute_script("""
                        const checkbox = arguments[0].querySelector('input[type="checkbox"]');
                        return checkbox ? checkbox.checked : false;
                    """, card)

                    if is_checked:
                        selected_count += 1

            except:
                pass

        print("Selected:", selected_count)

        if selected_count == 0:
            print("No inviteable users found.")
            break

        if testMode:
            print("TEST — would click Invite for", selected_count, "people. Skipping.")
        else:
            print("------Inviting--------")

            invite_result = driver.execute_script("""
                const host = document.querySelector('#interop-outlet');
                if (!host) return "ERROR: #interop-outlet not found";
                if (!host.shadowRoot) return "ERROR: shadowRoot not accessible";

                const shadow = host.shadowRoot;
                const btn = shadow.querySelector("button.artdeco-button--primary");

                if (!btn) return "ERROR: primary button not found in shadow DOM";
                if (btn.disabled) return "ERROR: button is disabled (nothing selected?)";

                btn.click();
                return "OK: clicked '" + btn.innerText.trim() + "'";
            """)
            print("Invite button result:", invite_result)
            if invite_result and invite_result.startswith("ERROR"):
                print("WARNING: Invite may NOT have been sent — check the browser!")

        totalConnectRequests += selected_count
        time.sleep(4)

    round += 1

if testMode:
    print("TEST — would have sent " + str(totalConnectRequests) + " invites. None were actually sent.")
else:
    print("Total invites sent: " + str(totalConnectRequests))
print("Script ends here")
