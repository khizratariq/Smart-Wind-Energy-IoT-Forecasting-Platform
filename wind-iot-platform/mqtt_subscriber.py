import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import json
import numpy as np
import pandas as pd
from collections import deque
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from tensorflow import keras
import joblib

# --- InfluxDB config ---
url    = "http://localhost:8086"
token  = "mdQBhAfUy9yRX5giPOZBLEH2Rsj9DWluNKKS7E8XM1H50_WgOc-yEnCqOnZMn0yotv2WH5bOuoX46_Ygo7oc6A=="
org    = "wind-iot"
bucket = "turbine-data"

client    = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

# --- MQTT config ---
BROKER = "localhost"
PORT   = 1883
TOPIC  = "turbine/sensors"

# --- model ---
model  = keras.models.load_model("wind_forecast_model.h5", compile=False)
scaler = joblib.load("wind_speed_scaler.save")
WINDOW = 30

# --- pre-fill buffer with first WINDOW rows from dataset ---
# so every MQTT message gets a forecast immediately, no rows wasted to buffering
df = pd.read_csv("actual_wind_speed.csv")
seed_values = df["WindSpeed"].values[:WINDOW].tolist()
wind_buffer = deque(seed_values, maxlen=WINDOW)
print(f"Buffer pre-filled with {WINDOW} seed values — forecast available from row 1")

def on_connect(mqttc, userdata, flags, rc):
    print(f"Connected (code {rc})")
    mqttc.subscribe(TOPIC)

def on_message(mqttc, userdata, msg):
    data         = json.loads(msg.payload.decode())
    actual_speed = float(data["wind_speed"])
    wind_buffer.append(actual_speed)   # buffer always full now, oldest drops off

    # forecast — buffer is always full so no need to check length
    window_arr     = np.array(wind_buffer).reshape(-1, 1)
    scaled_window  = scaler.transform(window_arr).reshape(1, WINDOW, 1)
    scaled_forecast = model.predict(scaled_window, verbose=0)
    forecast_speed = float(scaler.inverse_transform(scaled_forecast)[0][0])

    point = (
        Point("turbine_reading")
        .tag("turbine_id", data.get("turbine_id", "test-1"))
        .field("wind_speed",           actual_speed)
        .field("forecasted_wind_speed", forecast_speed)
    )
    write_api.write(bucket=bucket, org=org, record=point)
    print(f"Actual: {actual_speed:.2f}  |  Forecast: {forecast_speed:.2f}")

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(BROKER, PORT, 60)
mqtt_client.loop_forever()
