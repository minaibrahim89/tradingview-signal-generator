#!/bin/bash
# Extract output.tar.gz and start the application

echo "=== CRITICAL EXTRACTION SCRIPT ==="
echo "Starting extraction process at $(date)"
echo "Current directory: $(pwd)"
echo "Directory contents before extraction:"
ls -la

# Check if we're in the correct directory
if [ -d "/home/site/wwwroot" ] && [ "$(pwd)" != "/home/site/wwwroot" ]; then
  echo "Not in /home/site/wwwroot, changing directory"
  cd /home/site/wwwroot
  echo "Now in $(pwd)"
fi

# Look for any marker that indicates we were already unpacked
if [ -f "deployment_unpacked.txt" ]; then
  echo "Found marker file indicating deployment was already unpacked:"
  cat deployment_unpacked.txt
fi

# Extract output.tar.gz if it exists
if [ -f "output.tar.gz" ]; then
  echo "FOUND output.tar.gz - extracting contents"
  
  # Create backup directory for safety
  mkdir -p /tmp/backup_before_extract
  echo "Created backup directory in /tmp/backup_before_extract"
  
  # Copy existing important files to backup
  if [ -f "web.config" ]; then cp web.config /tmp/backup_before_extract/; fi
  if [ -f "extract_and_start.sh" ]; then cp extract_and_start.sh /tmp/backup_before_extract/; fi
  
  # Extract with verbose output
  echo "Extracting with verbose output:"
  tar -xzvf output.tar.gz
  EXTRACT_STATUS=$?
  
  if [ $EXTRACT_STATUS -eq 0 ]; then
    echo "Extraction completed successfully"
    
    # Remove the archive after extraction
    echo "Removing output.tar.gz"
    rm -f output.tar.gz
    
    # Make sure scripts are executable
    echo "Making scripts executable"
    chmod +x *.sh 2>/dev/null
    
    echo "Directory contents after extraction:"
    ls -la
  else
    echo "ERROR: Extraction failed with status $EXTRACT_STATUS"
    echo "Checking if backup files need to be restored"
    
    # Restore critical files from backup if needed
    if [ ! -f "web.config" ] && [ -f "/tmp/backup_before_extract/web.config" ]; then
      echo "Restoring web.config from backup"
      cp /tmp/backup_before_extract/web.config .
    fi
    
    if [ ! -f "extract_and_start.sh" ] && [ -f "/tmp/backup_before_extract/extract_and_start.sh" ]; then
      echo "Restoring extract_and_start.sh from backup"
      cp /tmp/backup_before_extract/extract_and_start.sh .
      chmod +x extract_and_start.sh
    fi
  fi
else
  echo "No output.tar.gz found - proceeding with startup"
fi

# Continue with normal startup
if [ -f "startup.sh" ]; then
  echo "Running startup.sh"
  bash startup.sh
else
  echo "startup.sh not found - starting app directly"
  
  # Make sure we have a static directory
  if [ ! -d "static" ]; then
    echo "Creating static directory"
    mkdir -p static
    echo '<html><body><h1>API Server Running</h1><p>Access the API at <a href="/docs">/docs</a></p></body></html>' > static/index.html
  fi
  
  # Install dependencies if requirements.txt exists
  if [ -f "requirements.txt" ]; then
    echo "Installing dependencies"
    pip install -r requirements.txt
  fi
  
  # Determine the port
  PORT=${WEBSITES_PORT:-${PORT:-${HTTP_PLATFORM_PORT:-8000}}}
  echo "Using port: $PORT"
  
  # Start the application directly
  echo "Starting application with gunicorn"
  python -m gunicorn main:app --bind=0.0.0.0:$PORT --workers=4 --worker-class=uvicorn.workers.UvicornWorker
fi 