"""MQTT client for sensor data and actuator control."""
import logging
import json
from typing import Callable, Optional, Dict, Any
import paho.mqtt.client as mqtt

from .config import MQTTConfig


logger = logging.getLogger(__name__)


class MQTTClient:
    """Handles MQTT communication for sensors and actuators."""
    
    def __init__(self, config: MQTTConfig):
        """
        Initialize MQTT client.
        
        Args:
            config: MQTT configuration
        """
        self.config = config
        self.client = mqtt.Client(client_id=config.client_id)
        self.sensor_callbacks = {}
        self.connected = False
        
        # Set up callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        # Set authentication if provided
        if config.username and config.password:
            self.client.username_pw_set(config.username, config.password)
            
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker."""
        if rc == 0:
            self.connected = True
            logger.info(f"Connected to MQTT broker at {self.config.broker}:{self.config.port}")
            
            # Subscribe to all sensor topics
            self._subscribe_to_sensors()
        else:
            logger.error(f"Failed to connect to MQTT broker, return code: {rc}")
            
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the broker."""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnect from MQTT broker, return code: {rc}")
        else:
            logger.info("Disconnected from MQTT broker")
            
    def _on_message(self, client, userdata, msg):
        """Callback for when a message is received."""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            logger.debug(f"Received message on topic {topic}: {payload}")
            
            # Parse JSON payload
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                # If not JSON, treat as plain value
                data = {'value': float(payload)}
            
            # Determine sensor type and call appropriate callback
            if topic == self.config.topic_ph:
                self._handle_sensor_data('ph', data)
            elif topic == self.config.topic_ec:
                self._handle_sensor_data('ec', data)
            elif topic == self.config.topic_temp:
                self._handle_sensor_data('temperature', data)
            elif topic == self.config.topic_bme280:
                self._handle_sensor_data('bme280', data)
            else:
                logger.warning(f"Received message on unknown topic: {topic}")
                
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
            
    def _handle_sensor_data(self, sensor_type: str, data: Dict[str, Any]):
        """
        Handle sensor data by calling registered callbacks.
        
        Args:
            sensor_type: Type of sensor
            data: Sensor data dictionary
        """
        if sensor_type in self.sensor_callbacks:
            for callback in self.sensor_callbacks[sensor_type]:
                try:
                    callback(sensor_type, data)
                except Exception as e:
                    logger.error(f"Error in sensor callback for {sensor_type}: {e}")
                    
    def _subscribe_to_sensors(self):
        """Subscribe to all sensor topics."""
        topics = [
            (self.config.topic_ph, 0),
            (self.config.topic_ec, 0),
            (self.config.topic_temp, 0),
            (self.config.topic_bme280, 0),
        ]
        
        for topic, qos in topics:
            self.client.subscribe(topic, qos)
            logger.info(f"Subscribed to topic: {topic}")
            
    def connect(self):
        """Connect to MQTT broker."""
        try:
            self.client.connect(self.config.broker, self.config.port, 60)
            self.client.loop_start()
            logger.info(f"Connecting to MQTT broker at {self.config.broker}:{self.config.port}")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise
            
    def disconnect(self):
        """Disconnect from MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT client disconnected")
        
    def register_sensor_callback(self, sensor_type: str, callback: Callable):
        """
        Register a callback for sensor data.
        
        Args:
            sensor_type: Type of sensor (e.g., 'ph', 'ec', 'temperature', 'bme280')
            callback: Callback function that takes (sensor_type, data) as arguments
        """
        if sensor_type not in self.sensor_callbacks:
            self.sensor_callbacks[sensor_type] = []
        self.sensor_callbacks[sensor_type].append(callback)
        logger.debug(f"Registered callback for {sensor_type} sensor")
        
    def publish_command(self, actuator: str, command: str, duration_ms: Optional[int] = None):
        """
        Publish command to actuator.
        
        Args:
            actuator: Actuator name (e.g., 'ph_pump', 'nutrient_pump', 'lights', 'fans')
            command: Command to send (e.g., 'ON', 'OFF')
            duration_ms: Optional duration in milliseconds for timed commands
        """
        topic_map = {
            'ph_pump': self.config.topic_ph_pump,
            'nutrient_pump': self.config.topic_nutrient_pump,
            'main_pump': self.config.topic_main_pump,
            'lights': self.config.topic_lights,
            'fans': self.config.topic_fans,
        }
        
        if actuator not in topic_map:
            logger.error(f"Unknown actuator: {actuator}")
            return
            
        topic = topic_map[actuator]
        
        # Build payload
        payload = {
            'command': command,
        }
        if duration_ms is not None:
            payload['duration_ms'] = duration_ms
            
        # Publish message
        try:
            payload_json = json.dumps(payload)
            result = self.client.publish(topic, payload_json, qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published command to {actuator}: {payload_json}")
            else:
                logger.error(f"Failed to publish command to {actuator}")
        except Exception as e:
            logger.error(f"Error publishing command: {e}")
