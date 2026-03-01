import pymssql

from config import DB_CONFIG


def get_connection():
    return pymssql.connect(
        server=DB_CONFIG["server"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
    )


ALLOWED_COLUMNS = {"proxy_location", "proxy_rotation_strategy", "proxy_type", "proxy_provider_name"}


def build_proxy_query(filters: dict) -> tuple[str, tuple]:
    where_clauses = []
    params = []
    for column, value in filters.items():
        if column not in ALLOWED_COLUMNS:
            raise ValueError(f"Invalid filter column: {column}")
        if value is not None:
            where_clauses.append(f"{column} = %s")
            params.append(value)

    where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
    query = f"SELECT TOP 1 proxy_url FROM armada_proxies{where_sql} ORDER BY NEWID()"
    return query, tuple(params)


def fetch_random_proxy(query: str, params: tuple) -> str | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row else None    