"""Configuration module for PFAL Controller."""
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


@dataclass
class MQTTConfig:
    """MQTT configuration."""
    broker: str
    port: int
    username: Optional[str]
    password: Optional[str]
    client_id: str
    
    # Sensor topics
    topic_ph: str
    topic_ec: str
    topic_temp: str
    topic_bme280: str
    
    # Actuator topics
    topic_ph_pump: str
    topic_nutrient_pump: str
    topic_main_pump: str
    topic_lights: str
    topic_fans: str


@dataclass
class InfluxDBConfig:
    """InfluxDB 2 configuration."""
    url: str
    token: str
    org: str
    bucket: str


@dataclass
class ControlConfig:
    """Control thresholds and parameters."""
    ph_target: float
    ph_tolerance: float
    ec_target: float
    ec_tolerance: float
    temp_min: float
    temp_max: float
    lights_on_hour: int
    lights_off_hour: int
    ph_pump_duration_ms: int
    nutrient_pump_duration_ms: int


@dataclass
class Config:
    """Main configuration container."""
    mqtt: MQTTConfig
    influxdb: InfluxDBConfig
    control: ControlConfig


def load_config(env_file: Optional[str] = None) -> Config:
    """
    Load configuration from environment variables.
    
    Args:
        env_file: Path to .env file (optional)
        
    Returns:
        Config object with all settings
    """
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()
    
    mqtt_config = MQTTConfig(
        broker=os.getenv('MQTT_BROKER', 'localhost'),
        port=int(os.getenv('MQTT_PORT', '1883')),
        username=os.getenv('MQTT_USERNAME') or None,
        password=os.getenv('MQTT_PASSWORD') or None,
        client_id=os.getenv('MQTT_CLIENT_ID', 'pfal_controller'),
        topic_ph=os.getenv('MQTT_TOPIC_PH', 'pfal/sensors/ph'),
        topic_ec=os.getenv('MQTT_TOPIC_EC', 'pfal/sensors/ec'),
        topic_temp=os.getenv('MQTT_TOPIC_TEMP', 'pfal/sensors/temperature'),
        topic_bme280=os.getenv('MQTT_TOPIC_BME280', 'pfal/sensors/bme280'),
        topic_ph_pump=os.getenv('MQTT_TOPIC_PH_PUMP', 'pfal/actuators/ph_pump'),
        topic_nutrient_pump=os.getenv('MQTT_TOPIC_NUTRIENT_PUMP', 'pfal/actuators/nutrient_pump'),
        topic_main_pump=os.getenv('MQTT_TOPIC_MAIN_PUMP', 'pfal/actuators/main_pump'),
        topic_lights=os.getenv('MQTT_TOPIC_LIGHTS', 'pfal/actuators/lights'),
        topic_fans=os.getenv('MQTT_TOPIC_FANS', 'pfal/actuators/fans'),
    )
    
    influxdb_config = InfluxDBConfig(
        url=os.getenv('INFLUXDB_URL', 'http://localhost:8086'),
        token=os.getenv('INFLUXDB_TOKEN', ''),
        org=os.getenv('INFLUXDB_ORG', 'pfal'),
        bucket=os.getenv('INFLUXDB_BUCKET', 'pfal_sensors'),
    )
    
    control_config = ControlConfig(
        ph_target=float(os.getenv('PH_TARGET', '6.0')),
        ph_tolerance=float(os.getenv('PH_TOLERANCE', '0.3')),
        ec_target=float(os.getenv('EC_TARGET', '1.5')),
        ec_tolerance=float(os.getenv('EC_TOLERANCE', '0.2')),
        temp_min=float(os.getenv('TEMP_MIN', '20.0')),
        temp_max=float(os.getenv('TEMP_MAX', '28.0')),
        lights_on_hour=int(os.getenv('LIGHTS_ON_HOUR', '6')),
        lights_off_hour=int(os.getenv('LIGHTS_OFF_HOUR', '22')),
        ph_pump_duration_ms=int(os.getenv('PH_PUMP_DURATION_MS', '1000')),
        nutrient_pump_duration_ms=int(os.getenv('NUTRIENT_PUMP_DURATION_MS', '2000')),
    )
    
    return Config(
        mqtt=mqtt_config,
        influxdb=influxdb_config,
        control=control_config,
    )
