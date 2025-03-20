#!/bin/bash
# This script helps with Azure deployments to avoid SCM container restart issues

# Ensure the script is executable
chmod +x startup.sh

# Make sure files have correct line endings
find . -type f -name "*.sh" -exec dos2unix {} \;

# Extract static files if archive exists
if [ -f "output.tar.gz" ]; then
  echo "Extracting static files..."
  mkdir -p static
  tar -xzf output.tar.gz -C static
  rm output.tar.gz
fi

echo "Deployment script completed"
exit 0 