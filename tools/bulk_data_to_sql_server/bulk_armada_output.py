import sys
import csv
from db_config import get_connection

# armada_output columns:
#   run_uuid VARCHAR(255)
#   data VARCHAR(MAX)
#   timestamp DATETIME

EXPECTED_COLUMNS = ['run_uuid', 'data', 'timestamp']

INSERT_SQL = """
    INSERT INTO armada_output (run_uuid, data, timestamp)
    VALUES (%s, %s, %s)
"""


def bulk_insert(csv_path):
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = [
            (row['run_uuid'], row['data'], row['timestamp'] or None)
            for row in reader
        ]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(INSERT_SQL, rows)
    conn.commit()
    conn.close()
    print(f"{len(rows)} rows inserted into armada_output.")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <csv_file>")
        sys.exit(1)
    bulk_insert(sys.argv[1])
