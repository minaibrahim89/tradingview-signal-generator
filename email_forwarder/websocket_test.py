import asyncio
import websockets
import json
import sys

async def test_websocket_connection():
    """Test WebSocket connectivity to the email notifications endpoint"""
    uri = "ws://localhost:8000/api/v1/ws/emails"
    
    print(f"Attempting to connect to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected successfully!")
            
            # Try to receive the initial connection message
            response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            print(f"Received message: {response}")
            
            # Send a ping
            ping_msg = json.dumps({"type": "ping"})
            print(f"Sending ping: {ping_msg}")
            await websocket.send(ping_msg)
            
            # Wait for pong response
            pong_response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            print(f"Received pong: {pong_response}")
            
            print("Test successful! WebSocket connection is working correctly.")
            return True
    except asyncio.TimeoutError:
        print("Timeout waiting for server response")
    except ConnectionRefusedError:
        print("Connection refused. Make sure the server is running.")
    except Exception as e:
        print(f"Error: {e}")
    
    print("Test failed!")
    return False

if __name__ == "__main__":
    result = asyncio.run(test_websocket_connection())
 