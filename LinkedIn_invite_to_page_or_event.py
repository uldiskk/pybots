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
invitesInOneRound = 2
roundsToRepeat = 3
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

    driver.execute_script("""
        const share = document.querySelector('[data-view-name="event-management-share-event-tab"]');
        if (share) share.click();
    """)

    time.sleep(2)

    driver.execute_script("""
        const invite = document.querySelector('[data-view-name="event-management-invite"]');
        if (invite) invite.click();
    """)

    time.sleep(3)


def scroll_event_modal(driver, max_rounds=40):

    for _ in range(max_rounds):

        # Check if there are inviteable unchecked users
        has_inviteable = driver.execute_script("""
            const host = document.querySelector('#interop-outlet');
            if (!host || !host.shadowRoot) return false;

            const shadow = host.shadowRoot;
            const cards = shadow.querySelectorAll('.invitee-picker__result-item');

            for (let card of cards) {

                const checkbox = card.querySelector('input[type="checkbox"]');
                const invitedLabel = card.innerText.includes("Invited");

                if (checkbox && !checkbox.checked && !invitedLabel) {
                    return true;
                }
            }

            return false;
        """)

        # If we found unchecked inviteable users → stop loading
        if has_inviteable:
            return

        # Otherwise try clicking Show more
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
            break

        time.sleep(1.5)


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

round = 0

while round < roundsToRepeat:

    driver.get(people_list_url)
    time.sleep(4)

    if "/events/" not in people_list_url:

        utils.clickFilterByLocation(driver, verboseOn, filterByFirstLocation, f2, f3, f4, f5, f6)
        utils.loadContactsToInvite(driver, pagesToScan, verboseOn)

        all_checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
        print("Found " + str(len(all_checkboxes)) + " contacts. Selecting:")

        invitesSelected = 0

        for btn in all_checkboxes:
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

        print("------Inviting--------")

        invite = driver.find_element(By.CSS_SELECTOR, "button.artdeco-button--primary")
        invite.click()
        totalConnectRequests += invitesSelected
        time.sleep(4)

    else:

        open_event_invite_dialog(driver, people_list_url)

        scroll_event_modal(driver)

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
                    result.push(card);
                }

                if (result.length >= arguments[0]) break;
            }

            return result;
        """, invitesInOneRound)

        selected_count = 0

        for card in card_elements:
            try:
                driver.execute_script("""
                    const checkbox = arguments[0].querySelector('input[type="checkbox"]');
                    if (checkbox && !checkbox.checked) {
                        checkbox.click();
                    }
                """, card)

                time.sleep(1)

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

print("Total invites sent:" + str(totalConnectRequests))
print("Script ends here")