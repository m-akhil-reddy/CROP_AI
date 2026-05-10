#!/bin/bash
echo "============================================================"
echo " AI-Based Crop Damage Assessment - Setup Script (Linux/Mac)"
echo "============================================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 is not installed."
    echo "Install with: sudo apt install python3 python3-venv python3-pip"
    exit 1
fi

# Create virtual environment
echo "[1/4] Creating Python virtual environment..."
cd "$(dirname "$0")/backend"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "       Virtual environment created."
else
    echo "       Virtual environment already exists."
fi

# Activate and install
echo "[2/4] Installing Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt --quiet

cd "$(dirname "$0")"

echo "[3/4] Setup complete!"
echo ""
echo "============================================================"
echo " To start the server, run:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python app.py"
echo "============================================================"
echo ""

# Start server
echo "[4/4] Starting Flask server..."
cd "$(dirname "$0")/backend"
source venv/bin/activate
python app.py
