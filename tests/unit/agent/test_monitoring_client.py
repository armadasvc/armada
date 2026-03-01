import re
import pytest
from unittest.mock import patch, MagicMock
from requests.exceptions import Timeout, HTTPError, RequestException

from monitoring_client import MonitoringClient


def _make_http_error(status_code=500, text="Internal Server Error"):
    """Helper to build an HTTPError with a fake response."""
    response = MagicMock()
    response.status_code = status_code
    response.text = text
    return HTTPError(response=response)


class TestMonitoringClientInit:
    def test_stores_identifiers(self):
        mc = MonitoringClient("run-uuid", "0", "job-uuid")
        assert mc.run_uuid == "run-uuid"
        assert mc.agent_number == "0"
        assert mc.job_uuid == "job-uuid"


class TestNow:
    def test_format(self):
        mc = MonitoringClient("r", "0", "j")
        ts = mc._now()
        assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.000", ts)


class TestRecordSuccessEvent:
    @patch("monitoring_client.requests.patch")
    @patch("monitoring_client.requests.post")
    def test_payload(self, mock_post, mock_patch):
        mc = MonitoringClient("r", "0", "j")
        mc.record_finalsuccess_event("Step 1 done")
        payload = mock_post.call_args[1]["json"]
        assert payload["event_status"] == "Success"
        assert payload["event_content"] == "Step 1 done"
        assert payload["job_uuid"] == "j"
        assert "event_uuid" in payload
        assert "event_datetime" in payload


class TestRecordFinalSuccessEvent:
    @patch("monitoring_client.requests.patch")
    @patch("monitoring_client.requests.post")
    def test_post_and_patch(self, mock_post, mock_patch):
        mc = MonitoringClient("r", "0", "j")
        mc.record_finalsuccess_event("All done")
        mock_post.assert_called_once()
        mock_patch.assert_called_once()

    @patch("monitoring_client.requests.patch")
    @patch("monitoring_client.requests.post")
    def test_event_payload(self, mock_post, mock_patch):
        mc = MonitoringClient("r", "0", "j")
        mc.record_finalsuccess_event("All done")
        event_payload = mock_post.call_args[1]["json"]
        assert event_payload["event_status"] == "Success"
        assert event_payload["event_content"] == "All done"

    @patch("monitoring_client.requests.patch")
    @patch("monitoring_client.requests.post")
    def test_job_patched_to_success(self, mock_post, mock_patch):
        mc = MonitoringClient("r", "0", "j")
        mc.record_finalsuccess_event("All done")
        patch_payload = mock_patch.call_args[1]["json"]
        assert patch_payload["job_uuid"] == "j"
        assert patch_payload["job_status"] == "Success"


class TestRecordFailedEvent:
    @patch("monitoring_client.requests.patch")
    @patch("monitoring_client.requests.post")
    def test_post_and_patch(self, mock_post, mock_patch):
        mc = MonitoringClient("r", "0", "j")
        mc.record_failed_event("Crash")
        mock_post.assert_called_once()
        mock_patch.assert_called_once()

    @patch("monitoring_client.requests.patch")
    @patch("monitoring_client.requests.post")
    def test_event_status_failed(self, mock_post, mock_patch):
        mc = MonitoringClient("r", "0", "j")
        mc.record_failed_event("Crash")
        event_payload = mock_post.call_args[1]["json"]
        assert event_payload["event_status"] == "Failed"

    @patch("monitoring_client.requests.patch")
    @patch("monitoring_client.requests.post")
    def test_job_patched_to_failed(self, mock_post, mock_patch):
        mc = MonitoringClient("r", "0", "j")
        mc.record_failed_event("Crash")
        patch_payload = mock_patch.call_args[1]["json"]
        assert patch_payload["job_status"] == "Failed"


