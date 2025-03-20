#!/bin/bash

# Check for output.tar.gz and remove it if found
if [ -f "output.tar.gz" ]; then
  echo "Found output.tar.gz - removing it"
  rm -f output.tar.gz
fi

# Remove any tar.gz files
find . -name "*.tar.gz" -delete 2>/dev/null

# Normal startup continues
echo "Starting application at $(date)"
echo "Current directory: $(pwd)"

# Check static directory
if [ ! -d "static" ]; then
  echo "Static directory missing, creating it"
  mkdir -p static
  echo '<html><body><h1>App is running</h1></body></html>' > static/index.html
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Determine the port
PORT=${WEBSITES_PORT:-${PORT:-${HTTP_PLATFORM_PORT:-8000}}}
echo "Using port: $PORT"

# Run Gunicorn for production on Azure
echo "Starting Gunicorn on 0.0.0.0:$PORT"
exec gunicorn \
  --bind=0.0.0.0:$PORT \
  --worker-class=uvicorn.workers.UvicornWorker \
  --workers=4 \
  --timeout=600 \
  --log-level=info \
  main:app
