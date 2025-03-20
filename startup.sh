#!/bin/bash
# Add a small delay to ensure SCM container is fully initialized
sleep 5
echo "Starting application setup..."

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Get the port from environment or default to 8000
PORT=${PORT:-8000}
echo "Using port: $PORT"

# Start the application
echo "Starting application..."
sleep 10
echo "Starting application after waiting for SCM initialization..."
gunicorn main:app --bind=0.0.0.0:8000 --worker-class=uvicorn.workers.UvicornWorker --timeout 600 --workers 4
