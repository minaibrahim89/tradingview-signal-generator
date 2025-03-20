#!/usr/bin/env python3
"""
Simple diagnostic script for Azure Web App deployment
"""
import os
import sys
import platform
import json
import datetime

def check_deployment():
    """Run deployment diagnostics"""
    info = {
        "timestamp": datetime.datetime.now().isoformat(),
        "environment": {
            "python_version": sys.version,
            "platform": platform.platform(),
            "node_version": os.popen("node -v 2>/dev/null || echo 'Not installed'").read().strip(),
            "npm_version": os.popen("npm -v 2>/dev/null || echo 'Not installed'").read().strip(),
        },
        "directories": {
            "current": os.getcwd(),
            "files_in_current": os.listdir("."),
            "wwwroot_exists": os.path.exists("/home/site/wwwroot"),
            "static_exists": os.path.exists("static"),
            "static_files": os.listdir("static") if os.path.exists("static") else [],
        },
        "deployment": {
            "tar_gz_exists": os.path.exists("output.tar.gz"),
            "any_tar_gz": len(list(filter(lambda f: f.endswith('.tar.gz'), os.listdir(".")))) > 0,
            "web_config_exists": os.path.exists("web.config"),
            "startup_sh_exists": os.path.exists("startup.sh"),
            "main_py_exists": os.path.exists("main.py"),
        }
    }
    
    return info

if __name__ == "__main__":
    info = check_deployment()
    print(json.dumps(info, indent=2))
    
    # Check for critical issues
    if info["deployment"]["tar_gz_exists"]:
        print("\n⚠️ WARNING: output.tar.gz still exists!")
    
    if not info["deployment"]["web_config_exists"]:
        print("\n⚠️ WARNING: web.config is missing!")
        
    if not info["deployment"]["startup_sh_exists"]:
        print("\n⚠️ WARNING: startup.sh is missing!")
        
    if not info["deployment"]["main_py_exists"]:
        print("\n⚠️ WARNING: main.py is missing!")
        
    if not info["directories"]["static_exists"]:
        print("\n⚠️ WARNING: static directory is missing!")