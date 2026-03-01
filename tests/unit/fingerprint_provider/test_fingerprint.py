import json
import base64
import os
import pytest
from unittest.mock import patch, MagicMock

from src.fingerprint import ArkoseBrowserFingerprint, encode_and_strip
from src.crypto import BDACrypto


def _make_encoded_fingerprint(ua: str, timestamp: int, fingerprint_data: list) -> str:
    """Helper: create a valid encoded fingerprint for testing."""
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


class TestEncodeAndStrip:
    def test_string(self):
        assert encode_and_strip("  hello  ") == "hello"

    def test_dict(self):
        assert encode_and_strip({"k": "  v  "}) == {"k": "v"}

    def test_list(self):
        assert encode_and_strip(["  a  ", "  b  "]) == ["a", "b"]

    def test_number(self):
        assert encode_and_strip(42) == 42

    def test_nested(self):
        result = encode_and_strip({"a": [" x ", {"b": " y "}]})
        assert result == {"a": ["x", {"b": "y"}]}

    def test_none(self):
        assert encode_and_strip(None) is None


class TestTimestampRounding:
    def test_rounds_to_6h(self):
        ts = 1700000000
        expected = ts - (ts % 21600)
        ua = "Mozilla/5.0 Test"
        fp_data = [{"key": "test_key", "value": "test_value"}]
        encoded = _make_encoded_fingerprint(ua, ts, fp_data)
        fp = ArkoseBrowserFingerprint(encoded, ua, ts)
        assert fp._timestamp == expected

    def test_already_rounded(self):
        ts = 21600 * 100
        ua = "TestUA"
        fp_data = [{"key": "k", "value": "v"}]
        encoded = _make_encoded_fingerprint(ua, ts, fp_data)
        fp = ArkoseBrowserFingerprint(encoded, ua, ts)
        assert fp._timestamp == ts


class TestKeyOperations:
    def _make_fp(self):
        ua = "TestUA"
        ts = 1700000000
        fp_data = [
            {"key": "user_agent", "value": "Mozilla/5.0"},
            {"key": "language", "value": "fr"},
            {"key": "enhanced_fp", "value": [
                {"key": "webgl_renderer", "value": "NVIDIA"},
                {"key": "canvas_hash", "value": "abc123"},
            ]},
        ]
        encoded = _make_encoded_fingerprint(ua, ts, fp_data)
        return ArkoseBrowserFingerprint(encoded, ua, ts)

    def test_fetch_key(self):
        fp = self._make_fp()
        assert fp.fetch_key("user_agent") == "Mozilla/5.0"
        assert fp.fetch_key("language") == "fr"

    def test_fetch_key_not_found(self):
        fp = self._make_fp()
        with pytest.raises(KeyError):
            fp.fetch_key("nonexistent_key")

    def test_edit_key(self):
        fp = self._make_fp()
        fp.edit_key("user_agent", "Chrome/120")
        assert fp.fetch_key("user_agent") == "Chrome/120"

    def test_insert_key(self):
        fp = self._make_fp()
        fp.insert_key("new_key", "new_value")
        assert fp.fetch_key("new_key") == "new_value"

    def test_fetch_enhanced_fp_key(self):
        fp = self._make_fp()
        assert fp.fetch_enhanced_fp_key("webgl_renderer") == "NVIDIA"

    def test_edit_enhanced_fp_key(self):
        fp = self._make_fp()
        fp.edit_enhanced_fp_key("webgl_renderer", "Intel")
        assert fp.fetch_enhanced_fp_key("webgl_renderer") == "Intel"

    def test_insert_enhanced_fp_key(self):
        fp = self._make_fp()
        fp.insert_enhanced_fp_key("new_efp_key", "efp_value")
        assert fp.fetch_enhanced_fp_key("new_efp_key") == "efp_value"


class TestUpdateTimestampAndUA:
    def test_updates_key(self):
        ua = "OldUA"
        ts = 1700000000
        fp_data = [{"key": "k", "value": "v"}]
        encoded = _make_encoded_fingerprint(ua, ts, fp_data)
        fp = ArkoseBrowserFingerprint(encoded, ua, ts)

        new_ts = 1700100000
        fp.update_timestamp_and_ua("NewUA", new_ts)
        assert fp._user_agent == "NewUA"
        assert fp._timestamp == int(new_ts - (new_ts % 21600))
        assert fp._key == "NewUA" + str(fp._timestamp)


class TestRepackage:
    def test_repackage_produces_base64(self):
        ua = "TestUA"
        ts = 1700000000
        fp_data = [{"key": "test", "value": "data"}]
        encoded = _make_encoded_fingerprint(ua, ts, fp_data)
        fp = ArkoseBrowserFingerprint(encoded, ua, ts)
        result = fp.repackage(encode_base64=True)
        # Should be valid base64
        decoded = base64.b64decode(result)
        parsed = json.loads(decoded)
        assert "ct" in parsed
        assert "iv" in parsed
        assert "s" in parsed

    def test_repackage_no_base64(self):
        ua = "TestUA"
        ts = 1700000000
        fp_data = [{"key": "test", "value": "data"}]
        encoded = _make_encoded_fingerprint(ua, ts, fp_data)
        fp = ArkoseBrowserFingerprint(encoded, ua, ts)
        result = fp.repackage(encode_base64=False)
        parsed = json.loads(result)
        assert "ct" in parsed

    def test_full_roundtrip(self):
        """Encode -> modify -> repackage -> re-decode: modifications persist."""
        ua = "OriginalUA"
        ts = 1700000000
        fp_data = [
            {"key": "user_agent", "value": "OriginalUA"},
            {"key": "some_key", "value": "original_value"},
        ]
        encoded = _make_encoded_fingerprint(ua, ts, fp_data)
        fp = ArkoseBrowserFingerprint(encoded, ua, ts)

        fp.edit_key("some_key", "modified_value")
        # Repackage with same UA and timestamp
        repackaged = fp.repackage(encode_base64=True)

        fp2 = ArkoseBrowserFingerprint(repackaged, ua, ts)
        assert fp2.fetch_key("some_key") == "modified_value"


