import json
from datetime import datetime, timezone
from src.database_connector import DatabaseConnector #type: ignore


class StandardOutput:
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.db = DatabaseConnector()

    def send(self, data: dict):
        data_str = json.dumps(data)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000")
        self.db.post_to_db(
            "INSERT INTO armada_output (run_uuid, data, timestamp) VALUES (%s, %s, %s)",
            self.run_id,
            data_str,
            timestamp,
        )

