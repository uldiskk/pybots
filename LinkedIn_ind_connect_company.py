import re
import string
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from random import randint
import time
import utils

search_keywords = ''
target_keywords = ''
exclude_keywords = ''
#***************** CONSTANTS ***********************
# search_keywords = [ #use %20 for space symbol; and 6 keywords is a limit
                #    'CTO', 'CEO', 'CIO', 'director', 'executive', 'founder'
                #    'CTO', 'CSO', 'scrum', 'coach', 'CIO'                 
                #  , 'lead', 
# ]
# target_keywords = [
#     'CTO', 'CEO', 'CIO', 'chairman', 'director', 'executive', 'founder', 'investor'
#     'board member', 'CFO', 'CSO', 'chief', 'president',
#     'department lead', 'head of', 'vice', 'managing'
# ]
# exclude_keywords = [
#     # 'engineer', kills 'engineering director'
#     'programmer', 'developer', 'designer', 'specialist', 'data scientist', 'analyst',
#     'qa', 'quality assurance', 'testing'
#     # , 'product owner', 'team lead', 'coordinator', 'project manager', 'product manager', 'operations manager', 'master'
#     # 'product', #because of CTO
#     #  'manager', 'team lead', 'teamlead', 
#     # 'service' #because of vice
#     # 'technical', 
# ]



search_keywords = [ #use %20 for space symbol; and 6 keywords is a limit
                #    'devops', 'agile', 'scrum', 'aws', 'azure', 'gcp'
                #    'devops', 'kubernetes', 'artificial intelligence', 'copilot', 'mlops'
                   'ceo', 'cto'
]
# target_keywords = [ 
    # 'engineer', 'programmer', 'developer', 'designer', 'specialist', 'technical', 'data scientist', 'analyst',
    # 'qa', 'quality assurance', 'testing', 
    # 'product owner', 'team lead', 'coordinator', 'project manager', 'product manager', 'operations manager', 'master'
# ]
# exclude_keywords = [
#   'board member', 'chairman',
# #   'CTO',    CTO kills "product"
#   'CEO', 'CFO', 'CSO', 'executive', 'chief', 'president'
# ]




geoLocation = '%5B%22104341318%22%5D'
#%5B%22104341318%22%5D for Latvia;       %5B%22106491660%22%5D for Riga;      %5B%22101869288%22%5D Riga, Riga, Latvia
#%5B"105117694"%5D Sweden; %5B"104514075"%5D Denmark; %5B"100456013"%5D Finland
#%5B"102974008"%5D Estonia; %5B"105072130"%5D Poland; %5B"104688944"%5D Croatia; %5B"106178099"%5D Moldova

company = ''    # %5B%22114044%22%5D for Evolution; dynatech %5B"17893047"%5D ; 28Stone %5B"2340444"%5D ; %5B"2553342"%5D 4finance ; %5B"19099020"%5D TET ; %5B"2715"%5D Swisscom global ; 
# %5B"61613"%5D airBaltic ; %5B"10648463"%5D printify ;   %5B%225333%22%5D If Insurance


maxConnects = 50
startingPage = 1
pagesToScan = 35 #10 on one page; 100 is max
credsFile = "../creds.txt"
verboseOn = 0

#********** LOG IN *************
adPrinted = 0
usr = utils.getUser(credsFile, adPrinted, verboseOn)
adPrinted = 1
pwd = utils.getPwd(credsFile, adPrinted, verboseOn)
options = Options()
options.add_experimental_option('detach', True)
driver = webdriver.Chrome('chromedriver.exe', options=options)

screen_found = 0
while screen_found < 1:
    try:
        driver.get('https://www.linkedin.com')
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



#***************** LOGIC ***********************
orText = '%20OR%20'
totalConnectRequests = 0

geoFilter = ''
if geoLocation == '':
    geoFilter = ''
else:
    geoFilter = 'geoUrn=' + geoLocation + '&'
companyFilter = ''
if company == '':
    companyFilter = ''
else:
    companyFilter = 'currentCompany=' + company + '&'

keywordsFilter = ''
if len(search_keywords) > 1:
    keywordsFilter = 'keywords='
    for i in range(len(search_keywords)):
        keywordsFilter += search_keywords[i]
        if i < len(search_keywords)-1:
            keywordsFilter += orText
    keywordsFilter += '&'
elif len(search_keywords) == 1:
    keywordsFilter = 'keywords=' + search_keywords[0] + '&'

people_list_url = 'https://www.linkedin.com/search/results/people/?' + geoFilter + companyFilter + keywordsFilter + 'network=%5B%22S%22%2C%22O%22%5D&origin=FACETED_SEARCH&spellCorrectionEnabled=false&'

