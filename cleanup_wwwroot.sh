#!/bin/bash
# This script is specifically designed to clean up output.tar.gz from the wwwroot directory on Azure

echo "========== CRITICAL WWWROOT CLEANUP SCRIPT =========="
echo "Current directory: $(pwd)"
echo "Running as user: $(whoami)"
echo "Date/time: $(date)"

# Force remove output.tar.gz in various locations
echo "Checking for output.tar.gz in current directory..."
if [ -f "output.tar.gz" ]; then
  echo "FOUND output.tar.gz in current directory - removing it"
  rm -f output.tar.gz
else
  echo "No output.tar.gz found in current directory"
fi

# Check if we're in /home/site/wwwroot
if [ "$(pwd)" != "/home/site/wwwroot" ]; then
  echo "Not in /home/site/wwwroot, checking there explicitly..."
  if [ -f "/home/site/wwwroot/output.tar.gz" ]; then
    echo "FOUND output.tar.gz in /home/site/wwwroot - removing it"
    rm -f /home/site/wwwroot/output.tar.gz
  else
    echo "No output.tar.gz found in /home/site/wwwroot"
  fi
fi

# Check for any tar.gz files in the entire wwwroot
echo "Checking for any tar.gz files in wwwroot and subdirectories..."
find /home/site/wwwroot -name "*.tar.gz" > /tmp/wwwroot_targz_files.txt
if [ -s /tmp/wwwroot_targz_files.txt ]; then
  echo "Found tar.gz files in wwwroot:"
  cat /tmp/wwwroot_targz_files.txt
  echo "Removing all tar.gz files..."
  find /home/site/wwwroot -name "*.tar.gz" -delete
  echo "All tar.gz files removed from wwwroot"
else
  echo "No tar.gz files found in wwwroot"
fi

# Create a marker to indicate this script has run
echo "Cleanup completed at $(date)" > wwwroot_cleanup_completed.txt
echo "=================================================="

exit 0 