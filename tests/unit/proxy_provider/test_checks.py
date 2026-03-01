from unittest.mock import patch, MagicMock

from checks import check_ip, check_quality, check_location, run_checks


class TestCheckIp:
    @patch("checks.requests.get")
    def test_success(self, mock_get):
        mock_get.return_value.text = "1.2.3.4"
        result = check_ip("http://proxy:8080")
        assert result == {"ip": "1.2.3.4"}

    @patch("checks.requests.get", side_effect=Exception("timeout"))
    def test_failure(self, mock_get):
        result = check_ip("http://bad-proxy:8080")
        assert result == {"ip": None}


class TestCheckQuality:
    @patch("checks.requests.get")
    def test_pass(self, mock_get):
        mock_get.return_value.json.return_value = {"fraud_score": 20}
        mock_get.return_value.raise_for_status = MagicMock()
        result = check_quality("1.2.3.4", 70)
        assert result["fraud_score_inverted"] == 80
        assert result["quality_pass"] is True
        assert result["quality_threshold"] == 70

    @patch("checks.requests.get")
    def test_fail(self, mock_get):
        mock_get.return_value.json.return_value = {"fraud_score": 50}
        mock_get.return_value.raise_for_status = MagicMock()
        result = check_quality("1.2.3.4", 70)
        assert result["fraud_score_inverted"] == 50
        assert result["quality_pass"] is False

    @patch("checks.requests.get")
    def test_exact_threshold(self, mock_get):
        mock_get.return_value.json.return_value = {"fraud_score": 30}
        mock_get.return_value.raise_for_status = MagicMock()
        result = check_quality("1.2.3.4", 70)
        assert result["fraud_score_inverted"] == 70
        assert result["quality_pass"] is False  # > not >=

    @patch("checks.requests.get", side_effect=Exception("API down"))
    def test_api_error(self, mock_get):
        result = check_quality("1.2.3.4")
        assert result["quality_pass"] is False
        assert result["fraud_score_inverted"] is None


class TestCheckLocation:
    @patch("checks.requests.get")
    def test_match(self, mock_get):
        mock_get.return_value.json.return_value = {"timezone": "Europe/Paris"}
        mock_get.return_value.raise_for_status = MagicMock()
        result = check_location("1.2.3.4", "Europe")
        assert result["location_match"] is True

    @patch("checks.requests.get")
    def test_no_match(self, mock_get):
        mock_get.return_value.json.return_value = {"timezone": "America/New_York"}
        mock_get.return_value.raise_for_status = MagicMock()
        result = check_location("1.2.3.4", "Europe")
        assert result["location_match"] is False

    @patch("checks.requests.get")
    def test_case_insensitive(self, mock_get):
        mock_get.return_value.json.return_value = {"timezone": "EUROPE/PARIS"}
        mock_get.return_value.raise_for_status = MagicMock()
        result = check_location("1.2.3.4", "europe")
        assert result["location_match"] is True

    @patch("checks.requests.get", side_effect=Exception("network error"))
    def test_api_error(self, mock_get):
        result = check_location("1.2.3.4", "Europe")
        assert result["location_match"] is False
        assert "error" in result


class TestRunChecks:
    @patch("checks.check_location")
    @patch("checks.check_quality")
    def test_all_pass(self, mock_quality, mock_location):
        mock_quality.return_value = {"fraud_score_inverted": 90, "quality_pass": True, "quality_threshold": 70}
        mock_location.return_value = {"location_match": True, "actual_timezone": "Europe/Paris", "expected_location": "Europe"}
        passed, result = run_checks("proxy", "1.2.3.4", True, True, "Europe", 70)
        assert passed is True

    @patch("checks.check_quality")
    def test_quality_fail(self, mock_quality):
        mock_quality.return_value = {"fraud_score_inverted": 40, "quality_pass": False, "quality_threshold": 70}
        passed, result = run_checks("proxy", "1.2.3.4", True, False, None, 70)
        assert passed is False

    def test_no_ip_quality(self):
        passed, result = run_checks("proxy", None, True, False, None, 70)
        assert passed is False
        assert "error" in result["verify_quality"]

    def test_no_location_param(self):
        passed, result = run_checks("proxy", "1.2.3.4", False, True, None, 70)
        assert passed is False
        assert "proxy_location parameter is required" in result["verify_location"]["error"]

    def test_no_ip_location(self):
        passed, result = run_checks("proxy", None, False, True, "Europe", 70)
        assert passed is False
        assert "IP not resolved" in result["verify_location"]["error"]

    def test_no_checks(self):
        passed, result = run_checks("proxy", "1.2.3.4", False, False, None, 70)
        assert passed is True
        assert result == {}


