import pymssql
import os
import functools


def database_enabled(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.enabled:
            return None
        return func(self, *args, **kwargs)
    return wrapper


class DatabaseConnector:
    def __init__(self):
        self.enabled = 1
        self._credentials_loaded = False

    @database_enabled
    def _load_credentials(self):
        if self._credentials_loaded:
            return
        self.server = os.getenv('SQL_SERVER_NAME')
        self.database = os.getenv('SQL_SERVER_DB')
        self.username = os.getenv('SQL_SERVER_USER')
        self.password_db = os.getenv('SQL_SERVER_PASSWORD')
        self._credentials_loaded = True

    def _connect(self, autocommit=False):
        return pymssql.connect(
            server=self.server,
            user=self.username,
            password=self.password_db,
            database=self.database,
            port=1433,
            autocommit=autocommit
        )

    @database_enabled
    def post_to_db(self, query, *args):
        self._load_credentials()
        connection = self._connect()
        cursor = connection.cursor()
        cursor.execute(query, args)
        connection.commit()
        cursor.close()
        connection.close()

    @database_enabled
    def select_from_db(self, query, *args):
        self._load_credentials()
        connection = self._connect()
        cursor = connection.cursor()
        cursor.execute(query, args)
        results = cursor.fetchall()
        cursor.close()
        connection.close()
        return results

    @database_enabled
    def select_with_commit_from_db(self, query, *args):
        self._load_credentials()
        connection = self._connect(autocommit=True)
        cursor = connection.cursor()
        cursor.execute(query, args)
        results = cursor.fetchall()
        cursor.close()
        connection.close()
        return results
