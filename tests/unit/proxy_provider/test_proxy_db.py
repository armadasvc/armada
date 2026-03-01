from unittest.mock import patch, MagicMock

from db import build_proxy_query, fetch_random_proxy


class TestBuildProxyQuery:
    def test_empty_filters(self):
        query, params = build_proxy_query({})
        assert query == "SELECT TOP 1 proxy_url FROM armada_proxies ORDER BY NEWID()"
        assert params == ()

    def test_with_filters(self):
        query, params = build_proxy_query({
            "proxy_provider_name": "provider_a",
            "proxy_type": "residential",
        })
        assert "proxy_provider_name = %s" in query
        assert "proxy_type = %s" in query
        assert params == ("provider_a", "residential")

    def test_none_values_ignored(self):
        query, params = build_proxy_query({
            "proxy_provider_name": "provider_a",
            "proxy_location": None,
        })
        assert "proxy_provider_name = %s" in query
        assert "proxy_location" not in query
        assert params == ("provider_a",)

    def test_all_none(self):
        query, params = build_proxy_query({
            "proxy_provider_name": None,
            "proxy_type": None,
        })
        assert "WHERE" not in query
        assert params == ()


class TestFetchRandomProxy:
    @patch("db.get_connection")
    def test_found(self, mock_get_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("http://proxy:8080",)
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        result = fetch_random_proxy("SELECT TOP 1 proxy_url FROM armada_proxies", ())
        assert result == "http://proxy:8080"
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("db.get_connection")
    def test_not_found(self, mock_get_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        result = fetch_random_proxy("SELECT TOP 1 proxy_url FROM armada_proxies", ())
        assert result is None
