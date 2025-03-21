#!/bin/bash
# Standard Azure App Service startup script

echo "=============================================="
echo "Running startup script from site/scripts directory"
echo "=============================================="

# Change to the wwwroot directory
cd /home/site/wwwroot

# Execute the main startup script if it exists
if [ -f "startup.sh" ]; then
  echo "Executing startup.sh in wwwroot"
  bash startup.sh
else
  echo "No startup.sh found in wwwroot, checking for fallback scripts"
  
  # Execute .azure/startup.sh if it exists
  if [ -f ".azure/startup.sh" ]; then
    echo "Found .azure/startup.sh, executing it"
    bash .azure/startup.sh
  else
    echo "No startup scripts found - using default startup"
    
    # Create and activate Python virtual environment
    python -m venv antenv
    source antenv/bin/activate
    pip install -r requirements.txt
    
    # Start application with gunicorn
    PORT=${PORT:-8000}
    gunicorn --bind=0.0.0.0:$PORT --worker-class=uvicorn.workers.UvicornWorker --workers=4 --timeout=600 main:app
  fi
fi 