import os
import pymssql
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

SQL_SERVER_USER = os.getenv('SQL_SERVER_USER')
SQL_SERVER_PASSWORD = os.getenv('SQL_SERVER_PASSWORD')
SQL_SERVER_DB = os.getenv('SQL_SERVER_DB')
SQL_SERVER_NAME = os.getenv('SQL_SERVER_NAME')

TABLES = [
    """
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='armada_jobs' AND xtype='U')
    CREATE TABLE armada_jobs (
        job_uuid VARCHAR(255),
        run_uuid VARCHAR(255),
        job_datetime DATETIME,
        job_associated_agent VARCHAR(255),
        job_status VARCHAR(255)
    )
    """,
    """
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='armada_fingerprints' AND xtype='U')
    CREATE TABLE armada_fingerprints (
        antibot_vendor VARCHAR(255),
        website VARCHAR(255),
        data VARCHAR(MAX),
        collecting_date DATE
    )
    """,
    """
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='armada_runs' AND xtype='U')
    CREATE TABLE armada_runs (
        run_uuid VARCHAR(255),
        run_datetime DATETIME
    )
    """,
    """
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='armada_events' AND xtype='U')
    CREATE TABLE armada_events (
        event_uuid VARCHAR(255),
        event_content VARCHAR(255),
        job_uuid VARCHAR(255),
        event_datetime DATETIME,
        event_status VARCHAR(255)
    )
    """,
    """
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='armada_proxies' AND xtype='U')
    CREATE TABLE armada_proxies (
        proxy_url VARCHAR(255),
        proxy_provider_name VARCHAR(255),
        proxy_type VARCHAR(255),
        proxy_rotation_strategy VARCHAR(255),
        proxy_location VARCHAR(255)
    )
    """,
    """
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='armada_output' AND xtype='U')
    CREATE TABLE armada_output (
        run_uuid VARCHAR(255),
        data VARCHAR(MAX),
        timestamp DATETIME
    )
    """,
]


def bootstrap():
    conn = pymssql.connect(
        server=SQL_SERVER_NAME,
        user=SQL_SERVER_USER,
        password=SQL_SERVER_PASSWORD,
        database=SQL_SERVER_DB,
    )
    cursor = conn.cursor()

    for ddl in TABLES:
        cursor.execute(ddl)

    conn.commit()
    conn.close()
    print("Bootstrap done – all tables verified/created.")


if __name__ == '__main__':
    bootstrap()
