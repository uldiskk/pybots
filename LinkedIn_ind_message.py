import re
import string
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
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
pagesToScan = 50 #10 on one page
verboseOn = 0
fileOfExcludedNames = "../exclude.txt"
credsFile = "../creds.txt"


#-----FUNCTIONS-------------
def saveName(name, fileOfUsedNames):
    with open(fileOfUsedNames, 'a', encoding="utf8") as file:
        file.write(name + '\n')
    print("Name " + name + " saved")

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

people_list_url = 'https://www.linkedin.com/search/results/people/?' + geoFilter + 'keywords=' 
if len(search_keywords) > 1:
    for i in range(len(search_keywords)-1):
        people_list_url += search_keywords[i] + orText
    people_list_url += search_keywords[len(search_keywords)-1] + '&'
else:
    people_list_url += search_keywords[0] + '&'

people_list_url += firstLevelFilter
print("Search URL: " + people_list_url)

#iterate pages until the limit
pageNr = startingPage
while pageNr < pagesToScan+startingPage:
    people_list_url_pg = people_list_url + '&page=' + str(pageNr)
    print("Search URL: " + people_list_url_pg)
    driver.get(people_list_url_pg)
    time.sleep(5)

    #find contact first names
    all_span = ''
    try:
        all_span = driver.find_elements(By.TAG_NAME, value="span")
        all_span = [s for s in all_span if s.get_attribute("aria-hidden") == "true" and s.text != "Messaging"]
    except:
        print("Something crashed when reading people names. Wait 2s and try again.")
        time.sleep(2)
        all_span = driver.find_elements(By.TAG_NAME, value="span")
        all_span = [s for s in all_span if s.get_attribute("aria-hidden") == "true" and s.text != "Messaging"]

    if verboseOn:
        counter = 0
        for n in all_span:
            print(":" + str(counter))
            print(n.text + "|len:" + str(len(n.text)) )
            counter+=1


    all_full_names = []
    all_names = []
    for j in range(len(all_span)):
        if len(all_span[j].text) > 5 and "Talks about" not in all_span[j].text:
            all_full_names.append(all_span[j].text)
            all_names.append(all_span[j].text.split(" ")[0])
        
    #get all Message buttons
    all_buttons = driver.find_elements(By.TAG_NAME, value="button")
    message_buttons = ''
    try:
        message_buttons = [btn for btn in all_buttons if btn.text == "Message"]
        print("message_buttons loaded and len = " + str(len(message_buttons)))
    except:
        print("Scanning for [Message] buttons failed. Did someone send a chat message? Refreshing the screen.")
        continue
    
    crashCount = 0
    for i in range(0, len(message_buttons)):
        if crashCount > 2:
            print("Something weird is going on. Exiting.")
            exit()
        boolToExclude = False
        for excludedContact in excludeList:
            if excludedContact.strip().lower() in re.sub(r"[\n\t\s]*", "", all_full_names[i].lower()):
                boolToExclude = True
        if boolToExclude == False:
            greetings_idx = randint(0, len(greetings)-1)
            # message = greetings[greetings_idx] + " " + all_names[i] + ", " + message_text
            message = message_text
            if verboseOn: print(message)

            # click on [Message]
            driver.execute_script("arguments[0].click();", message_buttons[i])
            time.sleep(3)

            # activate curson on text box
            try:
                main_div = driver.find_element(by=By.XPATH, value="//div[starts-with(@class, 'msg-form__msg-content-container')]")
                driver.execute_script("arguments[0].click()", main_div)
                time.sleep(2)
            except Exception:
                print("Couldn't select text area. Skipping " + all_names[i])                
            
            # type in the message
            try:
                input_field = driver.find_element(by=By.XPATH, value="//div[starts-with(@class, 'msg-form__contenteditable')]")
                time.sleep(2)
                input_field.send_keys(Keys.ENTER)
                input_field.send_keys(message)
                time.sleep(2)
                # paragraphs[-5].send_keys(message) #CRASHED HERE WHEN SOMEONE SENDS MESSAGE
            except Exception as e:
                time.sleep(1)
                if verboseOn: print("ERROR:", e)
                print("Crashed on .send_keys(message), will try to close unexpected dialog box")
                time.sleep(1)
                try:
                    x_button = driver.find_element(by=By.XPATH, value="//button[starts-with(@class, 'msg-overlay-bubble-header__control artdeco-button artdeco-button--circle artdeco-button--1 artdeco-button--primary ember-view')]")
                    driver.execute_script("arguments[0].click()", x_button)
                    time.sleep(2)
                except Exception:
                    time.sleep(1)
                try:
                    x_button = driver.find_element(by=By.XPATH, value="//button[starts-with(@class, 'msg-overlay-bubble-header__control artdeco-button artdeco-button--circle artdeco-button--muted artdeco-button--1 artdeco-button--tertiary ember-view')]")
                    driver.execute_script("arguments[0].click()", x_button)
                    time.sleep(2)
                except Exception:
                    time.sleep(1)
                try:
                    discard_button = driver.find_element(by=By.XPATH, value="//button[starts-with(@class, 'artdeco-button artdeco-button--2 artdeco-button--primary ember-view artdeco-modal__confirm-dialog-btn')]")
                    driver.execute_script("arguments[0].click()", discard_button)
                    time.sleep(2)
                except Exception:
                    time.sleep(1)                        
            else:
                if verboseOn: print("Typing the message is successful. Sending...")
                time.sleep(1)

                try:
                    if not testMode:
                        #click SEND button with type submit
                        submit_button = driver.find_element(by=By.XPATH, value="//button[@type='submit']").click()
                    saveName(all_full_names[i], fileOfUsedNames)
                    time.sleep(2)
                        
                    #CLOSE 1:1 message window
                    close_button = driver.find_element(by=By.XPATH, value="//button[starts-with(@class, 'msg-overlay-bubble-header__control artdeco-button artdeco-button--circle artdeco-button--muted artdeco-button--1 artdeco-button--tertiary ember-view')]")
                    driver.execute_script("arguments[0].click()", close_button)
                    time.sleep(2)

                    ######DISCARD button for testing when typed message is not sent
                    if testMode:
                        time.sleep(3)
                        x_button = driver.find_element(by=By.XPATH, value="//button[starts-with(@class, 'msg-overlay-bubble-header__control artdeco-button artdeco-button--circle artdeco-button--muted artdeco-button--1 artdeco-button--tertiary ember-view')]")
                        driver.execute_script("arguments[0].click()", x_button)
                        time.sleep(2)
                        discard_button = driver.find_element(by=By.XPATH, value="//button[starts-with(@class, 'artdeco-button artdeco-button--2 artdeco-button--primary ember-view artdeco-modal__confirm-dialog-btn')]")
                        driver.execute_script("arguments[0].click()", discard_button)


                    totalMessages += 1
                except:
                    print("Something crushed while sending the message. Continue...")
                    crashCount += 1
                time.sleep(randint(2, 10))
        else:
            print("Excluding: " + all_full_names[i])
    pageNr += 1
    #go to the next page

print("Messages sent:" + str(totalMessages))

print("Script ends here")