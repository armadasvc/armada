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


class TestGetJobs:
    @patch.object(db, "fetchall", new_callable=AsyncMock)
    @patch.object(db, "fetchone", new_callable=AsyncMock)
    def test_all_jobs(self, mock_fetchone, mock_fetchall):
        mock_fetchone.return_value = {"total": 5}
        mock_fetchall.return_value = [
            {"job_uuid": "j1", "run_uuid": "r1", "job_datetime": "2024-01-01T00:00:00",
             "job_associated_agent": "0", "job_status": "Running"},
        ]
        response = client.get("/api/jobs/?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5

    @patch.object(db, "fetchall", new_callable=AsyncMock)
    @patch.object(db, "fetchone", new_callable=AsyncMock)
    def test_filtered_by_run_uuid(self, mock_fetchone, mock_fetchall):
        mock_fetchone.return_value = {"total": 2}
        mock_fetchall.return_value = []
        response = client.get("/api/jobs/?run_uuid=abc&page=1&page_size=10")
        assert response.status_code == 200
        # Verify that fetchone was called with a query containing run_uuid filter
        call_args = mock_fetchone.call_args
        assert "run_uuid" in call_args[0][0]


class TestCreateJob:
    @patch.object(ws_manager, "broadcast", new_callable=AsyncMock)
    @patch.object(db, "execute", new_callable=AsyncMock)
    def test_creates_with_auto_uuid(self, mock_execute, mock_broadcast):
        response = client.post("/api/jobs/", json={
            "run_uuid": "r1",
            "job_datetime": "2024-01-01T00:00:00.000",
            "job_associated_agent": "0",
            "job_status": "Running",
        })
        assert response.status_code == 201
        data = response.json()
        assert "job_uuid" in data
        assert data["run_uuid"] == "r1"
        mock_broadcast.assert_called_once()

    @patch.object(ws_manager, "broadcast", new_callable=AsyncMock)
    @patch.object(db, "execute", new_callable=AsyncMock)
    def test_creates_with_provided_uuid(self, mock_execute, mock_broadcast):
        response = client.post("/api/jobs/", json={
            "run_uuid": "r1",
            "job_uuid": "custom-uuid",
            "job_datetime": "2024-01-01T00:00:00.000",
            "job_status": "Running",
        })
        assert response.status_code == 201
        assert response.json()["job_uuid"] == "custom-uuid"


class TestUpdateJobStatus:
    @patch.object(ws_manager, "broadcast", new_callable=AsyncMock)
    @patch.object(db, "execute", new_callable=AsyncMock)
    def test_updates_status(self, mock_execute, mock_broadcast):
        response = client.patch("/api/jobs/status", json={
            "job_uuid": "j1",
            "job_status": "Success",
        })
        assert response.status_code == 200
        mock_execute.assert_called_once()
        mock_broadcast.assert_called_once()
        broadcast_data = mock_broadcast.call_args[0][0]
        assert broadcast_data["type"] == "update_job_status"
        assert broadcast_data["data"]["job_status"] == "Success"
