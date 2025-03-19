from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
import json
from typing import Dict, List, Set
import asyncio
from starlette.websockets import WebSocketState

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter()

# Store for active WebSocket connections
active_connections: List[WebSocket] = []


@router.websocket("/emails")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time email notifications"""
    client_info = f"{websocket.client.host}:{websocket.client.port}"
    logger.info(f"WebSocket connection request from {client_info}")

    try:
        await websocket.accept()
        active_connections.append(websocket)
        logger.info(
            f"New WebSocket client connected from {client_info}. Total active connections: {len(active_connections)}")

        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection_status",
            "status": "connected",
            "message": "WebSocket connection established"
        }))

        while True:
            # Keep the connection alive until client disconnects
            data = await websocket.receive_text()
            logger.info(f"Received message from client {client_info}: {data}")

            # Handle ping messages
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    logger.info(
                        f"Ping received from {client_info}, sending pong")
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": "now"
                    }))
            except Exception as e:
                logger.error(f"Error handling client message: {e}")
    except WebSocketDisconnect:
        # Remove the connection on disconnect
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.info(
            f"WebSocket client {client_info} disconnected. Remaining connections: {len(active_connections)}")
    except Exception as e:
        logger.error(f"WebSocket error with client {client_info}: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)


# Function to broadcast a message to all connected clients
async def broadcast_email_processed(email_data: dict):
    """Broadcast a new processed email to all WebSocket clients"""
    if not active_connections:
        logger.info("No WebSocket clients connected, skipping broadcast")
        return

    # Convert to JSON string
    message = json.dumps({
        "type": "email_processed",
        "data": email_data
    })

    logger.info(
        f"Broadcasting email update to {len(active_connections)} clients")
    logger.info(
        f"Broadcast content summary: Subject: {email_data.get('subject', 'Unknown')}, ID: {email_data.get('id', 'Unknown')}")

    # Track disconnected clients to remove them
    disconnected = []

    # Send to all connected clients
    for i, connection in enumerate(active_connections):
        try:
            if connection.client_state == WebSocketState.CONNECTED:
                await connection.send_text(message)
                logger.info(f"Message sent to client {i+1}")
            else:
                logger.warning(
                    f"Client {i+1} is not in CONNECTED state, marking for removal")
                disconnected.append(i)
        except WebSocketDisconnect:
            logger.error(
                f"Client {i+1} disconnected during send, marking for removal")
            disconnected.append(i)
        except Exception as e:
            logger.error(
                f"Error sending WebSocket message to client {i+1}: {e}")
            disconnected.append(i)

    # Remove disconnected clients (in reverse order to avoid index issues)
    if disconnected:
        logger.info(f"Removing {len(disconnected)} disconnected clients")
        for i in sorted(disconnected, reverse=True):
            try:
                logger.info(f"Removing disconnected client at index {i}")
                del active_connections[i]
            except IndexError:
                logger.warning(
                    f"Failed to remove client at index {i}, index out of range")

    logger.info(
        f"Broadcast complete. {len(active_connections)} active connections remaining")
