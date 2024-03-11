# USE parallel_scrape instead
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
import threading
from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import os
import shutil
from selenium import webdriver

from selenium.webdriver.chrome.service import Service as ChromeService

from webdriver_manager.chrome import ChromeDriverManager

service = ChromeService(ChromeDriverManager().install())
# Setup
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
# DRIVER_BIN = os.path.join(PROJECT_ROOT, "chromedriver")
# service = Service(executable_path=DRIVER_BIN)
chrome_options = Options()
# chrome_options.add_argument("--headless")
os.makedirs("dlip_files_inactive", exist_ok=True)
target_folder = os.path.join(PROJECT_ROOT, "dlip_files_inactive")

chrome_options.add_experimental_option(
    "prefs",
    {
        "download.default_directory": target_folder,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    },
)
driver = webdriver.Chrome(service=service, options=chrome_options)


def download_molecule(link):
    try:
        temp_driver = webdriver.Chrome(service=service, options=chrome_options)
        compound_name = link.text  # Get the name/text of the link
        url = "https://skb-insilico.com/dlip/compound/" + compound_name
        temp_driver.get(url)
        time.sleep(0.5)
        try:
            if any(compound_name in filename for filename in os.listdir(target_folder)):
                print(f"{compound_name} already exists. Skipping download.")
                return
            temp_driver.find_element(By.ID, "download-button").click()
            time.sleep(0.5)
            print(f"Successfully downloaded info for {compound_name}")
        finally:
            temp_driver.close()
    except Exception as e:
        print(f"Error downloading {link.text}: {str(e)}")


try:
    # Navigate to the website
    driver.get("https://skb-insilico.com/dlip/compound-search/curated-data/rule-based")
    time.sleep(0.5)  # wait for the page to load

    # Select 'Active'
    select = Select(driver.find_element(By.ID, "active"))
    select.select_by_value("false")

    # Click 'Search'
    driver.find_element(
        By.CSS_SELECTOR, "button.btn.btn-outline.btn-default.btn-lg.btn-block.btn-green"
    ).click()
    time.sleep(0.5)  # wait for results to load

    while True:
        # Get all compound links
        compound_links = driver.find_elements(By.CSS_SELECTOR, 'tr[role="row"] a')
        for link in compound_links:
            download_molecule(link)
        next_button = driver.find_element(By.ID, "compound-list-table_next")
        if "disabled" in next_button.get_attribute("class"):
            break  # exit the loop if we are on the last page
        else:
            next_button.click()
            time.sleep(1)  # wait for the page to load

finally:
    driver.quit()  # ensure the driver is closed properly
