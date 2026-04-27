import csv
import hmac
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Client Interview Feedback", page_icon="📝", layout="centered")

APP_PASSWORD = "RevPBforest26"
DATA_FILE = Path("output/client_interview_feedback.csv")

PRODUCT_OPTIONS = {
    "Investments": [
        "Additional Assets (ETF’s)",
        "Additional Assets (Stocks)",
        "Additional Assets (Commodities)",
        "Additional Assets (Bonds)",
        "Structured Products",
        "Other",
    ],
    "Lending": [
        "Credit cards",
        "Mortgages",
        "Lombard Lending",
        "Overdraft",
    ],
    "Plan / Lifestyle": [
        "Insurance",
        "Software Subscriptions",
        "Family Plan",
        "Other",
    ],
    "Tech Functionality": [
        "Tax API integrations",
        "WhatsApp",
        "24/7 Call Support",
        "Other",
    ],
    "Tax Wrappers": [
        "Tax API integrations",
        "WhatsApp",
        "24/7 Call Support",
        "Asset Transfer",
        "Other",
    ],
}

COLUMNS = [
    "Submitted At",
    "Banker Initials",
    "User Interview Date",
    "Product Type",
    "Product Sub Type",
    "Optional Additional Information",
    "Unlockable AUM in £m",
    "Is It A Dealbreaker For The Client",
    "Timeframe for moving across",
]


def load_data() -> pd.DataFrame:
    if DATA_FILE.exists():
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=COLUMNS)


def save_row(row: dict) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    file_exists = DATA_FILE.exists()
    with DATA_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def valid_initials(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z]{2,10}", value.strip()))


def valid_ddmmyyyy(value: str) -> bool:
    try:
        parsed = datetime.strptime(value.strip(), "%d/%m/%Y")
        return parsed.strftime("%d/%m/%Y") == value.strip()
    except ValueError:
        return False


def password_gate() -> bool:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.title("Client Interview Feedback")
    st.caption("Enter the password to unlock the feedback form.")

    with st.form("login_form"):
        entered_password = st.text_input("Password", type="password")
        unlock = st.form_submit_button("Unlock")

    if unlock:
        if hmac.compare_digest(entered_password, APP_PASSWORD):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")

    return False


def sync_product_subtype_selection() -> None:
    current_type = st.session_state.get("product_type", list(PRODUCT_OPTIONS.keys())[0])
    valid_subtypes = PRODUCT_OPTIONS[current_type]
    current_subtype = st.session_state.get("product_sub_type")

    if current_subtype not in valid_subtypes:
        st.session_state.product_sub_type = valid_subtypes[0]


if not password_gate():
    st.stop()

if "product_type" not in st.session_state:
    st.session_state.product_type = list(PRODUCT_OPTIONS.keys())[0]

sync_product_subtype_selection()

st.title("Client Interview Feedback")
st.caption("Capture interview feedback and download all submissions as a CSV file.")

with st.form("feedback_form", clear_on_submit=True):
    product_type = st.selectbox(
        "Product Type",
        options=list(PRODUCT_OPTIONS.keys()),
        key="product_type",
        on_change=sync_product_subtype_selection,
    )
    product_sub_type = st.selectbox(
        "Product Sub Type",
        options=PRODUCT_OPTIONS[st.session_state.product_type],
        key="product_sub_type",
    )

    banker_initials = st.text_input("Banker Initials", max_chars=10, help="Use letters only, for example AB.")
    interview_date = st.text_input("Date of user interview (DD/MM/YYYY)", placeholder="DD/MM/YYYY")
    additional_info = st.text_area("Optional Additional Information", height=120)
    unlockable_aum = st.text_input("Unlockable AUM in £m")
    dealbreaker = st.selectbox("Is It A Dealbreaker For The Client", options=["Yes", "No"])
    timeframe = st.selectbox(
        "Timeframe for moving across",
        options=["< 1 month", "1-3 months", "3-6 months", "Over 6 months"],
    )

    submitted = st.form_submit_button("Submit Feedback")

if submitted:
    errors = []

    if not valid_initials(banker_initials):
        errors.append("Banker Initials must contain only letters and be 2 to 10 characters long.")

    if not valid_ddmmyyyy(interview_date):
        errors.append("The interview date must be in valid DD/MM/YYYY format.")

    if not unlockable_aum.strip():
        errors.append("Unlockable AUM in £m is required.")

    if errors:
        for error in errors:
            st.error(error)
    else:
        row = {
            "Submitted At": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "Banker Initials": banker_initials.strip().upper(),
            "User Interview Date": interview_date.strip(),
            "Product Type": product_type,
            "Product Sub Type": product_sub_type,
            "Optional Additional Information": additional_info.strip(),
            "Unlockable AUM in £m": unlockable_aum.strip(),
            "Is It A Dealbreaker For The Client": dealbreaker,
            "Timeframe for moving across": timeframe,
        }
        save_row(row)
        st.success("Feedback submitted successfully.")
        st.session_state.product_type = list(PRODUCT_OPTIONS.keys())[0]
        st.session_state.product_sub_type = PRODUCT_OPTIONS[st.session_state.product_type][0]


df = load_data()

st.divider()
st.subheader("Stored Feedback")

if df.empty:
    st.info("No feedback has been submitted yet.")
else:
    st.dataframe(df, use_container_width=True, hide_index=True)

csv_bytes = df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download feedback as CSV",
    data=csv_bytes,
    file_name="client_interview_feedback.csv",
    mime="text/csv",
)

st.markdown(
    """
    ### Run locally
    1. Save this file as `client_interview_feedback_app.py`.
    2. Install requirements: `pip install -r requirements.txt`.
    3. Start the app: `streamlit run client_interview_feedback_app.py`.
    """
)
