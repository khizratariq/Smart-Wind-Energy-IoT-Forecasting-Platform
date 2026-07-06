# Smart Wind Energy IoT \& Forecasting Platform

An end-to-end IoT and machine learning platform for real-time wind speed monitoring, deep learning-based forecasting, and forecast-assisted MPPT optimization, built to demonstrate a complete data pipeline from sensor hardware to live analytics dashboard.

\---

## Demo

\[Dashboard Demo]

> Live dashboard showing: actual vs forecasted wind speed (left), baseline vs forecast-assisted MPPT power output (bottom left), energy capture comparison (top right), and cumulative improvement % (bottom right).

\---

## Key Result

> Forecast-assisted MPPT captured \*\*2.21% more energy\*\* than a purely reactive baseline controller on the same wind dataset.

While 2.21% may seem modest, at the scale of a commercial wind farm (e.g. 9 MW), this translates to meaningful additional energy yield over an operating year — demonstrating the practical value of integrating short-term forecasting into turbine control.

\---

## Architecture

```
\[ESP32 + Anemometer]
        │
        │  MQTT over WiFi (JSON payload)
        ▼
\[Eclipse Mosquitto Broker]
        │
        │  paho-mqtt subscriber
        ▼
\[Python Inference Layer]
   → Sliding window of last 30 readings
   → LSTM model predicts next wind speed
        │
        │  influxdb-client writes
        ▼
\[InfluxDB Time-Series Database]
        │
        │  Flux queries
        ▼
\[Grafana Live Dashboard]

─────────────────────────────────────────

\[Offline MPPT Study — runs separately]

\[Public Wind SCADA Dataset]
        │
        ▼
\[Python: offline\_forecast.py]
   → Generates forecast for full dataset
   → Exports wind\_forecast\_data.csv
        │
        ▼
\[MATLAB/Simulink: mppt\_comparison.m]
   → Baseline MPPT (reactive, current wind speed)
   → Forecast-Assisted MPPT (uses predicted wind speed)
   → Exports mppt\_timeseries\_results.csv
        │
        ▼
\[Python: mppt\_results\_publisher.py]
   → Streams results row-by-row to InfluxDB
   → Updates Grafana MPPT panels progressively
```

\---

## Tech Stack

|Layer|Technology|
|-|-|
|Edge / Sensing|ESP32, Cup Anemometer|
|Connectivity|MQTT (Eclipse Mosquitto)|
|Storage|InfluxDB 2.x (time-series)|
|ML Framework|TensorFlow / Keras (LSTM)|
|Control Simulation|MATLAB / Simulink|
|Dashboard|Grafana 13|
|Infrastructure|Docker|
|Language|Python 3.13, C++ (Arduino/ESP32)|

\---

## Project Structure

```
wind-iot-platform/
├── esp32\_wind/
│   └──  esp32\_wind.ino            ← ESP32 firmware (primary hardware publisher)
├── simulation/
│   └── mqtt\_publisher.py          ← CSV-based publisher for testing without hardware
├── mqtt\_subscriber.py             ← Receives MQTT, runs inference, writes to InfluxDB
├── offline\_forecast.py            ← Generates full-dataset forecast for MPPT study
├── mppt\_results\_publisher.py     ← Streams Simulink MPPT results to InfluxDB
├── run\_mppt\_study.py
├── matlab/
│   └── mppt\_comparison.m          ← Simulink runner: baseline vs forecast-assisted MPPT
├── dashboard/
│   └── wind\_iq\_dashboard.json    ← Grafana dashboard export (import to reproduce)
```

\---

## Hardware Setup

### Components

* ESP32 DevKit V1
* Cup anemometer with pulse output (reed switch or hall effect)
* 10kΩ pull-up resistor
* Jumper wires

### Wiring

```
Anemometer VCC    →  ESP32 3.3V
Anemometer GND    →  ESP32 GND
Anemometer Signal →  ESP32 GPIO 34

3.3V ──\[10kΩ]──┬── GPIO 34
                │
           Anemometer Signal
```

> If your anemometer outputs 5V signals, add a voltage divider (10kΩ + 20kΩ) before GPIO 34 — ESP32 pins are not 5V tolerant.

### Calibration

Update `CALIBRATION\_FACTOR` in `esp32\_wind.ino` to match your anemometer's datasheet.
Default: `0.667` (corresponds to 1 Hz = 2.4 km/h, a common cup anemometer spec).

\---

## How to Run

### Prerequisites

* Docker Desktop (WSL2 backend on Windows)
* Miniconda (Python 3.13 environment)
* MATLAB with Simulink (for MPPT study only)
* Arduino IDE with ESP32 board support (for hardware publisher)

### 1\. Start infrastructure

```bash
docker start mosquitto
docker start influxdb
docker start grafana
```

### 2\. Create Python environment

```bash
conda create -n wind-iot python=3.13
conda activate wind-iot
pip install pandas numpy paho-mqtt influxdb-client tensorflow joblib scikit-learn
```

### 3\. Configure credentials

In `mqtt\_subscriber.py`, `offline\_forecast.py`, and `mppt\_results\_publisher.py`, fill in:

```python
url    = "http://localhost:8086"
token  = "YOUR\_INFLUXDB\_TOKEN"
org    = "YOUR\_ORG\_NAME"
bucket = "turbine-data"
```

### 4\. Import Grafana dashboard

Open `http://localhost:3000` → Dashboards → Import → upload `dashboard/wind\_iq\_dashboard.json`.

### 5\. Run the live pipeline

```bash
# Terminal 1 — stream wind data (ESP32 does this in hardware mode)
python simulation/mqtt\_publisher.py

# Terminal 2 — receive data, run inference, write to InfluxDB
python mqtt\_subscriber.py
```

### 6\. Run the MPPT study (one-time)

```bash
python run\_mppt\_study.py
```

This runs offline forecast → MATLAB/Simulink comparison → streams results to InfluxDB.

\---

## Model Details

**Architecture:** LSTM (Long Short-Term Memory)
**Input:** Sliding window of 30 past wind speed readings
**Output:** Predicted wind speed at next timestep (1-step-ahead)
**Training data:** Public wind turbine SCADA dataset (15-minute interval readings)
**Framework:** TensorFlow / Keras
**Training environment:** Google Colab (GPU)


\---

## MPPT Study

Two controller strategies were compared on the same wind speed dataset using a DFIG wind turbine model in MATLAB/Simulink:

|Controller|Strategy|
|-|-|
|Baseline MPPT|Reactive — adjusts torque/pitch based on instantaneous wind speed only|
|Forecast-Assisted MPPT|Predictive — uses LSTM forecast to pre-adjust setpoints ahead of wind changes|

**Result: forecast-assisted MPPT captured 2.21% more energy** over the study period.

The MPPT comparison runs offline using `run\_mppt\_study.py` and results are streamed progressively to Grafana to simulate a real-time analysis view.

\---

## Simulation Mode (No Hardware Required)

The CSV-based publisher (`simulation/mqtt\_publisher.py`) replicates the exact MQTT message format produced by the ESP32 firmware, streaming rows from a real wind SCADA dataset at configurable intervals. The rest of the pipeline requires **zero modification** to switch between simulation and hardware modes.

> The dashboard demo was recorded using simulation mode on a public wind turbine SCADA dataset. The ESP32 firmware produces an identical message format — the downstream pipeline is hardware-agnostic by design.

\---

## License

MIT License — free to use, modify, and distribute with attribution.

