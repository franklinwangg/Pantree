import streamlit as st
import requests
import pandas as pd

# --- Sidebar ---
st.sidebar.title("Pantree Subscribe & Save")
user_id = st.sidebar.text_input("User ID", "cust_001")
month = st.sidebar.selectbox("Month", [f"Month {i}" for i in range(1, 7)])
submit_btn = st.sidebar.button("Get Recommendations")

# --- Main ---
st.title("Subscribe & Save Recommendations")

if submit_btn:
    st.info("Fetching recommendations...")

    # Example: call local SageMaker / FastAPI endpoint
    payload = {
        "customer_id": user_id,
        "month": month,
        "items": [
            {"name": "Bananas", "price": 1.99},
            {"name": "Chicken Breast", "price": 12.99},
            {"name": "Milk", "price": 5.49}
        ]
    }

    try:
        response = requests.post("http://localhost:8000/api/v1/process", json=payload)
        data = response.json()
        recs = data.get("recommendations", {}).get("recommendations", [])

        if recs:
            df = pd.DataFrame(recs)
            st.success("Recommendations received!")
            st.dataframe(df)
        else:
            st.warning("No recommendations found.")

    except Exception as e:
        st.error(f"Error: {e}")
