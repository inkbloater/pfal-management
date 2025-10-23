#!/usr/bin/env python3
"""
PFAL Controller - Main entry point for Raspberry Pi PFAL automation.

This script provides rule-based control for a Plant Factory with Artificial Lighting (PFAL).
It subscribes to MQTT topics from ESP32 sensor nodes and publishes commands to actuators
based on simple IF-THEN rules. All sensor data is persisted to InfluxDB 2.

Usage:
    python main.py [--config CONFIG_FILE]
    
Environment variables can be set in a .env file or in the system environment.
See config/config.example.env for configuration options.
"""

import sys
import os
import argparse

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pfal_controller import main


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PFAL Controller - Rule-based automation')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    args = parser.parse_args()
    
    # Set config file if provided
    if args.config:
        os.environ['CONFIG_FILE'] = args.config
    
    main()
