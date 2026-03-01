import uuid
import os


class JobContext():
    def __init__(self, job_message):
        self.job_message = job_message
        self.job_id = str(uuid.uuid4())

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass
