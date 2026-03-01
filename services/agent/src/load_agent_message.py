import json
import os
import redis

def load_agent_message():
    agent_message = retrieve_agent_message_from_redis()
    agent_message = add_elements_to_agent_message(agent_message)
    return agent_message


def retrieve_agent_message_from_redis():
    redis_var_env = os.getenv("REDIS_HOST_VAR_ENV","localhost")
    redis_var_env_port = os.getenv("REDIS_PORT_VAR_ENV","6379")
    pod_index = os.getenv("POD_INDEX","0")
    run_id = os.getenv("RUN_ID")
    r = redis.Redis(host=redis_var_env, port=redis_var_env_port, db=0)
    redis_value = r.get(run_id+pod_index).decode("utf-8")
    agent_message = json.loads(redis_value)
    return agent_message

def add_elements_to_agent_message(agent_message):
    pod_index = os.getenv("POD_INDEX","0")
    run_id = os.getenv("RUN_ID")
    agent_message["run_id"]=run_id
    agent_message["pod_index"]=pod_index
    return agent_message
