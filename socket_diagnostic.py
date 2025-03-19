import asyncio
import websockets
import json
import sys


async def echo(websocket):
    print(f"New connection from {websocket.remote_address}")
    try:
        async for message in websocket:
            print(f"Received message: {message}")
            response = {"type": "echo", "message": message}
            await websocket.send(json.dumps(response))
            print(f"Sent response: {response}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print(f"Connection closed from {websocket.remote_address}")


async def main():
    port = 8765
    print(f"Starting WebSocket diagnostic server on port {port}")
    async with websockets.serve(echo, "localhost", port):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
