from src.load_agent_message import load_agent_message
from celery import Celery
import os
agent_message = load_agent_message()
app = Celery('celery_app')
app.conf.update(
    broker_url=os.getenv("RABBITMQ_URL","amqp://localhost:5672")
)
exec(agent_message["code"],{'app':app,'agent_message':agent_message})