from fantomas import Screen, FantomasNoDriver
from src.database_connector import DatabaseConnector #type: ignore
from src.proxy_manager import ProxyManager #type: ignore
from src.fingerprint_manager import FingerprintManager #type: ignore
from src.standard_output import StandardOutput ##type: ignore

class AgentContext:

    def __init__(self, agent_message):
        self.agent_message = agent_message

    def instantiate_default(self):
        self.proxy_manager = ProxyManager(self.agent_message["config_proxy"]).launch_proxy()
        self.fingerprint_manager = FingerprintManager(self.agent_message["config_fingerprint"])
        self.database = DatabaseConnector()
        self.output_manager = StandardOutput(self.agent_message["run_id"])

    async def __aenter__(self):
        self.instantiate_default()
        self.screen = Screen(self.agent_message["config_fantomas"]["config_screen"]).launch_screen()
        self.browser = await FantomasNoDriver(self.agent_message["config_fantomas"]["config_browser"]).launch_browser()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.browser.stop()
        self.screen.stop_screen()