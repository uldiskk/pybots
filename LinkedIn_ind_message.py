import re
import os
import string
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver import Keys
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

#***************** CONSTANTS ***********************
startingPage = 1
pagesToScan = 4
verboseOn = 0
fileOfExcludedNames = "../exclude.txt"
credsFile = "../creds.txt"

#-----FUNCTIONS-------------
def saveName(name, fileOfUsedNames):
    with open(fileOfUsedNames, 'a', encoding="utf8") as file:
        file.write(name + '\n')
    print("Name " + name + " saved")

def handle_discard_popup(driver):
    """If 'Leave?' discard popup appears, click 'Discard' to continue."""
    try:
        discard_button = driver.find_element(
            By.XPATH,
            "//button[contains(@class,'artdeco-button') and (normalize-space()='Discard' or contains(.,'Discard'))]"
        )
        driver.execute_script("arguments[0].click();", discard_button)
        print("Detected and clicked 'Discard' on popup.")
        time.sleep(1)
    except Exception:
        pass

def close_all_message_popups(driver, max_passes=5):
    """
    Close every open LinkedIn message overlay. If a Discard prompt appears,
    click 'Discard'. Run multiple passes to catch newly-surfaced overlays.
    """
    for _ in range(max_passes):
        closed_any = False

        # find all visible 'close' buttons on message overlays
        try:
            close_btns = driver.find_elements(
                By.XPATH,
                "//button[contains(@class,'msg-overlay-bubble-header__control')"
                " and contains(@class,'artdeco-button--circle') and not(@disabled)]"
            )
            close_btns = [b for b in close_btns if b.is_displayed()]
        except Exception:
            close_btns = []

        for b in close_btns:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", b)
                driver.execute_script("arguments[0].click();", b)
                time.sleep(0.2)
                handle_discard_popup(driver)
                closed_any = True
            except Exception:
                pass

        # also close the “minimized” docked threads if present
        try:
            minimized_close_btns = driver.find_elements(
                By.XPATH,
                "//button[contains(@class,'msg-overlay-list-bubble__dismiss-button')]"
            )
            minimized_close_btns = [b for b in minimized_close_btns if b.is_displayed()]
            for b in minimized_close_btns:
                try:
                    driver.execute_script("arguments[0].click();", b)
                    time.sleep(0.2)
                    handle_discard_popup(driver)
                    closed_any = True
                except Exception:
                    pass
        except Exception:
            pass

        if not closed_any:
            break

    time.sleep(0.3)

def get_latest_message_textbox(driver):
    """
    Return the *most recently opened* visible message textbox.
    LinkedIn can have multiple; picking the last visible one avoids typing
    into an older chat.
    """
    boxes = driver.find_elements(By.XPATH, "//div[@role='textbox' and @contenteditable='true']")
    boxes = [b for b in boxes if b.is_displayed()]
    if not boxes:
        raise RuntimeError("No visible message textbox found")
    return boxes[-1]


#********** LOG IN *************
adPrinted = 0
usr = utils.getUser(credsFile, adPrinted, verboseOn)
adPrinted = 1
pwd = utils.getPwd(credsFile, adPrinted, verboseOn)

