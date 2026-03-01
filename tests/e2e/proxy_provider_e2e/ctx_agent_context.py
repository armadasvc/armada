from fantomas import Screen, FantomasNoDriver
from src.proxy_manager import ProxyManager #type: ignore


class AgentContext:

    def __init__(self, agent_message):
        self.agent_message = agent_message

    def instantiate_default(self):
        # Initialize ProxyManager but do NOT launch yet.
        # This allows ctx_script.py to register modifiers/retrievers
        # before the mitmproxy subprocess starts.
        self.proxy_manager = ProxyManager(self.agent_message["config_proxy"])

    def launch_proxy(self):
        """Call this after registering all modifiers/retrievers."""
        self.proxy_manager.launch_proxy()

    async def __aenter__(self):
        self.instantiate_default()
        self.screen = Screen(self.agent_message["config_fantomas"]["config_screen"]).launch_screen()
        self.browser = await FantomasNoDriver(self.agent_message["config_fantomas"]["config_browser"]).launch_browser()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.proxy_manager.exit_local_proxy()
        self.browser.stop()
        self.screen.stop_screen()
