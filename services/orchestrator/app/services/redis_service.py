import json
import redis


class RedisService:
    def __init__(self, host: str, port: int, db: int = 0):
        self.client = redis.Redis(host=host, port=port, db=db)

    def send_config(self, run_id: str, agent_index: int, config_message: dict) -> None:
        config_message_str = json.dumps(config_message)
        key = f"{run_id}{agent_index}"
        self.client.set(key, config_message_str)

    def close(self) -> None:
        self.client.close()
