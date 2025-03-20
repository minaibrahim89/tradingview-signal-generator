#!/bin/bash

# Log startup
echo "Starting application at $(date)"
echo "Running as user: $(whoami)"
echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la

# Extract static files if archive exists
if [ -f "output.tar.gz" ]; then
  echo "Extracting static files..."
  mkdir -p static
  tar -xzf output.tar.gz -C static
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create touchfile for Azure App Service
touch /home/site/wwwroot/startup_complete.txt
touch /tmp/startup_complete.txt

# Determine the port
PORT=${WEBSITES_PORT:-${PORT:-${HTTP_PLATFORM_PORT:-8000}}}
echo "Using port: $PORT"

# Create debug log for potential issues
echo "Environment variables:" > azure-debug.log
env | grep -v "APPSETTING_\|SECRET_" >> azure-debug.log

# Check if static directory exists
if [ -d "static" ]; then
  echo "Static directory exists with contents:"
  ls -la static/
else
  echo "Static directory does not exist, creating it"
  mkdir -p static
fi

# Check for web.config file
if [ -f "web.config" ]; then
  echo "web.config exists"
  cat web.config >> azure-debug.log
else
  echo "web.config MISSING!"
fi

# If web.config.deploy exists, use it
if [ -f "web.config.deploy" ]; then
  echo "Using web.config.deploy"
  cp web.config.deploy web.config
  cat web.config >> azure-debug.log
fi

# Run Gunicorn for production on Azure
echo "Starting Gunicorn on 0.0.0.0:$PORT"

# Use this explicit command for Azure compatibility
exec gunicorn \
  --bind=0.0.0.0:$PORT \
  --worker-class=uvicorn.workers.UvicornWorker \
  --workers=4 \
  --timeout=600 \
  --log-level=info \
  --capture-output \
  --access-logfile=- \
  --error-logfile=- \
  main:app
