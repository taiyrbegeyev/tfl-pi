#!/bin/bash
# Setup script for TfL Pi

set -e

echo "======================================"
echo "TfL Pi Setup Script"
echo "======================================"
echo ""

# Check if running on Raspberry Pi
if [ -f /proc/device-tree/model ]; then
    MODEL=$(cat /proc/device-tree/model)
    echo "Detected device: $MODEL"
else
    echo "Warning: Not running on Raspberry Pi. Some features may not work."
fi

echo ""
echo "Step 1: Updating system packages..."
sudo apt-get update

echo ""
echo "Step 2: Installing system dependencies..."
sudo apt-get install -y python3-pip python3-venv python3-pil python3-numpy swig

echo ""
echo "Step 3: Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created"
else
    echo "Virtual environment already exists"
fi

echo ""
echo "Step 4: Installing Python dependencies in virtual environment..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Step 5: Downloading Waveshare e-Paper driver..."
if [ ! -d "waveshare_epd" ]; then
    echo "Cloning Waveshare e-Paper library..."
    git clone https://github.com/waveshare/e-Paper.git ./e-Paper-temp
    cp -r ./e-Paper-temp/RaspberryPi_JetsonNano/python/lib/waveshare_epd ./
    rm -rf ./e-Paper-temp
    echo "Driver installed successfully"
else
    echo "Driver already exists, skipping..."
fi

echo ""
echo "Step 6: Configuring SPI interface..."
if ! grep -q "^dtparam=spi=on" /boot/config.txt; then
    echo "Enabling SPI..."
    sudo raspi-config nonint do_spi 0
    echo "SPI enabled. You may need to reboot."
else
    echo "SPI already enabled"
fi

echo ""
echo "Step 7: Creating configuration file..."
if [ ! -f "config.json" ]; then
    cp config.example.json config.json
    echo "config.json created. Please edit it with your API keys and stop IDs:"
    echo "  nano config.json"
else
    echo "config.json already exists"
fi

echo ""
echo "Step 8: Generating systemd service file..."
CURRENT_USER=$(whoami)
INSTALL_DIR=$(pwd)

# Generate service file from template
sed -e "s|__USER__|${CURRENT_USER}|g" \
    -e "s|__INSTALL_DIR__|${INSTALL_DIR}|g" \
    tfl-display.service.template > tfl-display.service

echo "Service file generated for user: ${CURRENT_USER}"
echo "Install directory: ${INSTALL_DIR}"

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Edit config.json with your TfL API key and stop IDs:"
echo "   nano config.json"
echo ""
echo "2. Get your TfL API key from: https://api.tfl.gov.uk/"
echo ""
echo "3. Test the application:"
echo "   source venv/bin/activate"
echo "   python3 main.py"
echo ""
echo "To install as a system service:"
echo "   sudo cp tfl-display.service /etc/systemd/system/"
echo "   sudo systemctl enable tfl-display.service"
echo "   sudo systemctl start tfl-display.service"
echo ""
echo "To view logs:"
echo "   sudo journalctl -u tfl-display.service -f"
echo ""
echo "NOTE: The systemd service will use the virtual environment automatically."
echo ""
