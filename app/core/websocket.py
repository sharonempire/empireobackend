"""WebSocket connection manager for real-time notifications."""

import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger("empireo.websocket")


class ConnectionManager:
    """Manages active WebSocket connections per user.

    Each user can have multiple connections (e.g. multiple browser tabs).
    Messages are sent as JSON to all connections for a given user.
    """

    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """Accept the WebSocket and register it under the user's connection list."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info("WebSocket connected for user %s (total: %d)", user_id, len(self.active_connections[user_id]))

    async def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        """Remove a WebSocket from the user's connection list."""
        if user_id in self.active_connections:
            try:
                self.active_connections[user_id].remove(websocket)
            except ValueError:
                pass
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info("WebSocket disconnected for user %s", user_id)

    async def send_personal(self, user_id: str, message: dict[str, Any]) -> None:
        """Send a JSON message to all connections for a specific user."""
        connections = self.active_connections.get(user_id, [])
        disconnected: list[WebSocket] = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        # Clean up stale connections
        for conn in disconnected:
            try:
                self.active_connections[user_id].remove(conn)
            except (ValueError, KeyError):
                pass
        if user_id in self.active_connections and not self.active_connections[user_id]:
            del self.active_connections[user_id]

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Send a JSON message to all connected users."""
        disconnected_pairs: list[tuple[str, WebSocket]] = []
        for user_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected_pairs.append((user_id, connection))
        # Clean up stale connections
        for user_id, conn in disconnected_pairs:
            try:
                self.active_connections[user_id].remove(conn)
            except (ValueError, KeyError):
                pass
        # Remove empty user entries
        empty_users = [uid for uid, conns in self.active_connections.items() if not conns]
        for uid in empty_users:
            del self.active_connections[uid]


# Singleton instance used across the application
manager = ConnectionManager()
