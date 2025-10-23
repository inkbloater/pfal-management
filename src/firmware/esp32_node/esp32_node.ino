// Include libraries for WiFi, MQTT, and all your sensors
#include <WiFi.h>
#include <PubSubClient.h>
#include <Adafruit_BME280.h>
#include <OneWire.h>
#include <DallasTemperature.h>
// ... other sensor/actuator libraries

// WiFi & MQTT Config
const char* ssid = "Parikh";
const char* password = "darkknight22";
const char* mqtt_server = "192.168.1.46";
const char* node_id = "esp32_tier1"; // Unique ID for each ESP32

// Sensor & Actuator Pin Definitions
#define BME_SCK 22
#define BME_SDA 21
#define ONEWIRE_BUS 4
#define PH_DOWN_PUMP_PIN 26
#define LIGHTS_RELAY_PIN 27

// Initialize clients and sensors
WiFiClient espClient;
PubSubClient mqttClient(espClient);
Adafruit_BME280 bme;
OneWire oneWire(ONEWIRE_BUS);
DallasTemperature temp_sensors(&oneWire);

void setup() {
  Serial.begin(115200);
  pinMode(PH_DOWN_PUMP_PIN, OUTPUT);
  pinMode(LIGHTS_RELAY_PIN, OUTPUT);

  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  // Connect to sensors
  bme.begin(0x76); // Or your BME280 address
  temp_sensors.begin();

  // Connect to MQTT Broker
  mqttClient.setServer(mqtt_server, 1883);
  mqttClient.setCallback(callback); // Function to handle incoming commands
}

// This function is called when a message is received from the MQTT broker
void callback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.print("Message arrived on topic: ");
  Serial.println(topic);

  // --- Rule-based command handling ---
  if (String(topic) == "pfal/tier1/ph_down/command") {
    if (message == "ON") {
      digitalWrite(PH_DOWN_PUMP_PIN, HIGH);
    } else {
      digitalWrite(PH_DOWN_PUMP_PIN, LOW);
    }
  }
  // ... add more else-if blocks for other actuators
}

void reconnect() {
  while (!mqttClient.connected()) {
    if (mqttClient.connect(node_id)) {
      Serial.println("MQTT Connected!");
      // Subscribe to command topics for this node
      mqttClient.subscribe("pfal/tier1/ph_down/command");
      mqttClient.subscribe("pfal/tier1/lights/command");
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      delay(5000);
    }
  }
}

void loop() {
  if (!mqttClient.connected()) {
    reconnect();
  }
  mqttClient.loop();

  // --- Read Sensors and Publish Data ---
  static unsigned long lastMsg = 0;
  if (millis() - lastMsg > 30000) { // Publish every 30 seconds
    lastMsg = millis();

    // Read BME280
    float air_temp = bme.readTemperature();
    float humidity = bme.readHumidity();

    // Read DS18B20
    temp_sensors.requestTemperatures();
    float water_temp = temp_sensors.getTempCByIndex(0);

    // Create a JSON payload
    String payload = "{\"air_temp\":" + String(air_temp) + ", \"humidity\":" + String(humidity) + ", \"water_temp\":" + String(water_temp) + "}";

    // Publish to a unique topic for this node's sensor data
    mqttClient.publish("pfal/tier1/sensors", payload.c_str());
  }
}