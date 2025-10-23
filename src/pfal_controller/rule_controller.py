"""Rule-based control logic for PFAL automation."""
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from .config import ControlConfig


logger = logging.getLogger(__name__)


class RuleBasedController:
    """Implements IF-THEN rules for PFAL control."""
    
    def __init__(self, config: ControlConfig):
        """
        Initialize rule-based controller.
        
        Args:
            config: Control configuration with thresholds
        """
        self.config = config
        self.last_sensor_readings = {}
        
    def update_sensor_reading(self, sensor_type: str, value: Any):
        """
        Update the latest sensor reading.
        
        Args:
            sensor_type: Type of sensor (e.g., 'ph', 'ec', 'temperature', 'humidity')
            value: Sensor value
        """
        self.last_sensor_readings[sensor_type] = {
            'value': value,
            'timestamp': datetime.now()
        }
        logger.debug(f"Updated {sensor_type} reading: {value}")
        
    def evaluate_ph_control(self) -> Optional[Dict[str, Any]]:
        """
        Evaluate pH control rules.
        
        Returns:
            Command dictionary if action needed, None otherwise
        """
        if 'ph' not in self.last_sensor_readings:
            return None
            
        ph_value = self.last_sensor_readings['ph']['value']
        ph_min = self.config.ph_target - self.config.ph_tolerance
        ph_max = self.config.ph_target + self.config.ph_tolerance
        
        # Rule: IF pH is too low, THEN activate pH up pump
        if ph_value < ph_min:
            logger.info(f"pH too low ({ph_value:.2f} < {ph_min:.2f}), activating pH pump")
            return {
                'action': 'ph_pump',
                'command': 'ON',
                'duration_ms': self.config.ph_pump_duration_ms,
                'reason': f'pH {ph_value:.2f} below target range'
            }
        
        # Rule: IF pH is too high, THEN log warning (pH down could be added)
        elif ph_value > ph_max:
            logger.warning(f"pH too high ({ph_value:.2f} > {ph_max:.2f})")
            # Could add pH down pump control here
            
        return None
        
    def evaluate_ec_control(self) -> Optional[Dict[str, Any]]:
        """
        Evaluate EC (nutrient) control rules.
        
        Returns:
            Command dictionary if action needed, None otherwise
        """
        if 'ec' not in self.last_sensor_readings:
            return None
            
        ec_value = self.last_sensor_readings['ec']['value']
        ec_min = self.config.ec_target - self.config.ec_tolerance
        
        # Rule: IF EC is too low, THEN activate nutrient pump
        if ec_value < ec_min:
            logger.info(f"EC too low ({ec_value:.2f} < {ec_min:.2f}), activating nutrient pump")
            return {
                'action': 'nutrient_pump',
                'command': 'ON',
                'duration_ms': self.config.nutrient_pump_duration_ms,
                'reason': f'EC {ec_value:.2f} below target range'
            }
            
        return None
        
    def evaluate_temperature_control(self) -> Optional[Dict[str, Any]]:
        """
        Evaluate temperature control rules.
        
        Returns:
            Command dictionary if action needed, None otherwise
        """
        if 'temperature' not in self.last_sensor_readings:
            return None
            
        temp_value = self.last_sensor_readings['temperature']['value']
        
        # Rule: IF temperature is too high, THEN activate fans
        if temp_value > self.config.temp_max:
            logger.info(f"Temperature too high ({temp_value:.2f}°C > {self.config.temp_max:.2f}°C), activating fans")
            return {
                'action': 'fans',
                'command': 'ON',
                'reason': f'Temperature {temp_value:.2f}°C above maximum'
            }
        
        # Rule: IF temperature is in range, THEN turn off fans (if not needed for humidity)
        elif temp_value <= self.config.temp_max - 2.0:  # 2°C hysteresis
            # Only turn off if humidity is also okay
            if 'humidity' not in self.last_sensor_readings or self.last_sensor_readings['humidity']['value'] < self.config.humidity_max:
                return {
                    'action': 'fans',
                    'command': 'OFF',
                    'reason': f'Temperature {temp_value:.2f}°C in normal range'
                }
            
        return None

    def evaluate_humidity_control(self) -> Optional[Dict[str, Any]]:
        """
        Evaluate humidity control rules.

        Returns:
            Command dictionary if action needed, None otherwise
        """
        if 'humidity' not in self.last_sensor_readings:
            return None

        humidity_value = self.last_sensor_readings['humidity']['value']

        # Rule: IF humidity is too high, THEN activate fans
        if humidity_value > self.config.humidity_max:
            logger.info(f"Humidity too high ({humidity_value:.2f}% > {self.config.humidity_max:.2f}%), activating fans")
            return {
                'action': 'fans',
                'command': 'ON',
                'reason': f'Humidity {humidity_value:.2f}% above maximum'
            }
        
        # Rule: IF humidity is in range, THEN turn off fans (if not needed for temp)
        elif humidity_value < self.config.humidity_max - 5.0: # 5% hysteresis
            if 'temperature' not in self.last_sensor_readings or self.last_sensor_readings['temperature']['value'] < self.config.temp_max:
                return {
                    'action': 'fans',
                    'command': 'OFF',
                    'reason': f'Humidity {humidity_value:.2f}% in normal range'
                }

        return None
        
    def evaluate_lighting_schedule(self) -> Optional[Dict[str, Any]]:
        """
        Evaluate lighting schedule rules.
        
        Returns:
            Command dictionary if action needed, None otherwise
        """
        current_hour = datetime.now().hour
        
        # Rule: IF current time is within lighting hours, THEN lights ON
        if self.config.lights_on_hour <= current_hour < self.config.lights_off_hour:
            return {
                'action': 'lights',
                'command': 'ON',
                'reason': f'Within lighting schedule ({self.config.lights_on_hour}:00-{self.config.lights_off_hour}:00)'
            }
        # Rule: ELSE lights OFF
        else:
            return {
                'action': 'lights',
                'command': 'OFF',
                'reason': f'Outside lighting schedule'
            }
            
    def evaluate_all_rules(self) -> list:
        """
        Evaluate all control rules.
        
        Returns:
            List of command dictionaries for actions that need to be taken
        """
        commands = []
        
        # The order can matter. Temp/Humidity might both want to control fans.
        # A simple approach is to collect all desired commands and merge them.
        # A more complex one would prioritize. For now, let's just collect.
        
        ph_command = self.evaluate_ph_control()
        if ph_command:
            commands.append(ph_command)
            
        ec_command = self.evaluate_ec_control()
        if ec_command:
            commands.append(ec_command)
            
        temp_command = self.evaluate_temperature_control()
        if temp_command:
            commands.append(temp_command)

        humidity_command = self.evaluate_humidity_control()
        if humidity_command:
            commands.append(humidity_command)
            
        light_command = self.evaluate_lighting_schedule()
        if light_command:
            commands.append(light_command)
            
        return commands

