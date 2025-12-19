#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "Deploying Spike AI Backend..."

# Create virtual environment at repo root
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Ensure credentials.json exists
if [ ! -f "credentials.json" ]; then
    echo "ERROR: credentials.json not found at project root."
    echo "GA4 authentication cannot proceed."
    exit 1
fi

# Explicitly point Google SDK to credentials.json
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/credentials.json"

echo "Starting FastAPI server on port 8080..."
nohup uvicorn main:app --host 0.0.0.0 --port 8080 > server.log 2>&1 &

echo "Deployment complete."
