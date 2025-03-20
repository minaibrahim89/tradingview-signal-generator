#!/bin/bash

# Log startup
echo "Starting application at $(date)"
echo "Running as user: $(whoami)"
echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la

# Log static directory information
echo "Checking static directory:"
if [ -d "static" ]; then
  echo "Static directory exists and contains:"
  ls -la static/
  
  # Check deployment verification file
  if [ -f "static/direct_deployment.txt" ]; then
    echo "Static files were deployed directly via GitHub Actions"
    cat static/direct_deployment.txt
  else
    echo "No direct deployment verification found"
  fi
else
  echo "WARNING: Static directory is missing, creating it now"
  mkdir -p static
  echo "Created static directory"
  
  # Create a simple placeholder index.html
  cat > static/index.html << 'EOL'
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>App Status - Emergency Recovery</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
    h1 { color: #333; }
    .card { border: 1px solid #ddd; padding: 20px; border-radius: 5px; margin-bottom: 20px; background-color: #f8f9fa; }
    .warning { color: #856404; background-color: #fff3cd; border-color: #ffeeba; }
  </style>
</head>
<body>
  <h1>Application Status</h1>
  <div class="card warning">
    <h2>Warning: Static Directory Missing</h2>
    <p>The static directory was missing and has been created during startup.</p>
    <p>This is an emergency recovery page.</p>
  </div>
  <div class="card">
    <h2>API Server is running</h2>
    <p>The backend API server is operational.</p>
    <p>Try accessing the API directly at <a href="/api/v1/webhooks/">/api/v1/webhooks/</a></p>
    <p>For API documentation, visit <a href="/docs">/docs</a></p>
    <p>For application health status, check <a href="/health">/health</a></p>
  </div>
  <p>Server time: <script>document.write(new Date().toISOString())</script></p>
  <p>Server started at: <script>document.write(new Date().toLocaleString())</script></p>
</body>
</html>
EOL
  echo "Created emergency placeholder index.html"
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

# Create debug log
echo "Environment variables:" > azure-debug.log
env | grep -v "APPSETTING_\|SECRET_" >> azure-debug.log

# Check for web.config file
if [ -f "web.config" ]; then
  echo "web.config exists"
  cat web.config >> azure-debug.log
else
  echo "web.config MISSING!"
fi

# Check main.py file exists
if [ ! -f "main.py" ]; then
  echo "CRITICAL ERROR: main.py is missing!"
  exit 1
fi

# Log system information
echo "Python version: $(python --version)"
echo "System: $(uname -a)"
echo "Memory: $(free -h || echo 'free command not available')"
echo "Disk space: $(df -h . || echo 'df command not available')"

# Create a startup verification file
echo "Application started at $(date)" > startup_verification.txt
echo "Running as: $(whoami)" >> startup_verification.txt
echo "In directory: $(pwd)" >> startup_verification.txt

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
