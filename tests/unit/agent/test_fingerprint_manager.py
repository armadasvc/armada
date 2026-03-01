from unittest.mock import patch, MagicMock

from fingerprint_manager import FingerprintManager


class TestFingerprintManagerInit:
    def test_defaults(self):
        fm = FingerprintManager()
        assert fm.antibot_vendor == "arkose"
        assert fm.website == "X"
        assert fm.collection_date_day == "01"
        assert fm.collection_date_month == "01"
        assert fm.collection_date_year == "1900"

    def test_overrides(self):
        fm = FingerprintManager({
            "antibot_vendor": "recaptcha",
            "website": "Google",
            "collection_date_year": "2024",
        })
        assert fm.antibot_vendor == "recaptcha"
        assert fm.website == "Google"
        assert fm.collection_date_year == "2024"

    def test_partial_override(self):
        fm = FingerprintManager({"website": "Facebook"})
        assert fm.website == "Facebook"
        assert fm.antibot_vendor == "arkose"  # default


class TestGetFingerprint:
    @patch("fingerprint_manager.requests.get")
    def test_basic_call(self, mock_get):
        mock_get.return_value.text = "base64_fingerprint_data"
        fm = FingerprintManager({"antibot_vendor": "arkose", "website": "X"})
        result = fm.get_fingerprint()
        assert result == "base64_fingerprint_data"
        mock_get.assert_called_once()

    @patch("fingerprint_manager.requests.get")
    def test_with_additional_data(self, mock_get):
        mock_get.return_value.text = "fp_data"
        fm = FingerprintManager({"antibot_vendor": "arkose", "website": "X"})
        result = fm.get_fingerprint({"desired_ua": "Mozilla/5.0"})
        assert result == "fp_data"
        call_kwargs = mock_get.call_args[1]
        assert "additional_data" in call_kwargs["json"]
        assert call_kwargs["json"]["additional_data"]["desired_ua"] == "Mozilla/5.0"

    @patch("fingerprint_manager.requests.get")
    def test_without_additional_data(self, mock_get):
        mock_get.return_value.text = "fp_data"
        fm = FingerprintManager({"antibot_vendor": "arkose"})
        fm.get_fingerprint()
        call_kwargs = mock_get.call_args[1]
        assert "additional_data" not in call_kwargs["json"]

    @patch("fingerprint_manager.requests.get")
    @patch.dict("os.environ", {"FINGERPRINT_PROVIDER_URL": "http://custom:9999"})
    def test_custom_provider_url(self, mock_get):
        mock_get.return_value.text = "data"
        fm = FingerprintManager({"antibot_vendor": "arkose"})
        fm.get_fingerprint()
        url_called = mock_get.call_args[0][0]
        assert url_called.startswith("http://custom:9999")
