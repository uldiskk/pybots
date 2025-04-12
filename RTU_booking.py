# conda install -c anaconda openpyxl
# conda install -c anaconda beautifulsoup4

import pandas as pd
import re
import string
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import utils


### CONSTANTS ###
excel_file_path = 'Book_8.oct.xlsx'  # Update with your actual file path
event_URL = "https://telpas.rtu.lv/attendance/create/?eventDateId=975035"
credsFile = "../creds_RTU.txt"


# Load the data from Excel file
data = pd.read_excel(excel_file_path, header=None)  # Load without headers initially
data.columns = ['ID']

# Setup Selenium WebDriver
driver = webdriver.Chrome()  # Ensure ChromeDriver is installed or replace with appropriate driver
wait = WebDriverWait(driver, 10)

# Step 1: Go to login page
driver.get(event_URL)
time.sleep(5)


# Step 2: Authorize by entering username and password
adPrinted = 0
usr = utils.getUser(credsFile, adPrinted, False)
adPrinted = 1
pwd = utils.getPwd(credsFile, adPrinted, False)

driver.find_element(By.ID, "i0116").send_keys(usr)
time.sleep(3)
driver.find_element(By.ID, "idSIButton9").click()
time.sleep(5)

try:
    driver.find_element(By.ID, "i0118").send_keys(pwd)
    time.sleep(3)
    driver.find_element(By.ID, "idSIButton9").click()
    print("Watch your phone and authenticate!!!")
except:
    print('')
time.sleep(15)

# Step 3: iterate over each ID from excel, find it on values and mark Go to specific day time edit booking page	

options_data = [f"{row['ID']}" for _, row in data.iterrows()]

table = driver.find_element(by=By.XPATH, value="//table[@class='table table-striped table-sm']")
for row in table.find_elements(by=By.XPATH, value=".//tr"):
    tds = row.find_elements(by=By.XPATH, value=".//td")
    if len(tds) > 1:
        name_id = tds[1].text
        withoutSpaceAndTrail = re.sub(r"[\n\t\s]*", "", name_id.lower())
        for option in options_data:
            if(len(option) > 3):
                if option.strip().lower() in withoutSpaceAndTrail:
                    boolToMark = True
                    print("checking in " + name_id)
                    checkbox = row.find_element(by=By.XPATH, value=".//input")
                    if not checkbox.is_selected():
                        checkbox.click()

time.sleep(3)
driver.find_element(By.ID, "attendance-save-button").click()

# Keep the program running until manually closed
print("Script completed. Press [Izveidot] if you are happy with the result.")
while True:
    time.sleep(1)