class TestMonitoringEdgeCases:
    @patch("monitoring_client.requests.post", side_effect=Exception("Connection refused"))
    def test_create_run_propagates_network_error(self, mock_post):
        """If the monitoring backend is down, the exception should propagate."""
        mc = MonitoringClient("r", "0", "j")
        import pytest
        with pytest.raises(Exception, match="Connection refused"):
            mc.create_job()

    @patch("monitoring_client.requests.post", side_effect=Exception("timeout"))
    def test_record_success_propagates_network_error(self, mock_post):
        mc = MonitoringClient("r", "0", "j")
        import pytest
        with pytest.raises(Exception, match="timeout"):
            mc.record_finalsuccess_event("Step done")

    @patch("monitoring_client.requests.patch", side_effect=Exception("503"))
    @patch("monitoring_client.requests.post")
    def test_finalsuccess_event_posted_but_patch_fails(self, mock_post, mock_patch):
        """The event POST succeeds but the job PATCH fails — exception should propagate."""
        mc = MonitoringClient("r", "0", "j")
        import pytest
        with pytest.raises(Exception, match="503"):
            mc.record_finalsuccess_event("Done")
        # The POST still happened before the PATCH failed
        mock_post.assert_called_once()

    def test_event_uuids_are_unique(self):
        """Each event should get a unique UUID."""
        with patch("monitoring_client.requests.post") as mock_post, \
             patch("monitoring_client.requests.patch"):
            mc = MonitoringClient("r", "0", "j")
            mc.record_finalsuccess_event("Step 1")
            mc.record_finalsuccess_event("Step 2")
            uuid1 = mock_post.call_args_list[0][1]["json"]["event_uuid"]
            uuid2 = mock_post.call_args_list[1][1]["json"]["event_uuid"]
            assert uuid1 != uuid2



# ---------------------------------------------------------------------------
# Error-handling tests  (Timeout / HTTPError / RequestException → RuntimeError)
# ---------------------------------------------------------------------------


class TestCreateRunAndJobErrorHandling:
    @patch("monitoring_client.requests.post", side_effect=Timeout("connect timed out"))
    def test_timeout_raises_runtime_error(self, mock_post):
        mc = MonitoringClient("r", "0", "j")
        with pytest.raises(RuntimeError, match="API request timed out") as exc_info:
            mc.create_job()
        assert isinstance(exc_info.value.__cause__, Timeout)

    @patch("monitoring_client.requests.post")
    def test_http_error_includes_status_and_body(self, mock_post):
        response = MagicMock()
        response.raise_for_status.side_effect = _make_http_error(422, "Validation failed")
        mock_post.return_value = response
        mc = MonitoringClient("r", "0", "j")
        with pytest.raises(RuntimeError, match="HTTP error: 422 - Validation failed") as exc_info:
            mc.create_job()
        assert isinstance(exc_info.value.__cause__, HTTPError)

    @patch("monitoring_client.requests.post", side_effect=RequestException("DNS resolution failed"))
    def test_request_exception_raises_runtime_error(self, mock_post):
        mc = MonitoringClient("r", "0", "j")
        with pytest.raises(RuntimeError, match="Network error during API request: DNS resolution failed") as exc_info:
            mc.create_job()
        assert isinstance(exc_info.value.__cause__, RequestException)


