import sys
import csv
from db_config import get_connection

# armada_events columns:
#   event_uuid VARCHAR(255)
#   event_content VARCHAR(255)
#   job_uuid VARCHAR(255)
#   event_datetime DATETIME
#   event_status VARCHAR(255)

EXPECTED_COLUMNS = ['event_uuid', 'event_content', 'job_uuid', 'event_datetime', 'event_status']

INSERT_SQL = """
    INSERT INTO armada_events (event_uuid, event_content, job_uuid, event_datetime, event_status)
    VALUES (%s, %s, %s, %s, %s)
"""


def bulk_insert(csv_path):
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = [
            (row['event_uuid'], row['event_content'], row['job_uuid'],
             row['event_datetime'] or None, row['event_status'])
            for row in reader
        ]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(INSERT_SQL, rows)
    conn.commit()
    conn.close()
    print(f"{len(rows)} rows inserted into armada_events.")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <csv_file>")
        sys.exit(1)
    bulk_insert(sys.argv[1])
