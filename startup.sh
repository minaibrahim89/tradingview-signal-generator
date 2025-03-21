#!/bin/bash
# Main application startup script

echo "Application startup script starting at $(date)"

# Set up environment directory if it doesn't exist
if [ ! -d "antenv" ]; then
  echo "Creating Python virtual environment..."
  python -m venv antenv
  source antenv/bin/activate
  pip install -r requirements.txt
else
  echo "Using existing virtual environment"
  source antenv/bin/activate
fi

# Ensure static directory exists
if [ ! -d "static" ]; then
  echo "Creating static directory"
  mkdir -p static
  echo '<html><body><h1>API Server Running</h1></body></html>' > static/index.html
fi

# Determine port to run on
PORT=${PORT:-${WEBSITES_PORT:-${HTTP_PLATFORM_PORT:-8000}}}
echo "Starting application on port $PORT"

# Start the application with Gunicorn
gunicorn main:app \
  --bind=0.0.0.0:$PORT \
  --worker-class=uvicorn.workers.UvicornWorker \
  --workers=4 \
  --timeout=600 \
  --log-level=info \
  --access-logfile '-'
