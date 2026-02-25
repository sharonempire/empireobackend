"""WebSocket connection manager for real-time notifications and table change events."""

import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger("empireo.websocket")


class ConnectionManager:
    """Manages active WebSocket connections per user with channel subscriptions.

    Each user can have multiple connections (e.g. multiple browser tabs).
    Users can subscribe to channels to receive table change events.

    Channels map to database tables:
      - "leads" → leadslist INSERT/UPDATE/DELETE
      - "call_events" → call_events INSERT/UPDATE/DELETE
      - "lead_info" → lead_info UPDATE
      - "applied_courses" → applied_courses INSERT
    """

    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = {}
        # Channel subscriptions: channel_name -> set of user_ids
        self.channel_subscriptions: dict[str, set[str]] = {}

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
                # Unsubscribe from all channels
                for channel_subs in self.channel_subscriptions.values():
                    channel_subs.discard(user_id)
        logger.info("WebSocket disconnected for user %s", user_id)

    def subscribe(self, user_id: str, channel: str) -> None:
        """Subscribe a user to a channel for table change events."""
        if channel not in self.channel_subscriptions:
            self.channel_subscriptions[channel] = set()
        self.channel_subscriptions[channel].add(user_id)
        logger.debug("User %s subscribed to channel %s", user_id, channel)

    def unsubscribe(self, user_id: str, channel: str) -> None:
        """Unsubscribe a user from a channel."""
        if channel in self.channel_subscriptions:
            self.channel_subscriptions[channel].discard(user_id)

    async def send_personal(self, user_id: str, message: dict[str, Any]) -> None:
        """Send a JSON message to all connections for a specific user."""
        connections = self.active_connections.get(user_id, [])
        disconnected: list[WebSocket] = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
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
        for user_id, conn in disconnected_pairs:
            try:
                self.active_connections[user_id].remove(conn)
            except (ValueError, KeyError):
                pass
        empty_users = [uid for uid, conns in self.active_connections.items() if not conns]
        for uid in empty_users:
            del self.active_connections[uid]

    async def broadcast_to_channel(self, channel: str, message: dict[str, Any]) -> None:
        """Send a JSON message to all users subscribed to a channel."""
        subscribers = self.channel_subscriptions.get(channel, set())
        for user_id in list(subscribers):
            if user_id in self.active_connections:
                await self.send_personal(user_id, message)


# Singleton instance used across the application
manager = ConnectionManager()


async def broadcast_table_change(
    table: str,
    event_type: str,
    record_id: Any,
    data: dict[str, Any] | None = None,
) -> None:
    """Broadcast a table change event to all subscribed WebSocket clients.

    Args:
        table: The table/channel name (e.g. "leads", "call_events")
        event_type: One of "INSERT", "UPDATE", "DELETE"
        record_id: The primary key of the changed record
        data: Optional dict of changed fields/values
    """
    message = {
        "type": "table_change",
        "table": table,
        "event_type": event_type,
        "record_id": str(record_id) if record_id is not None else None,
    }
    if data:
        message["data"] = data

    await manager.broadcast_to_channel(table, message)