class TestRecordFinalSuccessEventErrorHandling:
    @patch("monitoring_client.requests.post", side_effect=Timeout("timed out"))
    def test_timeout_on_event_post(self, mock_post):
        mc = MonitoringClient("r", "0", "j")
        with pytest.raises(RuntimeError, match="API request timed out"):
            mc.record_finalsuccess_event("done")

    @patch("monitoring_client.requests.patch", side_effect=Timeout("timed out"))
    @patch("monitoring_client.requests.post")
    def test_timeout_on_job_patch(self, mock_post, mock_patch):
        mc = MonitoringClient("r", "0", "j")
        with pytest.raises(RuntimeError, match="API request timed out"):
            mc.record_finalsuccess_event("done")
        mock_post.assert_called_once()

    @patch("monitoring_client.requests.post")
    def test_http_error_on_event_post(self, mock_post):
        response = MagicMock()
        response.raise_for_status.side_effect = _make_http_error(500, "Server Error")
        mock_post.return_value = response
        mc = MonitoringClient("r", "0", "j")
        with pytest.raises(RuntimeError, match="HTTP error: 500 - Server Error"):
            mc.record_finalsuccess_event("done")

    @patch("monitoring_client.requests.patch")
    @patch("monitoring_client.requests.post")
    def test_http_error_on_job_patch(self, mock_post, mock_patch):
        bad_response = MagicMock()
        bad_response.raise_for_status.side_effect = _make_http_error(503, "Unavailable")
        mock_patch.return_value = bad_response
        mc = MonitoringClient("r", "0", "j")
        with pytest.raises(RuntimeError, match="HTTP error: 503 - Unavailable"):
            mc.record_finalsuccess_event("done")

    @patch("monitoring_client.requests.post", side_effect=RequestException("connection reset"))
    def test_request_exception_on_event_post(self, mock_post):
        mc = MonitoringClient("r", "0", "j")
        with pytest.raises(RuntimeError, match="Network error during API request: connection reset"):
            mc.record_finalsuccess_event("done")

    @patch("monitoring_client.requests.patch", side_effect=RequestException("broken pipe"))
    @patch("monitoring_client.requests.post")
    def test_request_exception_on_job_patch(self, mock_post, mock_patch):
        mc = MonitoringClient("r", "0", "j")
        with pytest.raises(RuntimeError, match="Network error during API request: broken pipe"):
            mc.record_finalsuccess_event("done")


class TestRecordFailedEventErrorHandling:
    @patch("monitoring_client.requests.post", side_effect=Timeout("timed out"))
    def test_timeout_on_event_post(self, mock_post):
        mc = MonitoringClient("r", "0", "j")
        with pytest.raises(RuntimeError, match="API request timed out"):
            mc.record_failed_event("error")

    @patch("monitoring_client.requests.patch", side_effect=Timeout("timed out"))
    @patch("monitoring_client.requests.post")
    def test_timeout_on_job_patch(self, mock_post, mock_patch):
        mc = MonitoringClient("r", "0", "j")
        with pytest.raises(RuntimeError, match="API request timed out"):
            mc.record_failed_event("error")
        mock_post.assert_called_once()

    @patch("monitoring_client.requests.post")
    def test_http_error_on_event_post(self, mock_post):
        response = MagicMock()
        response.raise_for_status.side_effect = _make_http_error(400, "Bad Request")
        mock_post.return_value = response
        mc = MonitoringClient("r", "0", "j")
        with pytest.raises(RuntimeError, match="HTTP error: 400 - Bad Request"):
            mc.record_failed_event("error")

    @patch("monitoring_client.requests.patch")
    @patch("monitoring_client.requests.post")
    def test_http_error_on_job_patch(self, mock_post, mock_patch):
        bad_response = MagicMock()
        bad_response.raise_for_status.side_effect = _make_http_error(502, "Bad Gateway")
        mock_patch.return_value = bad_response
        mc = MonitoringClient("r", "0", "j")
        with pytest.raises(RuntimeError, match="HTTP error: 502 - Bad Gateway"):
            mc.record_failed_event("error")

    @patch("monitoring_client.requests.post", side_effect=RequestException("no route to host"))
    def test_request_exception_on_event_post(self, mock_post):
        mc = MonitoringClient("r", "0", "j")
        with pytest.raises(RuntimeError, match="Network error during API request: no route to host"):
            mc.record_failed_event("error")

    @patch("monitoring_client.requests.patch", side_effect=RequestException("reset by peer"))
    @patch("monitoring_client.requests.post")
    def test_request_exception_on_job_patch(self, mock_post, mock_patch):
        mc = MonitoringClient("r", "0", "j")
        with pytest.raises(RuntimeError, match="Network error during API request: reset by peer"):
            mc.record_failed_event("error")

    def test_exception_chaining_preserved(self):
        """Verify __cause__ is set so traceback shows the original exception."""
        with patch("monitoring_client.requests.post", side_effect=Timeout("slow")):
            mc = MonitoringClient("r", "0", "j")
            with pytest.raises(RuntimeError) as exc_info:
                mc.record_failed_event("error")
            assert isinstance(exc_info.value.__cause__, Timeout)
