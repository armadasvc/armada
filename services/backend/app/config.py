import os

def load_env():
    try:
        from dotenv import find_dotenv, dotenv_values
        env_file = find_dotenv(usecwd=True)
        if env_file:
            return {**os.environ, **dotenv_values(env_file)}
    except ImportError:
        pass
    return os.environ

env_values = load_env()

DB_CONFIG = {
    "server": env_values["SQL_SERVER_NAME"],
    "user": env_values["SQL_SERVER_USER"],
    "password": env_values["SQL_SERVER_PASSWORD"],
    "database": env_values["SQL_SERVER_DB"],
}