class TestRunChecksFullCombinatorics:
    """Test every meaningful combination of (verify_quality, verify_location, ip, proxy_location)."""

    @patch("checks.check_location")
    @patch("checks.check_quality")
    def test_quality_pass_location_fail(self, mock_q, mock_l):
        mock_q.return_value = {"fraud_score_inverted": 90, "quality_pass": True, "quality_threshold": 70}
        mock_l.return_value = {"location_match": False, "actual_timezone": "America/NY", "expected_location": "Europe"}
        passed, result = run_checks("p", "1.2.3.4", True, True, "Europe", 70)
        assert passed is False
        assert result["verify_quality"]["quality_pass"] is True
        assert result["verify_location"]["location_match"] is False

    @patch("checks.check_location")
    @patch("checks.check_quality")
    def test_quality_fail_location_pass(self, mock_q, mock_l):
        mock_q.return_value = {"fraud_score_inverted": 30, "quality_pass": False, "quality_threshold": 70}
        mock_l.return_value = {"location_match": True, "actual_timezone": "Europe/Paris", "expected_location": "Europe"}
        passed, result = run_checks("p", "1.2.3.4", True, True, "Europe", 70)
        assert passed is False

    @patch("checks.check_location")
    @patch("checks.check_quality")
    def test_both_fail(self, mock_q, mock_l):
        mock_q.return_value = {"fraud_score_inverted": 20, "quality_pass": False, "quality_threshold": 70}
        mock_l.return_value = {"location_match": False, "actual_timezone": "Asia/Tokyo", "expected_location": "Europe"}
        passed, result = run_checks("p", "1.2.3.4", True, True, "Europe", 70)
        assert passed is False

    def test_no_ip_both_checks(self):
        """With no IP, both quality and location should fail."""
        passed, result = run_checks("p", None, True, True, "Europe", 70)
        assert passed is False
        assert result["verify_quality"]["quality_pass"] is False
        assert result["verify_location"]["location_match"] is False

    @patch("checks.check_quality")
    def test_quality_only_no_location(self, mock_q):
        """Only quality check enabled, location disabled."""
        mock_q.return_value = {"fraud_score_inverted": 80, "quality_pass": True, "quality_threshold": 70}
        passed, result = run_checks("p", "1.2.3.4", True, False, None, 70)
        assert passed is True
        assert "verify_location" not in result

    @patch("checks.check_location")
    def test_location_only_no_quality(self, mock_l):
        """Only location check enabled, quality disabled."""
        mock_l.return_value = {"location_match": True, "actual_timezone": "Europe/Paris", "expected_location": "Europe"}
        passed, result = run_checks("p", "1.2.3.4", False, True, "Europe", 70)
        assert passed is True
        assert "verify_quality" not in result


class TestCheckQualityEdgeCases:
    @patch("checks.requests.get")
    def test_fraud_score_zero(self, mock_get):
        """fraud_score=0 should give inverted=100, which is > any reasonable threshold."""
        mock_get.return_value.json.return_value = {"fraud_score": 0}
        mock_get.return_value.raise_for_status = MagicMock()
        result = check_quality("1.2.3.4", 70)
        assert result["fraud_score_inverted"] == 100
        assert result["quality_pass"] is True

    @patch("checks.requests.get")
    def test_fraud_score_100(self, mock_get):
        """fraud_score=100 (worst) should give inverted=0, always fails."""
        mock_get.return_value.json.return_value = {"fraud_score": 100}
        mock_get.return_value.raise_for_status = MagicMock()
        result = check_quality("1.2.3.4", 0)
        assert result["fraud_score_inverted"] == 0
        assert result["quality_pass"] is False  # 0 > 0 is False

    @patch("checks.requests.get")
    def test_threshold_zero(self, mock_get):
        """With threshold=0, almost any fraud_score should pass (inverted > 0)."""
        mock_get.return_value.json.return_value = {"fraud_score": 99}
        mock_get.return_value.raise_for_status = MagicMock()
        result = check_quality("1.2.3.4", 0)
        assert result["fraud_score_inverted"] == 1
        assert result["quality_pass"] is True


class TestCheckLocationEdgeCases:
    @patch("checks.requests.get")
    def test_partial_match(self, mock_get):
        """'Paris' is 'in' 'Europe/Paris' — verify substring matching."""
        mock_get.return_value.json.return_value = {"timezone": "Europe/Paris"}
        mock_get.return_value.raise_for_status = MagicMock()
        result = check_location("1.2.3.4", "Paris")
        assert result["location_match"] is True

    @patch("checks.requests.get")
    def test_empty_timezone_from_api(self, mock_get):
        """If the API returns an empty timezone, no location should match."""
        mock_get.return_value.json.return_value = {"timezone": ""}
        mock_get.return_value.raise_for_status = MagicMock()
        result = check_location("1.2.3.4", "Europe")
        assert result["location_match"] is False

    @patch("checks.requests.get")
    def test_missing_timezone_key(self, mock_get):
        """If 'timezone' key is absent, should default to empty string and not crash."""
        mock_get.return_value.json.return_value = {}
        mock_get.return_value.raise_for_status = MagicMock()
        result = check_location("1.2.3.4", "Europe")
        assert result["location_match"] is False
