#!/bin/bash
# This script helps with Azure deployments to avoid SCM container restart issues

# Ensure the script is executable
chmod +x startup.sh

# Make sure files have correct line endings
find . -type f -name "*.sh" -exec dos2unix {} \;

echo "Deployment script completed"
exit 0 