import sys
import csv
from db_config import get_connection

# armada_jobs columns:
#   job_uuid VARCHAR(255)
#   run_uuid VARCHAR(255)
#   job_datetime DATETIME
#   job_associated_agent VARCHAR(255)
#   job_status VARCHAR(255)

EXPECTED_COLUMNS = ['job_uuid', 'run_uuid', 'job_datetime', 'job_associated_agent', 'job_status']

INSERT_SQL = """
    INSERT INTO armada_jobs (job_uuid, run_uuid, job_datetime, job_associated_agent, job_status)
    VALUES (%s, %s, %s, %s, %s)
"""


def bulk_insert(csv_path):
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = [
            (row['job_uuid'], row['run_uuid'], row['job_datetime'] or None,
             row['job_associated_agent'], row['job_status'])
            for row in reader
        ]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(INSERT_SQL, rows)
    conn.commit()
    conn.close()
    print(f"{len(rows)} rows inserted into armada_jobs.")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <csv_file>")
        sys.exit(1)
    bulk_insert(sys.argv[1])