if os.name == 'nt':
    options = Options()
    options.add_experimental_option('detach', True)
    service = Service(executable_path='chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=options)
else:
    service = Service(executable_path=r'./chromedriver')
    options = webdriver.ChromeOptions()
    #options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=service, options=options)

utils.loginToLinkedin(driver, usr, pwd)

#***************** LOGIC ***********************
orText = '%20OR%20'
firstLevelFilter = 'network=%5B%22F%22%5D' + '&'
totalMessages = 0

###read file with names to exclude
excludeList = utils.getExcludeList(fileOfExcludedNames, adPrinted, verboseOn)
fileOfUsedNames = utils.getFileOfUsedNames(configFile)
excludeList = utils.appendListFromFileToList(excludeList, fileOfUsedNames)

search_keywords = utils.getKeywords(configFile)
message_text = utils.getMessageText(configFile)
greetings = utils.getGreetings(configFile)
geoLocation = utils.getGeoLocation(configFile)
testMode = utils.getTestMode(configFile)

geoFilter = ''
if geoLocation == '':
    geoFilter = ''
else:
    geoFilter = 'geoUrn=' + geoLocation + '&'

#----------------------------------------------------------
# Run separate searches because LinkedIn ignores OR now
#----------------------------------------------------------
if len(search_keywords) > 1:
    search_keyword_combos = search_keywords
else:
    search_keyword_combos = [search_keywords[0]]

keywords_searched = 0
any_new_messages = False  # track if at least one new person was messaged

for keyword in search_keyword_combos:
    keywords_searched += 1
    print("\n========== Searching for keyword:", keyword, "==========")
    people_list_url = (
        'https://www.linkedin.com/search/results/people/?'
        + geoFilter
        + 'keywords='
        + keyword
        + '&'
        + firstLevelFilter
    )
    print("Search URL:", people_list_url)

    new_people_found = False
    keyword_message_count = 0
    no_results_flag = False

    pageNr = startingPage
    while pageNr < pagesToScan + startingPage:
        people_list_url_pg = people_list_url + 'page=' + str(pageNr)
        print("Search URL:", people_list_url_pg)
        driver.get(people_list_url_pg)
        time.sleep(5)

        # ---------- DETECT "NO RESULTS FOUND" PAGE ----------
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            if "no results found" in page_text:
                print(f"No results found on page {pageNr}. Stopping page loop for keyword: {keyword}")
                no_results_flag = True
                break
        except Exception:
            pass

        # ---------- FIND CONTACT NAMES ----------
        all_span = ''
        try:
            all_span = driver.find_elements(By.TAG_NAME, value="span")
            all_span = [s for s in all_span if s.get_attribute("aria-hidden") == "true" and s.text != "Messaging"]
        except:
            print("Something crashed when reading people names. Retrying...")
            time.sleep(2)
            all_span = driver.find_elements(By.TAG_NAME, value="span")
            all_span = [s for s in all_span if s.get_attribute("aria-hidden") == "true" and s.text != "Messaging"]

        if not all_span:
            print(f"No people found in spans on page {pageNr}. Stopping page loop for keyword: {keyword}")
            no_results_flag = True
            break

        all_full_names = []
        all_names = []
        for j in range(len(all_span)):
            if len(all_span[j].text) > 5 and "Talks about" not in all_span[j].text:
                all_full_names.append(all_span[j].text)
                all_names.append(all_span[j].text.split(" ")[0])

        excluded_count = sum(
            1 for name in all_full_names
            if any(ex.strip().lower() in re.sub(r"[\n\t\s]*", "", name.lower()) for ex in excludeList)
        )
        if excluded_count == len(all_full_names):
            print("All contacts already messaged on this page. Skipping page.")
            pageNr += 1
            continue

        new_people_found = True

        # ---------- GET ALL MESSAGE BUTTONS ----------
        try:
            message_buttons = driver.find_elements(
                By.XPATH,
                "//button[contains(@aria-label,'Message')"
                " or contains(@data-control-name,'message')"
                " or contains(@class,'message-anywhere')"
                " or .//span[normalize-space()='Message']]"
            )
            message_buttons = [b for b in message_buttons if b.is_displayed()]
            for b in message_buttons:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", b)
                    driver.execute_script("arguments[0].removeAttribute('disabled');", b)
                except:
                    pass
            print("message_buttons loaded and len =", len(message_buttons))
        except Exception as e:
            print("Scanning for [Message] buttons failed. Refreshing the screen.", e)
            continue

        # ---------- PROCESS MESSAGES ----------
        max_len = min(len(message_buttons), len(all_full_names), len(all_names))
        crashCount = 0
        for i in range(max_len):
            if crashCount > 2:
                print("Something weird is going on. Exiting.")
                exit()

            boolToExclude = False
            for excludedContact in excludeList:
                if excludedContact.strip().lower() in re.sub(r"[\n\t\s]*", "", all_full_names[i].lower()):
                    boolToExclude = True
            if boolToExclude:
                print("Excluding:", all_full_names[i])
                continue

            greetings_idx = randint(0, len(greetings) - 1)
            message = message_text
            if verboseOn:
                print(message)

            # ensure no previous popups are open before messaging
            close_all_message_popups(driver)

            # click on [Message]
            try:
                driver.execute_script("arguments[0].click();", message_buttons[i])
            except Exception as e:
                print("Cannot click message button:", e)
                continue
            time.sleep(3)

            # activate and type message
            try:
                containers = driver.find_elements(
                    By.XPATH,
                    "//div[contains(@class,'msg-form__msg-content-container') or contains(@class,'msg-form__container')]"
                )
                containers = [c for c in containers if c.is_displayed()]
                if containers:
                    driver.execute_script("arguments[0].click()", containers[-1])
                    time.sleep(0.5)
            except Exception:
                pass

            try:
                input_field = get_latest_message_textbox(driver)
                input_field.send_keys(Keys.ENTER)
                input_field.send_keys(message)
                time.sleep(1)
            except Exception as e:
                print("ERROR typing message:", e)
                crashCount += 1
                continue

            # send or skip in test mode
            try:
                if not testMode:
                    try:
                        driver.find_element(
                            By.XPATH,
                            "//button[@type='submit' and contains(@class,'msg-form__send-button')]"
                        ).click()
                    except Exception:
                        try:
                            driver.find_element(By.XPATH, "//button[contains(@aria-label,'Send')]").click()
                        except Exception:
                            driver.find_element(By.XPATH, "//button[@type='submit']").click()

                saveName(all_full_names[i], fileOfUsedNames)
                time.sleep(1)

                # close message window
                try:
                    close_button = driver.find_element(
                        By.XPATH,
                        "//button[contains(@class,'msg-overlay-bubble-header__control') and contains(@class,'artdeco-button--circle')]"
                    )
                    driver.execute_script("arguments[0].click()", close_button)
                    time.sleep(1)
                except Exception:
                    pass

                # handle discard popup if shown
                handle_discard_popup(driver)

                # ensure all closed before next person
                close_all_message_popups(driver)

                totalMessages += 1
                keyword_message_count += 1
                any_new_messages = True
            except Exception as e:
                print("Something crashed while sending the message. Continue...", e)
                crashCount += 1

            time.sleep(randint(2, 10))

        if no_results_flag:
            break
        pageNr += 1

    if no_results_flag:
        print(f"Stopping early for keyword '{keyword}' (no further pages).")
    elif not new_people_found:
        print("No new people found for keyword:", keyword)
    else:
        print(f"Finished keyword '{keyword}' — sent {keyword_message_count} new messages.")

print("\n================ SUMMARY ================")
print(f"Keywords searched: {keywords_searched}")
print(f"Total messages sent: {totalMessages}")
if not any_new_messages:
    print("No new people left to message. Script ends here.")
else:
    print("Done. Script ends successfully.")
print("=========================================")
