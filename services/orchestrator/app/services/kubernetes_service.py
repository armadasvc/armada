from dataclasses import dataclass

from kubernetes import client, config


@dataclass
class AgentConfig:
    run_id: str
    image_name: str
    image_version: str
    num_pods: int
    agent_cpu: str
    agent_memory: str
    docker_hub_username: str
    proxy_provider_url: str
    fingerprint_provider_url: str
    backend_url: str
    distrib: str
    requirements_txt: str = ""


class KubernetesService:
    def __init__(self):
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()

    def _create_agent_object(self, config: AgentConfig) -> client.V1Job:
        if config.distrib == "minikube":
            image_pull_secrets_variable = None
            image_pull_policy_variable = "Never"
        else:
            image_pull_secrets_variable = [client.V1LocalObjectReference(name="armada-docker-registry-secret")]
            image_pull_policy_variable = "Always"

        pod_labels = {"app": config.image_name}

        return client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(name=f"{config.image_name}-{config.run_id}"),
            spec=client.V1JobSpec(
                completions=config.num_pods,
                parallelism=config.num_pods,
                ttl_seconds_after_finished=1000000,
                completion_mode="Indexed",
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels=pod_labels),
                    spec=client.V1PodSpec(
                        restart_policy="Never",
                        image_pull_secrets=image_pull_secrets_variable,
                        containers=[
                            client.V1Container(
                                name=config.image_name,
                                image=f"{config.docker_hub_username}/{config.image_name}:{config.image_version}",
                                image_pull_policy=image_pull_policy_variable,
                                resources=client.V1ResourceRequirements(
                                    requests={"cpu": config.agent_cpu, "memory": config.agent_memory}
                                ),
                                env=[
                                    client.V1EnvVar(name="RUN_ID", value=config.run_id),
                                    client.V1EnvVar(name="REDIS_HOST_VAR_ENV", value="armada-redis"),
                                    client.V1EnvVar(name="REDIS_PORT_VAR_ENV", value="6379"),
                                    client.V1EnvVar(name="RABBITMQ_URL", value="amqp://armada-rabbitmq:5672"),
                                    client.V1EnvVar(
                                        name="SQL_SERVER_USER",
                                        value_from=client.V1EnvVarSource(
                                            secret_key_ref=client.V1SecretKeySelector(
                                                name="armada-sql-server-secret",
                                                key="SQL_SERVER_USER",
                                            )
                                        ),
                                    ),
                                    client.V1EnvVar(
                                        name="SQL_SERVER_DB",
                                        value_from=client.V1EnvVarSource(
                                            secret_key_ref=client.V1SecretKeySelector(
                                                name="armada-sql-server-secret",
                                                key="SQL_SERVER_DB",
                                            )
                                        ),
                                    ),
                                    client.V1EnvVar(
                                        name="SQL_SERVER_PASSWORD",
                                        value_from=client.V1EnvVarSource(
                                            secret_key_ref=client.V1SecretKeySelector(
                                                name="armada-sql-server-secret",
                                                key="SQL_SERVER_PASSWORD",
                                            )
                                        ),
                                    ),
                                    client.V1EnvVar(
                                        name="SQL_SERVER_NAME",
                                        value_from=client.V1EnvVarSource(
                                            secret_key_ref=client.V1SecretKeySelector(
                                                name="armada-sql-server-secret",
                                                key="SQL_SERVER_NAME",
                                            )
                                        ),
                                    ),
                                    client.V1EnvVar(name="PROXY_PROVIDER_URL", value=config.proxy_provider_url),
                                    client.V1EnvVar(name="FINGERPRINT_PROVIDER_URL", value=config.fingerprint_provider_url),
                                    client.V1EnvVar(name="BACKEND_URL", value=config.backend_url),
                                    client.V1EnvVar(name="REQUIREMENTS_TXT", value=config.requirements_txt),
                                    client.V1EnvVar(
                                        name="POD_INDEX",
                                        value_from=client.V1EnvVarSource(
                                            field_ref=client.V1ObjectFieldSelector(
                                                field_path="metadata.annotations['batch.kubernetes.io/job-completion-index']"
                                            )
                                        ),
                                    ),
                                ],
                            )
                        ],
                        topology_spread_constraints=[
                            client.V1TopologySpreadConstraint(
                                max_skew=1,
                                topology_key="kubernetes.io/hostname",
                                when_unsatisfiable="ScheduleAnyway",
                                label_selector=client.V1LabelSelector(match_labels={"app": config.image_name}),
                            )
                        ],
                    ),
                ),
            ),
        )

    def create_agent(self, config: AgentConfig, namespace: str = "default") -> client.V1Job:
        batch_v1 = client.BatchV1Api()
        job = self._create_agent_object(config)
        return batch_v1.create_namespaced_job(namespace=namespace, body=job)