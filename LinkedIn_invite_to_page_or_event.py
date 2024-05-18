import string
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
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
pagesToScan = 100
invitesInOneRound = 30
roundsToRepeat = 35
verboseOn = 1
fileOfExcludedNames = "../exclude.txt"
credsFile = "../creds.txt"


#********** LOG IN *************
adPrinted = 0
usr = utils.getUser(credsFile, adPrinted, verboseOn)
adPrinted = 1
pwd = utils.getPwd(credsFile, adPrinted, verboseOn)
options = Options()
options.add_experimental_option('detach', True)
driver = webdriver.Chrome('chromedriver.exe', options=options)
utils.loginToLinkedin(driver, usr, pwd)

#***************** LOGIC ***********************
totalConnectRequests = 0

excludeList = utils.getExcludeList(fileOfExcludedNames, adPrinted, verboseOn)
people_list_url = utils.getUrl(configFile)
search_keywords = utils.getKeywords(configFile)
filterByFirstLocation = utils.getBoolFirstLocation(configFile)


# ---> some contacts can not be invited and break the whole flow. We must catch those manually. That's why invitations are done in small invitesInOneRound batches
namesInvited = []
round = 0
while round < roundsToRepeat:
    ###open page to invite contacts
    driver.get(people_list_url)
    time.sleep(5)

    ###click "Locations" and select top location for filter
    if filterByFirstLocation: utils.clickFilterByFirstLocation(driver, verboseOn)

    ###click "Show more results" button many times to load more contacts
    utils.loadContactsToInvite(driver, pagesToScan, verboseOn)

    ###click checkboxes based on search_keyword and exclude ones from the file listOfExcludedNames
    all_checkboxes = driver.find_elements(by=By.XPATH, value="//input[@type='checkbox']")
    checkboxes = [btn for btn in all_checkboxes]
    print("Selecting:")
    invitesSelected = 0
    namesSelected = []    
    for btn in checkboxes:
        nameSelected = utils.selectContactToInvite(driver, btn, search_keywords, excludeList, verboseOn)
        if len(nameSelected) > 0 :
            namesSelected.append(nameSelected)
            invitesSelected += 1
            totalConnectRequests += 1
        if invitesSelected == invitesInOneRound: break
    if invitesSelected == 0:
        print("No people match the search criteria. Leaving the browser open and exiting.")
        round = 99999
    elif namesSelected == namesInvited :
        print("!!! There's a glitch! These names were already invited. Leaving the browser open and exiting.")
        print("Sometimes there is a weird problem with a concrete contact that breaks the flow. You can add such contact to the " + fileOfExcludedNames + " file.")
        print("Other times the LinkedIn just stops accepting more invites to an event without an explanation. Try again after 24 hours.")
        if verboseOn: 
            print("---names selected:")
            print(nameSelected)
            print("---previously invited:")
            print(namesInvited)
        round = 99999
    else:
        print("------Inviting--------")
        ###click Invite button for selected contacts
        invite = driver.find_element(by=By.XPATH, value="//button[@class='artdeco-button artdeco-button--2 artdeco-button--primary ember-view']")
        print("Clicking button ["+invite.text+"]")
        driver.execute_script("arguments[0].click();", invite)
        namesInvited = namesSelected.copy()
        time.sleep(2)
    round += 1

print("Total invites sent:" + str(totalConnectRequests))
print("Script ends here")