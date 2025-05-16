#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Starting setup for Cyberscape: Digital Dread..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null
then
    echo "Error: python3 could not be found. Please install Python 3."
    exit 1
fi

echo "Python 3 found."

# Create a virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment '.venv'..."
    python3 -m venv .venv
    echo "Virtual environment created."
else
    echo "Virtual environment '.venv' already exists."
fi

# Activate the virtual environment (for the current script)
# This is not strictly necessary for the install command below,
# but good practice if the script were to do more within the venv.
# source .venv/bin/activate # Uncomment if you need to activate within the script

echo "Installing dependencies from requirements.txt..."
# Install dependencies using the python executable from the virtual environment
.venv/bin/pip install -r requirements.txt

echo "Dependencies installed."

echo "Setup complete."

# Note: To use the virtual environment in your terminal, run:
# source .venv/bin/activate