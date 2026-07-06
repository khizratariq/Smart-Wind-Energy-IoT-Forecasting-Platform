import pandas as pd
import numpy as np
from tensorflow import keras
import joblib

WINDOW = 30
df = pd.read_csv("actual_wind_speed.csv")
model = keras.models.load_model("wind_forecast_model.h5", compile=False)
scaler = joblib.load("wind_speed_scaler.save")

wind = df["WindSpeed"].values.reshape(-1, 1)
scaled = scaler.transform(wind)

# pad first 30 with actual wind speed instead of NaN
forecasts = list(wind[:WINDOW].flatten())

for i in range(len(scaled) - WINDOW):
    window = scaled[i:i+WINDOW].reshape(1, WINDOW, 1)
    pred = scaler.inverse_transform(model.predict(window, verbose=0))[0][0]
    forecasts.append(pred)

df["forecasted_wind_speed"] = forecasts
df["time_seconds"] = np.arange(len(df)) * 2

df[["time_seconds", "WindSpeed", "forecasted_wind_speed"]].rename(
    columns={"WindSpeed": "actual_wind_speed"}
).to_csv("wind_forecast_data.csv", index=False)
print(f"Saved wind_forecast_data.csv with {len(df)} rows")
