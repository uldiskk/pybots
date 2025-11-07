import re
import os
import string
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver import Keys
from random import randint
import time
import os.path
import sys
import utils
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

if len(sys.argv) < 2:
    print("Please specify the configuration file as a cmd parameter")
    exit(1)
else:
    configFile = sys.argv[1]

#***************** CONSTANTS ***********************
startingPage = 1
pagesToScan = 50
verboseOn = 0
fileOfExcludedNames = "../exclude.txt"
credsFile = "../creds.txt"

# ========================= HELPERS =============================

def saveName(name, fileOfUsedNames):
    with open(fileOfUsedNames, "a", encoding="utf8") as f:
        f.write(name + "\n")
    print("Name", name, "saved")


def handle_discard_popup(driver):
    try:
        discard_button = driver.find_element(
            By.XPATH,
            "//button[contains(@class,'artdeco-button') and (normalize-space()='Discard' or contains(.,'Discard'))]",
        )
        driver.execute_script("arguments[0].click();", discard_button)
        print("Detected and clicked 'Discard' popup.")
        time.sleep(1)
    except Exception:
        pass


def close_all_message_popups(driver, max_passes=4):
    """Close all LinkedIn message overlays."""
    for _ in range(max_passes):
        closed_any = False
        try:
            close_btns = driver.find_elements(
                By.XPATH,
                "//button[contains(@class,'msg-overlay-bubble-header__control') and contains(@class,'artdeco-button--circle')]",
            )
            for b in close_btns:
                if b.is_displayed():
                    driver.execute_script("arguments[0].click();", b)
                    closed_any = True
                    time.sleep(0.3)
                    handle_discard_popup(driver)
        except Exception:
            pass

        try:
            minimized = driver.find_elements(
                By.XPATH,
                "//button[contains(@class,'msg-overlay-list-bubble__dismiss-button')]",
            )
            for b in minimized:
                if b.is_displayed():
                    driver.execute_script("arguments[0].click();", b)
                    closed_any = True
                    time.sleep(0.3)
                    handle_discard_popup(driver)
        except Exception:
            pass

        if not closed_any:
            break
    time.sleep(0.4)


def extract_conversation_name(driver):
    """Read popup header like 'Close your conversation with ...'"""
    js = r"""
    (function(){
      function deepQueryAll(root, selector){
        const els=[...root.querySelectorAll(selector)];
        const hosts=[...root.querySelectorAll('*')].filter(e=>e.shadowRoot);
        for(const h of hosts) els.push(...deepQueryAll(h.shadowRoot, selector));
        return els;
      }
      const allBtns=deepQueryAll(document,'button');
      for(const btn of allBtns){
        const html=btn.outerHTML||'';
        const text=(btn.innerText||'').trim();
        if(
          html.includes('msg-overlay-bubble-header__control') &&
          (html.includes('close-small')||html.includes('close-medium')) &&
          text.toLowerCase().includes('close your conversation with')
        ){ return text; }
      }
      return '';
    })();
    """
    try:
        result = driver.execute_script(js)
        if result:
            name = result.replace("Close your conversation with", "").strip()
            name = name.replace("and", ",").strip()
            print(f"[DEBUG] Extracted popup name: {name}")
            return name
    except Exception as e:
        print("[WARN] Could not extract popup header name:", e)
    return "Unknown"


def deep_close_linkedin_msg(driver):
    """Force-close any open message popup (shadow DOM safe)."""
    js = r"""
    (function deepCloseLinkedInMsg(){
      function deepQueryAll(root,selector){
        const els=[...root.querySelectorAll(selector)];
        const hosts=[...root.querySelectorAll('*')].filter(e=>e.shadowRoot);
        for(const h of hosts) els.push(...deepQueryAll(h.shadowRoot,selector));
        return els;
      }
      const allButtons=deepQueryAll(document,'button');
      for(const btn of allButtons){
        const html=btn.outerHTML||'';
        const text=btn.innerText?.trim()||'';
        if(
          html.includes('msg-overlay-bubble-header__control') &&
          (html.includes('close-small')||html.includes('close-medium')) &&
          (text.includes('Close')||text.includes('conversation'))
        ){
          ['mouseover','mousedown','mouseup','click'].forEach(ev =>
            btn.dispatchEvent(new MouseEvent(ev,{bubbles:true,cancelable:true,view:window}))
          );
          console.log('Closed popup:', text);
          return true;
        }
      }
      console.log('No popup close button found.');
      return false;
    })();
    """
    try:
        driver.execute_script(js)
        time.sleep(1)
    except Exception:
        pass

