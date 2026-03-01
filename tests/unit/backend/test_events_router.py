import pytest
from unittest.mock import patch, AsyncMock

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


class TestGetEvents:
    @patch.object(db, "fetchall", new_callable=AsyncMock)
    def test_all_events(self, mock_fetchall):
        mock_fetchall.return_value = [
            {"event_uuid": "e1", "event_content": "Step 1", "job_uuid": "j1",
             "event_datetime": "2024-01-01T00:00:00", "event_status": "Success"},
        ]
        response = client.get("/api/events/")
        assert response.status_code == 200
        assert len(response.json()) == 1

    @patch.object(db, "fetchall", new_callable=AsyncMock)
    def test_filtered_by_job_uuid(self, mock_fetchall):
        mock_fetchall.return_value = []
        response = client.get("/api/events/?job_uuid=j1")
        assert response.status_code == 200
        call_args = mock_fetchall.call_args
        assert "job_uuid" in call_args[0][0]


class TestCreateEvent:
    @patch.object(ws_manager, "broadcast", new_callable=AsyncMock)
    @patch.object(db, "execute", new_callable=AsyncMock)
    def test_creates_event(self, mock_execute, mock_broadcast):
        response = client.post("/api/events/", json={
            "event_content": "Step done",
            "job_uuid": "j1",
            "event_datetime": "2024-01-01T00:00:00.000",
            "event_status": "Success",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["event_content"] == "Step done"
        assert data["job_uuid"] == "j1"
        assert "event_uuid" in data
        mock_broadcast.assert_called_once()
        broadcast_data = mock_broadcast.call_args[0][0]
        assert broadcast_data["type"] == "new_event"

    @patch.object(ws_manager, "broadcast", new_callable=AsyncMock)
    @patch.object(db, "execute", new_callable=AsyncMock)
    def test_creates_with_provided_uuid(self, mock_execute, mock_broadcast):
        response = client.post("/api/events/", json={
            "event_uuid": "custom-uuid",
            "event_content": "Step done",
            "job_uuid": "j1",
            "event_datetime": "2024-01-01T00:00:00.000",
            "event_status": "Success",
        })
        assert response.status_code == 201
        assert response.json()["event_uuid"] == "custom-uuid"


class TestUpdateEventStatus:
    @patch.object(ws_manager, "broadcast", new_callable=AsyncMock)
    @patch.object(db, "execute", new_callable=AsyncMock)
    def test_updates_status(self, mock_execute, mock_broadcast):
        response = client.patch("/api/events/status", json={
            "event_uuid": "e1",
            "event_status": "Failed",
        })
        assert response.status_code == 200
        mock_execute.assert_called_once()
        mock_broadcast.assert_called_once()
        broadcast_data = mock_broadcast.call_args[0][0]
        assert broadcast_data["type"] == "update_event_status"
        assert broadcast_data["data"]["event_status"] == "Failed"
