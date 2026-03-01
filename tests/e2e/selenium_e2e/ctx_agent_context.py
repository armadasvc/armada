from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

class AgentContext:

    def __init__(self, agent_message):
        self.agent_message = agent_message

    def _build_chrome_options(self):
        config_selenium = self.agent_message.get("config_selenium", {})
        chrome_options = Options()
        for arg in config_selenium.get("chrome_arguments", []):
            if arg:
                chrome_options.add_argument(arg)
        return chrome_options

    async def __aenter__(self):
        chrome_options = self._build_chrome_options()
        self.driver = webdriver.Chrome(options=chrome_options)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.driver.quit()