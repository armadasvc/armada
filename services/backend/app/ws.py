"""
WebSocket manager — handles connected clients and broadcasting.

Usage in a router:
    from app.ws import ws_manager

    await ws_manager.connect(websocket)
    ws_manager.disconnect(websocket)
    await ws_manager.broadcast({"event_uuid": "...", "event_content": "..."})
"""

from fastapi import WebSocket


class WebSocketManager:
    def __init__(self):
        self._clients: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._clients.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self._clients:
            self._clients.remove(ws)

    async def broadcast(self, data: dict):
        disconnected = []
        for client in self._clients:
            try:
                await client.send_json(data)
            except Exception:
                disconnected.append(client)
        for client in disconnected:
            if client in self._clients:
                self._clients.remove(client)


# Global instance
ws_manager = WebSocketManager()
