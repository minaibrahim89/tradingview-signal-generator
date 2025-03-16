import os
import sys
import requests
import time

def wait_for_server(url, max_retries=5, retry_delay=2):
    """Wait for the server to become available."""
    for i in range(max_retries):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print(f"Server is up and running at {url}")
                return True
        except requests.RequestException:
            print(f"Waiting for server to start (attempt {i+1}/{max_retries})...")
            time.sleep(retry_delay)
    print("Failed to connect to server after multiple attempts")
    return False

def test_api_endpoints():
    """Test various API endpoints."""
    base_url = "http://localhost:8000"
    
    # Wait for server to start
    if not wait_for_server(f"{base_url}/health"):
        return
    
    # Test endpoints
    endpoints = [
        "/api/v1/webhooks",
        "/api/v1/webhooks/",
        "/api/v1/email-configs",
        "/api/v1/email-configs/",
        "/health",
        "/api/test"
    ]
    
    print("\nTesting API endpoints:")
    print("="*50)
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url)
            status = response.status_code
            print(f"{url:<40} {status} {'✓' if status == 200 else '✗'}")
        except requests.RequestException as e:
            print(f"{url:<40} Error: {str(e)}")
    
    print("\nDetailed test of problematic endpoints:")
    print("="*50)
    
    # More detailed test for the problematic endpoints
    problematic = ["/api/v1/webhooks", "/api/v1/email-configs"]
    for endpoint in problematic:
        for method in ["GET", "POST"]:
            url = f"{base_url}{endpoint}"
            try:
                if method == "GET":
                    response = requests.get(url)
                else:
                    response = requests.post(url, json={})
                
                print(f"{method} {url}")
                print(f"Status: {response.status_code}")
                print(f"Headers: {dict(response.headers)}")
                print(f"Content: {response.text[:200]}...")
                print("-"*50)
            except requests.RequestException as e:
                print(f"{method} {url}")
                print(f"Error: {str(e)}")
                print("-"*50)

if __name__ == "__main__":
    print("\nStarting API tests...")
    test_api_endpoints() 