import json
import base64
import os
from unittest.mock import patch, MagicMock

from src.forge_arkose_fingerprint import generate, forge_arkose_fingerprint
from src.crypto import BDACrypto


def _make_encoded_fingerprint(ua: str, timestamp: int, fingerprint_data: list) -> str:
    ts_rounded = int(timestamp - (timestamp % 21600))
    key = ua + str(ts_rounded)
    crypto = BDACrypto(key)
    salt = os.urandom(8).hex()
    iv = os.urandom(16).hex()
    fp_json = json.dumps(fingerprint_data, separators=(",", ":"))
    fp_data = {"iv": iv, "s": salt, "ct": ""}
    encrypted = crypto.re_encrypt(fp_json, fp_data)
    raw = json.dumps(encrypted, separators=(",", ":"), sort_keys=True)
    return base64.b64encode(raw.encode()).decode()


class TestGenerate:
    def test_returns_base64_string(self):
        ua = "OriginalUA"
        ts = 1700000000
        fp_data = [{"key": "user_agent", "value": ua}]
        encoded = _make_encoded_fingerprint(ua, ts, fp_data)

        result = generate(ua, "NewUA", encoded, ts)
        assert isinstance(result, str)
        # Should be valid base64
        decoded = base64.b64decode(result)
        parsed = json.loads(decoded)
        assert "ct" in parsed


class TestForgeArkoseFingerprint:
    def test_with_mock(self):
        with patch("src.forge_arkose_fingerprint.ArkoseBrowserFingerprint") as MockFP:
            mock_instance = MockFP.return_value
            mock_instance.repackage.return_value = "new_bda_base64"

            result = forge_arkose_fingerprint(
                {"ua": "old_ua", "bda": "encoded_bda", "ts": "1700000000"},
                "new_ua",
            )

            MockFP.assert_called_once_with("encoded_bda", "old_ua", 1700000000)
            mock_instance.update_timestamp_and_ua.assert_called_once_with("new_ua")
            mock_instance.repackage.assert_called_once()
            assert result == "new_bda_base64"

    def test_end_to_end(self):
        ua = "OriginalUA"
        ts = 1700000000
        fp_data = [{"key": "user_agent", "value": ua}, {"key": "lang", "value": "fr"}]
        encoded = _make_encoded_fingerprint(ua, ts, fp_data)

        result = forge_arkose_fingerprint(
            {"ua": ua, "bda": encoded, "ts": str(ts)},
            "NewUA",
        )
        assert isinstance(result, str)
        assert len(result) > 0
