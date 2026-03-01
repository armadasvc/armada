import sys
import csv
from db_config import get_connection

# armada_fingerprints columns:
#   antibot_vendor VARCHAR(255)
#   website VARCHAR(255)
#   data VARCHAR(MAX)
#   collecting_date DATE

EXPECTED_COLUMNS = ['antibot_vendor', 'website', 'data', 'collecting_date']

INSERT_SQL = """
    INSERT INTO armada_fingerprints (antibot_vendor, website, data, collecting_date)
    VALUES (%s, %s, %s, %s)
"""


def bulk_insert(csv_path):
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = [
            (row['antibot_vendor'], row['website'], row['data'],
             row['collecting_date'] or None)
            for row in reader
        ]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(INSERT_SQL, rows)
    conn.commit()
    conn.close()
    print(f"{len(rows)} rows inserted into armada_fingerprints.")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <csv_file>")
        sys.exit(1)
    bulk_insert(sys.argv[1])
