#!/usr/bin/env python3
"""
Local development entry point for project.

This script simulates the agent execution environment locally,
allowing you to test ctx_script.py without deploying to Kubernetes.

Usage:
    cd project
    python -m workbench.run_local
"""

import os
import sys

# Ensure we're in the right directory context
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
os.chdir(project_dir)
sys.path.insert(0, project_dir)

from celery import Celery
import uuid
from workbench.get_messages import local_get_messages
from workbench.lib_loader import local_lib_loader
from load_env import *


def main():

    with open('workbench/agent_path', 'r') as file:
        agent_path = file.read()
    
    print(agent_path)

    # Load agent modules into path
    local_lib_loader(agent_path)

    # Load configuration from config files
    agent_message, job_message = local_get_messages()

    # Generate unique run_id for this local run
    run_id = str(uuid.uuid4())
    agent_message["run_id"] = run_id
    job_message["run_id"] = run_id
    agent_message["pod_index"] = 0
    job_message["pod_index"]= 0

    print(f"[run_local] Starting local run with run_id: {run_id}")

    # Create Celery app (same as agent does)
    app = Celery(
        'celery_app',
        broker="amqp://localhost"
    )

    # Read main.py content
    main_path = os.path.join(project_dir, 'main.py')
    with open(main_path, 'r') as f:
        main_code = f.read()

    # Execute main.py with injected variables (same pattern as agent)
    namespace = {
        'app': app,
        'agent_message': agent_message,
        'job_message': job_message,
        '__name__': '__main__',
        '__file__': main_path,
    }
    exec(main_code, namespace)

    # Manually trigger the worker initialization and job execution
    # (In production, Celery handles this via signals and task consumption)
    print("[run_local] Initializing worker...")
    namespace['init_worker'](sender="local-test")

    print("[run_local] Running job...")
    namespace['run_job'](job_message)

    print("[run_local] Shutting down worker...")
    namespace['shutdown_worker'](sender="local-test")

    print("[run_local] Job completed.")


if __name__ == '__main__':
    main()
