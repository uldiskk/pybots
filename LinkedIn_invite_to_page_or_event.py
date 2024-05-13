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
    print("Please specific the configuration file as a cmd parameter")
    exit(1)
else:
    configFile = sys.argv[1]

#***************** CONSTANTS ***********************
pagesToScan = 115
invitesInOneRound = 50
roundsToRepeat = 35
verboseOn = 0
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
    for btn in checkboxes:
        invitesSelected += utils.selectContactToInvite(driver, btn, search_keywords, verboseOn)
        if invitesSelected == invitesInOneRound: break
    ###click Invite button for selected contacts
    if invitesSelected == 0:
        print("No people match the search criteria. Leaving the browser open and exiting")
        round = 99999
    else:
        print("------Inviting--------")
        invite = driver.find_element(by=By.XPATH, value="//button[@class='artdeco-button artdeco-button--2 artdeco-button--primary ember-view']")
        print("Clicking button ["+invite.text+"]")
        driver.execute_script("arguments[0].click();", invite)
        time.sleep(2)
    round += 1

print("Total invites sent:" + str(totalConnectRequests))
print("Script ends here")