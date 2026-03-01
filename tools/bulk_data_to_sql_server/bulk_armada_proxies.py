import sys
import csv
from db_config import get_connection

# armada_proxies columns:
#   proxy_url VARCHAR(255)
#   proxy_provider_name VARCHAR(255)
#   proxy_type VARCHAR(255)
#   proxy_rotation_strategy VARCHAR(255)
#   proxy_location VARCHAR(255)

EXPECTED_COLUMNS = ['proxy_url', 'proxy_provider_name', 'proxy_type', 'proxy_rotation_strategy', 'proxy_location']

INSERT_SQL = """
    INSERT INTO armada_proxies (proxy_url, proxy_provider_name, proxy_type, proxy_rotation_strategy, proxy_location)
    VALUES (%s, %s, %s, %s, %s)
"""


def bulk_insert(csv_path):
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = [
            (row['proxy_url'], row['proxy_provider_name'], row['proxy_type'],
             row['proxy_rotation_strategy'], row['proxy_location'])
            for row in reader
        ]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(INSERT_SQL, rows)
    conn.commit()
    conn.close()
    print(f"{len(rows)} rows inserted into armada_proxies.")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <csv_file>")
        sys.exit(1)
    bulk_insert(sys.argv[1])
