import json
import time
import pandas as pd
import paho.mqtt.client as mqtt

# --- config ---
BROKER = "localhost"
PORT = 1883
TOPIC = "turbine/sensors"
CSV_PATH = "actual_wind_speed.csv"     
WIND_COLUMN = "WindSpeed"             
INTERVAL = 2                           # seconds between each reading

# --- setup ---
client = mqtt.Client()
client.connect(BROKER, PORT, 60)
client.loop_start()
time.sleep(1)

df = pd.read_csv(CSV_PATH)
print(f"Dataset loaded: {len(df)} rows")
print(f"Columns: {list(df.columns)}")  

# --- stream continuously ---
print("Streaming... (Ctrl+C to stop)")
while True:
    for _, row in df.iterrows():
        reading = {
            "turbine_id": "test-1",
            "wind_speed": float(row[WIND_COLUMN]),
        }
        client.publish(TOPIC, json.dumps(reading))
        print(f"Published: {reading}")
        time.sleep(INTERVAL)
    print("Dataset complete — looping back to start...")