def inject_js_compose_and_send(driver, message_text):
    """Same logic as test mode, but presses Send instead of closing/discarding."""
    safe_message = (
        message_text.replace("`", "\\`")
        .replace("\\", "\\\\")
        .replace("\n", "\\n")
    )

    js_code = f"""
    (async () => {{
      console.log("Starting LinkedIn live send (same logic as test mode).");

      function deepFind(predicate, root = document) {{
        try {{
          if (!root) return null;
          if (predicate(root)) return root;
          if (root.shadowRoot) {{
            const r = deepFind(predicate, root.shadowRoot);
            if (r) return r;
          }}
          for (const c of root.children || []) {{
            const f = deepFind(predicate, c);
            if (f) return f;
          }}
        }} catch (e) {{}}
        return null;
      }}

      // Wait for compose box
      let box = null;
      for (let i = 0; i < 40; i++) {{
        box = deepFind(n => {{
          const a = (n.getAttribute?.('aria-label') || '').toLowerCase();
          const d = (n.getAttribute?.('data-placeholder') || '').toLowerCase();
          return a.includes('write a message') || d.includes('write a message');
        }}, document);
        if (box) break;
        await new Promise(r => setTimeout(r, 250));
      }}
      if (!box) return console.warn("❌ No message box found.");

      // Type message
      const msg = `{safe_message}`;
      box.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
      box.style.outline = '2px solid green';
      try {{ box.innerHTML = `<p>${{msg}}</p>`; }} catch(e){{ box.textContent = msg; }}
      box.dispatchEvent(new InputEvent('input', {{ bubbles: true, composed: true }}));
      ['keydown','keyup','keypress'].forEach(k =>
        box.dispatchEvent(new KeyboardEvent(k, {{ key:'a', code:'KeyA', bubbles:true, composed:true }}))
      );
      box.focus?.();
      console.log("Message inserted.");

      await new Promise(r => setTimeout(r, 1200));

      // Find and click Send button
      const sendBtn = deepFind(n => {{
        try {{
          return n.tagName === 'BUTTON' && 
                 (n.className || '').includes('msg-form__send-button') && 
                 !n.disabled;
        }} catch (e) {{ return false; }}
      }}, document);
      if (sendBtn) {{
        console.log("Found Send button → clicking now.");
        ['mouseover','mousedown','mouseup','click'].forEach(ev =>
          sendBtn.dispatchEvent(new MouseEvent(ev, {{ bubbles: true, cancelable: true, view: window }}))
        );
      }} else {{
        console.warn("No send button found!");
      }}

      console.log("Done — message sent.");
    }})();
    """
    driver.execute_script(js_code)
    time.sleep(6)


