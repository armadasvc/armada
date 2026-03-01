import os
import pymssql
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

SQL_SERVER_USER = os.getenv('SQL_SERVER_USER')
SQL_SERVER_PASSWORD = os.getenv('SQL_SERVER_PASSWORD')
SQL_SERVER_DB = os.getenv('SQL_SERVER_DB')
SQL_SERVER_NAME = os.getenv('SQL_SERVER_NAME')


def get_connection():
    return pymssql.connect(
        server=SQL_SERVER_NAME,
        user=SQL_SERVER_USER,
        password=SQL_SERVER_PASSWORD,
        database=SQL_SERVER_DB,
    )
