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
pagesToScan = 50
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
        try:
            close_btns = driver.find_elements(
                By.XPATH,
                "//button[contains(@class,'msg-overlay-bubble-header__control')"
                " and contains(@class,'artdeco-button--circle')]"
            )
            close_btns = [b for b in close_btns if b.is_displayed()]
        except Exception:
            close_btns = []

        for b in close_btns:
            try:
                driver.execute_script("arguments[0].click();", b)
                time.sleep(0.3)
                handle_discard_popup(driver)
                closed_any = True
            except Exception:
                pass

        # also close minimized chat heads
        try:
            minimized = driver.find_elements(
                By.XPATH,
                "//button[contains(@class,'msg-overlay-list-bubble__dismiss-button')]"
            )
            minimized = [b for b in minimized if b.is_displayed()]
            for b in minimized:
                try:
                    driver.execute_script("arguments[0].click();", b)
                    time.sleep(0.3)
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
    """Return the most recently opened visible message textbox."""
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
    service = Service('chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=options)
else:
    service = Service(executable_path=r'./chromedriver')
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
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

# build search URL with OR keywords (same logic as before)
people_list_url = 'https://www.linkedin.com/search/results/people/?' + geoFilter + 'keywords='
if len(search_keywords) > 1:
    for i in range(len(search_keywords) - 1):
        people_list_url += search_keywords[i] + orText
    people_list_url += search_keywords[len(search_keywords) - 1] + '&'
else:
    people_list_url += search_keywords[0] + '&'

people_list_url += firstLevelFilter
print("Search URL: " + people_list_url)

# iterate pages until limit
pageNr = startingPage
while pageNr < pagesToScan + startingPage:
    people_list_url_pg = people_list_url + '&page=' + str(pageNr)
    print("Search URL: " + people_list_url_pg)
    driver.get(people_list_url_pg)
    time.sleep(5)

    # find contact first names
    all_span = ''
    try:
        all_span = driver.find_elements(By.TAG_NAME, value="span")
        all_span = [s for s in all_span if s.get_attribute("aria-hidden") == "true" and s.text != "Messaging"]
    except:
        print("Something crashed when reading people names. Wait 2s and try again.")
        time.sleep(2)
        all_span = driver.find_elements(By.TAG_NAME, value="span")
        all_span = [s for s in all_span if s.get_attribute("aria-hidden") == "true" and s.text != "Messaging"]

    all_full_names = []
    all_names = []
    for j in range(len(all_span)):
        if len(all_span[j].text) > 5 and "Talks about" not in all_span[j].text:
            all_full_names.append(all_span[j].text)
            all_names.append(all_span[j].text.split(" ")[0])

    # get all Message buttons
    all_buttons = driver.find_elements(By.TAG_NAME, value="button")
    message_buttons = ''
    try:
        message_buttons = [btn for btn in all_buttons if btn.text == "Message"]
        print("message_buttons loaded and len = " + str(len(message_buttons)))
    except:
        print("Scanning for [Message] buttons failed. Refreshing the screen.")
        continue

    crashCount = 0
    for i in range(0, len(message_buttons)):
        if crashCount > 2:
            print("Something weird is going on. Exiting.")
            exit()

        # skip excluded names
        boolToExclude = any(
            ex.strip().lower() in re.sub(r"[\n\t\s]*", "", all_full_names[i].lower()) for ex in excludeList
        )
        if boolToExclude:
            print("Excluding: " + all_full_names[i])
            continue

        # --- NEW FIX ---
        close_all_message_popups(driver)
        # ----------------

        greetings_idx = randint(0, len(greetings) - 1)
        message = message_text
        if verboseOn:
            print(message)

        # click on [Message]
        driver.execute_script("arguments[0].click();", message_buttons[i])
        time.sleep(3)

        # activate cursor on text box
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
            print("Couldn't select text area. Skipping " + all_names[i])
            continue

        # type in message
        try:
            input_field = get_latest_message_textbox(driver)
            input_field.send_keys(Keys.ENTER)
            input_field.send_keys(message)
            time.sleep(1)
        except Exception as e:
            print("ERROR typing message:", e)
            crashCount += 1
            continue

        # send or skip
        try:
            if not testMode:
                send_clicked = False
                send_xpaths = [
                    # new UI (most common now)
                    "//button[contains(@class,'msg-form__send-button') and not(@disabled)]",
                    # older fallback
                    "//button[@type='submit' and not(@disabled)]",
                    # another variant (aria-label)
                    "//button[contains(@aria-label,'Send') and not(@disabled)]"
                ]

                for xp in send_xpaths:
                    try:
                        btn = driver.find_element(By.XPATH, xp)
                        if btn.is_displayed():
                            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                            time.sleep(0.3)
                            driver.execute_script("arguments[0].click();", btn)
                            send_clicked = True
                            print("Message sent successfully.")
                            break
                    except Exception:
                        continue

                if not send_clicked:
                    print("Could not find [Send] button - possibly new layout or missing selector. Please contact Ricards for a fix.")


            saveName(all_full_names[i], fileOfUsedNames)
            time.sleep(1)

            # close chat window
            try:
                close_button = driver.find_element(
                    By.XPATH,
                    "//button[contains(@class,'msg-overlay-bubble-header__control') and contains(@class,'artdeco-button--circle')]"
                )
                driver.execute_script("arguments[0].click()", close_button)
                time.sleep(1)
            except Exception:
                pass

            handle_discard_popup(driver)
            close_all_message_popups(driver)

            totalMessages += 1
        except Exception as e:
            print("Something crashed while sending the message. Continue...", e)
            crashCount += 1

        time.sleep(randint(2, 10))

    pageNr += 1

print("Messages sent:" + str(totalMessages))
print("Script ends here")
