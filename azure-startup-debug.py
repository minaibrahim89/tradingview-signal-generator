import os
import sys
import platform
import datetime

# Log file for Azure debugging
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "azure-debug.log")

with open(log_path, "a") as log:
    log.write(f"\n\n--- Azure Debug Log: {datetime.datetime.now()} ---\n")
    
    # System info
    log.write(f"Python version: {sys.version}\n")
    log.write(f"Platform: {platform.platform()}\n")
    log.write(f"Current working directory: {os.getcwd()}\n")
    
    # Environment variables
    log.write("\nEnvironment Variables:\n")
    for key, value in sorted(os.environ.items()):
        if not key.startswith(("APPSETTING_", "SECRET_")):  # Skip sensitive values
            log.write(f"{key}={value}\n")
    
    # Check for required files
    files_to_check = [
        "main.py", 
        "startup.sh", 
        "requirements.txt", 
        "static/index.html",
        "output.tar.gz"
    ]
    
    log.write("\nFile Existence Checks:\n")
    for file in files_to_check:
        exists = os.path.exists(file)
        log.write(f"{file}: {'EXISTS' if exists else 'MISSING'}\n")
        
    # Check static directory
    if os.path.exists("static"):
        static_files = os.listdir("static")
        log.write(f"\nStatic directory contains {len(static_files)} files\n")
        if len(static_files) < 10:
            log.write(f"Static files: {', '.join(static_files)}\n")
    else:
        log.write("Static directory is MISSING\n")

print(f"Debug information written to {log_path}") 