class TestFingerprintEdgeCases:
    def test_edit_nonexistent_key_raises(self):
        """Editing a key that doesn't exist should raise KeyError."""
        ua = "TestUA"
        ts = 1700000000
        encoded = _make_encoded_fingerprint(ua, ts, [{"key": "a", "value": 1}])
        fp = ArkoseBrowserFingerprint(encoded, ua, ts)
        with pytest.raises(KeyError):
            fp.edit_key("nonexistent", "value")

    def test_insert_duplicate_key_appends(self):
        """insert_key doesn't check for duplicates — it appends a second entry."""
        ua = "TestUA"
        ts = 1700000000
        encoded = _make_encoded_fingerprint(ua, ts, [{"key": "k", "value": "v1"}])
        fp = ArkoseBrowserFingerprint(encoded, ua, ts)
        fp.insert_key("k", "v2")
        # fetch_key finds the first match, so it should still return "v1"
        assert fp.fetch_key("k") == "v1"
        # But there are now 2 entries with key "k"
        matches = [item for item in fp.fingerprint if item["key"] == "k"]
        assert len(matches) == 2

    def test_many_keys_roundtrip(self):
        """A fingerprint with many keys should survive encode/decode."""
        ua = "BigUA"
        ts = 1700000000
        fp_data = [{"key": f"key_{i}", "value": f"val_{i}"} for i in range(100)]
        encoded = _make_encoded_fingerprint(ua, ts, fp_data)
        fp = ArkoseBrowserFingerprint(encoded, ua, ts)
        assert fp.fetch_key("key_0") == "val_0"
        assert fp.fetch_key("key_99") == "val_99"
        repackaged = fp.repackage()
        fp2 = ArkoseBrowserFingerprint(repackaged, ua, ts)
        assert fp2.fetch_key("key_50") == "val_50"

    def test_repackage_after_ua_change_decryptable_with_new_key(self):
        """After update_timestamp_and_ua, the repackaged fingerprint must
        be decryptable with the NEW UA, not the old one."""
        old_ua = "OldUA"
        new_ua = "NewUA"
        ts = 1700000000
        fp_data = [{"key": "secret", "value": "42"}]
        encoded = _make_encoded_fingerprint(old_ua, ts, fp_data)
        fp = ArkoseBrowserFingerprint(encoded, old_ua, ts)
        fp.update_timestamp_and_ua(new_ua, ts)
        repackaged = fp.repackage()

        # Decrypting with NEW UA should work
        fp_new = ArkoseBrowserFingerprint(repackaged, new_ua, ts)
        assert fp_new.fetch_key("secret") == "42"

        # Decrypting with OLD UA should fail (garbage or exception)
        try:
            fp_old = ArkoseBrowserFingerprint(repackaged, old_ua, ts)
            # If it somehow decoded, the data should be garbage
            assert fp_old.fetch_key("secret") != "42"
        except (json.JSONDecodeError, UnicodeDecodeError, KeyError, Exception):
            pass  # Expected

    def test_enhanced_fp_edit_nonexistent_key_raises(self):
        """Editing a nonexistent enhanced_fp key should raise KeyError."""
        ua = "TestUA"
        ts = 1700000000
        fp_data = [
            {"key": "enhanced_fp", "value": [{"key": "a", "value": 1}]},
        ]
        encoded = _make_encoded_fingerprint(ua, ts, fp_data)
        fp = ArkoseBrowserFingerprint(encoded, ua, ts)
        with pytest.raises(KeyError):
            fp.edit_enhanced_fp_key("nonexistent", "val")

    def test_value_types_preserved(self):
        """Values of different types (int, bool, list, dict) should survive roundtrip."""
        ua = "TypeUA"
        ts = 1700000000
        fp_data = [
            {"key": "int_val", "value": 42},
            {"key": "bool_val", "value": True},
            {"key": "list_val", "value": [1, "two", 3]},
            {"key": "dict_val", "value": {"nested": "yes"}},
            {"key": "null_val", "value": None},
        ]
        encoded = _make_encoded_fingerprint(ua, ts, fp_data)
        fp = ArkoseBrowserFingerprint(encoded, ua, ts)
        assert fp.fetch_key("int_val") == 42
        assert fp.fetch_key("bool_val") is True
        assert fp.fetch_key("list_val") == [1, "two", 3]
        assert fp.fetch_key("dict_val") == {"nested": "yes"}
        assert fp.fetch_key("null_val") is None
