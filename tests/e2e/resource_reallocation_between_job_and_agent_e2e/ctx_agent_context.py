from fantomas import Screen, FantomasNoDriver
from src.database_connector import DatabaseConnector #type: ignore
from src.proxy_manager import ProxyManager #type: ignore
from src.fingerprint_manager import FingerprintManager #type: ignore

class AgentContext:

    def __init__(self, agent_message):
        self.agent_message = agent_message

    def instantiate_default(self):
        self.proxy_manager = ProxyManager(self.agent_message["config_proxy"]).launch_proxy()
        self.fingerprint_manager = FingerprintManager(self.agent_message["config_fingerprint"])
        self.database = DatabaseConnector()

    async def __aenter__(self):
        self.instantiate_default()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass