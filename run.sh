#!/bin/bash
# Quick start script for local development

echo "Starting SecAPI development server..."
echo "API will be available at http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Installing dependencies..."
    ./venv/bin/pip install -r requirements-dev.txt
fi

# Start server
./venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
