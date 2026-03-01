import pytest
from unittest.mock import patch, AsyncMock, MagicMock

# Mock DB env vars before import
with patch.dict("os.environ", {
    "SQL_SERVER_NAME": "test-server",
    "SQL_SERVER_USER": "test-user",
    "SQL_SERVER_PASSWORD": "test-pass",
    "SQL_SERVER_DB": "test-db",
}):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db import db
    from app.ws import ws_manager


client = TestClient(app)


class TestGetRuns:
    @patch.object(db, "fetchall", new_callable=AsyncMock)
    @patch.object(db, "fetchone", new_callable=AsyncMock)
    def test_paginated(self, mock_fetchone, mock_fetchall):
        mock_fetchone.return_value = {"total": 10}
        mock_fetchall.return_value = [
            {"run_uuid": "r1", "run_datetime": "2024-01-01T00:00:00"},
        ]
        response = client.get("/api/runs/?page=1&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        assert len(data["runs"]) == 1
        assert data["page"] == 1
        assert data["page_size"] == 5

    @patch.object(db, "fetchall", new_callable=AsyncMock)
    @patch.object(db, "fetchone", new_callable=AsyncMock)
    def test_empty(self, mock_fetchone, mock_fetchall):
        mock_fetchone.return_value = {"total": 0}
        mock_fetchall.return_value = []
        response = client.get("/api/runs/")
        assert response.status_code == 200
        assert response.json()["total"] == 0


class TestCreateRun:
    @patch.object(ws_manager, "broadcast", new_callable=AsyncMock)
    @patch.object(db, "execute", new_callable=AsyncMock)
    def test_creates_run(self, mock_execute, mock_broadcast):
        response = client.post("/api/runs/", json={
            "run_uuid": "new-run",
            "run_datetime": "2024-01-01T00:00:00.000",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["run_uuid"] == "new-run"
        mock_execute.assert_called_once()
        mock_broadcast.assert_called_once()
        broadcast_data = mock_broadcast.call_args[0][0]
        assert broadcast_data["type"] == "new_run"


class TestDeleteRun:
    @patch.object(ws_manager, "broadcast", new_callable=AsyncMock)
    @patch.object(db, "execute", new_callable=AsyncMock)
    def test_cascade_delete(self, mock_execute, mock_broadcast):
        response = client.delete("/api/runs/run-uuid")
        assert response.status_code == 200
        # 3 DELETE calls: events, jobs, run
        assert mock_execute.call_count == 3
        mock_broadcast.assert_called_once()
        broadcast_data = mock_broadcast.call_args[0][0]
        assert broadcast_data["type"] == "delete_run"
        assert broadcast_data["data"]["run_uuid"] == "run-uuid"
