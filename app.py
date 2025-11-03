import streamlit as st
import pandas as pd
import requests
from gmail_utils import (
    get_gmail_credentials,
    authorize_gmail_flow,
    save_credentials,
    fetch_emails,
    extract_items_from_emails
)

st.set_page_config(page_title="Pantree Subscribe & Save", layout="wide")
st.title("📦 Pantree Subscribe & Save Recommendations")

# --- Tabs ---
tab_gmail, tab_manual = st.tabs(["Gmail Import", "Manual Entry"])

# -------------------------------
# Manual Tab
# -------------------------------
with tab_manual:
    st.subheader("Enter purchases manually")
    user_id = st.text_input("User ID", "cust_001")
    month = st.selectbox("Month", [f"Month {i}" for i in range(1, 7)])
    items_text = st.text_area(
        "Enter purchased items (name,price per line)",
        "Bananas,1.99\nChicken Breast,12.99\nMilk,5.49"
    )
    submit_manual = st.button("Get Recommendations (Manual)")

    if submit_manual:
        items = [{"name": n.strip(), "price": float(p.strip())} 
                 for line in items_text.strip().split("\n") if "," in line 
                 for n,p in [line.split(",",1)]]
        payload = {"customer_id": user_id, "month": month, "items": items}
        try:
            response = requests.post("http://localhost:8000/api/v1/process", json=payload)
            data = response.json()
            recs = data.get("recommendations", {}).get("recommendations", [])
            if recs:
                st.success("Recommendations received!")
                st.dataframe(pd.DataFrame(recs))
            else:
                st.warning("No recommendations found.")
        except Exception as e:
            st.error(f"Error: {e}")

# -------------------------------
# Gmail Tab
# -------------------------------
with tab_gmail:
    st.subheader("Fetch purchases from Gmail")
    creds = get_gmail_credentials()

    # If no credentials, show authorization link
    if not creds:
        flow, auth_url = authorize_gmail_flow()
        st.markdown(f"[Click here to authorize Gmail]({auth_url})", unsafe_allow_html=True)
        code = st.text_input("Enter the authorization code here")
        if code:
            flow.fetch_token(code=code)
            creds = flow.credentials
            save_credentials(creds)
            st.success("Authorization complete! You can now fetch emails.")

    # If we have credentials, fetch emails
    if creds:
        fetch_btn = st.button("Fetch Recent Purchases from Gmail")
        if fetch_btn:
            try:
                snippets = fetch_emails(creds)
                items = extract_items_from_emails(snippets)
                if items:
                    st.success(f"Found {len(items)} items in emails!")
                    df = pd.DataFrame(items)
                    st.dataframe(df)

                    # Send to backend for recommendations
                    user_id = st.text_input("User ID for Gmail data", "cust_001")
                    month = st.selectbox("Month for Gmail data", [f"Month {i}" for i in range(1, 7)], key="gmail_month")
                    submit_gmail = st.button("Get Recommendations (Gmail)")
                    if submit_gmail:
                        payload = {"customer_id": user_id, "month": month, "items": items}
                        response = requests.post("http://localhost:8000/api/v1/process", json=payload)
                        data = response.json()
                        recs = data.get("recommendations", {}).get("recommendations", [])
                        if recs:
                            st.success("Recommendations received!")
                            st.dataframe(pd.DataFrame(recs))
                        else:
                            st.warning("No recommendations found.")
                else:
                    st.warning("No purchase items detected in emails.")
            except Exception as e:
                st.error(f"Gmail fetch failed: {e}")
