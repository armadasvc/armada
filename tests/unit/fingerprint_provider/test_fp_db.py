import json
import sys
from unittest.mock import patch, MagicMock

import db as fp_db
from db import build_fingerprint_query, fetch_random_fingerprint


class TestBuildFingerprintQuery:
    def test_no_filters(self):
        query, params = build_fingerprint_query({})
        assert "WHERE" not in query
        assert "ORDER BY NEWID()" in query
        assert params == ()

    def test_with_filters(self):
        query, params = build_fingerprint_query({
            "antibot_vendor": "arkose",
            "website": "X",
        })
        assert "antibot_vendor = %s" in query
        assert "website = %s" in query
        assert params == ("arkose", "X")

    def test_collecting_date_uses_greater_than(self):
        query, params = build_fingerprint_query({
            "collecting_date": "2024-01-01",
        })
        assert "collecting_date > %s" in query
        assert params == ("2024-01-01",)

    def test_falsy_values_ignored(self):
        query, params = build_fingerprint_query({
            "antibot_vendor": "",
            "website": None,
            "collecting_date": 0,
        })
        assert "WHERE" not in query
        assert params == ()

    def test_mixed_filters(self):
        query, params = build_fingerprint_query({
            "antibot_vendor": "arkose",
            "website": "",
            "collecting_date": "2024-06-01",
        })
        assert "antibot_vendor = %s" in query
        assert "website" not in query
        assert "collecting_date > %s" in query
        assert params == ("arkose", "2024-06-01")


class TestFetchRandomFingerprint:
    @patch.object(fp_db, "get_connection")
    def test_returns_parsed_json(self, mock_get_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ('{"ua": "test", "bda": "data", "ts": "123"}',)
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        result = fetch_random_fingerprint("SELECT TOP 1 (data) FROM armada_fingerprints", ())
        assert result["ua"] == "test"
        assert result["bda"] == "data"
        assert result["ts"] == "123"
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()
