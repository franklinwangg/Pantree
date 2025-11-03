import streamlit as st
from gmail_utils import fetch_recent_emails, extract_items_from_emails
import pandas as pd
import requests

st.set_page_config(page_title="Pantree - Recommendations", page_icon="🛒")

st.title("🛒 Pantree Subscribe & Save Recommendations")

if "gmail_connected" not in st.session_state or not st.session_state.gmail_connected:
    st.warning("Please connect your Gmail account first on the home page.")
    st.stop()

# Fetch data from Gmail
st.write("Fetching your recent purchase emails...")

try:
    emails = fetch_recent_emails(max_results=5)
    items = extract_items_from_emails(emails)
    st.success(f"Found {len(items)} items from recent emails.")
    st.dataframe(pd.DataFrame(items, columns=["Item", "Price"]))
except Exception as e:
    st.error(f"Failed to fetch Gmail data: {e}")
    st.stop()

# Optional: Call backend for recommendations
if st.button("Get Recommendations"):
    st.info("Requesting personalized recommendations...")
    try:
        payload = {"items": [{"name": i[0], "price": i[1]} for i in items]}
        resp = requests.post("http://localhost:8000/api/v1/proces
