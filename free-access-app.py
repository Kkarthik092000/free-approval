import streamlit as st
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ---------------------------------------
# STREAMLIT CONFIG
# ---------------------------------------
st.set_page_config(page_title="Auto Approval", layout="wide")
st.title("🤖 Free Access Auto Approval Tool")

# ---------------------------------------
# AUTOMATION FUNCTION
# ---------------------------------------
def run_automation(log_box):
    logs = []
    approved_count = 0

    # ✅ SECURE CREDENTIALS FROM SECRETS
    EMAIL = st.secrets["EMAIL"]
    PASSWORD = st.secrets["PASSWORD"]

    def log(msg):
        logs.append(msg)
        log_box.text("\n".join(logs))

    LOGIN_URL = "https://api.mycaptain.co.in/users/sign_in"
    DATA_URL = "https://api.mycaptain.co.in/operations/kickstarter_transactions"

    options = webdriver.ChromeOptions()

    # ✅ HEADLESS MODE (REQUIRED FOR CLOUD)
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    try:
        # LOGIN
        log("🔐 Logging in...")
        driver.get(LOGIN_URL)

        wait.until(EC.presence_of_element_located((By.NAME, "user[email]"))).send_keys(EMAIL)
        driver.find_element(By.NAME, "user[password]").send_keys(PASSWORD)
        driver.find_element(By.NAME, "user[password]").submit()

        time.sleep(5)

        # OPEN PAGE
        log("📊 Opening Transactions Page...")
        driver.get(DATA_URL)
        time.sleep(5)

        # MAIN LOOP
        while True:
            found = False
            log("🔍 Scanning page...")

            rows = driver.find_elements(By.XPATH, "//table/tbody/tr")

            for i in range(len(rows)):
                try:
                    rows = driver.find_elements(By.XPATH, "//table/tbody/tr")
                    row = rows[i]
                    cols = row.find_elements(By.TAG_NAME, "td")

                    if len(cols) < 17:
                        continue

                    status = cols[2].text.strip().lower()
                    mode = cols[16].text.strip().lower()

                    if status == "created" and "free" in mode:
                        found = True
                        log(f"✅ Approving row {i+1}")

                        driver.execute_script("arguments[0].scrollIntoView(true);", row)
                        time.sleep(1)

                        # Click Actions
                        dropdown = row.find_element(By.XPATH, ".//button[contains(@class,'dropdown-toggle')]")
                        driver.execute_script("arguments[0].click();", dropdown)

                        # Click Approve
                        approve_btn = row.find_element(By.XPATH, ".//a[contains(text(),'Approve')]")
                        driver.execute_script("arguments[0].click();", approve_btn)

                        # Handle popup
                        wait.until(EC.alert_is_present())
                        driver.switch_to.alert.accept()

                        approved_count += 1
                        log(f"🎉 Approved: {approved_count}")

                        time.sleep(3)

                        # Reload page
                        driver.get(DATA_URL)
                        time.sleep(5)

                        break

                except Exception:
                    continue

            if not found:
                log("🚀 No more free approvals")
                break

    except Exception as e:
        log(f"❌ Error: {str(e)}")

    finally:
        driver.quit()

    return approved_count


# ---------------------------------------
# BUTTON ONLY
# ---------------------------------------
if st.button("🚀 Start Auto Approval"):
    log_box = st.empty()

    with st.spinner("Running automation..."):
        total = run_automation(log_box)

    st.success(f"✅ Done! Total Approved: {total}")