from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


class TestFetchProxyEndpoint:
    @patch("main.fetch_random_proxy")
    @patch("main.build_proxy_query")
    def test_simple_no_checks(self, mock_build, mock_fetch):
        mock_build.return_value = ("SELECT ...", ())
        mock_fetch.return_value = "http://proxy:8080"

        response = client.get("/fetch_proxy?proxy_type=residential")
        assert response.status_code == 200
        data = response.json()
        assert data["proxy_url"] == "http://proxy:8080"
        assert data["attempt"] == 1

    @patch("main.fetch_random_proxy")
    @patch("main.build_proxy_query")
    def test_not_found(self, mock_build, mock_fetch):
        mock_build.return_value = ("SELECT ...", ())
        mock_fetch.return_value = None

        response = client.get("/fetch_proxy")
        assert response.status_code == 404

    @patch("main.IPQUALITYSCORE_API_KEY", "fake-key")
    @patch("main.run_checks")
    @patch("main.check_ip")
    @patch("main.fetch_random_proxy")
    @patch("main.build_proxy_query")
    def test_with_checks_pass(self, mock_build, mock_fetch, mock_check_ip, mock_run_checks):
        mock_build.return_value = ("SELECT ...", ())
        mock_fetch.return_value = "http://proxy:8080"
        mock_check_ip.return_value = {"ip": "1.2.3.4"}
        mock_run_checks.return_value = (True, {"verify_quality": {"quality_pass": True}})

        response = client.get("/fetch_proxy?verify_ip=true&verify_quality=true")
        assert response.status_code == 200
        assert response.json()["proxy_url"] == "http://proxy:8080"

    @patch("main.IPQUALITYSCORE_API_KEY", "fake-key")
    @patch("main.run_checks")
    @patch("main.check_ip")
    @patch("main.fetch_random_proxy")
    @patch("main.build_proxy_query")
    def test_retry_on_check_fail(self, mock_build, mock_fetch, mock_check_ip, mock_run_checks):
        mock_build.return_value = ("SELECT ...", ())
        mock_fetch.return_value = "http://proxy:8080"
        mock_check_ip.return_value = {"ip": "1.2.3.4"}
        # First call fails, second passes
        mock_run_checks.side_effect = [
            (False, {"verify_quality": {"quality_pass": False}}),
            (True, {"verify_quality": {"quality_pass": True}}),
        ]

        response = client.get("/fetch_proxy?verify_quality=true&max_queries_number=2")
        assert response.status_code == 200
        assert response.json()["attempt"] == 2

    @patch("main.check_ip")
    @patch("main.fetch_random_proxy")
    @patch("main.build_proxy_query")
    def test_no_ip_resolved_retries(self, mock_build, mock_fetch, mock_check_ip):
        mock_build.return_value = ("SELECT ...", ())
        mock_fetch.return_value = "http://proxy:8080"
        mock_check_ip.return_value = {"ip": None}

        response = client.get("/fetch_proxy?verify_ip=true&max_queries_number=2")
        assert response.status_code == 404

    @patch("main.fetch_random_proxy")
    @patch("main.build_proxy_query")
    def test_db_exception(self, mock_build, mock_fetch):
        mock_build.return_value = ("SELECT ...", ())
        mock_fetch.side_effect = Exception("DB connection error")

        response = client.get("/fetch_proxy")
        assert response.status_code == 500
