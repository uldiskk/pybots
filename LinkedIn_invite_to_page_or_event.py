import string
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
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
pagesToScan = 150
invitesInOneRound = 10
roundsToRepeat = 10
verboseOn = 0
fileOfExcludedNames = "../exclude.txt"
credsFile = "../creds.txt"

# ********** LOG IN *************
adPrinted = 0
usr = utils.getUser(credsFile, adPrinted, verboseOn)
adPrinted = 1
pwd = utils.getPwd(credsFile, adPrinted, verboseOn)

if os.name == 'nt':
    from webdriver_manager.chrome import ChromeDriverManager
    options = Options()
    options.add_experimental_option('detach', True)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
else:
    service = Service(executable_path=r'./chromedriver')
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=service, options=options)

driver.set_window_size(1000, 650)

utils.loginToLinkedin(driver, usr, pwd)


# EVENT FLOW
def open_event_invite_dialog(driver, people_list_url):
    if "/events/" not in people_list_url:
        return

    print("Detected event URL. Opening Share and Invite flow.")
    time.sleep(3)

    share_selectors = [
        '[data-view-name="event-management-share-event-tab"]',
        '[data-view-name="event-management-share"]',
        'button[aria-label*="Share"]',
        'a[aria-label*="Share"]',
        '.event-management__share-tab',
    ]
    share_clicked = driver.execute_script("""
        const selectors = arguments[0];
        for (let sel of selectors) {
            const el = document.querySelector(sel);
            if (el) { el.click(); return sel; }
        }
        return null;
    """, share_selectors)

    if share_clicked:
        print("Clicked Share tab via:", share_clicked)
    else:
        print("WARNING: Share tab not found with any selector. Attempting text-based fallback.")
        driver.execute_script("""
            const all = Array.from(document.querySelectorAll('button, a, li'));
            const el = all.find(e => e.innerText && e.innerText.trim().toLowerCase() === 'share');
            if (el) el.click();
        """)

    time.sleep(2)

    invite_selectors = [
        '[data-view-name="event-management-invite"]',
        '[data-view-name="event-management-invite-tab"]',
        'button[aria-label*="Invite"]',
        'a[aria-label*="Invite"]',
        '.event-management__invite-tab',
    ]
    invite_clicked = driver.execute_script("""
        const selectors = arguments[0];
        for (let sel of selectors) {
            const el = document.querySelector(sel);
            if (el) { el.click(); return sel; }
        }
        return null;
    """, invite_selectors)

    if invite_clicked:
        print("Clicked Invite tab via:", invite_clicked)
    else:
        print("WARNING: Invite button not found with any selector. Attempting text-based fallback.")
        driver.execute_script("""
            const all = Array.from(document.querySelectorAll('button, a, li'));
            const el = all.find(e => e.innerText && e.innerText.trim().toLowerCase() === 'invite');
            if (el) el.click();
        """)

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

        if "?invite=true" not in people_list_url and not testMode:
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

            driver.execute_script("""
                const host = document.querySelector('#interop-outlet');
                if (!host || !host.shadowRoot) return;

                const shadow = host.shadowRoot;
                const btn = shadow.querySelector("button.artdeco-button--primary");

                if (btn && !btn.disabled) {
                    btn.click();
                }
            """)

        totalConnectRequests += selected_count
        time.sleep(4)

    round += 1

if testMode:
    print("TEST — would have sent " + str(totalConnectRequests) + " invites. None were actually sent.")
else:
    print("Total invites sent: " + str(totalConnectRequests))
print("Script ends here")