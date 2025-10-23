"""InfluxDB persistence module for sensor data."""
import logging
from datetime import datetime
from typing import Dict, Any
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from .config import InfluxDBConfig


logger = logging.getLogger(__name__)


class InfluxDBPersistence:
    """Handles persistence of sensor data to InfluxDB 2."""
    
    def __init__(self, config: InfluxDBConfig):
        """
        Initialize InfluxDB client.
        
        Args:
            config: InfluxDB configuration
        """
        self.config = config
        self.client = None
        self.write_api = None
        
    def connect(self):
        """Establish connection to InfluxDB."""
        try:
            self.client = InfluxDBClient(
                url=self.config.url,
                token=self.config.token,
                org=self.config.org
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            logger.info(f"Connected to InfluxDB at {self.config.url}")
        except Exception as e:
            logger.error(f"Failed to connect to InfluxDB: {e}")
            raise
            
    def disconnect(self):
        """Close connection to InfluxDB."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from InfluxDB")
            
    def write_sensor_data(self, measurement: str, tags: Dict[str, str], 
                         fields: Dict[str, Any], timestamp: datetime = None):
        """
        Write sensor data to InfluxDB.
        
        Args:
            measurement: Measurement name (e.g., 'ph', 'ec', 'temperature')
            tags: Dictionary of tags (e.g., {'sensor_id': 'esp32_1', 'location': 'zone_a'})
            fields: Dictionary of field values (e.g., {'value': 6.5})
            timestamp: Optional timestamp (defaults to current time)
        """
        if not self.write_api:
            logger.error("InfluxDB write API not initialized")
            return
            
        try:
            point = Point(measurement)
            
            # Add tags
            for tag_key, tag_value in tags.items():
                point.tag(tag_key, tag_value)
            
            # Add fields
            for field_key, field_value in fields.items():
                point.field(field_key, field_value)
            
            # Set timestamp if provided
            if timestamp:
                point.time(timestamp)
            
            # Write to InfluxDB
            self.write_api.write(bucket=self.config.bucket, record=point)
            logger.debug(f"Wrote {measurement} data to InfluxDB: {fields}")
            
        except Exception as e:
            logger.error(f"Failed to write data to InfluxDB: {e}")
            
    def write_ph_reading(self, ph_value: float, sensor_id: str = "default"):
        """Write pH sensor reading."""
        self.write_sensor_data(
            measurement="ph",
            tags={"sensor_id": sensor_id},
            fields={"value": ph_value}
        )
        
    def write_ec_reading(self, ec_value: float, sensor_id: str = "default"):
        """Write EC sensor reading."""
        self.write_sensor_data(
            measurement="ec",
            tags={"sensor_id": sensor_id},
            fields={"value": ec_value}
        )
        
    def write_temperature_reading(self, temp_value: float, sensor_id: str = "default"):
        """Write temperature sensor reading."""
        self.write_sensor_data(
            measurement="temperature",
            tags={"sensor_id": sensor_id},
            fields={"value": temp_value}
        )
        
    def write_bme280_reading(self, temperature: float, humidity: float, 
                            pressure: float, sensor_id: str = "default"):
        """Write BME280 sensor reading (temperature, humidity, pressure)."""
        self.write_sensor_data(
            measurement="bme280",
            tags={"sensor_id": sensor_id},
            fields={
                "temperature": temperature,
                "humidity": humidity,
                "pressure": pressure
            }
        )
