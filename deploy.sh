#!/bin/bash
# This script helps with Azure deployments to avoid SCM container restart issues

# Create marker file for Azure
echo "Creating marker file for Azure deployment"
touch deployment_complete.txt

# Debug information
echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la

# Ensure scripts are executable
chmod +x startup.sh

# Make sure files have correct line endings
find . -type f -name "*.sh" -exec dos2unix {} \;

# Use the deployment-specific web.config if available
if [ -f "web.config.deploy" ]; then
  echo "Using deployment-specific web.config"
  cp web.config.deploy web.config
fi

# Extract static files if archive exists
if [ -f "output.tar.gz" ]; then
  echo "Extracting static files during deployment..."
  
  # Remove any existing static directory to start clean
  rm -rf static
  
  # Create static directory
  mkdir -p static
  
  # Extract the archive
  tar -xzf output.tar.gz -C static
  echo "Static files extracted successfully"
  echo "Static directory contents:"
  ls -la static/
  
  # Create a verification file in the static directory
  echo "Static files were extracted at $(date)" > static/extraction_verified.txt
  
  # Remove the archive after extraction
  echo "Removing output.tar.gz after extraction"
  rm -f output.tar.gz
else
  echo "WARNING: output.tar.gz not found!"
  # Create a minimal static directory
  mkdir -p static
  echo "Created minimal static directory"
  
  # Create a simple placeholder
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
    <h2>Static files not found</h2>
    <p>The API server is running but the frontend static files were not found.</p>
    <p>You can access the API at:</p>
    <ul>
      <li><a href="/api/v1/webhooks/">/api/v1/webhooks/</a></li>
      <li><a href="/health">/health</a> (health check endpoint)</li>
      <li><a href="/docs">/docs</a> (API documentation)</li>
    </ul>
  </div>
  <p>Server time: <script>document.write(new Date().toISOString())</script></p>
</body>
</html>
EOL
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

# Ensure static directory is properly configured for FastAPI
echo "Checking if main.py mounts static directory..."
if grep -q "app.mount(\"/static\"" main.py; then
  echo "Static directory is mounted in main.py"
else
  echo "WARNING: Static directory might not be mounted in main.py"
fi

echo "Deployment script completed"
ls -la
exit 0 