#!/bin/bash
# Custom startup script for Azure App Service
# This file is typically located at /home/site/scripts/startup.sh in Azure

echo "Azure App Service startup script started at $(date)"

# Change to the wwwroot directory
cd /home/site/wwwroot || exit 1

# Check if main startup script exists and run it
if [ -f "startup.sh" ]; then
  echo "Found startup.sh, executing it..."
  chmod +x startup.sh
  ./startup.sh
else
  echo "No startup.sh found, setting up environment..."
  
  # Set up Python virtual environment if it doesn't exist
  if [ ! -d "antenv" ]; then
    echo "Creating Python virtual environment..."
    python -m venv antenv
  fi
  
  # Activate virtual environment and install dependencies
  source antenv/bin/activate
  pip install -r requirements.txt
  
  # Ensure static directory exists
  if [ ! -d "static" ]; then
    mkdir -p static
    echo '<html><body><h1>API Server Running</h1></body></html>' > static/index.html
  fi
  
  # Determine port to run on
  PORT=${PORT:-8000}
  echo "Starting application on port $PORT"
  
  # Start the application
  gunicorn --bind=0.0.0.0:$PORT --timeout 600 --access-logfile '-' main:app
fi 