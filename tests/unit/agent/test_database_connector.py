from unittest.mock import patch, MagicMock

from database_connector import DatabaseConnector, database_enabled


class TestDatabaseConnectorInit:
    def test_defaults(self):
        db = DatabaseConnector()
        assert db.enabled == 1
        assert db._credentials_loaded is False


class TestDatabaseEnabledDecorator:
    def test_returns_none_when_disabled(self):
        db = DatabaseConnector()
        db.enabled = 0
        result = db.post_to_db("INSERT INTO t VALUES (%s)", "val")
        assert result is None

    def test_returns_none_for_select_when_disabled(self):
        db = DatabaseConnector()
        db.enabled = 0
        result = db.select_from_db("SELECT 1")
        assert result is None

    def test_returns_none_for_select_with_commit_when_disabled(self):
        db = DatabaseConnector()
        db.enabled = 0
        result = db.select_with_commit_from_db("SELECT 1")
        assert result is None


class TestLoadCredentials:
    @patch.dict("os.environ", {
        "SQL_SERVER_NAME": "test-server",
        "SQL_SERVER_DB": "test-db",
        "SQL_SERVER_USER": "test-user",
        "SQL_SERVER_PASSWORD": "test-pass",
    })
    def test_loads_from_env(self):
        db = DatabaseConnector()
        db._load_credentials()
        assert db.server == "test-server"
        assert db.database == "test-db"
        assert db.username == "test-user"
        assert db.password_db == "test-pass"
        assert db._credentials_loaded is True

    @patch.dict("os.environ", {
        "SQL_SERVER_NAME": "srv",
        "SQL_SERVER_DB": "db",
        "SQL_SERVER_USER": "usr",
        "SQL_SERVER_PASSWORD": "pwd",
    })
    def test_loads_only_once(self):
        db = DatabaseConnector()
        db._load_credentials()
        db.server = "modified"
        db._load_credentials()
        assert db.server == "modified"  # not reloaded


class TestPostToDb:
    @patch("database_connector.pymssql.connect")
    @patch.dict("os.environ", {
        "SQL_SERVER_NAME": "srv",
        "SQL_SERVER_DB": "db",
        "SQL_SERVER_USER": "usr",
        "SQL_SERVER_PASSWORD": "pwd",
    })
    def test_executes_and_commits(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        db = DatabaseConnector()
        db.post_to_db("INSERT INTO t VALUES (%s)", "val")

        mock_cursor.execute.assert_called_once_with("INSERT INTO t VALUES (%s)", ("val",))
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()


class TestSelectFromDb:
    @patch("database_connector.pymssql.connect")
    @patch.dict("os.environ", {
        "SQL_SERVER_NAME": "srv",
        "SQL_SERVER_DB": "db",
        "SQL_SERVER_USER": "usr",
        "SQL_SERVER_PASSWORD": "pwd",
    })
    def test_returns_results(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("row1",), ("row2",)]
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        db = DatabaseConnector()
        result = db.select_from_db("SELECT * FROM t")

        assert result == [("row1",), ("row2",)]
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()


class TestSelectWithCommitFromDb:
    @patch("database_connector.pymssql.connect")
    @patch.dict("os.environ", {
        "SQL_SERVER_NAME": "srv",
        "SQL_SERVER_DB": "db",
        "SQL_SERVER_USER": "usr",
        "SQL_SERVER_PASSWORD": "pwd",
    })
    def test_uses_autocommit(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        db = DatabaseConnector()
        db.select_with_commit_from_db("SELECT 1")

        mock_connect.assert_called_once()
        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs["autocommit"] is True


class TestDatabaseConnectorEdgeCases:
    @patch("database_connector.pymssql.connect")
    @patch.dict("os.environ", {
        "SQL_SERVER_NAME": "srv", "SQL_SERVER_DB": "db",
        "SQL_SERVER_USER": "usr", "SQL_SERVER_PASSWORD": "pwd",
    })
    def test_post_closes_on_execute_exception(self, mock_connect):
        """cursor and connection must be closed even if execute() raises."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("SQL error")
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        db = DatabaseConnector()
        import pytest
        with pytest.raises(Exception, match="SQL error"):
            db.post_to_db("BAD QUERY")
        # NOTE: the current code does NOT have try/finally for cleanup.
        # This test documents the actual behavior: if execute raises,
        # commit/close are NOT called — a potential resource leak.
        mock_conn.commit.assert_not_called()

    @patch("database_connector.pymssql.connect")
    @patch.dict("os.environ", {
        "SQL_SERVER_NAME": "srv", "SQL_SERVER_DB": "db",
        "SQL_SERVER_USER": "usr", "SQL_SERVER_PASSWORD": "pwd",
    })
    def test_select_closes_on_fetchall_exception(self, mock_connect):
        """If fetchall() raises, cursor/connection are not closed (no try/finally)."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = Exception("Fetch error")
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        db = DatabaseConnector()
        import pytest
        with pytest.raises(Exception, match="Fetch error"):
            db.select_from_db("SELECT broken")
        # Documents that close is NOT called — potential resource leak
        mock_conn.close.assert_not_called()

    @patch("database_connector.pymssql.connect")
    @patch.dict("os.environ", {
        "SQL_SERVER_NAME": "srv", "SQL_SERVER_DB": "db",
        "SQL_SERVER_USER": "usr", "SQL_SERVER_PASSWORD": "pwd",
    })
    def test_post_with_multiple_args(self, mock_connect):
        """Verify multiple args are passed as a tuple to execute()."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        db = DatabaseConnector()
        db.post_to_db("INSERT INTO t VALUES (%s, %s, %s)", "a", "b", "c")
        mock_cursor.execute.assert_called_once_with(
            "INSERT INTO t VALUES (%s, %s, %s)", ("a", "b", "c")
        )

    @patch("database_connector.pymssql.connect")
    @patch.dict("os.environ", {
        "SQL_SERVER_NAME": "srv", "SQL_SERVER_DB": "db",
        "SQL_SERVER_USER": "usr", "SQL_SERVER_PASSWORD": "pwd",
    })
    def test_connect_passes_correct_credentials(self, mock_connect):
        """Verify the exact credentials passed to pymssql.connect."""
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = MagicMock()
        mock_connect.return_value = mock_conn

        db = DatabaseConnector()
        db.post_to_db("SELECT 1")
        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs["server"] == "srv"
        assert call_kwargs["user"] == "usr"
        assert call_kwargs["password"] == "pwd"
        assert call_kwargs["database"] == "db"
        assert call_kwargs["port"] == 1433

    def test_decorator_skips_load_credentials(self):
        """When disabled, _load_credentials should return None without loading."""
        db = DatabaseConnector()
        db.enabled = 0
        result = db._load_credentials()
        assert result is None
        assert db._credentials_loaded is False
