import pytest
from unittest.mock import patch, MagicMock

# Mock DB_CONFIG before importing the module
with patch.dict("os.environ", {
    "SQL_SERVER_NAME": "test-server",
    "SQL_SERVER_USER": "test-user",
    "SQL_SERVER_PASSWORD": "test-pass",
    "SQL_SERVER_DB": "test-db",
}):
    from app.db import Database


class TestDatabaseConnect:
    @patch("pymssql.connect")
    def test_connect(self, mock_connect):
        db = Database()
        conn = db._connect()
        mock_connect.assert_called_once()
        assert conn is mock_connect.return_value


@patch.object(Database, '_connect')
class TestFetchAll:
    def test_returns_rows(self, mock_connect):
        db = Database()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{"col": "val1"}, {"col": "val2"}]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = db._fetchall("SELECT * FROM t")
        assert result == [{"col": "val1"}, {"col": "val2"}]
        mock_conn.cursor.assert_called_with(as_dict=True)
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_with_params(self, mock_connect):
        db = Database()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        db._fetchall("SELECT * FROM t WHERE id = %s", ("123",))
        mock_cursor.execute.assert_called_once_with("SELECT * FROM t WHERE id = %s", ("123",))


@patch.object(Database, '_connect')
class TestFetchOne:
    def test_returns_row(self, mock_connect):
        db = Database()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"col": "val"}
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = db._fetchone("SELECT TOP 1 * FROM t")
        assert result == {"col": "val"}
        mock_conn.close.assert_called_once()

    def test_returns_none(self, mock_connect):
        db = Database()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = db._fetchone("SELECT TOP 1 * FROM t WHERE 1=0")
        assert result is None


@patch.object(Database, '_connect')
class TestExecute:
    def test_commits_on_success(self, mock_connect):
        db = Database()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        db._execute("INSERT INTO t VALUES (%s)", ("val",))
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_rollback_on_error(self, mock_connect):
        db = Database()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("SQL Error")
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        with pytest.raises(Exception, match="SQL Error"):
            db._execute("BAD SQL")
        mock_conn.rollback.assert_called_once()
        mock_conn.close.assert_called_once()


@patch.object(Database, '_connect')
class TestAsyncWrappers:
    @pytest.mark.asyncio
    async def test_async_fetchall(self, mock_connect):
        db = Database()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{"a": 1}]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = await db.fetchall("SELECT 1")
        assert result == [{"a": 1}]

    @pytest.mark.asyncio
    async def test_async_fetchone(self, mock_connect):
        db = Database()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"a": 1}
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = await db.fetchone("SELECT 1")
        assert result == {"a": 1}

    @pytest.mark.asyncio
    async def test_async_execute(self, mock_connect):
        db = Database()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        await db.execute("INSERT INTO t VALUES (%s)", ("val",))
        mock_conn.commit.assert_called_once()
