# PFAL Management System

Manages the automation of PFAL (Plant Factory with Artificial Lighting). This system provides a flexible, rule-based controller for monitoring and automating environmental conditions in a plant factory.

## Features

The current implementation provides a Raspberry Pi-based controller that:

- **Dynamic Crop Profiles**: Loads control setpoints from JSON-based crop profiles, allowing for easy switching between different plant requirements (e.g., spinach, basil).
- **Rule-Based Control**: Implements IF-THEN control logic for:
  - pH adjustment via peristaltic pump
  - Nutrient (EC) dosing via peristaltic pump
  - Temperature control via fans
  - Humidity control via fans
  - Lighting control based on a daily schedule
- **Data Persistence**: Persists all sensor data to InfluxDB 2 for historical analysis and monitoring.
- **MQTT Communication**: Subscribes to sensor topics and publishes commands to actuators using the standard MQTT protocol.

## Architecture

```
ESP32 Sensors → MQTT Topics → Raspberry Pi Controller → MQTT Commands → Actuators
                                        ↓
                                   InfluxDB 2
```

## Installation

### Prerequisites

- Python 3.7 or higher
- MQTT Broker (e.g., Mosquitto)
- InfluxDB 2.x

### Install Dependencies

For production/deployment:
```bash
pip install -r requirements.txt
```

For development and running tests:
```bash
pip install -r requirements-dev.txt
```

## Configuration

The system now uses a combination of a `.env` file for core settings and JSON files for crop-specific setpoints.

### 1. Create Crop Profiles

Create a JSON file for each crop you want to grow in the `config/profiles/` directory.

Example: `config/profiles/basil.json`
```json
{
    "profile_name": "Basil",
    "ph_target": 6.0,
    "ph_tolerance": 0.3,
    "ec_target": 1.6,
    "ec_tolerance": 0.2,
    "temp_min": 22.0,
    "temp_max": 28.0,
    "humidity_min": 50.0,
    "humidity_max": 70.0,
    "lights_on_hour": 5,
    "lights_off_hour": 23,
    "ph_pump_duration_ms": 1000,
    "nutrient_pump_duration_ms": 2000
}
```

### 2. Configure the Environment

1.  Copy the example configuration file:
    ```bash
    cp config/config.example.env .env
    ```

2.  Edit `.env` with your settings. The most important change is setting the `CROP_PROFILE`.

    ```dotenv
    # PFAL Crop Profile
    # The name of the JSON file in `config/profiles/` to use (without .json extension).
    CROP_PROFILE=basil

    # MQTT Configuration
    MQTT_BROKER=localhost
    MQTT_PORT=1883
    # ... other settings

    # InfluxDB 2 Configuration
    INFLUXDB_URL=http://localhost:8086
    INFLUXDB_TOKEN=your-influxdb-token
    # ... other settings
    ```

## Usage

### Run the Controller

```bash
python main.py
```

Or with a custom environment file:

```bash
python main.py --config /path/to/custom.env
```

### Run as a Service (systemd)

A `config/pfal-controller.service` file is provided. To install:
```bash
sudo cp config/pfal-controller.service /etc/systemd/system/
sudo systemctl enable pfal-controller
sudo systemctl start pfal-controller
sudo systemctl status pfal-controller
```

## Development & Testing

### Sensor Simulator
For local testing without hardware, you can run the ESP32 sensor simulator. It will publish random sensor data to the MQTT broker.

```bash
python examples/esp32_sensor_simulator.py
```

### Unit Tests
The project includes unit tests for the control logic. To run them, first install development dependencies (`pip install -r requirements-dev.txt`), then run `pytest`.

```bash
pytest
```

## Control Rules

- **pH Control**: Activates pH pump if `pH < (target - tolerance)`.
- **EC (Nutrient) Control**: Activates nutrient pump if `EC < (target - tolerance)`.
- **Temperature Control**: Activates fans if `temperature > max_threshold`.
- **Humidity Control**: Activates fans if `humidity > max_threshold`.
- **Fan Deactivation**: Fans are turned OFF only if **both** temperature and humidity are within their normal ranges (including hysteresis).
- **Lighting Control**: Lights are turned ON/OFF based on the `lights_on_hour` and `lights_off_hour` schedule.

## MQTT Topics & Message Format

These have not changed. Sensor data is expected on `pfal/sensors/*` and commands are published to `pfal/actuators/*`. See the original documentation below for formats.

### Sensor Topics (Subscribed)
- `pfal/sensors/ph`
- `pfal/sensors/ec`
- `pfal/sensors/temperature`
- `pfal/sensors/bme280`

### Actuator Topics (Published)
- `pfal/actuators/ph_pump`
- `pfal/actuators/nutrient_pump`
- `pfal/actuators/main_pump`
- `pfal/actuators/lights`
- `pfal/actuators/fans`

### Message Format
Sensor messages (JSON):
`{ "value": 6.5, "sensor_id": "esp32_1" }`

BME280 sensor message (JSON):
`{ "temperature": 24.5, "humidity": 65.0, "pressure": 1013.25, "sensor_id": "esp32_1" }`

Actuator command message (JSON):
`{ "command": "ON", "duration_ms": 1000 }`

## ESP32 Firmware

A reference firmware implementation for an ESP32 node is located at `src/firmware/esp32_node/esp32_node.ino`. This can be used as a starting point for developing the code for your physical hardware.

## Project Structure

```
pfal-management/
├── config/
│   ├── profiles/
│   │   ├── basil.json         # Example crop profile
│   │   └── spinach.json       # Example crop profile
│   ├── config.example.env     # Example configuration file
│   └── ...
├── examples/
│   └── esp32_sensor_simulator.py
├── src/
│   ├── firmware/
│   │   └── esp32_node/
│   │       └── esp32_node.ino   # Reference ESP32 firmware
│   └── pfal_controller/
│       ├── __init__.py
│       ├── config.py          # Configuration management
│       ├── controller.py      # Main controller orchestration
│       ├── influxdb_persistence.py # InfluxDB data persistence
│       ├── mqtt_client.py     # MQTT communication
│       └── rule_controller.py # Rule-based control logic
├── tests/
│   └── test_rule_controller.py  # Unit tests for control logic
├── main.py                    # Main entry point
├── requirements.txt           # Python dependencies
├── requirements-dev.txt       # Development/testing dependencies
└── README.md                  # This file
```

## Future Enhancements

Phase 2 and beyond will include:
- Machine learning-based predictive control
- A web-based dashboard for live monitoring and profile management
- Advanced analytics and reporting

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.