import pytest
from unittest.mock import AsyncMock

from app.ws import WebSocketManager


class TestWebSocketManagerConnect:
    @pytest.mark.asyncio
    async def test_accepts_and_adds(self):
        manager = WebSocketManager()
        mock_ws = AsyncMock()
        await manager.connect(mock_ws)
        mock_ws.accept.assert_awaited_once()
        assert mock_ws in manager._clients


class TestWebSocketManagerDisconnect:
    def test_removes_client(self):
        manager = WebSocketManager()
        mock_ws = AsyncMock()
        manager._clients.append(mock_ws)
        manager.disconnect(mock_ws)
        assert mock_ws not in manager._clients


class TestWebSocketManagerBroadcast:
    @pytest.mark.asyncio
    async def test_sends_to_all(self):
        manager = WebSocketManager()
        ws1, ws2 = AsyncMock(), AsyncMock()
        manager._clients = [ws1, ws2]
        await manager.broadcast({"type": "test"})
        ws1.send_json.assert_awaited_once_with({"type": "test"})
        ws2.send_json.assert_awaited_once_with({"type": "test"})

    @pytest.mark.asyncio
    async def test_cleans_dead_clients(self):
        manager = WebSocketManager()
        ws_alive = AsyncMock()
        ws_dead = AsyncMock()
        ws_dead.send_json.side_effect = Exception("disconnected")
        manager._clients = [ws_alive, ws_dead]
        await manager.broadcast({"type": "test"})
        assert ws_dead not in manager._clients
        assert ws_alive in manager._clients

    @pytest.mark.asyncio
    async def test_empty_clients(self):
        manager = WebSocketManager()
        await manager.broadcast({"type": "test"})  # Should not raise
