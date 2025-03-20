#!/bin/bash
# Simple cleanup script for Azure Web App

echo "=== Azure Deployment Cleanup ==="
echo "Running at $(date)"
echo "Current directory: $(pwd)"

# Critical - Find and remove output.tar.gz in wwwroot
if [ -f "output.tar.gz" ]; then
  echo "FOUND output.tar.gz - removing it"
  rm -f output.tar.gz
else
  echo "No output.tar.gz found in current directory"
fi

# Also check explicitly in /home/site/wwwroot
if [ -d "/home/site/wwwroot" ] && [ -f "/home/site/wwwroot/output.tar.gz" ]; then
  echo "FOUND output.tar.gz in /home/site/wwwroot - removing it"
  rm -f /home/site/wwwroot/output.tar.gz
fi

# Remove any tar.gz files in current directory and subdirectories
find . -name "*.tar.gz" -delete 2>/dev/null

echo "Cleanup completed at $(date)"
echo "===========================" 