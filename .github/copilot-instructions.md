<!--
Guidance for AI coding agents working on the PFAL Management System.
Focus: be immediately productive — understand architecture, key files, config, and common code patterns.
-->

# PFAL Management — Copilot / AI Agent Instructions

Brief, actionable notes to help an AI contributor make useful changes quickly.

- Big picture
  - This repository implements a rule-based Raspberry Pi controller for PFAL (plant factory) automation.
  - Data flow: ESP32 sensors -> MQTT topics -> `src/pfal_controller/mqtt_client.py` -> `PFALController` -> rules (`rule_controller.py`) -> actuator commands published back to MQTT. Sensor data is persisted to InfluxDB via `influxdb_persistence.py`.

- Key files to read first
  - `README.md` — project goals, MQTT topics, and example messages.
  - `src/pfal_controller/config.py` — environment-driven configuration. Uses `python-dotenv` and dataclasses; prefer using existing env var names when adding new settings.
  - `src/pfal_controller/mqtt_client.py` — MQTT subscription/dispatch and `publish_command()` mapping for actuator names to topics.
  - `src/pfal_controller/rule_controller.py` — all IF-THEN control logic and the expected command dict shape (keys: `action`, `command`, optional `duration_ms`, `reason`).
  - `src/pfal_controller/influxdb_persistence.py` — examples of writing measurements and tags; follow established measurement names (`ph`, `ec`, `temperature`, `bme280`).
  - `src/pfal_controller/controller.py` — orchestration: how components are wired, callback signatures, periodic schedule check, and logging setup.

- Conventions & patterns (project-specific)
  - Configuration is read from environment variables via `load_config(env_file)` in `config.py`; when adding new config, add defaults using `os.getenv` and extend dataclasses.
  - Sensor callbacks: `MQTTClient.register_sensor_callback(sensor_type, callback)` expects callbacks with signature `(sensor_type, data_dict)` and `data` usually contains `value` and `sensor_id`.
  - Command dictionaries returned by rule evaluation must include an `action` that maps to one of: `ph_pump`, `nutrient_pump`, `main_pump`, `lights`, `fans` and a `command` string (`'ON'`/`'OFF'`). Timed actions include `duration_ms`.
  - InfluxDB measurements and tags: use measurement names and `sensor_id` tag as in `influxdb_persistence.py` for consistency in historical data.
  - Avoid redundant actuator publishes: `controller.py` tracks `last_light_state` and `last_fan_state` — preserve this pattern when adding stateful actuators.

- Integration points & external dependencies
  - MQTT broker (defaults: `localhost:1883`). See `MQTT_*` env vars in `config.py`.
  - InfluxDB 2.x client. `INFLUXDB_URL`, `INFLUXDB_TOKEN`, `INFLUXDB_ORG`, `INFLUXDB_BUCKET` are used. Use the provided write helper methods when recording sensor data.
  - Systemd service: `config/pfal-controller.service` (example) and `main.py` are entry points for deployment.

- Developer workflows & useful commands
  - Install deps: `pip install -r requirements.txt` (project uses `python-dotenv`, `paho-mqtt`, `influxdb-client` per `requirements.txt`).
  - Run locally: `python main.py` or `python main.py --config /path/to/.env`.
  - Logs: runtime file configured at `/var/log/pfal_controller.log` in `controller.setup_logging()`; when running locally as non-root, adjust or override logging handler to write to a local file.

- Testing & quick sanity checks (manual)
  - Simulate sensor messages using `examples/esp32_sensor_simulator.py` — it publishes sensor JSON to the MQTT topics defined in the README/config.
  - Unit-style test approach: small scripts that instantiate `RuleBasedController` with a `ControlConfig` and call `update_sensor_reading()` and `evaluate_all_rules()` to assert expected command dictionaries.

- When editing code, prefer these low-risk patterns
  - Keep the command dict shape stable. Many components rely on keys: `action`, `command`, `duration_ms`, `reason`.
  - Update `config.py` first when adding new env-configurable behavior; add sensible defaults and document new env vars in `config/config.example.env` and `README.md`.
  - Use existing helper methods for persistence (`InfluxDBPersistence.write_*`) rather than writing raw points in multiple places.

- Examples to copy/paste
  - Publish a 1s pH pump command: payload produced by `MQTTClient.publish_command('ph_pump', 'ON', duration_ms=1000)` — topic is `pfal/actuators/ph_pump` by default.
  - Sensor JSON example: `{'value': 6.5, 'sensor_id': 'esp32_1'}` — see `README.md` and `mqtt_client.py` parsing.

- Safety notes for agents
  - Don't hardcode credentials or tokens. New secrets must be added as env vars and documented in `config.example.env`.
  - Avoid changing topic names unless also updating `config.py` defaults, README, and `examples/esp32_sensor_simulator.py`.

If anything is unclear or you want the file tuned for a specific agent workflow (tests-first, example PRs, or stricter rules), tell me which area to expand and I'll iterate.
