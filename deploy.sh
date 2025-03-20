#!/bin/bash
# This script helps with Azure deployments to avoid SCM container restart issues

# Ensure the script is executable
chmod +x startup.sh

# Make sure files have correct line endings
find . -type f -name "*.sh" -exec dos2unix {} \;

# Extract static files if archive exists
if [ -f "output.tar.gz" ]; then
  echo "Extracting static files during deployment..."
  mkdir -p static
  tar -xzf output.tar.gz -C static
  echo "Static files extracted successfully"
  # Don't remove the archive - we'll keep it for the startup script as a backup
fi

# Create .env file with debug setting
echo "Creating .env file with debug settings..."
echo "DEBUG=True" > .env

echo "Deployment script completed"
exit 0 