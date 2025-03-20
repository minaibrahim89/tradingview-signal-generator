#!/bin/bash
# Add a small delay to ensure SCM container is fully initialized
sleep 5
echo "Starting application setup..."

# Run the debug script
echo "Running debug script..."
python azure-startup-debug.py

# Extract static files if archive exists
if [ -f "output.tar.gz" ]; then
  echo "Extracting static files..."
  mkdir -p static
  tar -xzf output.tar.gz -C static
  rm output.tar.gz
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Get the port from environment variables (Azure uses WEBSITES_PORT, PORT, or HTTP_PLATFORM_PORT)
PORT=${WEBSITES_PORT:-${PORT:-${HTTP_PLATFORM_PORT:-8000}}}
echo "Using port: $PORT"

# Create debug log for potential issues
echo "Environment variables:" > debug.log
env >> debug.log

# Start the application
echo "Starting application..."
echo "Binding to 0.0.0.0:$PORT"

# Start the application with proper port binding
gunicorn main:app --bind=0.0.0.0:$PORT --worker-class=uvicorn.workers.UvicornWorker --timeout 600 --workers 4 --log-level debug