def inject_js_compose_and_close(driver, message_text):
    """Exact console-tested logic: write message, close window, confirm discard if popup appears."""
    safe_message = (
        message_text.replace("`", "\\`")
        .replace("\\", "\\\\")
        .replace("\n", "\\n")
    )

    js_code = f"""
    (async () => {{
      console.log("Starting LinkedIn test (auto wait for compose box + close & discard)");

      // === Click first Message button ===
      const messageButtons = [...document.querySelectorAll("button,a")].filter(el => {{
        const label = (el.getAttribute("aria-label") || "").toLowerCase();
        const txt = (el.innerText || "").trim().toLowerCase();
        return (label.includes("message") || txt === "message") && el.offsetParent !== null;
      }});

      if (!messageButtons.length) return console.warn("❌ No Message buttons found.");
      const btn = messageButtons[0];
      console.log("Clicking first visible Message button:", btn);
      btn.scrollIntoView({{ behavior: "smooth", block: "center" }});
      ['mouseover','mousedown','mouseup','click'].forEach(ev =>
        btn.dispatchEvent(new MouseEvent(ev, {{ bubbles: true, cancelable: true }}))
      );

      console.log("Waiting up to 10 s for compose box to appear…");

      // === Helper: recursive deepFind for shadow roots ===
      function deepFind(predicate, root = document) {{
        try {{
          if (!root) return null;
          if (predicate(root)) return root;
          if (root.shadowRoot) {{
            const r = deepFind(predicate, root.shadowRoot);
            if (r) return r;
          }}
          const children = root.children || [];
          for (let i = 0; i < children.length; i++) {{
            const found = deepFind(predicate, children[i]);
            if (found) return found;
          }}
        }} catch (e) {{}}
        return null;
      }}

      // === Wait until compose box appears ===
      let box = null;
      for (let i = 0; i < 40; i++) {{ // 10s total
        box = deepFind(node => {{
          try {{
            if (!node.getAttribute) return false;
            const aria = (node.getAttribute('aria-label') || '').toLowerCase();
            const dp = (node.getAttribute('data-placeholder') || '').toLowerCase();
            return aria.includes('write a message') || dp.includes('write a message');
          }} catch (e) {{ return false; }}
        }}, document);
        if (box) break;
        await new Promise(r => setTimeout(r, 250));
      }}

      if (!box) return console.error("❌ Message box never appeared within 10 s.");

      // === Write message ===
      console.log("Found compose box:", box);
      box.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
      box.style.outline = "3px solid orange";
      const message = `{safe_message}`;
      try {{ box.innerHTML = `<p>${{message}}</p>`; }} catch (e) {{ box.textContent = message; }}
      box.dispatchEvent(new InputEvent('input', {{ bubbles: true, composed: true }}));
      ['keydown','keyup','keypress'].forEach(k =>
        box.dispatchEvent(new KeyboardEvent(k, {{ key: 'a', code: 'KeyA', bubbles: true, composed: true }}))
      );
      box.focus?.();
      console.log("Message inserted (test mode).");

      // === Wait before closing ===
      await new Promise(r => setTimeout(r, 1500));

      // === Close the message window ===
      function deepQueryAll(root, selector) {{
        const els = [...root.querySelectorAll(selector)];
        const hosts = [...root.querySelectorAll('*')].filter(e => e.shadowRoot);
        for (const h of hosts) els.push(...deepQueryAll(h.shadowRoot, selector));
        return els;
      }}

      const allBtns = deepQueryAll(document, "button");
      let closed = false;
      for (const b of allBtns) {{
        const html = b.outerHTML || "";
        const text = b.innerText?.trim() || "";
        if (
          html.includes("msg-overlay-bubble-header__control") &&
          (html.includes("close-small") || html.includes("close-medium")) &&
          (text.includes("Close") || text.includes("conversation"))
        ) {{
          console.log("Found close button → closing conversation.");
          ['mouseover','mousedown','mouseup','click'].forEach(ev =>
            b.dispatchEvent(new MouseEvent(ev, {{ bubbles: true, cancelable: true, view: window }}))
          );
          closed = true;
          break;
        }}
      }}

      if (!closed) {{
        console.warn("Close button not found. Probably in compose page, attempting back navigation.");
        if (window.location.href.includes('/messaging/compose')) window.history.back();
        return;
      }}

      // === Wait and handle “Discard message?” dialog ===
      await new Promise(r => setTimeout(r, 1200));
      console.log("Checking for 'Discard message?' popup...");
      const discardBtn = deepFind(node => {{
        try {{
          if (node.tagName === 'BUTTON') {{
            const txt = (node.textContent || '').toLowerCase();
            return txt.includes('discard') && !txt.includes('cancel');
          }}
          return false;
        }} catch (e) {{ return false; }}
      }}, document);

      if (discardBtn) {{
        console.log("Found 'Discard' button — clicking to confirm close.");
        ['mouseover','mousedown','mouseup','click'].forEach(ev =>
          discardBtn.dispatchEvent(new MouseEvent(ev, {{ bubbles: true, cancelable: true, view: window }}))
        );
      }} else {{
        console.log("No discard popup appeared (window closed cleanly).");
      }}

      console.log("Done — message written, closed, and discard handled.");
    }})();
    """
    driver.execute_script(js_code)
    time.sleep(7)

# ========================= LOGIN =============================

usr = utils.getUser(credsFile, 0, verboseOn)
pwd = utils.getPwd(credsFile, 1, verboseOn)

