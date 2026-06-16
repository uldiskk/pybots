import re
import os.path
import time
import sys
import json
from selenium.webdriver.common.by import By

#-----FUNCTIONS-------------

###read file with names to exclude
def getExcludeList(fileOfExcludedNames, adPrinted, verboseOn):
    adPrinted = printAd(adPrinted)
    excludeList = []
    if os.path.isfile(fileOfExcludedNames):
        with open(fileOfExcludedNames, encoding="utf8") as file_in:    
            for line in file_in:
                excName = re.sub(r"[\n\t\s]*", "", line)
                if len(excName) > 1:
                    excludeList.append(excName)
    else:
        print("The file " + fileOfExcludedNames + " doesn't exist. Nothing will be excluded.")
    return (excludeList)

def appendListFromFileToList(sourceList, fileName):
    if len(fileName) < 1:
        print("No file for storing used names has been specified in the config. Nothing will be saved.")
        return sourceList
    if os.path.isfile(fileName):
        with open(fileName, encoding="utf8") as file_in:    
            for line in file_in:
                excName = re.sub(r"[\n\t\s]*", "", line)
                if len(excName) > 1:
                    sourceList.append(excName)
    else:
        print("The file " + fileName + " doesn't exist. No items will be added to the list.")
    return sourceList

def getUser(fileName, adPrinted, verboseOn):
    adPrinted = printAd(adPrinted)
    user = ''
    if(verboseOn): print("fileName:" + fileName)
    if os.path.isfile(fileName):
        if(verboseOn): print("file found")
        with open(fileName, encoding="utf8") as file_in:
            counter = 0
            for line in file_in:
                if counter==0:
                    user = line
                counter += 1
            if(verboseOn): print("user:" + user)
    else:
        print("The file " + fileName + " doesn't exist. Can't read.")
    return (user)

def getPwd(fileName, adPrinted, verboseOn):
    adPrinted = printAd(adPrinted)
    pwd = ''
    if(verboseOn): print("fileName:" + fileName)
    if os.path.isfile(fileName):
        if(verboseOn): print("file found")
        with open(fileName, encoding="utf8") as file_in:
            counter = 0
            for line in file_in:
                if counter==1:
                    pwd = line
                counter += 1
            if(verboseOn): print("pwd:" + pwd)
    else:
        print("The file " + fileName + " doesn't exist. Can't read.")
    return (pwd)

def printAd(adPrinted):
    if (not adPrinted):
        print("#########################################################################")
        print("   Created by IT Coach - Uldis Karlovs-Karlovskis")
        print("   Check out my website at https://www.uldiskarlovskarlovskis.com/")
        print("#########################################################################")
    return 1
    
def loginToLinkedin(driver, usr, pwd):
    screen_found = 0
    while screen_found < 1:
        driver.get('https://www.linkedin.com')
        time.sleep(3)
        try:
            # bypass the login method screen that sometimes appears
            byEmailBtn = driver.find_element(
                By.XPATH,
                "//a[starts-with(@class, 'sign-in-form__sign-in-cta')]"
            )
            driver.execute_script("arguments[0].click()", byEmailBtn)
        except:
            pass

        try:
            time.sleep(3)
            username = driver.find_element(By.ID, "username")
            password = driver.find_element(By.XPATH, "//input[@name='session_password']")
            username.send_keys(usr)
            password.send_keys(pwd)
            screen_found = 1
            print("Used standard login screen.")
        except Exception:
            pass

        if screen_found < 1:
            try:
                # Alternative login screen (React-based with dynamic IDs)
                username = driver.find_element(By.CSS_SELECTOR, "input[autocomplete='username webauthn']")
                password = driver.find_element(By.CSS_SELECTOR, "input[autocomplete='current-password']")
                username.send_keys(usr)
                time.sleep(0.5)
                # React fields discard send_keys — use native setter + event dispatch so React registers the value
                driver.execute_script("""
                    var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    setter.call(arguments[0], arguments[1]);
                    arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                    arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                """, password, pwd.strip())
                screen_found = 1
                print("Used alternative login screen.")
            except Exception:
                print("Wrong login screen. Restarting...")
                time.sleep(3)

    time.sleep(1)

    # safer click handling: avoid race between find and redirect
    try:
        submit_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        driver.execute_script("arguments[0].click();", submit_btn)
        print("Clicked login button successfully.")
    except Exception:
        try:
            # Fallback: find button containing a "Sign in" span (alternative screen)
            submit_btn = driver.find_element(By.XPATH, "//button[.//span[text()='Sign in']]")
            driver.execute_script("arguments[0].click();", submit_btn)
            print("Clicked login button (alternative) successfully.")
        except Exception as e:
            print("Login likely succeeded but button vanished due to redirect:", e)

    # Give time for possible security / MFA or redirect
    time.sleep(15)
    return driver


def _open_locations_dropdown(driver, verboseOn):
    """Click the Locations filter pill and return (dropdown_element, checkboxes_list)."""
    if(verboseOn): print("Locating [Locations]")
    # Use aria-label — robust against class whitespace changes
    loc_btn = driver.find_element(By.XPATH, "//button[contains(@aria-label,'Locations filter')]")
    controls_id = loc_btn.get_attribute("aria-controls")
    if(verboseOn): print("Clicking [Locations]")
    driver.execute_script("arguments[0].click();", loc_btn)
    time.sleep(1)
    # Scope checkbox lookup to the specific dropdown (not all filters on the page)
    dropdown = driver.find_element(By.ID, controls_id)
    check_locs = dropdown.find_elements(By.CSS_SELECTOR, "input.search-reusables__select-input")
    return dropdown, check_locs

