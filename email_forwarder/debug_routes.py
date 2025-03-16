import sys
import os
from importlib import util
from pathlib import Path

# Add the current directory to sys.path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the FastAPI app from main.py
from main import app

def print_routes():
    """Print all registered routes in the FastAPI app."""
    print("\n" + "="*80)
    print("REGISTERED ROUTES")
    print("="*80)
    
    routes = []
    for route in app.routes:
        if hasattr(route, "path"):
            methods = getattr(route, "methods", set())
            methods_str = ", ".join(sorted(methods)) if methods else "No methods defined"
            routes.append((route.path, methods_str))
    
    # Sort routes by path for easier reading
    routes.sort(key=lambda x: x[0])
    
    for path, methods in routes:
        print(f"{path:<50} {methods}")
    
    print("\n" + "="*80)
    print("ROUTES SUMMARY")
    print("="*80)
    print(f"Total routes: {len(routes)}")
    
    # Check for specific routes that are causing issues
    webhooks_routes = [r for r in routes if "/webhooks" in r[0]]
    email_configs_routes = [r for r in routes if "/email-configs" in r[0]]
    
    print(f"\nWebhooks routes: {len(webhooks_routes)}")
    print(f"Email configs routes: {len(email_configs_routes)}")
    
    if not webhooks_routes:
        print("\n⚠️  WARNING: No webhooks routes found!")
    if not email_configs_routes:
        print("\n⚠️  WARNING: No email-configs routes found!")
    
    # Check for non-standard route patterns
    unusual_routes = [r for r in routes if "/api/v1" not in r[0] and not r[0].startswith("/docs") 
                      and not r[0].startswith("/openapi") and not r[0].startswith("/redoc") 
                      and not r[0] == "/health" and not r[0].startswith("/static")]
    
    if unusual_routes:
        print("\nPotentially unusual routes:")
        for route in unusual_routes:
            print(f"  {route[0]}")

if __name__ == "__main__":
    print_routes() 