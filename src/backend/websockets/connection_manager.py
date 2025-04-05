from typing import Dict

from fastapi import WebSocket
from src.utils.logger_config import setup_logger

logger = setup_logger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        # Maps session_id to WebSocket connection
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected for session {session_id}")

    def disconnect(self, session_id: str):
        """Remove a WebSocket connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected for session {session_id}")

    async def send_update(self, session_id: str, data: dict):
        """Send an update to a specific session"""
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(data)
                logger.info(f"Sent update to session {session_id}")
            except Exception as e:
                logger.error(f"Error sending update to session {session_id}: {str(e)}")
                self.disconnect(session_id)
        else:
            logger.warning(f"No active connection for session {session_id}")


# Create a singleton instance
connection_manager = ConnectionManager()
