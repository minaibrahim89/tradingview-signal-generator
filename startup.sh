#!/bin/bash
# Simple startup script for Azure Web App

# Run cleanup script first if it exists
if [ -f "cleanup.sh" ]; then
  echo "Running cleanup script..."
  chmod +x cleanup.sh
  ./cleanup.sh
fi

# Backup check for any tar.gz files
if [ -f "output.tar.gz" ]; then
  echo "Found output.tar.gz - removing it"
  rm -f output.tar.gz
fi
find . -name "*.tar.gz" -delete 2>/dev/null

# Ensure static directory exists
if [ ! -d "static" ]; then
  echo "Creating static directory"
  mkdir -p static
  echo '<html><body><h1>API Server Running</h1><p>Access the API at <a href="/docs">/docs</a></p></body></html>' > static/index.html
fi

# Install dependencies if needed
if [ ! -d "venv" ] && [ -f "requirements.txt" ]; then
  echo "Installing dependencies..."
  pip install -r requirements.txt
fi

# Determine the port
PORT=${WEBSITES_PORT:-${PORT:-${HTTP_PLATFORM_PORT:-8000}}}
echo "Starting application on port $PORT"

# Start the application
exec gunicorn main:app \
  --bind=0.0.0.0:$PORT \
  --worker-class=uvicorn.workers.UvicornWorker \
  --workers=4 \
  --timeout=600 \
  --log-level=info
