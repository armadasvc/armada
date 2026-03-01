import sys
import csv
from db_config import get_connection

# armada_runs columns:
#   run_uuid VARCHAR(255)
#   run_datetime DATETIME

EXPECTED_COLUMNS = ['run_uuid', 'run_datetime']

INSERT_SQL = """
    INSERT INTO armada_runs (run_uuid, run_datetime)
    VALUES (%s, %s)
"""


def bulk_insert(csv_path):
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = [
            (row['run_uuid'], row['run_datetime'] or None)
            for row in reader
        ]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(INSERT_SQL, rows)
    conn.commit()
    conn.close()
    print(f"{len(rows)} rows inserted into armada_runs.")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <csv_file>")
        sys.exit(1)
    bulk_insert(sys.argv[1])
