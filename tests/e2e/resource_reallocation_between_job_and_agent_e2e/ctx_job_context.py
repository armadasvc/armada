from fantomas import Identity
from src.monitoring_client import MonitoringClient #type: ignore
import uuid
import os
from fantomas import Screen, FantomasNoDriver



class JobContext():
    def __init__(self, job_message):
        self.job_message = job_message

    
    def instantiate_default(self):
        pod_index = os.getenv("POD_INDEX", 100)
        job_uuid = str(uuid.uuid4())
        self.monitoring_client = MonitoringClient(self.job_message["run_id"],pod_index,job_uuid).create_job()


    async def __aenter__(self):
        self.instantiate_default()
        self.identity = Identity().launch_identity_creation()
        self.screen = Screen(self.job_message["config_fantomas"]["config_screen"]).launch_screen()
        self.browser = await FantomasNoDriver(self.job_message["config_fantomas"]["config_browser"]).launch_browser()
        return self 
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        self.browser.stop()
        self.screen.stop_screen()