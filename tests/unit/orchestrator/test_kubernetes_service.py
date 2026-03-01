from unittest.mock import patch, MagicMock

from app.services.kubernetes_service import KubernetesService, AgentConfig


def _make_config(**overrides) -> AgentConfig:
    defaults = dict(
        run_id="run1",
        image_name="img",
        image_version="1.0",
        num_pods=1,
        agent_cpu="1",
        agent_memory="1Gi",
        docker_hub_username="dh",
        proxy_provider_url="pp",
        fingerprint_provider_url="fp",
        backend_url="mb",
        distrib="cloud",
    )
    defaults.update(overrides)
    return AgentConfig(**defaults)


class TestKubernetesServiceInit:
    @patch("app.services.kubernetes_service.config.load_incluster_config")
    def test_in_cluster(self, mock_load):
        service = KubernetesService()
        mock_load.assert_called_once()

    @patch("app.services.kubernetes_service.config.load_kube_config")
    @patch("app.services.kubernetes_service.config.load_incluster_config",
           side_effect=__import__("kubernetes").config.ConfigException)
    def test_local_fallback(self, mock_incluster, mock_kube):
        service = KubernetesService()
        mock_kube.assert_called_once()


class TestCreateAgentObject:
    @patch("app.services.kubernetes_service.config.load_incluster_config")
    def test_structure(self, mock_config):
        service = KubernetesService()
        cfg = _make_config(image_name="agent-img", num_pods=5, agent_memory="2Gi",
                           docker_hub_username="dockeruser",
                           proxy_provider_url="http://proxy:5001",
                           fingerprint_provider_url="http://fp:5005",
                           backend_url="http://monitor:8000")
        job = service._create_agent_object(cfg)
        assert job.spec.parallelism == 5
        assert job.spec.completions == 5
        assert job.spec.completion_mode == "Indexed"

    @patch("app.services.kubernetes_service.config.load_incluster_config")
    def test_container_image(self, mock_config):
        service = KubernetesService()
        cfg = _make_config(image_name="agent-img", image_version="2.0", num_pods=3,
                           agent_cpu="500m", agent_memory="1Gi",
                           docker_hub_username="myuser")
        job = service._create_agent_object(cfg)
        container = job.spec.template.spec.containers[0]
        assert container.image == "myuser/agent-img:2.0"

    @patch("app.services.kubernetes_service.config.load_incluster_config")
    def test_resources(self, mock_config):
        service = KubernetesService()
        cfg = _make_config(agent_cpu="2", agent_memory="4Gi")
        job = service._create_agent_object(cfg)
        container = job.spec.template.spec.containers[0]
        assert container.resources.requests["cpu"] == "2"
        assert container.resources.requests["memory"] == "4Gi"

    @patch("app.services.kubernetes_service.config.load_incluster_config")
    def test_env_vars(self, mock_config):
        service = KubernetesService()
        cfg = _make_config()
        job = service._create_agent_object(cfg)
        container = job.spec.template.spec.containers[0]
        env_names = {e.name for e in container.env}
        assert "RUN_ID" in env_names
        assert "POD_INDEX" in env_names
        assert "SQL_SERVER_PASSWORD" in env_names
        assert "PROXY_PROVIDER_URL" in env_names
        assert "FINGERPRINT_PROVIDER_URL" in env_names
        assert "BACKEND_URL" in env_names
        assert "REQUIREMENTS_TXT" in env_names

    @patch("app.services.kubernetes_service.config.load_incluster_config")
    def test_requirements_txt_env_var(self, mock_config):
        service = KubernetesService()
        cfg = _make_config(requirements_txt="cGFuZGFzPT0yLjAuMA==")
        job = service._create_agent_object(cfg)
        container = job.spec.template.spec.containers[0]
        req_env = next(e for e in container.env if e.name == "REQUIREMENTS_TXT")
        assert req_env.value == "cGFuZGFzPT0yLjAuMA=="

    @patch("app.services.kubernetes_service.config.load_incluster_config")
    def test_requirements_txt_empty_by_default(self, mock_config):
        service = KubernetesService()
        cfg = _make_config()
        job = service._create_agent_object(cfg)
        container = job.spec.template.spec.containers[0]
        req_env = next(e for e in container.env if e.name == "REQUIREMENTS_TXT")
        assert req_env.value == ""

    @patch("app.services.kubernetes_service.config.load_incluster_config")
    def test_job_metadata_name(self, mock_config):
        service = KubernetesService()
        cfg = _make_config(run_id="abc123", image_name="my-agent")
        job = service._create_agent_object(cfg)
        assert job.metadata.name == "my-agent-abc123"


class TestCreateAgent:
    @patch("app.services.kubernetes_service.client.BatchV1Api")
    @patch("app.services.kubernetes_service.config.load_incluster_config")
    def test_calls_api(self, mock_config, MockBatch):
        service = KubernetesService()
        cfg = _make_config(num_pods=3, agent_memory="2Gi")
        service.create_agent(cfg)
        MockBatch.return_value.create_namespaced_job.assert_called_once()

    @patch("app.services.kubernetes_service.client.BatchV1Api")
    @patch("app.services.kubernetes_service.config.load_incluster_config")
    def test_custom_namespace(self, mock_config, MockBatch):
        service = KubernetesService()
        cfg = _make_config()
        service.create_agent(cfg, namespace="custom-ns")
        call_kwargs = MockBatch.return_value.create_namespaced_job.call_args[1]
        assert call_kwargs["namespace"] == "custom-ns"
