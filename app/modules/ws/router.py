"""WebSocket endpoint for real-time notifications and table change events.

Clients can subscribe to channels to receive table change events:
  - "leads" → leadslist INSERT/UPDATE/DELETE
  - "call_events" → call_events INSERT/UPDATE/DELETE
  - "lead_info" → lead_info UPDATE
  - "applied_courses" → applied_courses INSERT

Subscribe message: {"type": "subscribe", "channel": "leads"}
Unsubscribe message: {"type": "unsubscribe", "channel": "leads"}
"""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.core.websocket import manager

logger = logging.getLogger("empireo.ws")

router = APIRouter()

VALID_CHANNELS = {"leads", "call_events", "lead_info", "applied_courses"}


@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str) -> None:
    """WebSocket endpoint authenticated via JWT token in the URL path.

    Supported client messages:
      - {"type": "ping"} → responds with {"type": "pong"}
      - {"type": "subscribe", "channel": "leads"} → subscribe to table changes
      - {"type": "unsubscribe", "channel": "leads"} → unsubscribe
    """
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

    await manager.connect(websocket, user_id)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg_type == "subscribe":
                channel = data.get("channel", "")
                if channel in VALID_CHANNELS:
                    manager.subscribe(user_id, channel)
                    await websocket.send_json({"type": "subscribed", "channel": channel})
                else:
                    await websocket.send_json({"type": "error", "message": f"Invalid channel: {channel}"})

            elif msg_type == "unsubscribe":
                channel = data.get("channel", "")
                manager.unsubscribe(user_id, channel)
                await websocket.send_json({"type": "unsubscribed", "channel": channel})

            else:
                await websocket.send_json({"type": "ack", "received": msg_type})

    except WebSocketDisconnect:
        await manager.disconnect(websocket, user_id)
        logger.info("WebSocket client disconnected: user %s", user_id)
    except Exception as exc:
        logger.error("WebSocket error for user %s: %s", user_id, exc)
        await manager.disconnect(websocket, user_id)
