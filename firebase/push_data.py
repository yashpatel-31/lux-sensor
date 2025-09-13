import serial
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

# --- 1. Firebase Setup ---
if not firebase_admin._apps:  # check to prevent duplicate init
    cred = credentials.Certificate(
        "C:/Users/yashp/Downloads/hackindore-b8070-firebase-adminsdk-fbsvc-434bc483cc.json"
    )
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://hackindore-b8070-default-rtdb.asia-southeast1.firebasedatabase.app/"
    })

# --- 2. Serial Port Setup ---
ser = serial.Serial("COM6", 115200, timeout=1)

print("Listening for sensor data...")

# --- 3. Read Loop ---
while True:
    line = ser.readline().decode("utf-8", errors="ignore").strip()
    if "Light (lux):" in line:
        try:
            lux_value = int(line.split(":")[1].strip())
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print(f"Lux = {lux_value}  |  Time = {timestamp}")

            # Firebase push
            ref = db.reference("lux_readings")
            ref.push().set({
                "lux": lux_value,
                "time": timestamp
            })

        except Exception as e:
            print("Error:", e)
