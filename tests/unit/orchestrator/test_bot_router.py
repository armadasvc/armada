import json
import io
import pytest
from unittest.mock import patch, MagicMock

from app.routers.bot import (
    parse_configtemplate_sync,
    parse_csv_inputs_sync,
    push_agent_configs_to_redis,
    deploy_kube_agent,
    dispatch_jobs_and_monitor,
    serialize_requirements,
)


class TestParseConfigtemplateSync:
    def test_valid_json(self):
        mock_file = MagicMock()
        mock_file.file.read.return_value = b'{"run_message": {}, "default_agent_message": {}}'
        result = parse_configtemplate_sync(mock_file)
        assert "run_message" in result
        assert "default_agent_message" in result

    def test_invalid_json(self):
        from fastapi import HTTPException
        mock_file = MagicMock()
        mock_file.file.read.return_value = b"not json"
        with pytest.raises(HTTPException) as exc_info:
            parse_configtemplate_sync(mock_file)
        assert exc_info.value.status_code == 400

    def test_empty_dict(self):
        mock_file = MagicMock()
        mock_file.file.read.return_value = b"{}"
        result = parse_configtemplate_sync(mock_file)
        assert result == {}


class TestParseCsvInputsSync:
    @patch("app.routers.bot.parse_csv_to_list")
    def test_adds_targetted_indices(self, mock_parse):
        mock_parse.side_effect = [
            [{"col1": "a"}, {"col1": "b"}],  # jobs
            [{"col1": "x"}],  # agents
        ]
        mock_job = MagicMock()
        mock_job.file.read.return_value = b"col1\na\nb"
        mock_agent = MagicMock()
        mock_agent.file.read.return_value = b"col1\nx"

        jobs, agents = parse_csv_inputs_sync(mock_job, mock_agent)
        assert jobs[0]["targetted_job"] == 0
        assert jobs[1]["targetted_job"] == 1
        assert agents[0]["targetted_agent"] == 0


class TestPushAgentConfigsToRedis:
    @patch("app.routers.bot.RedisService")
    def test_sends_all_configs(self, MockRedis):
        push_agent_configs_to_redis("run1", [{"a": 1}, {"b": 2}])
        assert MockRedis.return_value.send_config.call_count == 2
        MockRedis.return_value.close.assert_called_once()

    @patch("app.routers.bot.RedisService")
    def test_closes_on_error(self, MockRedis):
        MockRedis.return_value.send_config.side_effect = Exception("fail")
        with pytest.raises(Exception):
            push_agent_configs_to_redis("run1", [{"a": 1}])
        MockRedis.return_value.close.assert_called_once()


class TestDeployKubeAgent:
    @patch("app.routers.bot.PLATFORM", "local")
    @patch("app.routers.bot.KubernetesService")
    def test_skips_when_not_distant(self, MockK8s):
        deploy_kube_agent({}, "run1")
        MockK8s.assert_not_called()

    @patch("app.routers.bot.PLATFORM", "distant")
    @patch("app.routers.bot.KubernetesService")
    def test_deploys_when_distant(self, MockK8s):
        run_message = {
            "image_name": "img",
            "image_version": "1.0",
            "number_of_agents": 3,
            "agent_cpu": "1",
            "agent_memory": "2Gi",
        }
        deploy_kube_agent(run_message, "run1")
        MockK8s.return_value.create_agent.assert_called_once()


class TestSerializeRequirements:
    def test_none_returns_empty(self):
        assert serialize_requirements(None) == ""

    def test_empty_content_returns_empty(self):
        mock_file = MagicMock()
        mock_file.file.read.return_value = b""
        assert serialize_requirements(mock_file) == ""

    def test_whitespace_only_returns_empty(self):
        mock_file = MagicMock()
        mock_file.file.read.return_value = b"   \n  "
        assert serialize_requirements(mock_file) == ""

    def test_valid_content_returns_base64(self):
        import base64
        mock_file = MagicMock()
        mock_file.file.read.return_value = b"pandas==2.0.0\nrequests>=2.28"
        result = serialize_requirements(mock_file)
        decoded = base64.b64decode(result).decode("utf-8")
        assert decoded == "pandas==2.0.0\nrequests>=2.28"


class TestDeployKubeAgentWithRequirements:
    @patch("app.routers.bot.PLATFORM", "distant")
    @patch("app.routers.bot.KubernetesService")
    def test_passes_requirements_to_config(self, MockK8s):
        run_message = {
            "image_name": "img",
            "image_version": "1.0",
            "number_of_agents": 1,
            "agent_cpu": "1",
            "agent_memory": "1Gi",
        }
        deploy_kube_agent(run_message, "run1", requirements_txt_b64="dGVzdA==")
        call_args = MockK8s.return_value.create_agent.call_args[0][0]
        assert call_args.requirements_txt == "dGVzdA=="


class TestDispatchJobsAndMonitor:
    @patch("app.routers.bot.CeleryService")
    def test_sends_all_jobs(self, MockCelery):
        dispatch_jobs_and_monitor("run1", [{"job": 1}, {"job": 2}])
        assert MockCelery.return_value.send_message.call_count == 2
        MockCelery.return_value.start_monitoring_in_thread.assert_called_once_with("run1")

    @patch("app.routers.bot.CeleryService")
    def test_uses_correct_task_name(self, MockCelery):
        dispatch_jobs_and_monitor("run1", [{"job": 1}])
        call_args = MockCelery.return_value.send_message.call_args
        assert call_args[0][1] == "run1"  # queue_name
        assert call_args[0][2] == "tasks.consume_message"  # task_name
