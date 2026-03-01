from src.fingerprint_manager import FingerprintManager #type: ignore


class AgentContext:

    def __init__(self, agent_message):
        self.agent_message = agent_message

    def instantiate_default(self):
        self.fingerprint_manager = FingerprintManager(self.agent_message["config_fingerprint"])

    async def __aenter__(self):
        self.instantiate_default()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass
