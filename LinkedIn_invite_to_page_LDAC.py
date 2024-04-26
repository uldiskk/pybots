import string
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from random import randint
import time
import os.path
import sys
import utils

#***************** CONSTANTS ***********************
pageID = "90784427" #ID of the Latvia DevOps & Agile Community
search_keywords = ['devops', 'dev ops', 'DevSecOps', 'BizOps',
                  'system administrator', 'IT admin', 'sysadmin',
                  'database',
                  'configuration manager', 'scm',
                  'Network engineer', 'network infrastructure', 'network specialist',
                  'sre', 'site reliability',
                'full stack', 'full-stack', 'fullstack', 
                'ios dev', 'android developer',
                'web developer', 'go developer', 'java developer', 
                'software developer', 
                'software engineer', 'software team lead', 'software architect',
                'system engineer', 
                
                'aws', 'amazon', 
                'google', 'gcp',
                'azure', 'dot net', 

                'cloud', 'cloud engineer',
                'k8s', 'kubernetes',
                'solutions architect', 
                'network services',
                'operations manager', 
                'engineering manager', 'IT manager', 'project manager', 'delivery lead',
                'cto',
                'integration architect', 
                
                '.net developer', 
                'ui developer', 
                'IT operations', 
                'python', 
                'platform engineer', 
                'infrastructure',
                'agile', 'scrum', 'kanban' ] 
pagesToScan = 115
invitesInOneRound = 50
roundsToRepeat = 35
filterByFirstLocation = 1 #boolean
verboseOn = 0
listOfExcludedNames = "../exclude.txt"
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

# ---> some contacts can not be invited and break the whole flow. We must catch those manually. That's why invitations are done in small invitesInOneRound batches
###read file with names to exclude
excludeList = []
if os.path.isfile(listOfExcludedNames):
    with open(listOfExcludedNames, encoding="utf8") as file_in:    
        for line in file_in:
            excludeList.append(line)
else:
    print("The file " + listOfExcludedNames + " doesn't exist. Nothing will be excluded.")

round = 0
while round < roundsToRepeat:
    ###open page to invite contacts
    people_list_url = 'https://www.linkedin.com/company/' + pageID + '/admin/?invite=true'
    driver.get(people_list_url)
    time.sleep(5)

    ###click "Locations" and select top location for filter
    if filterByFirstLocation:
        print("Locating [Locations]")
        but_loc = driver.find_element(by=By.XPATH, value='''//button[@class='artdeco-pill artdeco-pill--slate artdeco-pill--choice artdeco-pill--2 search-reusables__filter-pill-button
       reusable-search-filter-trigger-and-dropdown__trigger']''')
        print("Clicking [Locations]")
        driver.execute_script("arguments[0].click();", but_loc)
        time.sleep(1)
        print("Locating checkbox")
        check_loc = driver.find_element(by=By.XPATH, value="//input[@class='search-reusables__select-input']")
        print("Clicking checkbox")
        driver.execute_script("arguments[0].click();", check_loc)
        time.sleep(1)
        ###click [Show Results]
        show_button = driver.find_element(by=By.XPATH, value="//button[@class='artdeco-button artdeco-button--2 artdeco-button--primary ember-view ml2']")
        print("Clicking button ["+show_button.text+"]")
        driver.execute_script("arguments[0].click();", show_button)
        time.sleep(2)
    print("------Inviting--------")
    ###click "Show more results" button many times to load more contacts
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
        except:
            print("-")
        time.sleep(2)
        pageNr += 1
    print("!")

    ###click checkboxes based on search_keyword and exclude ones from the file listOfExcludedNames
    all_checkboxes = driver.find_elements(by=By.XPATH, value="//input[@type='checkbox']")
    checkboxes = [btn for btn in all_checkboxes]
    print("Selecting:")
    invitesSelected = 0
    for btn in checkboxes:
        div_parent = btn.find_element(by=By.XPATH, value="..")
        for search_keyword in search_keywords:
            if search_keyword.lower() in div_parent.text.lower():
                boolToExclude = False
                for excludedContact in excludeList:
                    if excludedContact.strip().lower() in div_parent.text.lower():
                        boolToExclude = True
                if boolToExclude == False:
                    driver.execute_script("arguments[0].click();", btn)
                    print("+++INVITING:" + div_parent.text)
                    invitesSelected += 1
                    totalConnectRequests += 1
                    time.sleep(0.5)
                else:
                    print("!!!Excluding:" + div_parent.text)
                break
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