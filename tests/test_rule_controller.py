import pytest
from pfal_controller.rule_controller import RuleBasedController
from pfal_controller.config import ControlConfig

# A fixture to create a default config for all tests
@pytest.fixture
def default_config():
    """Returns a default ControlConfig for testing, including new humidity fields."""
    return ControlConfig(
        profile_name="test_profile",
        ph_target=6.0,
        ph_tolerance=0.3,
        ec_target=1.5,
        ec_tolerance=0.2,
        temp_min=20.0,
        temp_max=28.0,
        humidity_min=50.0,
        humidity_max=70.0,
        lights_on_hour=6,
        lights_off_hour=22,
        ph_pump_duration_ms=1000,
        nutrient_pump_duration_ms=2000,
    )

# --- Existing Tests (Still Valid) ---

def test_ph_too_low_triggers_pump(default_config):
    """
    GIVEN a default configuration
    WHEN the pH reading is below the minimum threshold
    THEN the controller should return a command to turn on the pH pump.
    """
    # Arrange
    controller = RuleBasedController(default_config)
    low_ph_value = 5.6
    controller.update_sensor_reading('ph', low_ph_value)

    # Act
    command = controller.evaluate_ph_control()

    # Assert
    assert command is not None
    assert command['action'] == 'ph_pump'
    assert command['command'] == 'ON'
    assert command['duration_ms'] == default_config.ph_pump_duration_ms

def test_ph_in_range_does_nothing(default_config):
    """
    GIVEN a default configuration
    WHEN the pH reading is within the target range
    THEN the controller should return None.
    """
    # Arrange
    controller = RuleBasedController(default_config)
    controller.update_sensor_reading('ph', 6.1)

    # Act
    command = controller.evaluate_ph_control()

    # Assert
    assert command is None

# --- New and Updated Tests for Temperature and Humidity ---

def test_temperature_too_high_triggers_fans(default_config):
    """
    GIVEN a default configuration
    WHEN the temperature reading is above the maximum
    THEN the temperature rule should return a command to turn on the fans.
    """
    # Arrange
    controller = RuleBasedController(default_config)
    controller.update_sensor_reading('temperature', 29.5)

    # Act
    command = controller.evaluate_temperature_control()

    # Assert
    assert command is not None
    assert command['action'] == 'fans'
    assert command['command'] == 'ON'

def test_humidity_too_high_triggers_fans(default_config):
    """
    GIVEN a default configuration
    WHEN the humidity reading is above the maximum
    THEN the humidity rule should return a command to turn on the fans.
    """
    # Arrange
    controller = RuleBasedController(default_config)
    controller.update_sensor_reading('humidity', 75.0)

    # Act
    command = controller.evaluate_humidity_control()

    # Assert
    assert command is not None
    assert command['action'] == 'fans'
    assert command['command'] == 'ON'

def test_fan_off_command_when_both_temp_and_humidity_are_normal(default_config):
    """
    GIVEN a default configuration
    WHEN both temperature and humidity are within their normal ranges (including hysteresis)
    THEN both rules should independently suggest turning the fans OFF.
    """
    # Arrange
    controller = RuleBasedController(default_config)
    controller.update_sensor_reading('temperature', 25.0) # Below temp_max - 2.0
    controller.update_sensor_reading('humidity', 64.0)  # Below humidity_max - 5.0

    # Act
    temp_command = controller.evaluate_temperature_control()
    humidity_command = controller.evaluate_humidity_control()

    # Assert
    assert temp_command is not None
    assert temp_command['action'] == 'fans'
    assert temp_command['command'] == 'OFF'

    assert humidity_command is not None
    assert humidity_command['action'] == 'fans'
    assert humidity_command['command'] == 'OFF'

def test_fan_off_command_is_suppressed_if_temp_ok_but_humidity_high(default_config):
    """
    GIVEN a default configuration
    WHEN temperature returns to normal but humidity is still high
    THEN the temperature rule should NOT return a command to turn fans OFF.
    """
    # Arrange
    controller = RuleBasedController(default_config)
    controller.update_sensor_reading('temperature', 25.0) # Temp is OK
    controller.update_sensor_reading('humidity', 75.0)  # Humidity is HIGH

    # Act
    temp_command = controller.evaluate_temperature_control() # This rule should now be suppressed
    humidity_command = controller.evaluate_humidity_control() # This rule should request ON

    # Assert
    assert temp_command is None # The temp rule should not try to turn the fan off
    assert humidity_command is not None
    assert humidity_command['command'] == 'ON'

def test_fan_off_command_is_suppressed_if_humidity_ok_but_temp_high(default_config):
    """
    GIVEN a default configuration
    WHEN humidity returns to normal but temperature is still high
    THEN the humidity rule should NOT return a command to turn fans OFF.
    """
    # Arrange
    controller = RuleBasedController(default_config)
    controller.update_sensor_reading('temperature', 30.0) # Temp is HIGH
    controller.update_sensor_reading('humidity', 64.0)  # Humidity is OK

    # Act
    temp_command = controller.evaluate_temperature_control() # This rule should request ON
    humidity_command = controller.evaluate_humidity_control() # This rule should now be suppressed

    # Assert
    assert temp_command is not None
    assert temp_command['command'] == 'ON'
    assert humidity_command is None # The humidity rule should not try to turn the fan off

# --- Existing Lighting Test (Still Valid) ---

@pytest.mark.parametrize("hour, expected_command", [
    (5, 'OFF'),  # Before schedule
    (6, 'ON'),   # Start of schedule
    (12, 'ON'),  # Middle of schedule
    (21, 'ON'),  # End of schedule
    (22, 'OFF'), # After schedule
])
def test_lighting_schedule(default_config, hour, expected_command, monkeypatch):
    """
    GIVEN a default configuration
    WHEN the time is at various hours of the day
    THEN the lighting command should be correct for that hour.
    """
    # Arrange
    class MockDateTime:
        def __init__(self, hour):
            self._hour = hour
        def now(self):
            return self
        @property
        def hour(self):
            return self._hour

    # Monkeypatch datetime.now() to control the time in the test
    monkeypatch.setattr('pfal_controller.rule_controller.datetime', MockDateTime(hour))
    controller = RuleBasedController(default_config)

    # Act
    command = controller.evaluate_lighting_schedule()

    # Assert
    assert command['command'] == expected_command