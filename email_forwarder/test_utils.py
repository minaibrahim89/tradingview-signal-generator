import os
import sys
import requests
import asyncio
import websockets
import json
import time
from importlib import util
from pathlib import Path

# Add the current directory to sys.path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import the FastAPI app (only needed for route inspection)
try:
    from main import app as fastapi_app
    FASTAPI_AVAILABLE = True
except ImportError:
    print("Warning: Could not import FastAPI app for route inspection")
    FASTAPI_AVAILABLE = False

# Constants
DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_WS_URLS = [
    "ws://localhost:8000/ws",
    "ws://localhost:8000/api/v1/ws/emails",
]

# Color codes for terminal output


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")


def wait_for_server(url, max_retries=5, retry_delay=2):
    """Wait for the server to become available."""
    for i in range(max_retries):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print(
                    f"{Colors.GREEN}Server is up and running at {url}{Colors.ENDC}")
                return True
        except requests.RequestException:
            print(
                f"{Colors.YELLOW}Waiting for server to start (attempt {i+1}/{max_retries})...{Colors.ENDC}")
            time.sleep(retry_delay)
    print(f"{Colors.RED}Failed to connect to server after multiple attempts{Colors.ENDC}")
    return False


def print_routes():
    """Print all registered routes in the FastAPI app."""
    if not FASTAPI_AVAILABLE:
        print(
            f"{Colors.RED}Cannot inspect routes: FastAPI app not available{Colors.ENDC}")
        return

    print_header("REGISTERED ROUTES")

    routes = []
    for route in fastapi_app.routes:
        if hasattr(route, "path"):
            methods = getattr(route, "methods", set())
            methods_str = ", ".join(
                sorted(methods)) if methods else "No methods defined"
            routes.append((route.path, methods_str))

    # Sort routes by path for easier reading
    routes.sort(key=lambda x: x[0])

    for path, methods in routes:
        print(f"{path:<50} {methods}")

    print_header("ROUTES SUMMARY")
    print(f"Total routes: {len(routes)}")

    # Check for specific routes
    webhooks_routes = [r for r in routes if "/webhooks" in r[0]]
    email_configs_routes = [r for r in routes if "/email-configs" in r[0]]
    websocket_routes = [
        r for r in routes if r[0].endswith("/ws") or "/ws/" in r[0]]

    print(f"\nWebhooks routes: {len(webhooks_routes)}")
    print(f"Email configs routes: {len(email_configs_routes)}")
    print(f"WebSocket routes: {len(websocket_routes)}")

    if not webhooks_routes:
        print(
            f"\n{Colors.YELLOW}⚠️  WARNING: No webhooks routes found!{Colors.ENDC}")
    if not email_configs_routes:
        print(
            f"\n{Colors.YELLOW}⚠️  WARNING: No email-configs routes found!{Colors.ENDC}")
    if not websocket_routes:
        print(
            f"\n{Colors.YELLOW}⚠️  WARNING: No WebSocket routes found!{Colors.ENDC}")

    # Check for unusual route patterns
    unusual_routes = [r for r in routes if "/api/v1" not in r[0] and not r[0].startswith("/docs")
                      and not r[0].startswith("/openapi") and not r[0].startswith("/redoc")
                      and not r[0] == "/health" and not r[0].startswith("/static")]

    if unusual_routes:
        print(f"\n{Colors.YELLOW}Potentially unusual routes:{Colors.ENDC}")
        for route in unusual_routes:
            print(f"  {route[0]}")


def test_api_endpoints(base_url=DEFAULT_BASE_URL):
    """Test various API endpoints."""
    # Wait for server to start
    if not wait_for_server(f"{base_url}/health"):
        return

    # Test endpoints
    endpoints = [
        "/api/v1/webhooks",
        "/api/v1/email-configs",
        "/health",
        "/api/test",
        "/api/v1/ws/emails",  # WebSocket as HTTP endpoint will return 400
    ]

    print_header("API ENDPOINT TESTS")

    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url)
            status = response.status_code
            status_color = Colors.GREEN if status < 400 else Colors.RED
            print(f"{url:<40} {status_color}Status: {status}{Colors.ENDC}")
        except requests.RequestException as e:
            print(f"{url:<40} {Colors.RED}Error: {str(e)}{Colors.ENDC}")


async def test_websocket_connection(url):
    """Test connection to a specific WebSocket endpoint"""
    print(f"Testing connection to {url}...")
    try:
        async with websockets.connect(url, timeout=5) as ws:
            print(f"{Colors.GREEN}✅ Connected to {url} successfully!{Colors.ENDC}")

            # Send a ping message
            await ws.send(json.dumps({"type": "ping"}))
            print(f"Sent ping to {url}")

            # Wait for response
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            print(f"Received response: {response}")

            return True
    except asyncio.TimeoutError:
        print(f"{Colors.RED}❌ Timeout waiting for response from {url}{Colors.ENDC}")
    except ConnectionRefusedError:
        print(
            f"{Colors.RED}❌ Connection refused to {url}. Make sure the server is running.{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.RED}❌ Failed to connect to {url}: {e}{Colors.ENDC}")

    return False


async def test_websockets(urls=DEFAULT_WS_URLS):
    """Test all WebSocket endpoints."""
    print_header("WEBSOCKET TESTS")

    # Try each endpoint
    results = []
    for endpoint in urls:
        success = await test_websocket_connection(endpoint)
        results.append((endpoint, success))

    # Print summary
    print_header("WEBSOCKET TEST RESULTS")
    any_success = False
    for endpoint, success in results:
        status = f"{Colors.GREEN}✅ WORKING{Colors.ENDC}" if success else f"{Colors.RED}❌ FAILED{Colors.ENDC}"
        print(f"{endpoint}: {status}")
        if success:
            any_success = True

    # Provide troubleshooting advice if all fail
    if not any_success:
        print(f"\n{Colors.YELLOW}--- TROUBLESHOOTING ADVICE ---{Colors.ENDC}")
        print("1. Verify FastAPI server is running on port 8000")
        print("2. Check for firewall or network issues")
        print("3. Ensure the WebSocket route is properly registered")
        print("4. Check server logs for any errors")
        print(
            "5. Try running the server with the --reload flag for better error visibility")
        return False

    return True


async def run_all_tests():
    """Run all available tests."""
    print_header("STARTING COMPREHENSIVE TESTS")

    # Test API endpoints
    test_api_endpoints()

    # Test WebSockets
    websocket_success = await test_websockets()

    # Print registered routes
    if FASTAPI_AVAILABLE:
        print_routes()

    # Print final summary
    print_header("TEST SUMMARY")
    if websocket_success:
        print(
            f"{Colors.GREEN}All tests completed. Some tests passed successfully.{Colors.ENDC}")
    else:
        print(
            f"{Colors.YELLOW}Tests completed with some failures. See above for details.{Colors.ENDC}")

if __name__ == "__main__":
    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(
        description="Test utility for the Email Forwarder application")
    parser.add_argument("--routes", action="store_true",
                        help="Print registered routes")
    parser.add_argument("--api", action="store_true",
                        help="Test API endpoints")
    parser.add_argument("--ws", action="store_true",
                        help="Test WebSocket endpoints")
    parser.add_argument("--all", action="store_true", help="Run all tests")

    args = parser.parse_args()

    # If no arguments provided, run all tests
    if not any(vars(args).values()):
        args.all = True

    # Run requested tests
    if args.routes:
        print_routes()

    if args.api:
        test_api_endpoints()

    if args.ws:
        asyncio.run(test_websockets())

    if args.all:
        asyncio.run(run_all_tests())
