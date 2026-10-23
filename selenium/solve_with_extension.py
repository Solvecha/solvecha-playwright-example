"""Selenium with the Solvecha extension. Needs a headed browser: use xvfb-run on a server."""
import os
import tempfile
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

KEY = os.environ.get("SOLVECHA_API_KEY")
if not KEY:
    raise SystemExit("Set SOLVECHA_API_KEY (get a key at https://solvecha.com/dashboard).")
EXTENSION = Path(os.environ.get("SOLVECHA_EXTENSION_DIR", "../solvecha-extension")).resolve()

options = webdriver.ChromeOptions()
if os.environ.get("CHROMIUM_PATH"):
    options.binary_location = os.environ["CHROMIUM_PATH"]
options.add_argument(f"--load-extension={EXTENSION}")
options.add_argument(f"--user-data-dir={tempfile.mkdtemp(prefix='solvecha-sel-')}")  # keeps the saved key
options.add_argument("--disable-blink-features=AutomationControlled")
if os.environ.get("NO_SANDBOX"):
    options.add_argument("--no-sandbox")  # inside containers
options.add_experimental_option("excludeSwitches", ["enable-automation"])

driver = webdriver.Chrome(options=options)
try:
    # Save the key once on the settings page of the extension. Its address holds the extension id.
    time.sleep(2)
    targets = driver.execute_cdp_cmd("Target.getTargets", {})["targetInfos"]
    worker = next(t for t in targets if t["type"] == "service_worker" and t["url"].startswith("chrome-extension://"))
    extension_id = worker["url"].split("/")[2]
    driver.get(f"chrome-extension://{extension_id}/options.html")
    driver.find_element(By.ID, "key").send_keys(KEY)
    driver.find_element(By.ID, "save-key").click()
    time.sleep(1)

    driver.get("https://www.google.com/recaptcha/api2/demo")
    WebDriverWait(driver, 120).until(
        lambda d: len(d.execute_script("return document.querySelector('#g-recaptcha-response')?.value ?? ''")) > 100
    )
    print("solved: token received")
finally:
    driver.quit()