def _click_show_results(driver, verboseOn):
    """Click the visible 'Show results' / 'Apply' button for the open filter dropdown."""
    show_button = None
    for btn in driver.find_elements(By.XPATH, "//button[contains(@class,'artdeco-button--primary') and @aria-label='Apply current filter to show results']"):
        if btn.is_displayed():
            show_button = btn
            break
    if not show_button:
        show_button = driver.find_element(By.XPATH, "//button[@class='artdeco-button artdeco-button--2 artdeco-button--primary ember-view ml2']")
    if(verboseOn): print("Clicking button [" + show_button.text + "]")
    driver.execute_script("arguments[0].click();", show_button)
    time.sleep(2)

def clickFilterByFirstLocation(driver, verboseOn):
    print("Filtering contacts by the first location...")
    dropdown, check_locs = _open_locations_dropdown(driver, verboseOn)
    if(verboseOn): print("Clicking checkbox 1")
    driver.execute_script("arguments[0].click();", check_locs[0])
    time.sleep(1)
    _click_show_results(driver, verboseOn)
    return

def clickFilterByLocation(driver, verboseOn, l1, l2, l3, l4, l5, l6):
    print("Filtering contacts by the location...")
    dropdown, check_locs = _open_locations_dropdown(driver, verboseOn)
    flags = [l1, l2, l3, l4, l5, l6]
    for i, flag in enumerate(flags):
        if flag and i < len(check_locs):
            if(verboseOn): print(f"Clicking checkbox {i+1}")
            driver.execute_script("arguments[0].click();", check_locs[i])
    time.sleep(1)
    _click_show_results(driver, verboseOn)
    return


def loadContactsToInvite(driver, pagesToScan, verboseOn):
    sys.stdout.write("Loading connections on screen")
    sys.stdout.flush()
    pageNr = 1
    
    while pageNr < pagesToScan:
        try:
            all_buttons = driver.find_elements(By.TAG_NAME, value="button")
            connect_buttons = [btn for btn in all_buttons if btn.text == "Show more results"]
            for btn in connect_buttons:
                sys.stdout.write(".")
                sys.stdout.flush()
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(1)
            pageNr += 1
        except:
            sys.stdout.write("-")
            sys.stdout.flush()
            time.sleep(3)
    print("!")
    return

def selectContactToInvite(driver, btn, search_keywords, excludeList, verboseOn):
    nameSelected = ""
    div_parent = btn.find_element(by=By.XPATH, value="..")
    for search_keyword in search_keywords:
        if search_keyword.lower() in div_parent.text.lower():
            boolToExclude = False
            for excludedContact in excludeList:
                withoutSpaceAndTrail = re.sub(r"[\n\t\s]*", "", div_parent.text.lower())
                if excludedContact.strip().lower() in withoutSpaceAndTrail:
                    boolToExclude = True
            if boolToExclude == False:
                driver.execute_script("arguments[0].click();", btn)
                print("+++INVITING:" + div_parent.text + " because matches " + search_keyword)
                nameSelected = div_parent.text.lower()
                time.sleep(0.1)
            else:
                print("!!!Excluding:" + div_parent.text)
            break
    return nameSelected

def dummySum(a, b):
    sum = a + b
    return sum

def getUrl(dictionaryFileName):
    return getStringOrIntFromConfig(dictionaryFileName, 'list_url')

def getBoolFirstLocation(dictionaryFileName):
    return getStringOrIntFromConfig(dictionaryFileName, 'filterFirstLocation')
def getBool2ndLocation(dictionaryFileName):
    return getStringOrIntFromConfig(dictionaryFileName, 'filter2ndLocation')
def getBool3rdLocation(dictionaryFileName):
    return getStringOrIntFromConfig(dictionaryFileName, 'filter3rdLocation')
def getBool4thLocation(dictionaryFileName):
    return getStringOrIntFromConfig(dictionaryFileName, 'filter4thLocation')
def getBool5thLocation(dictionaryFileName):
    return getStringOrIntFromConfig(dictionaryFileName, 'filter5thLocation')
def getBool6thLocation(dictionaryFileName):
    return getStringOrIntFromConfig(dictionaryFileName, 'filter6thLocation')

def getTestMode(dictionaryFileName):
    return getStringOrIntFromConfig(dictionaryFileName, 'testMode')

def getKeywords(dictionaryFileName):
    return getListFromConfig(dictionaryFileName,'search_keywords')

def getGreetings(dictionaryFileName):
    return getListFromConfig(dictionaryFileName,'greetings')

def getGeoLocation(dictionaryFileName):
    return getStringOrIntFromConfig(dictionaryFileName,'geoLocation')

def getMessageText(dictionaryFileName):
    return getStringOrIntFromConfig(dictionaryFileName, 'message_text')

def getFileOfUsedNames(dictionaryFileName):
    return getStringOrIntFromConfig(dictionaryFileName, 'fileOfUsedNames')



def getStringOrIntFromConfig(dictionaryFileName, key):
    with open(dictionaryFileName) as f: 
        data = f.read()
    # reconstructing the data as a dictionary 
    mydict = json.loads(data)
    return mydict.get(key)

def getListFromConfig(dictionaryFileName, key):
    with open(dictionaryFileName) as f: 
        data = f.read()
    # reconstructing the data as a dictionary 
    mydict = json.loads(data)
    return mydict.get(key).split(",")
