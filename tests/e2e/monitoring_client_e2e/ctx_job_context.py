from src.monitoring_client import MonitoringClient #type: ignore
import uuid
import os


class JobContext():
    def __init__(self, job_message):
        self.job_message = job_message

    def instantiate_default(self):
        pod_index = os.getenv("POD_INDEX", 100)
        job_uuid = str(uuid.uuid4())
        self.monitoring_client = MonitoringClient(
            self.job_message["run_id"], pod_index, job_uuid
        ).create_job()

    async def __aenter__(self):
        self.instantiate_default()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass
