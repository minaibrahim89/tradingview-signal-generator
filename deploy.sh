#!/bin/bash
# Simple deployment script for Azure

# Check for and remove any tar.gz files in wwwroot
echo "Checking for tar.gz files..."
find . -name "*.tar.gz" -delete

echo "Deployment started at $(date)"

# Ensure scripts are executable 
chmod +x *.sh

# Ensure static directory exists
if [ ! -d "static" ]; then
  echo "Creating static directory"
  mkdir -p static
  echo '<html><body><h1>API Server Running</h1><p>Access the API at <a href="/docs">/docs</a></p></body></html>' > static/index.html
fi

# Install dependencies
echo "Installing dependencies"
pip install -r requirements.txt

echo "Deployment completed at $(date)"

# Create marker file for Azure
echo "Creating marker file for Azure deployment"
touch deployment_complete.txt

# Debug information
echo "Directory contents:"
ls -la

# Use the deployment-specific web.config if available
if [ -f "web.config.deploy" ]; then
  echo "Using deployment-specific web.config"
  cp web.config.deploy web.config
fi

# Verify static directory
echo "Checking static directory..."
if [ -d "static" ]; then
  echo "Static directory exists with contents:"
  ls -la static/
  
  # Create a verification file
  echo "Static files verified during deployment at $(date)" > static/deployment_verified.txt
  
  # Make sure index.html exists
  if [ ! -f "static/index.html" ]; then
    echo "WARNING: index.html missing, creating placeholder"
    cat > static/index.html << 'EOL'
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>API Server</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
    h1 { color: #333; }
    .card { border: 1px solid #ddd; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
  </style>
</head>
<body>
  <h1>API Server Running</h1>
  <div class="card">
    <h2>Placeholder Page</h2>
    <p>This is a placeholder page created by deploy.sh script.</p>
    <p>You can access the API at:</p>
    <ul>
      <li><a href="/api/v1/webhooks/">/api/v1/webhooks/</a></li>
      <li><a href="/health">/health</a> (health check endpoint)</li>
      <li><a href="/docs">/docs</a> (API documentation)</li>
    </ul>
  </div>
  <p>Deployment time: <script>document.write(new Date('$(date -u +"%Y-%m-%dT%H:%M:%SZ")').toLocaleString())</script></p>
</body>
</html>
EOL
  fi
else
  echo "ERROR: Static directory is missing! Creating it now."
  mkdir -p static
  
  # Create a simple placeholder index.html for emergency
  cat > static/index.html << 'EOL'
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Emergency Static Page</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
    h1 { color: #333; }
    .card { border: 1px solid #ddd; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
    .error { background-color: #f8d7da; border-color: #f5c6cb; color: #721c24; }
  </style>
</head>
<body>
  <h1>API Server Running - Emergency Page</h1>
  <div class="card error">
    <h2>Static Directory Missing</h2>
    <p>The deploy.sh script had to create an emergency static directory!</p>
    <p>This indicates a problem with the deployment process.</p>
  </div>
  <div class="card">
    <p>You can access the API at:</p>
    <ul>
      <li><a href="/api/v1/webhooks/">/api/v1/webhooks/</a></li>
      <li><a href="/health">/health</a> (health check endpoint)</li>
      <li><a href="/docs">/docs</a> (API documentation)</li>
    </ul>
  </div>
  <p>Emergency page created at: <script>document.write(new Date('$(date -u +"%Y-%m-%dT%H:%M:%SZ")').toLocaleString())</script></p>
</body>
</html>
EOL

  echo "Created emergency index.html"
  echo "Emergency static directory created during deployment at $(date)" > static/emergency_creation.txt
fi

# Create simple test app for diagnostics
echo "Creating diagnostic test app..."
cat > app_test.py << 'EOL'
from fastapi import FastAPI
import uvicorn
import os
import platform
import sys

app = FastAPI()

@app.get("/")
async def root():
    return {
        "message": "Application is running!",
        "status": "active",
        "python_version": sys.version,
        "platform": platform.platform(),
        "directory": os.getcwd(),
        "files": os.listdir(".")
    }

@app.get("/test")
async def test():
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
EOL

# Create .env file with debug setting
echo "Creating .env file with debug settings..."
echo "DEBUG=True" > .env
echo "CORS_ORIGIN=*" >> .env

# Create a startup_command.txt file
echo "Creating startup command file..."
echo "gunicorn main:app --bind=0.0.0.0:\$PORT --worker-class=uvicorn.workers.UvicornWorker --timeout 600 --workers 4" > startup_command.txt

# Create a deployment verification file
echo "Deployment completed at $(date)" > deployment_verification.txt
echo "Files deployed:" >> deployment_verification.txt
ls -la >> deployment_verification.txt

# Final check for any tar.gz files
echo "Final check for any tar.gz files:"
find . -name "*.tar.gz" > /tmp/final_check.txt
if [ -s /tmp/final_check.txt ]; then
  echo "!!! WARNING: Still found tar.gz files after deployment:"
  cat /tmp/final_check.txt
  echo "Attempting final removal of all tar.gz files..."
  find . -name "*.tar.gz" -delete
  echo "Removed all tar.gz files"
else
  echo "✓ No tar.gz files found in final check"
fi

echo "Deployment script completed"
ls -la
exit 0 