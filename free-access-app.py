import streamlit as st
import requests
from bs4 import BeautifulSoup

# ---------------------------------------
# UI
# ---------------------------------------
st.set_page_config(page_title="Auto Approval", layout="wide")
st.title("🤖 Free Access Auto Approval Tool")

EMAIL = st.secrets["EMAIL"]
PASSWORD = st.secrets["PASSWORD"]

BASE_URL = "https://api.mycaptain.co.in"
LOGIN_URL = f"{BASE_URL}/users/sign_in"
DATA_URL = f"{BASE_URL}/operations/kickstarter_transactions"


# ---------------------------------------
# FUNCTION
# ---------------------------------------
def run_automation(log_box):
    session = requests.Session()
    logs = []
    approved_count = 0

    def log(msg):
        logs.append(msg)
        log_box.text("\n".join(logs))

    try:
        # ---------------------------------------
        # STEP 1: LOGIN PAGE
        # ---------------------------------------
        log("🔐 Opening login page...")
        login_page = session.get(LOGIN_URL)

        soup = BeautifulSoup(login_page.text, "html.parser")
        form_token = soup.find("input", {"name": "authenticity_token"})["value"]

        # ---------------------------------------
        # STEP 2: LOGIN
        # ---------------------------------------
        log("🔐 Logging in...")

        payload = {
            "authenticity_token": form_token,
            "user[email]": EMAIL,
            "user[password]": PASSWORD
        }

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": LOGIN_URL
        }

        session.post(LOGIN_URL, data=payload, headers=headers)
        log("✅ Logged in")

        # ---------------------------------------
        # STEP 3: LOAD TRANSACTIONS PAGE
        # ---------------------------------------
        log("📊 Loading transactions page...")
        page = session.get(DATA_URL)
        soup = BeautifulSoup(page.text, "html.parser")

        # ✅ IMPORTANT: get CSRF from META (NOT login page)
        meta_token = soup.find("meta", {"name": "csrf-token"})["content"]

        rows = soup.select("table tbody tr")

        for row in rows:
            cols = row.find_all("td")

            if len(cols) < 17:
                continue

            status = cols[2].text.strip().lower()
            mode = cols[16].text.strip().lower()

            if status == "created" and "free" in mode:
                approve_link = row.select_one("a[href*='approve']")

                if approve_link:
                    approve_url = BASE_URL + approve_link["href"]

                    log(f"⚡ Approving: {approve_url}")

                    approve_headers = {
                        "User-Agent": "Mozilla/5.0",
                        "Referer": DATA_URL,
                        "Origin": BASE_URL,
                        "X-CSRF-Token": meta_token,
                        "X-Requested-With": "XMLHttpRequest"
                    }

                    # ✅ NO payload needed (important)
                    response = session.post(
                        approve_url,
                        headers=approve_headers
                    )

                    if response.status_code in [200, 302]:
                        approved_count += 1
                        log(f"✅ Approved ({approved_count})")
                    else:
                        log(f"❌ Failed ({response.status_code})")

        log("🚀 Completed")

    except Exception as e:
        log(f"❌ Error: {str(e)}")

    return approved_count


# ---------------------------------------
# BUTTON
# ---------------------------------------
if st.button("🚀 Start Auto Approval"):
    log_box = st.empty()

    with st.spinner("Running..."):
        total = run_automation(log_box)

    st.success(f"✅ Total Approved: {total}")
