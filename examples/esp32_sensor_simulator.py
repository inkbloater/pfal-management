"""
Example ESP32 Sensor Node Code (for reference)

This is a Python representation of what an ESP32 sensor node might publish.
The actual ESP32 code would be in C++ using the Arduino framework.

This example shows the expected MQTT message formats.
"""

import paho.mqtt.client as mqtt
import json
import time
import random


class ESP32SensorSimulator:
    """Simulates an ESP32 sensor node for testing purposes."""
    
    def __init__(self, broker='localhost', port=1883, sensor_id='esp32_1'):
        self.broker = broker
        self.port = port
        self.sensor_id = sensor_id
        self.client = mqtt.Client(client_id=f'esp32_simulator_{sensor_id}')
        
    def connect(self):
        """Connect to MQTT broker."""
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()
        print(f"Connected to MQTT broker at {self.broker}:{self.port}")
        
    def disconnect(self):
        """Disconnect from MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()
        
    def publish_ph_reading(self, value):
        """Publish pH sensor reading."""
        payload = {
            'value': value,
            'sensor_id': self.sensor_id
        }
        self.client.publish('pfal/sensors/ph', json.dumps(payload))
        print(f"Published pH: {value}")
        
    def publish_ec_reading(self, value):
        """Publish EC sensor reading."""
        payload = {
            'value': value,
            'sensor_id': self.sensor_id
        }
        self.client.publish('pfal/sensors/ec', json.dumps(payload))
        print(f"Published EC: {value}")
        
    def publish_temperature_reading(self, value):
        """Publish temperature sensor reading."""
        payload = {
            'value': value,
            'sensor_id': self.sensor_id
        }
        self.client.publish('pfal/sensors/temperature', json.dumps(payload))
        print(f"Published Temperature: {value}°C")
        
    def publish_bme280_reading(self, temperature, humidity, pressure):
        """Publish BME280 sensor reading."""
        payload = {
            'temperature': temperature,
            'humidity': humidity,
            'pressure': pressure,
            'sensor_id': self.sensor_id
        }
        self.client.publish('pfal/sensors/bme280', json.dumps(payload))
        print(f"Published BME280: Temp={temperature}°C, Humidity={humidity}%, Pressure={pressure}hPa")
        
    def simulate_sensors(self):
        """Simulate sensor readings with some variation."""
        while True:
            # Simulate pH reading (target around 6.0)
            ph = 6.0 + random.uniform(-0.5, 0.5)
            self.publish_ph_reading(round(ph, 2))
            
            # Simulate EC reading (target around 1.5)
            ec = 1.5 + random.uniform(-0.3, 0.3)
            self.publish_ec_reading(round(ec, 2))
            
            # Simulate temperature reading
            temp = 24.0 + random.uniform(-3, 3)
            self.publish_temperature_reading(round(temp, 2))
            
            # Simulate BME280 reading
            bme_temp = 24.0 + random.uniform(-2, 2)
            bme_humidity = 65.0 + random.uniform(-10, 10)
            bme_pressure = 1013.25 + random.uniform(-5, 5)
            self.publish_bme280_reading(
                round(bme_temp, 2),
                round(bme_humidity, 2),
                round(bme_pressure, 2)
            )
            
            # Wait 10 seconds before next reading
            time.sleep(10)


if __name__ == '__main__':
    """
    Example usage for testing the PFAL controller.
    
    Run this simulator to generate test sensor data:
        python examples/esp32_sensor_simulator.py
    """
    simulator = ESP32SensorSimulator()
    simulator.connect()
    
    try:
        simulator.simulate_sensors()
    except KeyboardInterrupt:
        print("\nStopping simulator...")
    finally:
        simulator.disconnect()
