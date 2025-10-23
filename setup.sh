#!/bin/bash
# Setup script for PFAL Controller on Raspberry Pi

echo "=========================================="
echo "PFAL Controller Setup"
echo "=========================================="
echo ""

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "Warning: This script is designed for Raspberry Pi."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "Updating system packages..."
sudo apt-get update

# Install Python3 and pip if not already installed
echo "Installing Python3 and pip..."
sudo apt-get install -y python3 python3-pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Create configuration file
if [ ! -f .env ]; then
    echo "Creating configuration file..."
    cp config/config.example.env .env
    echo "Configuration file created at .env"
    echo "Please edit .env with your MQTT and InfluxDB settings."
else
    echo "Configuration file .env already exists."
fi

# Create log directory
echo "Creating log directory..."
sudo mkdir -p /var/log
sudo touch /var/log/pfal_controller.log
sudo chmod 666 /var/log/pfal_controller.log

# Make main.py executable
chmod +x main.py

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env with your configuration"
echo "2. Ensure MQTT broker is running"
echo "3. Ensure InfluxDB is running and configured"
echo "4. Run the controller: python3 main.py"
echo ""
echo "To install as a systemd service:"
echo "sudo cp config/pfal-controller.service /etc/systemd/system/"
echo "sudo systemctl enable pfal-controller"
echo "sudo systemctl start pfal-controller"
echo ""