if os.name == "nt":
    options = Options()
    options.add_experimental_option("detach", True)
    service = Service("chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)
else:
    service = Service(executable_path=r"./chromedriver")
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=service, options=options)

utils.loginToLinkedin(driver, usr, pwd)

# ========================= LOGIC =============================

orText = "%20OR%20"
firstLevelFilter = 'network=%5B%22F%22%5D' + "&"
totalMessages = 0

excludeList = utils.getExcludeList(fileOfExcludedNames, 0, verboseOn)
fileOfUsedNames = utils.getFileOfUsedNames(configFile)
excludeList = utils.appendListFromFileToList(excludeList, fileOfUsedNames)

search_keywords = utils.getKeywords(configFile)
message_text = utils.getMessageText(configFile)
greetings = utils.getGreetings(configFile)
geoLocation = utils.getGeoLocation(configFile)
testMode = utils.getTestMode(configFile)

geoFilter = f'geoUrn={geoLocation}&' if geoLocation else ''
people_list_url = f'https://www.linkedin.com/search/results/people/?{geoFilter}keywords='
people_list_url += orText.join(search_keywords) + "&" + firstLevelFilter
print("Search URL:", people_list_url)

pageNr = startingPage
while pageNr < pagesToScan + startingPage:
    people_list_url_pg = people_list_url + "&page=" + str(pageNr)
    print(f"\n========== PAGE {pageNr} ==========")
    print("Search URL:", people_list_url_pg)
    driver.get(people_list_url_pg)
    time.sleep(5)

    # === Simple and robust name extraction (matches console-tested logic) ===
    from selenium.common.exceptions import NoSuchElementException

    all_full_names = []
    message_anchors = driver.find_elements(By.XPATH, "//a[contains(@href,'/messaging/compose/')]")

    for btn in message_anchors:
        name_text = "Unknown"
        parent = btn
        try:
            # climb up to 10 levels to find any /in/ profile link
            for _ in range(10):
                try:
                    link = parent.find_element(By.XPATH, ".//a[contains(@href,'/in/')]")
                    text = link.text.strip()
                    if text:
                        name_text = text
                        break
                except NoSuchElementException:
                    pass
                parent = parent.find_element(By.XPATH, "..")
        except Exception:
            pass
        all_full_names.append(name_text)

    print("[DEBUG] Extracted names:", all_full_names)


    message_buttons = driver.find_elements(
        By.XPATH, "//*[self::button or self::a][contains(@aria-label,'Message') or normalize-space()='Message']"
    )
    print("[DEBUG] message_buttons len =", len(message_buttons))
    if not message_buttons:
        pageNr += 1
        continue

    for i, btn in enumerate(message_buttons):
        name = all_full_names[i] if i < len(all_full_names) else f"Unknown-{i}"
        if any(ex.strip().lower() in re.sub(r"[\n\t\s]*", "", name.lower()) for ex in excludeList):
            print("Excluding:", name)
            continue

        print(f"[FLOW] Messaging {name}")
        close_all_message_popups(driver)
        try:
            driver.execute_script("arguments[0].click();", btn)
            print("[FLOW] Clicked message button.")
        except Exception as e:
            print("Cannot click message button:", e)
            continue

        time.sleep(4)
        popup_name = name

        # ----- TEST MODE -----
        if testMode:
            inject_js_compose_and_close(driver, message_text)
            saveName(popup_name, fileOfUsedNames)
            deep_close_linkedin_msg(driver)
            close_all_message_popups(driver)
            totalMessages += 1
            print(f"[TEST MODE] Simulated message for {popup_name}")
            continue
        # ----------------------

        # ----- LIVE MODE -----
        try:
            inject_js_compose_and_send(driver, message_text)
            saveName(popup_name, fileOfUsedNames)
            deep_close_linkedin_msg(driver)
            close_all_message_popups(driver)
            totalMessages += 1
            print(f"[LIVE MODE] Message sent to {popup_name}")
        except Exception as e:
            print("Error sending to", popup_name, e)
            deep_close_linkedin_msg(driver)
            continue

        time.sleep(randint(2, 6))

    pageNr += 1

print("\nMessages processed:", totalMessages)
print("Script ends here.")
