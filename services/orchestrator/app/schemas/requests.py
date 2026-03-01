from pydantic import BaseModel, Field
from typing import Any


class RunMessage(BaseModel):
    platform: str
    image_name: str
    number_of_agents: int
    number_of_jobs: int
    redis_host: str
    redis_port: int
    rabbitmq_url: str
    plugin_repos: list[str] = []
    additional_private_lib: list[str] = []
    additional_lib: list[str] = []
    run_id: str = ""


class DefaultAgentMessage(BaseModel):
    class Config:
        extra = "allow"


class ConfigTemplate(BaseModel):
    run_message: RunMessage
    default_agent_message: DefaultAgentMessage
    default_job_message: dict[str, Any] = {}

    class Config:
        extra = "allow"
