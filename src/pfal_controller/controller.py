"""Main PFAL controller that orchestrates all components."""
import logging
import signal
import sys
import time
from typing import Dict, Any

from .config import load_config
from .mqtt_client import MQTTClient
from .influxdb_persistence import InfluxDBPersistence
from .rule_controller import RuleBasedController


logger = logging.getLogger(__name__)


class PFALController:
    """Main controller for PFAL automation system."""
    
    def __init__(self, config_file: str = None):
        """
        Initialize PFAL controller.
        
        Args:
            config_file: Path to configuration file (optional)
        """
        # Load configuration
        self.config = load_config(config_file)
        
        # Initialize components
        self.mqtt_client = MQTTClient(self.config.mqtt)
        self.influxdb = InfluxDBPersistence(self.config.influxdb)
        self.rule_controller = RuleBasedController(self.config.control)
        
        # Track last light state to avoid redundant commands
        self.last_light_state = None
        self.last_fan_state = None
        
        self.running = False
        
    def _handle_sensor_data(self, sensor_type: str, data: Dict[str, Any]):
        """
        Handle incoming sensor data.
        
        Args:
            sensor_type: Type of sensor
            data: Sensor data dictionary
        """
        try:
            # Parse sensor data and persist to InfluxDB
            if sensor_type == 'ph':
                value = data.get('value')
                if value is not None:
                    sensor_id = data.get('sensor_id', 'default')
                    self.influxdb.write_ph_reading(float(value), sensor_id)
                    self.rule_controller.update_sensor_reading('ph', float(value))
                    
            elif sensor_type == 'ec':
                value = data.get('value')
                if value is not None:
                    sensor_id = data.get('sensor_id', 'default')
                    self.influxdb.write_ec_reading(float(value), sensor_id)
                    self.rule_controller.update_sensor_reading('ec', float(value))
                    
            elif sensor_type == 'temperature':
                value = data.get('value')
                if value is not None:
                    sensor_id = data.get('sensor_id', 'default')
                    self.influxdb.write_temperature_reading(float(value), sensor_id)
                    self.rule_controller.update_sensor_reading('temperature', float(value))
                    
            elif sensor_type == 'bme280':
                temperature = data.get('temperature')
                humidity = data.get('humidity')
                pressure = data.get('pressure')
                if all([temperature is not None, humidity is not None, pressure is not None]):
                    sensor_id = data.get('sensor_id', 'default')
                    self.influxdb.write_bme280_reading(
                        float(temperature),
                        float(humidity),
                        float(pressure),
                        sensor_id
                    )
                    # Also update temperature for control decisions
                    self.rule_controller.update_sensor_reading('temperature', float(temperature))
                    
            # Evaluate control rules after each sensor update
            self._evaluate_and_execute_rules()
            
        except Exception as e:
            logger.error(f"Error handling sensor data for {sensor_type}: {e}")
            
    def _evaluate_and_execute_rules(self):
        """Evaluate control rules and execute necessary actions."""
        try:
            commands = self.rule_controller.evaluate_all_rules()
            
            for command in commands:
                action = command.get('action')
                cmd = command.get('command')
                duration_ms = command.get('duration_ms')
                reason = command.get('reason')
                
                # Avoid redundant light commands
                if action == 'lights':
                    if self.last_light_state == cmd:
                        continue
                    self.last_light_state = cmd
                    
                # Avoid redundant fan commands
                if action == 'fans':
                    if self.last_fan_state == cmd:
                        continue
                    self.last_fan_state = cmd
                
                logger.info(f"Executing action: {action} -> {cmd} (Reason: {reason})")
                self.mqtt_client.publish_command(action, cmd, duration_ms)
                
        except Exception as e:
            logger.error(f"Error evaluating rules: {e}")
            
    def _periodic_schedule_check(self):
        """Periodically check schedule-based rules (like lighting)."""
        while self.running:
            try:
                # Check lighting schedule
                light_command = self.rule_controller.evaluate_lighting_schedule()
                if light_command:
                    action = light_command.get('action')
                    cmd = light_command.get('command')
                    
                    # Only send if state changed
                    if self.last_light_state != cmd:
                        reason = light_command.get('reason')
                        logger.info(f"Executing scheduled action: {action} -> {cmd} (Reason: {reason})")
                        self.mqtt_client.publish_command(action, cmd)
                        self.last_light_state = cmd
                        
            except Exception as e:
                logger.error(f"Error in periodic schedule check: {e}")
                
            # Check schedule every 60 seconds
            time.sleep(60)
            
    def start(self):
        """Start the PFAL controller."""
        logger.info("Starting PFAL Controller...")
        
        try:
            # Connect to InfluxDB
            self.influxdb.connect()
            
            # Connect to MQTT broker
            self.mqtt_client.connect()
            
            # Register sensor callbacks
            self.mqtt_client.register_sensor_callback('ph', self._handle_sensor_data)
            self.mqtt_client.register_sensor_callback('ec', self._handle_sensor_data)
            self.mqtt_client.register_sensor_callback('temperature', self._handle_sensor_data)
            self.mqtt_client.register_sensor_callback('bme280', self._handle_sensor_data)
            
            self.running = True
            
            logger.info("PFAL Controller started successfully")
            
            # Run periodic schedule checks
            self._periodic_schedule_check()
            
        except Exception as e:
            logger.error(f"Failed to start PFAL Controller: {e}")
            self.stop()
            raise
            
    def stop(self):
        """Stop the PFAL controller."""
        logger.info("Stopping PFAL Controller...")
        
        self.running = False
        
        # Disconnect MQTT
        try:
            self.mqtt_client.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting MQTT client: {e}")
            
        # Disconnect InfluxDB
        try:
            self.influxdb.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting InfluxDB: {e}")
            
        logger.info("PFAL Controller stopped")
        

def setup_logging(log_level=logging.INFO):
    """Set up logging configuration."""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/var/log/pfal_controller.log', mode='a')
        ]
    )


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


def main():
    """Main entry point for PFAL controller."""
    # Set up logging
    setup_logging()
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start controller
    controller = PFALController()
    
    try:
        controller.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        controller.stop()


if __name__ == '__main__':
    main()
