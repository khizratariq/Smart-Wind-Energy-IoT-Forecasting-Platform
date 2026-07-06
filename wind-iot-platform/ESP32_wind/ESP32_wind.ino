#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// --- config ---
const char* ssid = "your_wifi";
const char* password = "your_password";
const char* mqtt_server = "your_broker_ip";
const char* topic = "turbine/sensors";
const float CALIBRATION_FACTOR = 0.667;  // adjust per anemometer datasheet
const int ANEMOMETER_PIN = 34;           // any GPIO with interrupt support

// --- globals ---
volatile int pulse_count = 0;
unsigned long last_publish = 0;

WiFiClient espClient;
PubSubClient client(espClient, mqtt_server, 1883);

void IRAM_ATTR countPulse() {
    pulse_count++;   // runs on each rising edge from anemometer
}

void setup() {
    Serial.begin(115200);
    pinMode(ANEMOMETER_PIN, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(ANEMOMETER_PIN), countPulse, RISING);

    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) delay(500);
    Serial.println("WiFi connected");
    client.connect("esp32-turbine");
}

void loop() {
    if (millis() - last_publish >= 2000) {  // every 2 seconds
        // snapshot and reset count atomically
        noInterrupts();
        int count = pulse_count;
        pulse_count = 0;
        interrupts();

        float wind_speed = count * CALIBRATION_FACTOR;  // convert to m/s

        // build JSON and publish
        StaticJsonDocument<64> doc;
        doc["turbine_id"] = "turbine-1";
        doc["wind_speed"] = wind_speed;
        char payload[64];
        serializeJson(doc, payload);

        client.publish(topic, payload);
        Serial.println(payload);
        last_publish = millis();
    }
    client.loop();
}