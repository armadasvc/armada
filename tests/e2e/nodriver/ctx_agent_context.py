import nodriver as uc

class AgentContext:

    def __init__(self, agent_message):
        self.agent_message = agent_message

    def _build_browser_args(self):
        config_nodriver = self.agent_message.get("config_nodriver", {})
        args = [arg for arg in config_nodriver.get("browser_arguments", []) if arg]
        headless = config_nodriver.get("headless", False)
        return args, headless

    async def __aenter__(self):
        args, headless = self._build_browser_args()
        self.browser = await uc.start(
            headless=headless,
            browser_args=args
        )
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.browser.stop()
