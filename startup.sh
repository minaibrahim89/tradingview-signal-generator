#!/bin/bash

# Log startup
echo "Starting application at $(date)"
echo "Running as user: $(whoami)"
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"

# Run the debug script
echo "Running debug script..."
python azure-startup-debug.py

# Extract static files if archive exists
if [ -f "output.tar.gz" ]; then
  echo "Extracting static files..."
  mkdir -p static
  tar -xzf output.tar.gz -C static
  # Keep the archive in case we need to extract again
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Determine the port
PORT=${WEBSITES_PORT:-${PORT:-${HTTP_PLATFORM_PORT:-8000}}}
echo "Using port: $PORT"

# Create debug log for potential issues
echo "Environment variables:" > debug.log
env | grep -v "APPSETTING_\|SECRET_" >> debug.log

# Load environment variables
if [ -f .env ]; then
  echo "Loading environment variables from .env"
  set -o allexport
  source .env
  set +o allexport
fi

# Log readiness
echo "Preparing to start application on port $PORT..."
echo "Static directory content:"
ls -la static/ || echo "Static directory not found"

# Ensure entry point is executable
chmod +x main.py

# Ensure we can find favicon.ico
if [ -f "static/favicon.ico" ]; then
  echo "Favicon found in static directory"
else
  echo "Warning: Favicon not found in static directory"
fi

# Start the application
echo "Starting application..."
echo "Binding to 0.0.0.0:$PORT"

# Run with Gunicorn for production on Azure
exec gunicorn main:app \
  --bind=0.0.0.0:$PORT \
  --worker-class=uvicorn.workers.UvicornWorker \
  --timeout 600 \
  --workers 4 \
  --log-level info
