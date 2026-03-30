#!/bin/bash
################################################################################
# MOTORCTL - PI DEPLOYMENT SETUP & TEST RUNNER
#
# This script automates the environment setup on the Raspberry Pi and executes
# the deployment test suite. Use this to verify hardware readiness before
# starting the full multi-node stack.
#
# Usage: 
#   chmod +x test_setup.sh
#   ./test_setup.sh
################################################################################

echo "--- Starting Motorctl Deployment Test ---"

# Move to the script's directory to ensure paths are relative to motorctl
cd "$(dirname "$0")"

# 1. Environment Configuration: Create a .env file if one doesn't exist.
if [ ! -f .env ]; then
    echo "Creating default .env file..."
    cat > .env <<EOF
MOONRAKER_URL=http://localhost:7125
NODE_ID=motor-node-pi
SERVER_URL=http://localhost:5000
EOF
fi

# 2. Virtual Environment Setup: Create and activate venv to avoid externally managed error.
VENV_DIR="./.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "Installing/Updating dependencies..."
python3 -m pip install --upgrade pip > /dev/null
python3 -m pip install -r ../requirements.txt pytest pytest-asyncio httpx python-dotenv > /dev/null

# 3. Run Test Suite: Export the src directory to Python path and execute pytest.
export PYTHONPATH=$PYTHONPATH:$(pwd)/src:$(pwd)

echo "Running Python test suite..."
pytest tests/test_deploy.py -v -s

if [ $? -eq 0 ]; then
    echo "--- ALL TESTS PASSED: Subsystem ready for backend integration ---"
else
    echo "--- TESTS FAILED: Check hardware connection and logs ---"
    exit 1
fi