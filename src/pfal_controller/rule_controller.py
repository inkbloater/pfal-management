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
            sensor_type: Type of sensor (e.g., 'ph', 'ec', 'temperature')
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
        
        # Rule: IF temperature is in range, THEN turn off fans
        elif temp_value <= self.config.temp_max - 2.0:  # 2°C hysteresis
            return {
                'action': 'fans',
                'command': 'OFF',
                'reason': f'Temperature {temp_value:.2f}°C in normal range'
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
        
        # Evaluate pH control
        ph_command = self.evaluate_ph_control()
        if ph_command:
            commands.append(ph_command)
            
        # Evaluate EC control
        ec_command = self.evaluate_ec_control()
        if ec_command:
            commands.append(ec_command)
            
        # Evaluate temperature control
        temp_command = self.evaluate_temperature_control()
        if temp_command:
            commands.append(temp_command)
            
        # Evaluate lighting schedule
        light_command = self.evaluate_lighting_schedule()
        if light_command:
            commands.append(light_command)
            
        return commands
