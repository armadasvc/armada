class JobContext():
    def __init__(self, job_message):
        self.job_message = job_message

    def instantiate_default(self):
        pass

    async def __aenter__(self):
        self.instantiate_default()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass
