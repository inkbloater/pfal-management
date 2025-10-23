import pytest
from pfal_controller.rule_controller import RuleBasedController
from pfal_controller.config import ControlConfig

# A fixture to create a default config for all tests
@pytest.fixture
def default_config():
    """Returns a default ControlConfig for testing."""
    return ControlConfig(
        ph_target=6.0,
        ph_tolerance=0.3,
        ec_target=1.5,
        ec_tolerance=0.2,
        temp_min=20.0,
        temp_max=28.0,
        lights_on_hour=6,
        lights_off_hour=22,
        ph_pump_duration_ms=1000,
        nutrient_pump_duration_ms=2000,
    )

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

def test_temperature_too_high_triggers_fans(default_config):
    """
    GIVEN a default configuration
    WHEN the temperature reading is above the maximum
    THEN the controller should return a command to turn on the fans.
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

def test_temperature_returns_to_normal_stops_fans(default_config):
    """
    GIVEN a default configuration
    WHEN the temperature is below the hysteresis threshold
    THEN the controller should return a command to turn off the fans.
    """
    # Arrange
    controller = RuleBasedController(default_config)
    # The hysteresis is hardcoded to 2.0 degrees below max
    controller.update_sensor_reading('temperature', 25.9) 

    # Act
    command = controller.evaluate_temperature_control()

    # Assert
    assert command is not None
    assert command['action'] == 'fans'
    assert command['command'] == 'OFF'

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