import base64
import json
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from ..config import (PLATFORM,REDIS_HOST,REDIS_PORT,RABBITMQ_URL, FINGERPRINT_PROVIDER_URL, PROXY_PROVIDER_URL,DOCKER_HUB_USERNAME,BACKEND_URL,DISTRIB)

from ..schemas import MessageResponse
from ..services import AgentConfig, CeleryService, KubernetesService, RedisService
from ..utils import merge_messages, parse_csv_to_list

router = APIRouter(prefix="/bot", tags=["bot"])


def parse_configtemplate_sync(configtemplate: UploadFile) -> dict:
    try:
        return json.loads(configtemplate.file.read())
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid configtemplate JSON",
        )


def parse_csv_inputs_sync(data_job: UploadFile, data_agent: UploadFile) -> tuple[list, list]:
    job_csv_content = data_job.file.read()
    agent_csv_content = data_agent.file.read()
    list_of_json_output_job = parse_csv_to_list(job_csv_content)
    list_of_json_output_agent = parse_csv_to_list(agent_csv_content)
    for index, item in enumerate(list_of_json_output_job):
        item["targetted_job"] = index
    for index, item in enumerate(list_of_json_output_agent):
        item["targetted_agent"] = index
    return list_of_json_output_job, list_of_json_output_agent


def build_consolidated_messages(
    configtemplate_content: dict,
    run_message: dict,
    list_of_json_output_job: list,
    list_of_json_output_agent: list,
) -> tuple[list, list]:
    consolidated_agent_messages = merge_messages(
        run_message["number_of_agents"],
        configtemplate_content["default_agent_message"],
        list_of_json_output_agent,
        "targetted_agent",
    )
    consolidated_job_messages = merge_messages(
        run_message["number_of_jobs"],
        configtemplate_content["default_job_message"],
        list_of_json_output_job,
        "targetted_job",
    )
    return consolidated_agent_messages, consolidated_job_messages


def push_agent_configs_to_redis(run_id: str, consolidated_agent_messages: list):
    redis_service = RedisService(REDIS_HOST, REDIS_PORT)
    try:
        for agent_index, agent_message in enumerate(consolidated_agent_messages):
            redis_service.send_config(run_id, agent_index, agent_message)
    finally:
        redis_service.close()


def deploy_kube_agent(run_message: dict, run_id: str, requirements_txt_b64: str = ""):
    if PLATFORM != "distant":
        return
    config = AgentConfig(
        run_id=run_id,
        image_name=run_message["image_name"],
        image_version=run_message["image_version"],
        num_pods=run_message["number_of_agents"],
        agent_cpu=run_message["agent_cpu"],
        agent_memory=run_message["agent_memory"],
        docker_hub_username=DOCKER_HUB_USERNAME,
        proxy_provider_url=PROXY_PROVIDER_URL,
        fingerprint_provider_url=FINGERPRINT_PROVIDER_URL,
        backend_url=BACKEND_URL,
        distrib=DISTRIB,
        requirements_txt=requirements_txt_b64,
    )
    kube_service = KubernetesService()
    kube_service.create_agent(config)


def dispatch_jobs_and_monitor(run_id: str, consolidated_job_messages: list):
    celery_service = CeleryService("dispatcher", broker=RABBITMQ_URL)
    celery_service.start_monitoring_in_thread(run_id)
    for job_message in consolidated_job_messages:
        celery_service.send_message(job_message, run_id, "tasks.consume_message")


def serialize_requirements(requirements_txt: Optional[UploadFile]) -> str:
    if requirements_txt is None:
        return ""
    content = requirements_txt.file.read().decode("utf-8").strip()
    if not content:
        return ""
    return base64.b64encode(content.encode("utf-8")).decode("ascii")


@router.post("/start", response_model=MessageResponse)
def start_bot(
    configtemplate: UploadFile = File(..., description="JSON configuration file"),
    data_job: UploadFile = File(..., description="Jobs CSV file"),
    data_agent: UploadFile = File(..., description="Agents CSV file"),
    python_code: str = Form(default=""),
    requirements_txt: Optional[UploadFile] = File(default=None, description="Python requirements file"),
) -> MessageResponse:
    """Start bots/agents according to the provided configuration."""
    configtemplate_content = parse_configtemplate_sync(configtemplate)
    list_of_json_output_job, list_of_json_output_agent = parse_csv_inputs_sync(data_job, data_agent)
    requirements_txt_b64 = serialize_requirements(requirements_txt)

    run_message = configtemplate_content["run_message"]
    run_id = run_message["run_id"]
    consolidated_agent_messages, consolidated_job_messages = build_consolidated_messages(
        configtemplate_content, run_message, list_of_json_output_job, list_of_json_output_agent,
    )

    push_agent_configs_to_redis(run_id, consolidated_agent_messages)
    deploy_kube_agent(run_message, run_id, requirements_txt_b64)
    dispatch_jobs_and_monitor(run_id, consolidated_job_messages)

    return MessageResponse(run_uuid=run_id)
