from playwright.async_api import async_playwright

class AgentContext:

    def __init__(self, agent_message):
        self.agent_message = agent_message

    def _build_launch_args(self):
        config_playwright = self.agent_message.get("config_playwright", {})
        args = [arg for arg in config_playwright.get("chrome_arguments", []) if arg]
        headless = config_playwright.get("headless", False)
        return args, headless

    async def __aenter__(self):
        args, headless = self._build_launch_args()
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=args
        )
        self.page = await self.browser.new_page()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.browser.close()
        await self.playwright.stop()
