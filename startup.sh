#!/bin/bash
# Add a small delay to ensure SCM container is fully initialized
sleep 10
echo "Starting application after waiting for SCM initialization..."
gunicorn main:app --bind=0.0.0.0:8000 --worker-class=uvicorn.workers.UvicornWorker --timeout 600 --workers 4
