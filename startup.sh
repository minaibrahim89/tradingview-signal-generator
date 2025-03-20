#!/bin/bash
cd /home/site/wwwroot
gunicorn main:app --bind=0.0.0.0:8000 --worker-class=uvicorn.workers.UvicornWorker --timeout 600 --workers 4
