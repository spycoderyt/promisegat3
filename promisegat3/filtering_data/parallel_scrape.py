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
from tqdm import tqdm

# Setup
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT, PROJECT_TAIL = os.path.split(PROJECT_ROOT)
# DRIVER_BIN = os.path.join(PROJECT_ROOT, "chromedriver")
# service = Service(executable_path=DRIVER_BIN)
service = ChromeService(ChromeDriverManager().install())

folder_dir = "dlip_files_inactive"
chrome_options = Options()
chrome_options.add_argument("--headless")
os.makedirs(folder_dir, exist_ok=True)
target_folder = os.path.join(PROJECT_ROOT, folder_dir)

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
    temp_driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
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
        except Exception as e:
            print(f"Error downloading {link.text}: {str(e)}")
    finally:
        temp_driver.close()


def count_files_in_directory(directory_path):
    return len(
        [
            f
            for f in os.listdir(directory_path)
            if os.path.isfile(os.path.join(directory_path, f))
        ]
    )

MAX_THREADS = 8
page_num = 1
total_items = 5848
start_time = time.time()
try:
    # Navigate to the website
    driver.get("https://skb-insilico.com/dlip/compound-search/curated-data/rule-based")
    time.sleep(0.5)  # wait for the page to load
    print(f"doing for folder{folder_dir}")
    # Select 'Active'
    select = Select(driver.find_element(By.ID, "active"))
    select.select_by_value("false")

    select = Select(driver.find_element(By.NAME, "compound-list-table_length"))
    select.select_by_value("100")
    # Click 'Search'
    driver.find_element(
        By.CSS_SELECTOR, "button.btn.btn-outline.btn-default.btn-lg.btn-block.btn-green"
    ).click()
    time.sleep(2)  # wait for results to load

    while True:
        # Get all compound links
        compound_links = driver.find_elements(By.CSS_SELECTOR, 'tr[role="row"] a')
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            executor.map(
                download_molecule, compound_links
            )  # map will block until all threads are finished

        # ...

        next_button = driver.find_element(By.ID, "compound-list-table_next")
        if "disabled" in next_button.get_attribute("class"):
            file_num = count_files_in_directory(target_folder)
            print(
                f"Currently at {file_num} at time {time.time() - start_time} seconds. Exiting."
            )
            break  # exit the loop if we are on the last page
        else:
            file_num = count_files_in_directory(target_folder)

            with tqdm(total=total_items, initial=file_num, unit="file") as pbar:
                pbar.update(file_num - pbar.n)
            print(f"On Page {page_num} we have {file_num} total files.")
            print(
                f"Currently at {file_num} at time {time.time() - start_time} seconds. Currently download files at a rate of {file_num/(time.time()-start_time)} per second."
            )
            page_num += 1
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(1)  # wait for the page to load

finally:
    driver.quit()  # ensure the driver is closed properly

    # total_items = 5848
    # with tqdm(total=total_items, initial=file_num, unit="file") as pbar:
    #     while file_num < total_items:
    #         # Update progress bar
    #         pbar.update(file_num - pbar.n)
    #         time.sleep(1)  # wait for the page to load

    #         # Print progress information
    #         print(f"On Page {page_num} we have {file_num} total files.")
    #         print(f"Currently at {file_num} at time {time.time() - start_time} seconds. Currently download files at a rate of {file_num / (time.time() - start_time)} per second.")

    #         page_num += 1
    #         driver.execute_script("arguments[0].click();", next_button)
    #         time.sleep(1)  # wait for the page to load
    #         file_num = count_files_in_directory(target_folder)
###

# try:
#     # Navigate to the website
#     driver.get("https://skb-insilico.com/dlip/compound-search/curated-data/rule-based")
#     time.sleep(0.5)  # wait for the page to load

#     # Select 'Active'
#     select = Select(driver.find_element(By.ID, "active"))
#     select.select_by_value("false")

#     # Click 'Search'
#     driver.find_element(
#         By.CSS_SELECTOR, "button.btn.btn-outline.btn-default.btn-lg.btn-block.btn-green"
#     ).click()
#     time.sleep(0.5)  # wait for results to load

#     while True:
#         # Get all compound links
#         compound_links = driver.find_elements(By.CSS_SELECTOR, 'tr[role="row"] a')
#         with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
#             executor.map(
#                 download_molecule, compound_links
#             )  # map will block until all threads are finished

#         # for link in compound_links:
#         #     download_molecule(link)
#         next_button = driver.find_element(By.ID, "compound-list-table_next")
#         if "disabled" in next_button.get_attribute("class"):
#             file_num = count_files_in_directory(target_folder)
#             print(
#                 f"Currently at {file_num} at time {time.time() - start_time} seconds. Exiting."
#             )
#             break  # exit the loop if we are on the last page
#         else:
#             file_num = count_files_in_directory(target_folder)
#             print(f"On Page {page_num} we have {file_num} total files.")
#             print(f"Currently at {file_num} at time {time.time() - start_time} seconds. Currently download files at a rate of {file_num/(time.time()-start_time)} per second.")
#             page_num += 1
#             driver.execute_script("arguments[0].click();", next_button)
#             time.sleep(1)  # wait for the page to load

# finally:
#     driver.quit()  # ensure the driver is closed properly
