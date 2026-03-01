import json
from unittest.mock import patch, MagicMock

from app.services.redis_service import RedisService


class TestRedisServiceInit:
    @patch("app.services.redis_service.redis.Redis")
    def test_creates_client(self, MockRedis):
        service = RedisService("localhost", 6379)
        MockRedis.assert_called_once_with(host="localhost", port=6379, db=0)

    @patch("app.services.redis_service.redis.Redis")
    def test_custom_db(self, MockRedis):
        service = RedisService("host", 6379, db=2)
        MockRedis.assert_called_once_with(host="host", port=6379, db=2)


class TestSendConfig:
    @patch("app.services.redis_service.redis.Redis")
    def test_stores_config(self, MockRedis):
        service = RedisService("localhost", 6379)
        service.send_config("run1", 3, {"key": "value"})
        service.client.set.assert_called_once_with(
            "run13",
            json.dumps({"key": "value"}),
        )

    @patch("app.services.redis_service.redis.Redis")
    def test_key_format(self, MockRedis):
        service = RedisService("localhost", 6379)
        service.send_config("abc", 0, {})
        service.client.set.assert_called_once_with("abc0", "{}")

    @patch("app.services.redis_service.redis.Redis")
    def test_key_concatenation(self, MockRedis):
        service = RedisService("localhost", 6379)
        service.send_config("run-xyz", 12, {"a": 1})
        call_args = service.client.set.call_args
        assert call_args[0][0] == "run-xyz12"


class TestClose:
    @patch("app.services.redis_service.redis.Redis")
    def test_closes_client(self, MockRedis):
        service = RedisService("localhost", 6379)
        service.close()
        service.client.close.assert_called_once()
