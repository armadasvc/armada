"""
Database layer — pymssql to SQL Server.

pymssql is synchronous, so each call is wrapped with asyncio.to_thread()
to avoid blocking FastAPI's async event loop.

Usage in a router:
    from app.db import db

    rows = await db.fetchall("SELECT * FROM armada_events")
    row  = await db.fetchone("SELECT * FROM armada_events WHERE event_uuid = %s", (uuid,))
    await db.execute("INSERT INTO armada_events (event_uuid, event_content) VALUES (%s, %s)", (uuid, content))
"""

import asyncio
import pymssql
import os
def load_env():
    try:
        from dotenv import find_dotenv, dotenv_values
        env_file = find_dotenv(usecwd=True)
        if env_file:
            return {**os.environ, **dotenv_values(env_file)}
    except ImportError:
        pass
    return os.environ

env_values = load_env()

DB_CONFIG = {
    "server": env_values["SQL_SERVER_NAME"],
    "user": env_values["SQL_SERVER_USER"],
    "password": env_values["SQL_SERVER_PASSWORD"],
    "database": env_values["SQL_SERVER_DB"],
}

# --- SQL Server connection config ---
DB_HOST = DB_CONFIG["server"]
DB_USER = DB_CONFIG["user"]
DB_PASSWORD = DB_CONFIG["password"]
DB_NAME = DB_CONFIG["database"]


class Database:
    def _connect(self) -> pymssql.Connection:
        return pymssql.connect(
            server=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
        )

    def _fetchall(self, query: str, params: tuple = ()) -> list[dict]:
        conn = self._connect()
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            return rows
        finally:
            conn.close()

    def _fetchone(self, query: str, params: tuple = ()) -> dict | None:
        conn = self._connect()
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.execute(query, params)
            row = cursor.fetchone()
            cursor.close()
            return row
        finally:
            conn.close()

    def _execute(self, query: str, params: tuple = ()):
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            cursor.close()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # --- Async versions (wrap sync methods with to_thread) ---

    async def fetchall(self, query: str, params: tuple = ()) -> list[dict]:
        return await asyncio.to_thread(self._fetchall, query, params)

    async def fetchone(self, query: str, params: tuple = ()) -> dict | None:
        return await asyncio.to_thread(self._fetchone, query, params)

    async def execute(self, query: str, params: tuple = ()):
        return await asyncio.to_thread(self._execute, query, params)


# Global instance — importable from any router
db = Database()
