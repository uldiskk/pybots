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
from selenium.common.exceptions import StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from random import randint
import time
import utils
import sys

search_keywords = ''
target_keywords = ''
exclude_keywords = ''
#***************** CONSTANTS ***********************
search_keywords = [ #use %20 for space symbol; and 6 keywords is a limit
                #'DevOps', 'artificial'
                 'CTO', 'CEO', 'executive', 'founder', 'director', 'board'
                #  'director', 'chief', 'education', 'edtech', 'govtech'
                # 'php', 'drupal', 'cpacc', 'nextjs'
                # 'prestashop', 'symfony', 'drupal', 'Software%20Engineer'
                #   'react', 'nodejs', 'python', 'quality'
                #    'CTO', 'CSO', 'scrum', 'coach', 
                #  , 'lead', 'director', 'chief', 'CIO'
                # 'recruitment', 'talent'
                # 'project', 'manager', 'intelligence'
                # 'board', 'founder'
                #   'speaker','intelligence'
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


geoLocation = ''
#%5B%22104341318%22%5D for Latvia;       %5B%22106491660%22%5D for Riga;      %5B%22101869288%22%5D Riga, Riga, Latvia
#%5B"105117694"%5D Sweden; %5B"104514075"%5D Denmark; %5B"100456013"%5D Finland
#%5B"102974008"%5D Estonia; %5B"105072130"%5D Poland; %5B"104688944"%5D Croatia; %5B"106178099"%5D Moldova
#%5B"103644278"%5D United States

company = ''    # %5B%22114044%22%5D for Evolution; dynatech %5B"17893047"%5D ; 28Stone %5B"2340444"%5D ; %5B"2553342"%5D 4finance ; %5B"19099020"%5D TET ; %5B"2715"%5D Swisscom global ;
# %5B"61613"%5D airBaltic ; %5B"10648463"%5D printify ;   %5B%225333%22%5D If Insurance


maxConnects = 100
startingPage = 1
pagesToScan = 50 #10 on one page; 100 is max
credsFile = "../creds.txt"
verboseOn = 0
TestMode = False
processedFile = "processed_profiles.txt"

#********** LOG IN *************
print("=== LinkedIn_ind_connect_company.py starting ===", flush=True)
adPrinted = 0
usr = utils.getUser(credsFile, adPrinted, verboseOn)
adPrinted = 1
pwd = utils.getPwd(credsFile, adPrinted, verboseOn)

use_visible_browser = utils.should_use_visible_browser()
if use_visible_browser:
    fail_count = utils.get_login_failure_count()
    print(f"Login has failed {fail_count} times in a row — launching a VISIBLE Chrome "
          f"window this run instead of headless.", flush=True)
else:
    print(f"Launching browser (headless) as {usr.strip()}...", flush=True)

if os.name == 'nt':
    options = Options()
    if not use_visible_browser:
        options.add_argument("--headless=new")
    options.add_experimental_option('detach', True)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
else:
    options = webdriver.ChromeOptions()
    options.binary_location = "/usr/bin/google-chrome"
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
    'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})
print("Browser launched. Attempting LinkedIn login...", flush=True)
utils.loginToLinkedin(driver, usr, pwd)
print(f"Login complete. Current page: {driver.title} | {driver.current_url}", flush=True)


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
print(f"Already-processed profiles: {len(processed_profiles)}", flush=True)
print(f"Settings: pagesToScan={pagesToScan}, maxConnects={maxConnects}, TestMode={TestMode}", flush=True)

def run_pymk_fallback(driver, maxConnects, totalConnectRequests, TestMode, processedFile, processed_profiles):
    """Top up connection requests via LinkedIn's 'People You May Know' page.

    Used when the keyword search runs dry (most often because the account has
    hit LinkedIn's monthly commercial-search-limit for the People search, which
    starves the search results down to near-zero regardless of retries). PYMK
    is a separate LinkedIn surface not subject to that limit, and unlike the
    search results page it typically sends the invite immediately on click
    rather than opening a 'Send without a note' confirmation modal — so both
    paths are handled below.
    """
    print("\n=== Falling back to People You May Know (search results exhausted) ===", flush=True)
    driver.get("https://www.linkedin.com/mynetwork/grow/")
    time.sleep(5)

    stall_rounds = 0
    while totalConnectRequests < maxConnects and stall_rounds < 4:
        connect_buttons = driver.find_elements(
            By.XPATH,
            "//button[contains(@aria-label,'Connect') or contains(@aria-label,'connect')]"
        )
        if not connect_buttons:
            print("No PYMK connect buttons found on page.", flush=True)
            break

        progressed = False
        for btn in connect_buttons:
            if totalConnectRequests >= maxConnects:
                break

            try:
                profile_url = driver.execute_script("""
                    let el = arguments[0], hops = 0;
                    while (el && el !== document.body && hops < 8) {
                        const a = el.querySelector ? el.querySelector('a[href*="/in/"]') : null;
                        if (a) return a.href;
                        el = el.parentElement;
                        hops++;
                    }
                    return null;
                """, btn)
            except Exception:
                continue

            if not profile_url:
                continue
            profile_url = profile_url.split('?')[0]

            if profile_url in processed_profiles:
                continue

            try:
                profile_name = btn.get_attribute("aria-label") or profile_url
            except Exception:
                profile_name = profile_url

            print(f"Clicking Connect (PYMK): {profile_name}", flush=True)

            try:
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
            except Exception as e:
                print(f"PYMK click failed for {profile_name}: {type(e).__name__}: {e}", flush=True)
                continue

            time.sleep(randint(2, 4))

            if TestMode:
                print("TEST MODE: PYMK connect clicked, confirmation skipped", flush=True)
                with open(processedFile, "a", encoding="utf-8") as f:
                    f.write(profile_url + "\n")
                    f.flush()
                processed_profiles.add(profile_url)
                progressed = True
                continue

            # Confirm the invite actually went out: either a confirmation modal
            # appears (older/'Add a note' style flow), or the button itself
            # disappears / flips to a pending state (the common PYMK behavior).
            # Note: if the card was already removed from the DOM by the time we
            # get here, Selenium raises StaleElementReferenceException just from
            # passing `btn` into execute_script (before any JS runs) — that in
            # itself is the strongest signal the invite went through.
            try:
                result = driver.execute_script(r"""
                const btn = arguments[0];
                const sleep = ms => new Promise(r => setTimeout(r, ms));
                async function run() {
                    for (let i = 0; i < 20; i++) {
                        const modalBtn = document.querySelector("button[aria-label='Send without a note']")
                            || document.querySelector("button[aria-label='Send now']")
                            || document.querySelector("button[aria-label='Send invitation']");
                        if (modalBtn) {
                            modalBtn.scrollIntoView({block:'center'});
                            modalBtn.focus();
                            ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(type => {
                                let ev;
                                if (type.startsWith('pointer')) {
                                    ev = new PointerEvent(type, {bubbles:true, cancelable:true});
                                } else {
                                    ev = new MouseEvent(type, {bubbles:true, cancelable:true, view:window});
                                }
                                modalBtn.dispatchEvent(ev);
                            });
                            modalBtn.click();
                            return 'modal_sent';
                        }
                        if (!document.body.contains(btn)) return 'removed';
                        const label = (btn.getAttribute('aria-label') || '').toLowerCase();
                        if (label.includes('pending')) return 'pending_label';
                        await sleep(250);
                    }
                    return 'timeout';
                }
                return run();
            """, btn)
            except StaleElementReferenceException:
                result = 'removed'

            if result == 'timeout':
                print(f"Could not confirm PYMK invite was sent for: {profile_name} (skipping, not marked processed)", flush=True)
                continue

            totalConnectRequests += 1
            progressed = True
            print(f"Connection request sent via PYMK ({totalConnectRequests}/{maxConnects}): {profile_name} [{result}]", flush=True)

            with open(processedFile, "a", encoding="utf-8") as f:
                f.write(profile_url + "\n")
                f.flush()
            processed_profiles.add(profile_url)

            time.sleep(randint(20, 40))

        if totalConnectRequests >= maxConnects:
            break

        stall_rounds = 0 if progressed else stall_rounds + 1

        # Try to load more suggestions before giving up.
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        try:
            for mb in driver.find_elements(By.XPATH, "//button[contains(.,'Show more')]"):
                if mb.is_displayed():
                    driver.execute_script("arguments[0].click();", mb)
                    time.sleep(3)
                    break
        except Exception:
            pass

    return totalConnectRequests


pageNr = startingPage
consecutive_empty = 0
pagesVisited = 0
while pageNr < pagesToScan+startingPage:
    people_list_url_pg = people_list_url + 'page=' + str(pageNr)
    print(f"\n--- Page {pageNr}/{pagesToScan} ---", flush=True)
    print(f"URL: {people_list_url_pg}", flush=True)
    driver.get(people_list_url_pg)
    time.sleep(5)
    pagesVisited += 1

    try:
        connect_buttons = driver.find_elements(
            By.XPATH,
            "//a[starts-with(@aria-label,'Invite') and contains(@aria-label,'connect')]"
        )

        print("Found Connect buttons:", len(connect_buttons), flush=True)

        if len(connect_buttons) == 0:
            print("Page title:", driver.title, flush=True)
            try:
                if "monthly limit for profile searches" in driver.find_element(By.TAG_NAME, "body").text.lower():
                    print("LinkedIn's monthly search limit has been reached for this account. "
                          "Search-based results will stay empty until it resets. "
                          "Stopping the search phase early.", flush=True)
                    consecutive_empty = 4  # force exit of the search phase below
            except Exception:
                pass
            consecutive_empty += 1
            if consecutive_empty > 3:
                print("Found Connect buttons: 0 more than 3 times in a row. Ending search phase.", flush=True)
                break
            pageNr += 1
            continue
        consecutive_empty = 0

        for btn in connect_buttons:

            if totalConnectRequests >= maxConnects:
                break

            # -------- extract profile URL for exclusion memory --------
            try:
                profile_url = btn.get_attribute("href")
            except Exception:
                profile_url = None

            if not profile_url:
                print("No profile URL found, skipping", flush=True)
                continue

            if profile_url in processed_profiles:
                print("Already processed, skipping:", profile_url, flush=True)
                continue

            profile_name = btn.get_attribute("aria-label") or profile_url

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
                    print("Skipping profile (target_keywords)", flush=True)
                    continue

            if exclude_keywords:
                if any(k.lower() in job_text for k in exclude_keywords):
                    print("Skipping profile (exclude_keywords)", flush=True)
                    continue

            print(f"Clicking Connect: {profile_name}", flush=True)

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
                print("TEST MODE: Connect clicked, confirmation skipped", flush=True)

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
                print(f"Send-without-note button not found for: {profile_name}", flush=True)
                continue

            totalConnectRequests += 1
            print(f"Connection request sent ({totalConnectRequests}/{maxConnects}): {profile_name}", flush=True)

            with open(processedFile, "a", encoding="utf-8") as f:
                f.write(profile_url + "\n")
                f.flush()
            processed_profiles.add(profile_url)


            time.sleep(randint(20, 40))

        if totalConnectRequests >= maxConnects:
            print(f"Max connects ({maxConnects}) reached. Stopping.", flush=True)
            break

    except Exception as e:
        print(f"Exception on page {pageNr}: {type(e).__name__}: {e}", flush=True)
        print("Attempting to close any open dialogs...", flush=True)
        crash += 1
        try:
            close_button = driver.find_element(by=By.XPATH, value="//button[starts-with(@class, 'msg-overlay-bubble-header__control')]")
            driver.execute_script("arguments[0].click()", close_button)
            time.sleep(1)
        except Exception:
            print("Closing dialog box failed", flush=True)
        if(crash > 3):
            print("Several crashes in a row. Exiting...", flush=True)
            exit()

    pageNr += 1

searchPhaseRequests = totalConnectRequests
if totalConnectRequests < maxConnects:
    try:
        totalConnectRequests = run_pymk_fallback(
            driver, maxConnects, totalConnectRequests, TestMode, processedFile, processed_profiles
        )
    except Exception as e:
        print(f"PYMK fallback failed: {type(e).__name__}: {e}", flush=True)

print(f"\n=== Run complete ===", flush=True)
print(f"From keyword search : {searchPhaseRequests}", flush=True)
print(f"From People You May Know : {totalConnectRequests - searchPhaseRequests}", flush=True)
print(f"Pages visited : {pagesVisited}", flush=True)
print(f"Requests sent : {totalConnectRequests}{' (TEST MODE)' if TestMode else ''}", flush=True)
print(f"Crashes       : {crash}", flush=True)
