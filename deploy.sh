#!/bin/bash
# This script helps with Azure deployments to avoid SCM container restart issues

# Create marker file for Azure
echo "Creating marker file for Azure deployment"
touch deployment_complete.txt

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
  mkdir -p static
  tar -xzf output.tar.gz -C static
  echo "Static files extracted successfully"
  # Don't remove the archive - we'll keep it for the startup script as a backup
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

echo "Deployment script completed"
exit 0 