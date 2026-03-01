import json
from unittest.mock import patch, MagicMock

from load_agent_message import (
    load_agent_message,
    retrieve_agent_message_from_redis,
    add_elements_to_agent_message,
)


class TestRetrieveAgentMessageFromRedis:
    @patch("load_agent_message.redis.Redis")
    @patch.dict("os.environ", {"RUN_ID": "run1", "POD_INDEX": "3", "REDIS_HOST_VAR_ENV": "localhost", "REDIS_PORT_VAR_ENV": "6379"})
    def test_reads_correct_key(self, MockRedis):
        mock_instance = MockRedis.return_value
        mock_instance.get.return_value = b'{"key": "value"}'
        result = retrieve_agent_message_from_redis()
        mock_instance.get.assert_called_once_with("run13")
        assert result == {"key": "value"}

    @patch("load_agent_message.redis.Redis")
    @patch.dict("os.environ", {"RUN_ID": "abc", "POD_INDEX": "0", "REDIS_HOST_VAR_ENV": "localhost", "REDIS_PORT_VAR_ENV": "6379"})
    def test_parses_json(self, MockRedis):
        mock_instance = MockRedis.return_value
        mock_instance.get.return_value = b'{"config_proxy": {"enabled": 1}}'
        result = retrieve_agent_message_from_redis()
        assert result["config_proxy"]["enabled"] == 1


class TestAddElementsToAgentMessage:
    @patch.dict("os.environ", {"RUN_ID": "run1", "POD_INDEX": "3"})
    def test_adds_run_id_and_pod_index(self):
        msg = {"config": "data"}
        result = add_elements_to_agent_message(msg)
        assert result["run_id"] == "run1"
        assert result["pod_index"] == "3"
        assert result["config"] == "data"

    @patch.dict("os.environ", {"RUN_ID": "abc", "POD_INDEX": "0"})
    def test_preserves_original_keys(self):
        msg = {"a": 1, "b": 2}
        result = add_elements_to_agent_message(msg)
        assert result["a"] == 1
        assert result["b"] == 2


class TestLoadAgentMessage:
    @patch("load_agent_message.redis.Redis")
    @patch.dict("os.environ", {"RUN_ID": "abc", "POD_INDEX": "0", "REDIS_HOST_VAR_ENV": "localhost", "REDIS_PORT_VAR_ENV": "6379"})
    def test_full_pipeline(self, MockRedis):
        mock_instance = MockRedis.return_value
        mock_instance.get.return_value = b'{"config_proxy": {}}'
        result = load_agent_message()
        assert result["run_id"] == "abc"
        assert result["pod_index"] == "0"
        assert "config_proxy" in result
