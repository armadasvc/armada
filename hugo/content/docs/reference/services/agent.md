---
title: 4.2.2. Agent
linkTitle: 4.2.2. Agent
weight: 2
description: Celery worker pod that loads config from Redis, executes user Python code via exec(), and consumes jobs from RabbitMQ
---

# Agent Service

Distributed Celery worker that executes dynamically loaded automation tasks. Each agent pod retrieves its task definition from Redis at startup, then runs it as a Celery worker consuming from a dedicated RabbitMQ queue.

## Architecture

```
Redis (task definitions) --> Agent Pod --> Celery Worker --> RabbitMQ (task queue)

```

At startup, the agent:
1. Fetches its task definition (code + config) from Redis using `RUN_ID` + `POD_INDEX` as key
2. Initializes a Celery app connected to RabbitMQ
3. Executes the dynamically loaded code with the Celery app and task config injected into scope

For the complete startup sequence and `exec()` mechanism, see [Code Bundling and Execution]({{< relref "/docs/reference/architecture/code-bundling-execution" >}}). For the full agent internals (container contents, concurrency model), see [Agent Internals]({{< relref "/docs/reference/architecture/agent-internals" >}}).

## Modules

| Module | Description |
|---|---|
| `main.py` | Entrypoint. Loads the agent message from Redis and executes its code via Celery. |
| `src/load_agent_message.py` | Retrieves and enriches the task definition from Redis. |
| `src/proxy_manager.py` | Local mitmproxy management with optional upstream proxy support. See [Proxy Provider guide]({{< relref "/docs/guides/proxy-provider" >}}). |
| `src/fingerprint_manager.py` | Fetches browser fingerprints from an external fingerprint provider service. See [Fingerprint Provider guide]({{< relref "/docs/guides/fingerprint-provider" >}}). |
| `src/database_connector.py` | MSSQL database connector with query execution helpers. See [Database Connector guide]({{< relref "/docs/guides/database-connector" >}}). |
| `src/monitoring_client.py` | Reports run/job lifecycle events to the backend monitoring API. See [Monitoring Client guide]({{< relref "/docs/guides/monitoring-client" >}}). |

## Environment Variables

Key variables: `RUN_ID`, `POD_INDEX`, `RABBITMQ_URL`, `REDIS_HOST_VAR_ENV`, `REDIS_PORT_VAR_ENV`, `BACKEND_URL`, `PROXY_PROVIDER_URL`, `FINGERPRINT_PROVIDER_URL`, and the standard `SQL_SERVER_*` credentials.

For the complete reference with sources, defaults, and injection channels, see [Environment Variables]({{< relref "/docs/reference/architecture/environment-variables" >}}).

## Docker

The image is based on `python:3.12-slim` and includes Chrome, Xvfb, xdotool, ImageMagick, and mitmproxy. The container runs as a non-root user (`celeryuser`). For the complete contents and startup sequence, see [Agent Internals]({{< relref "/docs/reference/architecture/agent-internals" >}}).

```bash
docker build -t armada-agent .
```

## Dependencies

Key Python packages:
- **celery** / **redis** - Task queue and message store
- **mitmproxy** - Programmable HTTP/HTTPS proxy
- **pymssql** - MSSQL database driver
- **pyvirtualdisplay** / **pillow** / **numpy** - Virtual display and image processing
