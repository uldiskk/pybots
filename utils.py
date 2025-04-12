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
            #bypass the login method screen that randomly appears
            byEmailBtn = driver.find_element(by=By.XPATH, value="//a[starts-with(@class, 'sign-in-form__sign-in-cta')]")
            driver.execute_script("arguments[0].click()", byEmailBtn)
        except:
            print('')
        try:            
            time.sleep(3)
            username = driver.find_element(by=By.XPATH, value="//input[@name='session_key']")
            password = driver.find_element(by=By.XPATH, value="//input[@name='session_password']")
            username.send_keys(usr)
            password.send_keys(pwd)
            screen_found = 1
        except Exception:
            print("Wrong login screen. Restarting...")
            time.sleep(3)
    time.sleep(1)
    submit = driver.find_element(by=By.XPATH, value="//button[@type='submit']").click()
    time.sleep(3)

    #after several tests LinkedIn started asking for Security check. Giving time to pass it manually
    time.sleep(15)
    return driver

def clickFilterByFirstLocation(driver, verboseOn):
    print("Filtering contacts by the first location...")
    if(verboseOn): print("Locating [Locations]")
    but_loc = driver.find_element(by=By.XPATH, value='''//button[@class='artdeco-pill artdeco-pill--slate artdeco-pill--choice artdeco-pill--2 search-reusables__filter-pill-button
       reusable-search-filter-trigger-and-dropdown__trigger']''')
    if(verboseOn): print("Clicking [Locations]")
    driver.execute_script("arguments[0].click();", but_loc)
    time.sleep(1)
    if(verboseOn): print("Locating checkbox")
    check_loc = driver.find_element(by=By.XPATH, value="//input[@class='search-reusables__select-input']")
    if(verboseOn): print("Clicking checkbox")
    driver.execute_script("arguments[0].click();", check_loc)
    time.sleep(1)
    ###click [Show Results]
    show_button = driver.find_element(by=By.XPATH, value="//button[@class='artdeco-button artdeco-button--2 artdeco-button--primary ember-view ml2']")
    if(verboseOn): print("Clicking button ["+show_button.text+"]")
    driver.execute_script("arguments[0].click();", show_button)
    time.sleep(2)
    return

def clickFilterByLocation(driver, verboseOn, l1, l2, l3, l4, l5, l6):
    print("Filtering contacts by the location...")
    if(verboseOn): print("Locating [Locations]")
    but_loc = driver.find_element(by=By.XPATH, value='''//button[@class='artdeco-pill artdeco-pill--slate artdeco-pill--choice artdeco-pill--2 search-reusables__filter-pill-button
       reusable-search-filter-trigger-and-dropdown__trigger']''')
    if(verboseOn): print("Clicking [Locations]")
    driver.execute_script("arguments[0].click();", but_loc)
    time.sleep(1)

    if(verboseOn): print("Locating checkbox")
    check_locs = driver.find_elements(by=By.XPATH, value="//input[@class='search-reusables__select-input']")
    if l1:
        if(verboseOn): print("Clicking checkbox 1")
        driver.execute_script("arguments[0].click();", check_locs[0])
    if l2:
        if(verboseOn): print("Clicking checkbox 2")
        driver.execute_script("arguments[0].click();", check_locs[1])
    if l3:
        if(verboseOn): print("Clicking checkbox 3")
        driver.execute_script("arguments[0].click();", check_locs[2])
    if l4:
        if(verboseOn): print("Clicking checkbox 4")
        driver.execute_script("arguments[0].click();", check_locs[3])
    if l5:
        if(verboseOn): print("Clicking checkbox 5")
        driver.execute_script("arguments[0].click();", check_locs[4])
    if l6:
        if(verboseOn): print("Clicking checkbox 6")
        driver.execute_script("arguments[0].click();", check_locs[5])

    time.sleep(1)

    ###click [Show Results]
    show_button = driver.find_element(by=By.XPATH, value="//button[@class='artdeco-button artdeco-button--2 artdeco-button--primary ember-view ml2']")
    if(verboseOn): print("Clicking button ["+show_button.text+"]")
    driver.execute_script("arguments[0].click();", show_button)
    time.sleep(2)
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
