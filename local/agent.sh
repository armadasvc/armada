#!/bin/bash

# Get the absolute path of the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Fixed relative path to the agent service
AGENT_PATH="$SCRIPT_DIR/../services/agent"

cd "$AGENT_PATH" || {
    echo "Unable to navigate to the directory."
    read -p "Press Enter to close..."
    exit 1
}

# Default values
DEFAULT_QUEUE=""
DEFAULT_POD_INDEX="0"
DEFAULT_REDIS_HOST="localhost"
DEFAULT_REDIS_PORT="6379"

# Load SQL defaults from parent .env
ENV_FILE="$SCRIPT_DIR/../.env"
if [ -f "$ENV_FILE" ]; then
    DEFAULT_SQL_USER=$(grep -m1 '^SQL_SERVER_USER=' "$ENV_FILE" | cut -d'=' -f2-)
    DEFAULT_SQL_PASSWORD=$(grep -m1 '^SQL_SERVER_PASSWORD=' "$ENV_FILE" | cut -d'=' -f2-)
    DEFAULT_SQL_DB=$(grep -m1 '^SQL_SERVER_DB=' "$ENV_FILE" | cut -d'=' -f2-)
    DEFAULT_SQL_SERVER=$(grep -m1 '^SQL_SERVER_NAME=' "$ENV_FILE" | cut -d'=' -f2-)
else
    echo "Warning: .env file not found at $ENV_FILE, SQL defaults will be empty."
    DEFAULT_SQL_USER=""
    DEFAULT_SQL_PASSWORD=""
    DEFAULT_SQL_DB=""
    DEFAULT_SQL_SERVER=""
fi

# YAD form
USER_INPUT=$(yad --form --title="Celery worker configuration" \
    --field="Queue name (RUN_ID):" "$DEFAULT_QUEUE" \
    --field="Pod index (POD_INDEX):" "$DEFAULT_POD_INDEX" \
    --field="Redis host (REDIS_HOST_VAR_ENV):" "$DEFAULT_REDIS_HOST" \
    --field="Redis port (REDIS_PORT_VAR_ENV):" "$DEFAULT_REDIS_PORT" \
    --field="SQL user (SQL_SERVER_USER):" "$DEFAULT_SQL_USER" \
    --field="SQL password (SQL_SERVER_PASSWORD):" "$DEFAULT_SQL_PASSWORD" \
    --field="SQL database (SQL_SERVER_DB):" "$DEFAULT_SQL_DB" \
    --field="SQL server (SQL_SERVER_NAME):" "$DEFAULT_SQL_SERVER" \
    --separator=",")

if [ $? -ne 0 ] || [ -z "$USER_INPUT" ]; then
    echo "No data specified. Aborting."
    read -p "Press Enter to close..."
    exit 1
fi

IFS=',' read -r \
    QUEUE POD_INDEX REDIS_HOST_VAR_ENV REDIS_PORT_VAR_ENV \
    SQL_SERVER_USER SQL_SERVER_PASSWORD SQL_SERVER_DB SQL_SERVER_NAME \
    <<< "$USER_INPUT"

# Exports
export POD_INDEX
export RUN_ID="$QUEUE"
export REDIS_HOST_VAR_ENV
export REDIS_PORT_VAR_ENV
export SQL_SERVER_USER
export SQL_SERVER_PASSWORD
export SQL_SERVER_DB
export SQL_SERVER_NAME

# Start Celery
bash -i -c "celery -A main worker --loglevel=warning --queues='$QUEUE' --concurrency=1 -n worker'$POD_INDEX' --prefetch-multiplier=1"

echo "Script finished."
exec bash