#iterate pages until the limit
pageNr = startingPage
while pageNr < pagesToScan+startingPage:
    people_list_url_pg = people_list_url + 'page=' + str(pageNr)
    print("Search URL: " + people_list_url_pg)
    driver.get(people_list_url_pg)
    time.sleep(5)

    try:
        #find contact first names
        all_span = driver.find_elements(By.TAG_NAME, value="span")
        all_span = [s for s in all_span if s.get_attribute("aria-hidden") == "true"]
        #find contact jobs
        all_jobs = driver.find_elements(by=By.XPATH, value="//div[starts-with(@class, 'entity-result__primary-subtitle t-14 t-black t-normal')]")

        ### OUTPUT FOR TESTING
        if (verboseOn):
            vcounter = 0
            for n in all_span:
                print(":" + str(vcounter))
                print(n.text + "|len:" + str(len(n.text)) )
                vcounter+=1
            print("--------------")
            vcounter = 0
            for n in all_jobs:
                print(":" + str(vcounter))
                print(n.text)
                vcounter+=1
            print("--------------")


        #make array of contact names out of messy array
        all_full_names = []
        all_names = []
        if (verboseOn): print(str(len(all_span)) + " elems in the messy array of tag 'span'")
        maxRange = 56
        if len(all_span) < maxRange:
            maxRange = len(all_span)
        for j in range(maxRange):
            if len(all_span[j].text) > 5 and "Talks about" not in all_span[j].text and "Messaging" not in all_span[j].text and "•" not in all_span[j].text:
                all_full_names.append(all_span[j].text)
                all_names.append(all_span[j].text.split(" ")[0])
            else:
                if(verboseOn): print(all_span[j].text + " ignored")

        isOutOfSearches = False
        namesOnPage = len(all_names)
        if namesOnPage != 10:
            if namesOnPage == 3 or namesOnPage == 4:
                print(str(len(all_names)) + " instead of 10 names. Run out of monthly limit of profile searches? Will try to ignore it with big waittimes..." )
                time.sleep(60*5)
                isOutOfSearches = True
            elif namesOnPage == 0:
                print("!!!!!!!!!!!!!!! oopsy doozi, no names found, which may mean you got blocked. Exiting...")
                pageNr = 1000
                exit()
            else:
                if (verboseOn):
                    print(str(namesOnPage) + " instead of 10 names.")
                    for n in all_names:
                        print(n)


        #get all Connect buttons
        all_buttons = driver.find_elements(By.TAG_NAME, value="button")

        ### OUTPUT FOR TESTING
        if(verboseOn):
            vcounter = 0
            for n in all_buttons:
                print(":" + str(vcounter))
                print(n.text)
                vcounter+=1
            print("--------------")

        contact_buttons = []
        for btn in all_buttons:
            if btn.text in ['Connect', 'Pending', 'Message', 'Follow']:
                contact_buttons.append(btn)
        if(verboseOn): print("contact_buttons loaded and len = " + str(len(contact_buttons)))
        if len(contact_buttons) != 10:
            if(isOutOfSearches):
                if(verboseOn): print("Found " + str(len(contact_buttons)) + " buttons.")
            elif(namesOnPage!=len(contact_buttons)):
                print(str(len(contact_buttons)) + " instead of " + str(namesOnPage) + " buttons. Skip the page.")
                pageNr += 1
                continue

        counter = 0
        for btn in contact_buttons:
            if (totalConnectRequests < maxConnects):
                boolToExclude = True
                theJob = all_jobs[counter].text.lower()
                if btn.text == "Connect":
                    if(verboseOn): print("checking job - " + theJob)
                    if len(target_keywords) > 0:
                        for targetRole in target_keywords:
                            if(verboseOn): print("comparing to - " + targetRole)
                            if targetRole.strip().lower() in re.sub(r"[\n\t\s]*", "", theJob):
                                print(targetRole + " is found in " + theJob)
                                boolToExclude = False
                    else:
                        boolToExclude = False
                    if len(exclude_keywords) > 0:
                        for excludeRole in exclude_keywords:
                            if excludeRole.strip().lower() in re.sub(r"[\n\t\s]*", "", theJob):
                                print(excludeRole + " is BADLY found in " + theJob)
                                boolToExclude = True
                else:
                    if(verboseOn): print("Ignoring "+ str(counter) + " contact because button=" + btn.text)
                    time.sleep(0.1)
                
                if boolToExclude == False:
                    print("Connecting with " + all_names[counter])
                    
                    # click on [Connect]
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(2)

                    note_button = driver.find_element(by=By.XPATH, value="//button[@aria-label='Send now']")
                    driver.execute_script("arguments[0].click();", note_button)
                    time.sleep(1)

                    try:
                        got_it_button = driver.find_element(by=By.XPATH, value="//button[@aria-label='Got it']")
                        print("Found [Got it] button which means you're out of weekly Connects. Exiting for your own sake.")
                        pageNr = 1000
                        counter = 1000
                        exit()
                    except Exception:
                        if(verboseOn): print("[Got it] button now found. Continuing safely.")


                    #Dismiss for people who ask to provide email
                    try:
                        dismiss_button = driver.find_element(by=By.XPATH, value="//button[@aria-label='Dismiss']")
                        driver.execute_script("arguments[0].click();", dismiss_button)
                    except Exception:
                        good = 0
                    totalConnectRequests += 1
                    time.sleep(randint(15, 30))
            else:
                print ("maxConnects of " + maxConnects + " is reached. Skipping.")
            counter+=1
    except:
        print("Something crashed. Looking for dialog boxes to close")
        try:
            close_button = driver.find_element(by=By.XPATH, value="//button[starts-with(@class, 'msg-overlay-bubble-header__control artdeco-button artdeco-button--circle artdeco-button--muted artdeco-button--1 artdeco-button--tertiary ember-view')]")
            driver.execute_script("arguments[0].click()", close_button)
            time.sleep(1)
        except Exception:
            print("1st Closing dialog box crashed, no worries")
        try:
            close_button = driver.find_element(by=By.XPATH, value="//button[starts-with(@class, 'msg-overlay-bubble-header__control artdeco-button artdeco-button--circle artdeco-button--1 artdeco-button--primary ember-view')]")
            driver.execute_script("arguments[0].click()", close_button)
            time.sleep(1)
        except Exception:
            print("2nd Closing dialog box crashed. Continuing with the next page")
    pageNr += 1
    #go to the next page

print("Requests sent:" + str(totalConnectRequests))


print("Script ends here")