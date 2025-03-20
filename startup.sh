#!/bin/bash

# Log startup
echo "Starting application at $(date)"
echo "Running as user: $(whoami)"
echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la

# Check if we have a deployment marker
if [ -f "deployment_complete.txt" ]; then
  echo "Deployment marker found, deployment script ran successfully"
else
  echo "WARNING: Deployment marker not found, deployment script might not have run!"
fi

# Check for any issues with output.tar.gz
if [ -f "output.tar.gz" ]; then
  echo "WARNING: output.tar.gz found in root directory - deploy.sh didn't run properly"
  echo "Attempting emergency extraction of static files..."
  rm -rf static
  mkdir -p static
  tar -xzf output.tar.gz -C static
  rm -f output.tar.gz
  echo "Emergency extraction completed"
fi

# Check if static directory exists and has content
if [ -d "static" ]; then
  echo "Static directory exists:"
  ls -la static/
  
  # Check if index.html exists
  if [ -f "static/index.html" ]; then
    echo "static/index.html found"
  else
    echo "WARNING: static/index.html not found, creating a placeholder"
    cat > static/index.html << 'EOL'
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>App Status</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
    h1 { color: #333; }
    .card { border: 1px solid #ddd; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
  </style>
</head>
<body>
  <h1>Application Status</h1>
  <div class="card">
    <h2>Server is running!</h2>
    <p>This is a placeholder page generated during startup.</p>
    <p>Try accessing the API directly at <a href="/api/v1/webhooks/">/api/v1/webhooks/</a></p>
    <p>For API documentation, visit <a href="/docs">/docs</a></p>
    <p>For application health status, check <a href="/health">/health</a></p>
  </div>
  <p>Server time: <script>document.write(new Date().toISOString())</script></p>
</body>
</html>
EOL
  fi
else
  echo "Static directory does not exist, creating it"
  mkdir -p static
  
  # Create a simple placeholder index.html
  cat > static/index.html << 'EOL'
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>App Status - Static Directory Missing</title>
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
    <p>This may indicate a deployment issue with the frontend files.</p>
  </div>
  <div class="card">
    <h2>API Server is running</h2>
    <p>The backend API server is operational.</p>
    <p>Try accessing the API directly at <a href="/api/v1/webhooks/">/api/v1/webhooks/</a></p>
    <p>For API documentation, visit <a href="/docs">/docs</a></p>
    <p>For application health status, check <a href="/health">/health</a></p>
  </div>
  <p>Server time: <script>document.write(new Date().toISOString())</script></p>
  <p>Server started at: <script>document.write(new Date('$(date -u +"%Y-%m-%dT%H:%M:%SZ")').toLocaleString())</script></p>
</body>
</html>
EOL
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
