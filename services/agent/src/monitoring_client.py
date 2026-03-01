import uuid
from datetime import datetime, timezone
import requests
from requests.exceptions import Timeout, HTTPError, RequestException
import os

BASE_URL = os.getenv("BACKEND_URL","http://localhost:8000")

class MonitoringClient:
    def __init__(self, run_uuid: str, agent_number: str, job_uuid: str):
        self.run_uuid = run_uuid
        self.job_uuid = job_uuid
        self.agent_number = agent_number

    def _now(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000")

    def create_job(self):
        try:
            job_response = requests.post(
                f"{BASE_URL}/api/jobs/",
                json={
                    "run_uuid": self.run_uuid,
                    "job_uuid": self.job_uuid,
                    "job_datetime": self._now(),
                    "job_associated_agent": str(self.agent_number),
                    "job_status": "Running",
                },
                timeout=10
            )
            job_response.raise_for_status()

            return self

        except Timeout as e:
            raise RuntimeError("API request timed out") from e

        except HTTPError as e:
            raise RuntimeError(
                f"HTTP error: {e.response.status_code} - {e.response.text}"
            ) from e

        except RequestException as e:
            raise RuntimeError(f"Network error during API request: {str(e)}") from e

    def record_finalsuccess_event(self, event_content: str):
        try:
            # Create success event
            event_response = requests.post(
                f"{BASE_URL}/api/events/",
                json={
                    "event_uuid": str(uuid.uuid4()),
                    "event_content": event_content,
                    "job_uuid": self.job_uuid,
                    "event_datetime": self._now(),
                    "event_status": "Success",
                },
                timeout=10
            )
            event_response.raise_for_status()

            # Update job status
            job_response = requests.patch(
                f"{BASE_URL}/api/jobs/status",
                json={
                    "job_uuid": self.job_uuid,
                    "job_status": "Success",
                },
                timeout=10
            )
            job_response.raise_for_status()

            return self

        except Timeout as e:
            raise RuntimeError("API request timed out") from e

        except HTTPError as e:
            raise RuntimeError(
                f"HTTP error: {e.response.status_code} - {e.response.text}"
            ) from e

        except RequestException as e:
            raise RuntimeError(
                f"Network error during API request: {str(e)}"
            ) from e

    def record_failed_event(self, event_content: str):
        try:
            # Create failed event
            event_response = requests.post(
                f"{BASE_URL}/api/events/",
                json={
                    "event_uuid": str(uuid.uuid4()),
                    "event_content": event_content,
                    "job_uuid": self.job_uuid,
                    "event_datetime": self._now(),
                    "event_status": "Failed",
                },
                timeout=10
            )
            event_response.raise_for_status()

            # Update job status
            job_response = requests.patch(
                f"{BASE_URL}/api/jobs/status",
                json={
                    "job_uuid": self.job_uuid,
                    "job_status": "Failed",
                },
                timeout=10
            )
            job_response.raise_for_status()

            return self

        except Timeout as e:
            raise RuntimeError("API request timed out") from e

        except HTTPError as e:
            raise RuntimeError(
                f"HTTP error: {e.response.status_code} - {e.response.text}"
            ) from e

        except RequestException as e:
            raise RuntimeError(
                f"Network error during API request: {str(e)}"
            ) from e

    def record_success_event(self, event_content: str):
        try:
            response = requests.post(
                f"{BASE_URL}/api/events/",
                json={
                    "event_uuid": str(uuid.uuid4()),
                    "event_content": event_content,
                    "job_uuid": self.job_uuid,
                    "event_datetime": self._now(),
                    "event_status": "Success",
                },
                timeout=10
            )
            response.raise_for_status()

            return self

        except Timeout as e:
            raise RuntimeError("API request timed out") from e

        except HTTPError as e:
            raise RuntimeError(
                f"HTTP error: {e.response.status_code} - {e.response.text}"
            ) from e

        except RequestException as e:
            raise RuntimeError(
                f"Network error during API request: {str(e)}"
            ) from e