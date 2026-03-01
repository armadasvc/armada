import pymssql

from config import DB_CONFIG
import json


def get_connection():
    return pymssql.connect(
        server=DB_CONFIG["server"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
    )


def build_fingerprint_query(filters: dict) -> tuple[str, tuple]:
    where_clauses = []
    params = []

    for column, value in filters.items():
        if not value:
            continue

        if column == "collecting_date":
            where_clauses.append(f"{column} > %s")
        else:
            where_clauses.append(f"{column} = %s")

        params.append(value)

    where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
    query = f"SELECT TOP 1 (data) FROM armada_fingerprints{where_sql} ORDER BY NEWID()"
    return query, tuple(params)



def fetch_random_fingerprint(query: str, params: tuple) -> str | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    print(row[0])
    return json.loads(row[0])