```

2.  **Update `src/pfal_controller/controller.py`** to handle humidity data.

````python name=src/pfal_controller/controller.py
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
                    # Also update temperature and humidity for control decisions
                    self.rule_controller.update_sensor_reading('temperature', float(temperature))
                    self.rule_controller.update_sensor_reading('humidity', float(humidity))
                    
            # Evaluate control rules after each sensor update
            self._evaluate_and_execute_rules()
            
        except Exception as e:
            logger.error(f"Error handling sensor data for {sensor_type}: {e}")
            
    def _evaluate_and_execute_rules(self):
        """Evaluate control rules and execute necessary actions."""
        try:
            commands = self.rule_controller.evaluate_all_rules()
            
            # Simple conflict resolution: if any rule wants fans ON, they are ON.
            fan_on_requested = any(cmd.get('action') == 'fans' and cmd.get('command') == 'ON' for cmd in commands)
            
            final_commands = []
            fan_command_processed = False
            for command in commands:
                action = command.get('action')
                
                if action == 'fans':
                    if not fan_command_processed:
                        # Add a single, resolved fan command
                        fan_cmd = 'ON' if fan_on_requested else 'OFF'
                        final_commands.append({'action': 'fans', 'command': fan_cmd, 'reason': 'Resolved from temp/humidity rules'})
                        fan_command_processed = True
                else:
                    # Add non-fan commands directly
                    final_commands.append(command)


            for command in final_commands:
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
        logger.info(f"Starting PFAL Controller with profile: {self.config.control.profile_name}")
        
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
            
            # Start periodic checks in a separate thread to not block the main loop
            import threading
            schedule_thread = threading.Thread(target=self._periodic_schedule_check, daemon=True)
            schedule_thread.start()
            
            # Keep the main thread alive to handle MQTT messages
            while self.running:
                time.sleep(1)
            
        except Exception as e:
            logger.error(f"Failed to start PFAL Controller: {e}")
            self.stop()
            raise
            
    def stop(self):
        """Stop the PFAL controller."""
        if not self.running:
            return
            
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
        stream=sys.stdout # Log to stdout by default
    )
    # File handler can be added here if needed, but consider permissions
    # handlers=[
    #     logging.StreamHandler(sys.stdout),
    #     logging.FileHandler('/var/log/pfal_controller.log', mode='a')
    # ]


def signal_handler(controller: PFALController):
    def handler(signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        controller.stop()
        sys.exit(0)
    return handler


def main():
    """Main entry point for PFAL controller."""
    # Set up logging
    setup_logging()
    
    # Create controller instance
    config_file = os.getenv('CONFIG_FILE')
    controller = PFALController(config_file=config_file)
    
    # Set up signal handlers for graceful shutdown
    shutdown_handler = signal_handler(controller)
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    try:
        controller.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        controller.stop()


if __name__ == '__main__':
    main()