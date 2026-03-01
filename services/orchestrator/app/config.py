import os
from dotenv import load_dotenv, find_dotenv
env_path = find_dotenv()
environment_variable = load_dotenv(env_path)

# Configuration
PLATFORM = os.getenv("PLATFORM", "local")
DISTRIB = os.getenv("DISTRIB", "kube")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://localhost:5672")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
PROXY_PROVIDER_URL=os.getenv("PROXY_PROVIDER_URL","http://127.0.0.1:5005")
BACKEND_URL=os.getenv("BACKEND_URL", "http://localhost:8000")
FINGERPRINT_PROVIDER_URL=os.getenv("FINGERPRINT_PROVIDER_URL","http://127.0.0.1:5005")
DOCKER_HUB_USERNAME=os.getenv("DOCKER_HUB_USERNAME", "armadasvc")