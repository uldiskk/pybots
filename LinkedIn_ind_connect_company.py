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
target_keywords = 'analyst'
exclude_keywords = 'atea'
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
processedFile = "processed_profiles.txt"

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

def normalize_keywords(val):
    if not val:
        return []
    if isinstance(val, list):
        return [v.lower() for v in val if v]
    return [val.lower()]

target_keywords = normalize_keywords(target_keywords)
exclude_keywords = normalize_keywords(exclude_keywords)

processed_profiles = set()

if os.path.exists(processedFile):
    with open(processedFile, "r", encoding="utf-8") as f:
        processed_profiles = set(
            line.strip() for line in f if line.strip()
        )


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

            # -------- extract profile URL for exclusion memory --------
            try:
                profile_url = btn.get_attribute("href")
            except Exception:
                profile_url = None

            if not profile_url:
                print("No profile URL found, skipping")
                continue

            if profile_url in processed_profiles:
                print("Already processed, skipping:", profile_url)
                continue


            job_text = driver.execute_script("""
                const btn = arguments[0];
                let el = btn;
                while (el && el !== document.body) {
                    if (el.getAttribute && el.getAttribute('role') === 'listitem') {
                        return el.innerText.toLowerCase();
                    }
                    el = el.parentElement;
                }
                return '';
            """, btn)


            if target_keywords:
                if not any(k.lower() in job_text for k in target_keywords):
                    print("Skipping profile (target_keywords)")
                    continue

            if exclude_keywords:
                if any(k.lower() in job_text for k in exclude_keywords):
                    print("Skipping profile (exclude_keywords)")
                    continue

            print("Clicking Connect button")

            driver.execute_script("""
                const el = arguments[0];
                el.scrollIntoView({block:'center', inline:'center'});
                el.focus();

                ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(type => {
                    let ev;
                    if (type.startsWith('pointer')) {
                        ev = new PointerEvent(type, {bubbles:true, cancelable:true});
                    } else {
                        ev = new MouseEvent(type, {bubbles:true, cancelable:true, view:window});
                    }
                    el.dispatchEvent(ev);
                });

                el.click();
            """, btn)

            time.sleep(randint(2, 4))

            if TestMode:
                print("TEST MODE: Connect clicked, confirmation skipped")
                
                with open(processedFile, "a", encoding="utf-8") as f:
                    f.write(profile_url + "\n")
                    f.flush()
                processed_profiles.add(profile_url)

                continue

            # If not test mode, click "Send without a note"
            clicked = driver.execute_script(r"""
                const sleep = ms => new Promise(r => setTimeout(r, ms));

                async function deepFind(predicate, root=document) {
                    try {
                        if (!root) return null;
                        if (predicate(root)) return root;
                        if (root.shadowRoot) {
                            const s = await deepFind(predicate, root.shadowRoot);
                            if (s) return s;
                        }
                        for (const c of root.children || []) {
                            const f = await deepFind(predicate, c);
                            if (f) return f;
                        }
                    } catch (e) {}
                    return null;
                }

                async function run() {
                    for (let i = 0; i < 40; i++) {
                        const b = await deepFind(n => {
                            try {
                                return n.tagName === 'BUTTON' &&
                                       n.getAttribute('aria-label') === 'Send without a note';
                            } catch (e) { return false; }
                        });
                        if (b) {
                            b.scrollIntoView({block:'center'});
                            b.focus();
                            ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(type => {
                                let ev;
                                if (type.startsWith('pointer')) {
                                    ev = new PointerEvent(type, {bubbles:true, cancelable:true});
                                } else {
                                    ev = new MouseEvent(type, {bubbles:true, cancelable:true, view:window});
                                }
                                b.dispatchEvent(ev);
                            });
                            b.click();
                            return true;
                        }
                        await sleep(250);
                    }
                    return false;
                }

                return run();
            """)

            if not clicked:
                print("Send-without-note button not found or click failed")
                continue

            print("Connection request sent.")
            totalConnectRequests += 1

            with open(processedFile, "a", encoding="utf-8") as f:
                f.write(profile_url + "\n")
                f.flush()
            processed_profiles.add(profile_url)


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