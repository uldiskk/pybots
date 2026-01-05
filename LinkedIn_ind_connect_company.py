import re
import os
import string
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from random import randint
import time
import utils
import sys

if len(sys.argv) < 2:
    print("Please specify the html class ID for job field as a cmd parameter")
    exit(1)
else:
    jobHtmlId = sys.argv[1]
    
search_keywords = ''
target_keywords = ''
exclude_keywords = ''
#***************** CONSTANTS ***********************
search_keywords = [ #use %20 for space symbol; and 6 keywords is a limit
                #'DevOps', 'artificial'
                # 'CTO', 'CEO', 'executive', 'founder', 'partner', 'director'
                #  'director', 'chief', 'education', 'edtech', 'govtech'
                # 'php', 'drupal', 'cpacc', 'nextjs'
                # 'prestashop', 'symfony', 'drupal', 'Software%20Engineer'
                #   'react', 'nodejs', 'python', 'quality'
                #    'CTO', 'CSO', 'scrum', 'coach', 'CIO'                 
                #  , 'lead', 'director',
                # 'recruitment', 'talent'
                # 'project', 'manager', 'intelligence'
                 'business', 'analyst'
#]
# target_keywords = [ 
    # 'engineer', 'programmer', 'developer', 'designer', 'specialist', 'technical', 'data scientist', 'analyst',
    # 'qa', 'quality assurance', 'testing', 
    # 'product owner', 'team lead', 'coordinator', 'project manager', 'product manager', 'operations manager', 'master'
# ]
# exclude_keywords = [
#   'board member', 'chairman',
# #   'CTO',    CTO kills "product"
#   'CEO', 'CFO', 'CSO', 'executive', 'chief', 'president'
 ]


geoLocation = '%5B%22106491660%22%5D'
#%5B%22104341318%22%5D for Latvia;       %5B%22106491660%22%5D for Riga;      %5B%22101869288%22%5D Riga, Riga, Latvia
#%5B"105117694"%5D Sweden; %5B"104514075"%5D Denmark; %5B"100456013"%5D Finland
#%5B"102974008"%5D Estonia; %5B"105072130"%5D Poland; %5B"104688944"%5D Croatia; %5B"106178099"%5D Moldova
#%5B"103644278"%5D United States

company = ''    # %5B%22114044%22%5D for Evolution; dynatech %5B"17893047"%5D ; 28Stone %5B"2340444"%5D ; %5B"2553342"%5D 4finance ; %5B"19099020"%5D TET ; %5B"2715"%5D Swisscom global ; 
# %5B"61613"%5D airBaltic ; %5B"10648463"%5D printify ;   %5B%225333%22%5D If Insurance


maxConnects = 3
startingPage = 1
pagesToScan = 1 #10 on one page; 100 is max
credsFile = "../creds.txt"
verboseOn = 0
TestMode = True

#********** LOG IN *************
adPrinted = 0
usr = utils.getUser(credsFile, adPrinted, verboseOn)
adPrinted = 1
pwd = utils.getPwd(credsFile, adPrinted, verboseOn)

if os.name == 'nt':
    options = Options()
    options.add_experimental_option('detach', True)
    service = Service("chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)
else:
    service = Service(executable_path=r'./chromedriver')
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=service, options=options)
utils.loginToLinkedin(driver, usr, pwd)


#***************** LOGIC ***********************
orText = '%20OR%20'
totalConnectRequests = 0
gotIt = 0
crash = 0

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

pageNr = startingPage
while pageNr < pagesToScan+startingPage:
    people_list_url_pg = people_list_url + 'page=' + str(pageNr)
    print("Search URL: " + people_list_url_pg)
    driver.get(people_list_url_pg)
    time.sleep(5)

    try:
        connect_buttons = driver.find_elements(
            By.XPATH,
            "//a[starts-with(@aria-label,'Invite') and contains(@aria-label,'connect')]"
        )

        print("Found Connect buttons:", len(connect_buttons))

        if len(connect_buttons) == 0:
            pageNr += 1
            continue

        for btn in connect_buttons:

            if totalConnectRequests >= maxConnects:
                break

            print("Clicking Connect button")

            driver.execute_script("""
                const btn = arguments[0];
                ['mouseover','mousedown','mouseup','click'].forEach(ev =>
                    btn.dispatchEvent(
                        new MouseEvent(ev, {bubbles:true, cancelable:true, view:window})
                    )
                );
            """, btn)

            time.sleep(2)

            if TestMode:
                print("TEST MODE: Connect clicked, confirmation skipped")

                driver.execute_script(r"""
                (async () => {
                    function deepFind(predicate, root = document) {
                        try {
                            if (!root) return null;
                            if (predicate(root)) return root;
                            if (root.shadowRoot) {
                                const r = deepFind(predicate, root.shadowRoot);
                                if (r) return r;
                            }
                            for (const c of root.children || []) {
                                const f = deepFind(predicate, c);
                                if (f) return f;
                            }
                        } catch (e) {}
                        return null;
                    }

                    let btn = null;
                    for (let i = 0; i < 40; i++) {
                        btn = deepFind(n => {
                            try {
                                return n.tagName === 'BUTTON' &&
                                    n.getAttribute?.('aria-label') === 'Dismiss';
                            } catch (e) { return false; }
                        }, document);
                        if (btn) break;
                        await new Promise(r => setTimeout(r, 250));
                    }

                    if (!btn) return false;

                    btn.scrollIntoView({ block: 'center' });
                    ['mouseover','mousedown','mouseup','click'].forEach(ev =>
                        btn.dispatchEvent(
                            new MouseEvent(ev, { bubbles:true, cancelable:true, view:window })
                        )
                    );

                    return true;
                })();
                """)


                time.sleep(1)
                continue 

            else:
                driver.execute_script(r"""
                (async () => {
                    function deepFind(predicate, root = document) {
                        try {
                            if (!root) return null;
                            if (predicate(root)) return root;
                            if (root.shadowRoot) {
                                const r = deepFind(predicate, root.shadowRoot);
                                if (r) return r;
                            }
                            for (const c of root.children || []) {
                                const f = deepFind(predicate, c);
                                if (f) return f;
                            }
                        } catch (e) {}
                        return null;
                    }

                    let btn = null;
                    for (let i = 0; i < 40; i++) {
                        btn = deepFind(n => {
                            try {
                                return n.tagName === 'BUTTON' &&
                                    n.getAttribute?.('aria-label') === 'Send without a note';
                            } catch (e) { return false; }
                        }, document);
                        if (btn) break;
                        await new Promise(r => setTimeout(r, 250));
                    }

                    if (!btn) return false;

                    btn.scrollIntoView({ block: 'center' });
                    ['mouseover','mousedown','mouseup','click'].forEach(ev =>
                        btn.dispatchEvent(
                            new MouseEvent(ev, { bubbles:true, cancelable:true, view:window })
                        )
                    );

                    return true;
                })();
                """)

                print("Connection request sent.")
                totalConnectRequests += 1
                time.sleep(randint(20, 40))


    except:
        print("Something crashed. Looking for dialog boxes to close")
        crash += 1
        try:
            close_button = driver.find_element(by=By.XPATH, value="//button[starts-with(@class, 'msg-overlay-bubble-header__control')]")
            driver.execute_script("arguments[0].click()", close_button)
            time.sleep(1)
        except Exception:
            print("Closing dialog box failed")
        if(crash > 3):
            print("Several crashes in a row. Exiting...")
            exit()

    pageNr += 1

print("Requests sent:", totalConnectRequests, "(TEST MODE)" if TestMode else "")
print("Script ends here")