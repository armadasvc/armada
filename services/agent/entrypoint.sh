#!/bin/sh

which celery || { echo "Celery not found in PATH"; exit 1; }

# Install additional requirements if provided (base64-encoded)
if [ -n "$REQUIREMENTS_TXT" ]; then
  echo "Installing additional requirements..."
  echo "$REQUIREMENTS_TXT" | base64 -d > /tmp/requirements.txt
  pip install -r /tmp/requirements.txt
  echo "Additional requirements installed."
fi

# Direct retrieval of environment variables
QUEUE_NAME="${RUN_ID:-default_queue}"
POD_INDEX="${POD_INDEX:-0}"

echo "Starting Celery with queue: $QUEUE_NAME"
echo "Starting Celery with index: $POD_INDEX"

exec python -m celery -A main worker \
  --queues="$QUEUE_NAME" \
  --concurrency=1 \
  -n worker"$POD_INDEX" \
  --prefetch-multiplier=1
