---
title: 4.2.1. Orchestrator
linkTitle: 4.2.1. Orchestrator
weight: 1
description: Central control plane that merges configurations, pushes agent configs to Redis, dispatches jobs via Celery, and creates Kubernetes Jobs
---

# Armada Orchestrator

The Orchestrator is the central control plane of the Armada platform. It receives run configurations, provisions agents on Kubernetes, distributes jobs via Celery/RabbitMQ, and stores agent configs in Redis.

## Architecture

```
Client (Frontend)
    │
    ▼
┌──────────────┐       ┌───────────┐
│ Orchestrator │──────▶│   Redis   │  (agent configs)
│  (FastAPI)   │       └───────────┘
│              │       ┌───────────┐
│              │──────▶│ RabbitMQ  │  (job dispatch via Celery)
│              │       └───────────┘
│              │       ┌────────────┐
│              │──────▶│ Kubernetes │  (agent pod deployment)
└──────────────┘       └────────────┘
```

## How It Works

1. The client sends a `POST /bot/start` multipart/form-data request with the following fields:
   - **configtemplate** (file, JSON) — run parameters: image name/version, number of agents/jobs, resource limits, and default messages for agents and jobs.
   - **data_job** (file, CSV) — per-job overrides merged on top of the default job message.
   - **data_agent** (file, CSV) — per-agent overrides merged on top of the default agent message.
   - **python_code** (form field, string, optional) — bundled Python script to be executed by agents.
   - **requirements_txt** (file, optional) — extra pip dependencies to install in agent pods.

2. The orchestrator:
   - Parses and validates the inputs.
   - Merges default messages with targeted CSV overrides to produce one config per agent and one message per job (see [Configuration Pipeline]({{< relref "/docs/reference/architecture/configuration-pipeline" >}})).
   - Pushes each agent config to **Redis** (key: `{run_id}{agent_index}`).
   - Creates a Kubernetes **Indexed Job** to spin up agent pods (see [Infrastructure]({{< relref "/docs/reference/architecture/infrastructure" >}}) for the topology and RBAC).
   - Dispatches job messages to agents through **RabbitMQ** via Celery and starts a background monitor that shuts down workers once all jobs are consumed.

## API

### `POST /bot/start`

Start a run. Accepts multipart/form-data.

**Form fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `configtemplate` | file (JSON) | yes | Processed configuration template |
| `data_job` | file (CSV) | yes | Per-job overrides |
| `data_agent` | file (CSV) | yes | Per-agent overrides |
| `python_code` | form field (string) | no | Bundled Python script |
| `requirements_txt` | file (text) | no | Extra pip dependencies |

### `GET /health`

Health check endpoint.

**Response:** `200 OK`

## Configuration

Key environment variables: `PLATFORM` (`local`/`distant`), `DISTRIB` (`kube`/`minikube`), `RABBITMQ_URL`, `REDIS_HOST`, `REDIS_PORT`, `BACKEND_URL`, `PROXY_PROVIDER_URL`, `FINGERPRINT_PROVIDER_URL`, `DOCKER_HUB_USERNAME`.

For the complete reference with defaults, sources, and injection channels, see [Environment Variables]({{< relref "/docs/reference/architecture/environment-variables" >}}).

## Getting Started

### Prerequisites

- Python 3.12+
- Redis
- RabbitMQ

### Install

```bash
pip install -r requirements.txt
```

### Run

```bash
python run.py
```

The server starts on port **8080**.

### Docker

```bash
docker build -t armada-orchestrator .
docker run -p 8080:8080 armada-orchestrator
```

## Tech Stack

- **FastAPI** — async HTTP framework
- **Celery** — distributed task queue (RabbitMQ broker)
- **Redis** — agent config store
- **Kubernetes Python Client** — programmatic Job creation
- **Pydantic** — request/response validation
