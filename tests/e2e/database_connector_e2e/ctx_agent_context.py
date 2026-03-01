from src.database_connector import DatabaseConnector #type: ignore


class AgentContext:

    def __init__(self, agent_message):
        self.agent_message = agent_message

    def instantiate_default(self):
        self.database = DatabaseConnector()

    async def __aenter__(self):
        self.instantiate_default()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass
