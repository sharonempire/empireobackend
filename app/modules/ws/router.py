"""WebSocket endpoint for real-time notifications."""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.core.websocket import manager

logger = logging.getLogger("empireo.ws")

router = APIRouter()


@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str) -> None:
    """WebSocket endpoint authenticated via JWT token in the URL path.

    The client connects to /ws/<jwt_token>. The server decodes the token
    to identify the user. If invalid, the connection is closed with code 4001.

    Once connected, the server keeps the connection alive. The client can
    send JSON messages; the server handles "ping" by responding with "pong".
    Real-time notifications are pushed to the client via the ConnectionManager.
    """
    # Validate JWT token
    payload = decode_token(token)
    if payload is None:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return

    token_type = payload.get("type")
    if token_type != "access":
        await websocket.close(code=4001, reason="Invalid token type")
        return

    user_id = payload.get("sub")
    if user_id is None:
        await websocket.close(code=4001, reason="Invalid token payload")
        return

    # Accept and register the connection
    await manager.connect(websocket, user_id)

    try:
        while True:
            # Wait for incoming messages from the client
            data = await websocket.receive_json()

            # Handle ping/pong keep-alive
            msg_type = data.get("type", "")
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            else:
                # Echo back unrecognized messages with an ack
                await websocket.send_json({"type": "ack", "received": msg_type})

    except WebSocketDisconnect:
        await manager.disconnect(websocket, user_id)
        logger.info("WebSocket client disconnected: user %s", user_id)
    except Exception as exc:
        logger.error("WebSocket error for user %s: %s", user_id, exc)
        await manager.disconnect(websocket, user_id)
