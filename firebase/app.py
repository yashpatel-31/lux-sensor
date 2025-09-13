import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import pandas as pd
import time

# --- Firebase Setup ---
if not firebase_admin._apps:   # 👈 yaha pe check lagaya
    cred = credentials.Certificate("C:/Users/yashp/Downloads/hackindore-b8070-firebase-adminsdk-fbsvc-434bc483cc.json")
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://hackindore-b8070-default-rtdb.asia-southeast1.firebasedatabase.app/"
    })

st.title("💡 Lux Sensor Dashboard")
st.write("Realtime light intensity values from VCNL4040 sensor")

ref = db.reference("lux_readings")

# --- Data Fetch Function ---
def get_data():
    data = ref.get()
    lux_list = []
    if data:
        for key, val in data.items():
            if isinstance(val, dict) and "lux" in val:
                lux_list.append({"id": key, "lux": val["lux"]})
    return pd.DataFrame(lux_list)

# --- Live Graph ---
placeholder = st.empty()

while True:
    df = get_data()
    if not df.empty:
        with placeholder.container():
            st.line_chart(df["lux"])
    time.sleep(5)
