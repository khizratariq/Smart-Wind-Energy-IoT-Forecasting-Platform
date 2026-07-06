# mppt_results_publisher.py
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import pandas as pd
import time
import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

url    = "http://localhost:8086"
token  = "mdQBhAfUy9yRX5giPOZBLEH2Rsj9DWluNKKS7E8XM1H50_WgOc-yEnCqOnZMn0yotv2WH5bOuoX46_Ygo7oc6A=="
org    = "wind-iot"
bucket = "turbine-data"

client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

results = pd.read_csv("mppt_results.csv")
print(f"Streaming {len(results)} MPPT result rows to InfluxDB...")

start_time = datetime.datetime.now(datetime.timezone.utc)

for i, row in results.iterrows():
    t = datetime.datetime.now(datetime.timezone.utc)    
    point = (
        Point("mppt_comparison")
        .field("power_baseline",  float(row["power_baseline"]))
        .field("power_forecast",  float(row["power_forecast"]))
        .time(t)
    )
    write_api.write(bucket=bucket, org=org, record=point)

    # compute running improvement so far
    chunk = results.iloc[:i+1]
    energy_baseline = chunk["power_baseline"].sum()
    energy_forecast = chunk["power_forecast"].sum()
    improvement = (energy_forecast - energy_baseline) / energy_baseline * 100

    # write running improvement stat
    stat_point = (
        Point("mppt_study")
        .tag("study_id", "latest")
        .field("energy_baseline",  energy_baseline)
        .field("energy_forecast",  energy_forecast)
        .field("improvement_pct",  improvement)
        .time(t)
    )
    write_api.write(bucket=bucket, org=org, record=stat_point)

    print(f"Row {i+1}/{len(results)} | improvement so far: {improvement:.2f}%")
    time.sleep(2)  # 2 second delay between rows — adjust for demo pacing

print("Done streaming MPPT results.")