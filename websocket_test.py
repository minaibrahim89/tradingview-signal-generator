import asyncio
import websockets
import json
import sys


async def test_connection(url):
    """Test connection to a specific WebSocket endpoint"""
    print(f"Testing connection to {url}...")
    try:
        async with websockets.connect(url, timeout=5) as ws:
            print(f"✅ Connected to {url} successfully!")

            # Send a ping message
            await ws.send(json.dumps({"type": "ping"}))
            print(f"Sent ping to {url}")

            # Wait for response
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            print(f"Received response: {response}")

            return True
    except asyncio.TimeoutError:
        print(f"❌ Timeout waiting for response from {url}")
    except ConnectionRefusedError:
        print(
            f"❌ Connection refused to {url}. Make sure the server is running.")
    except Exception as e:
        print(f"❌ Failed to connect to {url}: {e}")

    return False


async def main():
    # List of endpoints to test
    endpoints = [
        "ws://localhost:8000/ws",
        "ws://localhost:8000/api/v1/ws/emails",
        "ws://127.0.0.1:8000/ws",
        "ws://127.0.0.1:8000/api/v1/ws/emails"
    ]

    # Try each endpoint
    results = []
    for endpoint in endpoints:
        success = await test_connection(endpoint)
        results.append((endpoint, success))

    # Print summary
    print("\n--- RESULTS SUMMARY ---")
    any_success = False
    for endpoint, success in results:
        status = "✅ WORKING" if success else "❌ FAILED"
        print(f"{endpoint}: {status}")
        if success:
            any_success = True

    # Provide troubleshooting advice
    if not any_success:
        print("\n--- TROUBLESHOOTING ADVICE ---")
        print("1. Verify FastAPI server is running on port 8000")
        print("2. Check for firewall or network issues")
        print("3. Ensure the WebSocket route is properly registered")
        print("4. Check server logs for any errors")
        print(
            "5. Try running the server with the --reload flag for better error visibility")
        sys.exit(1)
    else:
        print("\nAt least one endpoint is working! Your WebSocket server is up.")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
