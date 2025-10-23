# PFAL Management System

Manages the automation of PFAL (Plant Factory with Artificial Lighting). This system provides rule-based control for monitoring and automating environmental conditions in a plant factory.

## Phase 1: Rule-Based Controller

The current implementation provides a Raspberry Pi-based controller that:

- **Subscribes to MQTT topics** from ESP32 sensor nodes for:
  - pH sensors
  - EC (Electrical Conductivity) sensors
  - Temperature sensors
  - BME280 environmental sensors (temperature, humidity, pressure)

- **Implements IF-THEN control logic** for:
  - pH adjustment via peristaltic pump
  - Nutrient dosing via peristaltic pump
  - Temperature control via fans
  - Lighting control based on schedule

- **Persists sensor data** to InfluxDB 2 for historical analysis and monitoring

- **Publishes MQTT commands** to control actuators:
  - Peristaltic pumps (pH and nutrient dosing)
  - Main water pump
  - Grow lights
  - Ventilation fans

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

```bash
pip install -r requirements.txt
```

### Configuration

1. Copy the example configuration file:
```bash
cp config/config.example.env .env
```

2. Edit `.env` with your settings:
   - MQTT broker address and credentials
   - InfluxDB URL and authentication token
   - Control thresholds (pH, EC, temperature)
   - Lighting schedule
   - Pump durations

## Usage

### Run the Controller

```bash
python main.py
```

Or with a custom configuration file:

```bash
python main.py --config /path/to/config.env
```

### Run as a Service (systemd)

Create a systemd service file at `/etc/systemd/system/pfal-controller.service`:

```ini
[Unit]
Description=PFAL Controller
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/pfal-management
ExecStart=/usr/bin/python3 /home/pi/pfal-management/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable pfal-controller
sudo systemctl start pfal-controller
sudo systemctl status pfal-controller
```

## Control Rules

### pH Control
- **IF** pH < (target - tolerance) **THEN** activate pH up pump for configured duration
- **IF** pH > (target + tolerance) **THEN** log warning (pH down control can be added)

### EC (Nutrient) Control
- **IF** EC < (target - tolerance) **THEN** activate nutrient pump for configured duration

### Temperature Control
- **IF** temperature > max threshold **THEN** turn fans ON
- **IF** temperature < (max - 2°C) **THEN** turn fans OFF (with hysteresis)

### Lighting Control
- **IF** current hour is within schedule **THEN** lights ON
- **ELSE** lights OFF

## MQTT Topics

### Sensor Topics (Subscribed)
- `pfal/sensors/ph` - pH sensor readings
- `pfal/sensors/ec` - EC sensor readings
- `pfal/sensors/temperature` - Temperature readings
- `pfal/sensors/bme280` - BME280 sensor data (temp, humidity, pressure)

### Actuator Topics (Published)
- `pfal/actuators/ph_pump` - pH adjustment pump commands
- `pfal/actuators/nutrient_pump` - Nutrient dosing pump commands
- `pfal/actuators/main_pump` - Main water pump commands
- `pfal/actuators/lights` - Grow light commands
- `pfal/actuators/fans` - Ventilation fan commands

### Message Format

Sensor messages (JSON):
```json
{
  "value": 6.5,
  "sensor_id": "esp32_1"
}
```

BME280 sensor message (JSON):
```json
{
  "temperature": 24.5,
  "humidity": 65.0,
  "pressure": 1013.25,
  "sensor_id": "esp32_1"
}
```

Actuator command message (JSON):
```json
{
  "command": "ON",
  "duration_ms": 1000
}
```

## InfluxDB Data Structure

All sensor readings are stored in InfluxDB with the following structure:

**Measurements:**
- `ph` - pH readings
- `ec` - EC readings
- `temperature` - Temperature readings
- `bme280` - BME280 sensor readings

**Tags:**
- `sensor_id` - Identifier for the sensor

**Fields:**
- `value` - Sensor reading value
- For BME280: `temperature`, `humidity`, `pressure`

## Project Structure

```
pfal-management/
├── src/
│   └── pfal_controller/
│       ├── __init__.py
│       ├── config.py              # Configuration management
│       ├── controller.py          # Main controller orchestration
│       ├── influxdb_persistence.py # InfluxDB data persistence
│       ├── mqtt_client.py         # MQTT communication
│       └── rule_controller.py     # Rule-based control logic
├── config/
│   └── config.example.env         # Example configuration file
├── main.py                        # Main entry point
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Future Enhancements

Phase 2 and beyond will include:
- Machine learning-based predictive control
- Supply chain management
- Logistics tracking
- Accounting integration
- Web-based monitoring dashboard
- Mobile app integration
- Advanced analytics and reporting

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
