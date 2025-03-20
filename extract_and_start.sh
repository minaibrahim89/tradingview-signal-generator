#!/bin/bash
# Extract output.tar.gz and start the application

echo "Starting extraction process at $(date)"
echo "Current directory: $(pwd)"
echo "Directory contents before extraction:"
ls -la

# Extract output.tar.gz if it exists
if [ -f "output.tar.gz" ]; then
  echo "Found output.tar.gz - extracting contents"
  tar -xzf output.tar.gz
  
  # Remove the archive after extraction
  echo "Removing output.tar.gz"
  rm -f output.tar.gz
  
  # Make sure scripts are executable
  chmod +x *.sh
  
  echo "Directory contents after extraction:"
  ls -la
else
  echo "No output.tar.gz found - proceeding with startup"
fi

# Continue with normal startup
if [ -f "startup.sh" ]; then
  echo "Running startup.sh"
  bash startup.sh
else
  echo "startup.sh not found - starting app directly"
  
  # Make sure we have a static directory
  if [ ! -d "static" ]; then
    echo "Creating static directory"
    mkdir -p static
    echo '<html><body><h1>API Server Running</h1><p>Access the API at <a href="/docs">/docs</a></p></body></html>' > static/index.html
  fi
  
  # Install dependencies if requirements.txt exists
  if [ -f "requirements.txt" ]; then
    echo "Installing dependencies"
    pip install -r requirements.txt
  fi
  
  # Determine the port
  PORT=${WEBSITES_PORT:-${PORT:-${HTTP_PLATFORM_PORT:-8000}}}
  echo "Using port: $PORT"
  
  # Start the application directly
  python -m gunicorn main:app --bind=0.0.0.0:$PORT --workers=4 --worker-class=uvicorn.workers.UvicornWorker
fi 