---
title: 4.1.6. Environment Variables
linkTitle: 4.1.6. Environment Variables
weight: 6
description: Complete reference of environment variables per service, injection channels (Kubernetes secrets, Helm, Docker Compose, python-dotenv), and defaults
---

## Overview

Environment variables are a cornerstone of Armada's configuration strategy. They serve as the primary mechanism for
passing credentials, service addresses, runtime parameters, and deployment-mode flags to every component in the system.
Because Armada runs in two fundamentally different environments — a **production Kubernetes cluster** and a **local
development stack** — the same set of variables must be delivered through entirely different channels depending on where
the code is executing.

In **production**, sensitive values such as database passwords and API keys are stored as Kubernetes Secrets, which are
created once during cluster bootstrap and then referenced by Helm-templated deployment manifests. Non-sensitive
configuration (service URLs, platform flags, distribution mode) is written directly into those same Helm templates and
rendered at deploy time. Agent pods, which are created dynamically at runtime by the Orchestrator, receive their
variables through a programmatically-built Job spec that mixes secret references, hard-coded values, and Kubernetes
downward-API fields.

In **local development**, the same variables originate from a single `.env` file at the repository root. Docker Compose
loads this file into every container via the `env_file` directive, while the Orchestrator container additionally receives
inter-service URLs through the `environment` block in `docker-compose.yml`. When running outside Docker entirely (the
workbench mode), `python-dotenv` reads the `.env` file into `os.environ` so that Python code can use the same `os.getenv()`
calls it would use in production.

Understanding which channel delivers each variable — and how that channel differs between environments — is essential
for debugging configuration issues, adding new services, or extending the platform with additional secrets.

---

## How Environment Variables Reach Each Component

The diagram below summarizes the injection channels for both deployment modes. Each arrow represents
a different mechanism that carries environment variables from their source into a running process.

```
                           PRODUCTION (Kubernetes)                                  LOCAL (Container mode / Workbench mode)
 ┌──────────────────────────────────────────────────────────────────┐  ┌──────────────────────────────────────────────────────────────────┐
 │                                                                  │  │                                                                  │
 │  .env file                                                       │  │  .env file                                                       │
 │    │                                                             │  │    │                                                             │
 │    ▼                                                             │  │    ├──▶ docker-compose env_file: ../.env                          │
 │  bootstrap_secrets.py                                            │  │    │     Loads SQL_SERVER_*, DOCKER_HUB_*, IPQS_KEY               │
 │    │                                                             │  │    │     into every application container                         │
 │    ├──▶ armada-sql-server-secret     (SQL credentials)           │  │    │                                                             │
 │    ├──▶ armada-docker-registry-secret (image pull auth)          │  │    ├──▶ docker-compose environment: block                         │
 │    ├──▶ armada-docker-username-secret (Docker Hub username)      │  │    │     Orchestrator only: PLATFORM, RABBITMQ_URL,               │
 │    └──▶ armada-ipqs-secret           (IPQualityScore API key)    │  │    │     REDIS_HOST, REDIS_PORT, service URLs                     │
 │              │                                                   │  │    │     Uses Docker DNS names as hostnames                        │
 │              ▼                                                   │  │    │                                                             │
 │  Helm templates (deploy/templates/*)                             │  │    └──▶ python-dotenv  (workbench only)                           │
 │    │                                                             │  │          load_env.py reads .env into os.environ                   │
 │    ├──▶ valueFrom.secretKeyRef  ─── reads secrets into pod env   │  │          Code uses os.getenv() with localhost defaults            │
 │    ├──▶ value: "..."            ─── hardcoded env vars           │  │                                                                  │
 │    └──▶ {{ .Values.* }}         ─── Helm values interpolation    │  │  Workbench-specific:                                             │
 │              │                                                   │  │    uuid.uuid4() ────▶ RUN_ID     (generated per run)              │
 │              ▼                                                   │  │    hardcoded 0  ────▶ POD_INDEX  (single-agent mode)               │
 │  Long-lived Deployments (Orchestrator, Backend, Proxy, etc.)     │  │                                                                  │
 │                                                                  │  └──────────────────────────────────────────────────────────────────┘
 │  Orchestrator (at runtime, via kubernetes_service.py):            │
 │    │                                                             │
 │    ├──▶ V1EnvVar(value=...)             ─── hardcoded values     │
 │    │     RUN_ID, REDIS_HOST, REDIS_PORT, RABBITMQ_URL,           │
 │    │     PROXY_PROVIDER_URL, FINGERPRINT_PROVIDER_URL,           │
 │    │     BACKEND_URL, REQUIREMENTS_TXT                           │
 │    │                                                             │
 │    ├──▶ V1EnvVar(valueFrom=secretKeyRef) ── secret references    │
 │    │     SQL_SERVER_USER, SQL_SERVER_DB,                          │
 │    │     SQL_SERVER_PASSWORD, SQL_SERVER_NAME                     │
 │    │                                                             │
 │    └──▶ V1EnvVar(valueFrom=fieldRef)     ── downward API         │
 │          POD_INDEX from job-completion-index annotation           │
 │              │                                                   │
 │              ▼                                                   │
 │  Short-lived Agent Pods (Indexed Jobs)                           │
 │                                                                  │
 └──────────────────────────────────────────────────────────────────┘
```

### Channel details

| Channel | When it runs | What it does | Files involved |
|---|---|---|---|
| **`bootstrap_secrets.py`** | Once, during cluster setup | Reads the `.env` file, builds four Kubernetes Secret objects via the Python K8s client, and applies them (create or update) to the target namespace. | `bootstrap/bootstrap_secrets.py` |
| **Helm template rendering** | At every `helm install` / `helm upgrade` | Templates in `deploy/templates/` are rendered with values from `deploy/values.yaml` and CLI `--set` overrides. `valueFrom.secretKeyRef` blocks reference the secrets created above; `{{ .Values.* }}` expressions inject non-secret config. | `deploy/templates/**/*.yaml`, `deploy/values.yaml` |
| **Orchestrator Job builder** | Every time a run is launched | `kubernetes_service.py` constructs a `V1Job` object in Python, embedding env vars as `V1EnvVar` entries — some with literal values, some with `secretKeyRef`, and `POD_INDEX` via the Kubernetes downward API `fieldRef`. | `services/orchestrator/app/services/kubernetes_service.py` |
| **Docker Compose `env_file`** | At `docker-compose up` | All application services declare `env_file: ../.env`, which loads every key=value pair from the root `.env` into the container environment. | `local/docker-compose.yml`, `.env` |
| **Docker Compose `environment`** | At `docker-compose up` | The Orchestrator service additionally receives inline env vars for inter-service URLs and platform flags. These use Docker Compose service names as hostnames (resolved by Docker's built-in DNS). | `local/docker-compose.yml` |
| **`python-dotenv` (workbench mode)** | When running `run_workbench.py` | `load_env.py` calls `dotenv.load_dotenv()` to inject `.env` values into `os.environ`. The workbench then generates a `RUN_ID` via `uuid.uuid4()` and sets `POD_INDEX=0` manually, since there is no Kubernetes to provide these. | `services/project/workbench/load_env.py`, `services/project/workbench/run_workbench.py` |

---

## Kubernetes Secrets — Creation and Lifecycle

Kubernetes Secrets are the secure storage mechanism for credentials in production. They are **not** part of the Helm
chart — they are created separately by the bootstrap script so that sensitive values never appear in version-controlled
Helm values files.

### How secrets are created

The script `bootstrap/bootstrap_secrets.py` performs the following steps:

1. **Reads the `.env` file** from the repository root using `python-dotenv`.
2. **Checks required keys** for each secret. If any key is missing, that secret is skipped with a warning.
3. **Builds `V1Secret` objects** using the Kubernetes Python client:
   - `armada-sql-server-secret` — type `Opaque`, contains `SQL_SERVER_USER`, `SQL_SERVER_PASSWORD`, `SQL_SERVER_DB`, `SQL_SERVER_NAME`.
   - `armada-docker-registry-secret` — type `kubernetes.io/dockerconfigjson`, contains a Docker config JSON with Hub credentials and a base64-encoded auth token.
   - `armada-docker-username-secret` — type `Opaque`, contains the Docker Hub `username` (used by the Orchestrator to build image references).
   - `armada-ipqs-secret` — type `Opaque`, contains the `IPQS_KEY` for IPQualityScore proxy quality checks.
4. **Applies each secret** to the target namespace (default: `default`). If the secret already exists, it is replaced; otherwise it is created.

```bash
# Typical usage during cluster bootstrap
pip install kubernetes python-dotenv
python bootstrap/bootstrap_secrets.py --namespace default
```

### How secrets are consumed

Helm deployment templates reference these secrets using `valueFrom.secretKeyRef`:

```yaml
# Example from deploy/templates/backend/backend-deployment.yaml
env:
  - name: SQL_SERVER_USER
    valueFrom:
      secretKeyRef:
        name: armada-sql-server-secret
        key: SQL_SERVER_USER
```

When Kubernetes creates or restarts a pod, the kubelet reads the referenced secret from the API server
and injects its value as a plain-text environment variable inside the container. The application code
reads it with a standard `os.getenv("SQL_SERVER_USER")` call — it has no knowledge that the value
originated from a Secret.

For agent pods, the Orchestrator's `kubernetes_service.py` builds the same `secretKeyRef` pattern
programmatically using `V1EnvVarSource(secret_key_ref=V1SecretKeySelector(...))`.

### Four secrets at a glance

| Secret name | Type | Keys | Created by | Consumed by |
|---|---|---|---|---|
| `armada-sql-server-secret` | `Opaque` | `SQL_SERVER_USER`, `SQL_SERVER_PASSWORD`, `SQL_SERVER_DB`, `SQL_SERVER_NAME` | `bootstrap_secrets.py` | Backend, Orchestrator, Proxy Provider, Fingerprint Provider, Agent pods |
| `armada-docker-registry-secret` | `kubernetes.io/dockerconfigjson` | `.dockerconfigjson` | `bootstrap_secrets.py` | Agent pods (`imagePullSecrets`) |
| `armada-docker-username-secret` | `Opaque` | `username` | `bootstrap_secrets.py` | Orchestrator (to build image references in Job specs) |
| `armada-ipqs-secret` | `Opaque` | `IPQS_KEY` | `bootstrap_secrets.py` | Proxy Provider (`optional: true`) |

---

## Helm Values Injection

Some environment variables in production originate from Helm values — template parameters that Helm
resolves at deploy time into the final Kubernetes YAML. When a Helm value is placed inside an `env:`
block, it becomes a container environment variable. But Helm values also control non-env aspects of the
manifest (image references, pull policies, registry secrets) that never reach the process environment.

For the complete reference on all Helm values — including those that do **not** become environment
variables — see the dedicated [Helm Values]({{< relref "helm-values" >}}) page.

---

## Agent Pod Environment Variables

These are the environment variables injected into every agent pod by the Kubernetes Job spec
built in `kubernetes_service.py`:

### Injected directly by the Orchestrator

| Variable | Source | Value example | Description |
|---|---|---|---|
| `RUN_ID` | Orchestrator (hardcoded in Job spec) | `a1b2c3d4-e5f6-...` | Unique run identifier. Also used as the Celery queue name. |
| `POD_INDEX` | Kubernetes downward API | `0`, `1`, `2` | Derived from `metadata.annotations['batch.kubernetes.io/job-completion-index']`. Identifies which agent this pod represents. |
| `REDIS_HOST_VAR_ENV` | Orchestrator (hardcoded) | `armada-redis` | Redis hostname for fetching agent config at startup. |
| `REDIS_PORT_VAR_ENV` | Orchestrator (hardcoded) | `6379` | Redis port. |
| `RABBITMQ_URL` | Orchestrator (hardcoded) | `amqp://armada-rabbitmq:5672` | RabbitMQ broker URL for the Celery worker. |
| `PROXY_PROVIDER_URL` | Orchestrator config | `http://armada-proxy-provider:5001` | URL of the proxy provider service. |
| `FINGERPRINT_PROVIDER_URL` | Orchestrator config | `http://armada-fingerprint-provider:5005` | URL of the fingerprint provider service. |
| `BACKEND_URL` | Orchestrator config | `http://armada-backend:8000` | URL of the backend API for monitoring events. |
| `REQUIREMENTS_TXT` | Orchestrator (base64-encoded) | `cmVxdWVzdHM9PTIuMzEuMA==` | Optional. Base64-encoded `requirements.txt` content. Decoded and installed by `entrypoint.sh` before the worker starts. |

### Injected from Kubernetes Secrets

| Variable | Secret name | Key | Description |
|---|---|---|---|
| `SQL_SERVER_NAME` | `armada-sql-server-secret` | `SQL_SERVER_NAME` | SQL Server hostname |
| `SQL_SERVER_DB` | `armada-sql-server-secret` | `SQL_SERVER_DB` | Database name |
| `SQL_SERVER_USER` | `armada-sql-server-secret` | `SQL_SERVER_USER` | Database username |
| `SQL_SERVER_PASSWORD` | `armada-sql-server-secret` | `SQL_SERVER_PASSWORD` | Database password |

### Defaults (used when variable is not set)

| Variable | Default | Used by |
|---|---|---|
| `RABBITMQ_URL` | `amqp://localhost:5672` | `services/agent/main.py` |
| `REDIS_HOST_VAR_ENV` | `localhost` | `services/agent/src/load_agent_message.py` |
| `REDIS_PORT_VAR_ENV` | `6379` | `services/agent/src/load_agent_message.py` |
| `BACKEND_URL` | `http://localhost:8000` | `services/agent/src/monitoring_client.py` |
| `PROXY_PROVIDER_URL` | `http://127.0.0.1:5001` | `services/agent/src/proxy_manager.py` |
| `FINGERPRINT_PROVIDER_URL` | `http://localhost:5005` | `services/agent/src/fingerprint_manager.py` |
| `POD_INDEX` | `0` | `services/agent/src/load_agent_message.py` |

---

## Orchestrator Environment Variables

| Variable | Source | Description |
|---|---|---|
| `PLATFORM` | Helm values / docker-compose | `"distant"` (production) or `"local"` (Docker Compose). Controls whether the orchestrator creates Kubernetes Jobs. |
| `DISTRIB` | Helm values | `"kube"` (production) or `"minikube"`. Controls `imagePullPolicy` (`Always` vs `Never`) and registry secrets. |
| `REDIS_HOST` | Helm values / docker-compose | Redis hostname for pushing agent configs. |
| `REDIS_PORT` | Helm values / docker-compose | Redis port. |
| `RABBITMQ_URL` | Helm values / docker-compose | RabbitMQ URL for dispatching job messages. |
| `PROXY_PROVIDER_URL` | Helm values / docker-compose | Forwarded to agent pods as env var. |
| `FINGERPRINT_PROVIDER_URL` | Helm values / docker-compose | Forwarded to agent pods as env var. |
| `BACKEND_URL` | Helm values / docker-compose | Forwarded to agent pods as env var. |
| `DOCKER_HUB_USERNAME` | Kubernetes Secret | Docker Hub username for image references in the Kubernetes Job spec. |

---

## Backend API Environment Variables

| Variable | Source | Description |
|---|---|---|
| `SQL_SERVER_NAME` | `.env` / Kubernetes Secret | SQL Server hostname |
| `SQL_SERVER_DB` | `.env` / Kubernetes Secret | Database name |
| `SQL_SERVER_USER` | `.env` / Kubernetes Secret | Database username |
| `SQL_SERVER_PASSWORD` | `.env` / Kubernetes Secret | Database password |

---

## Proxy Provider Environment Variables

| Variable | Source | Description |
|---|---|---|
| `SQL_SERVER_NAME` | `.env` / Kubernetes Secret | SQL Server hostname |
| `SQL_SERVER_DB` | `.env` / Kubernetes Secret | Database name |
| `SQL_SERVER_USER` | `.env` / Kubernetes Secret | Database username |
| `SQL_SERVER_PASSWORD` | `.env` / Kubernetes Secret | Database password |
| `IPQS_KEY` | `.env` / Kubernetes Secret | IPQualityScore API key for proxy quality checks |

---

## Fingerprint Provider Environment Variables

| Variable | Source | Description |
|---|---|---|
| `SQL_SERVER_NAME` | `.env` / Kubernetes Secret | SQL Server hostname |
| `SQL_SERVER_DB` | `.env` / Kubernetes Secret | Database name |
| `SQL_SERVER_USER` | `.env` / Kubernetes Secret | Database username |
| `SQL_SERVER_PASSWORD` | `.env` / Kubernetes Secret | Database password |

---

## Local Development — Container mode (Docker Compose)

In `local/docker-compose.yml`, environment variables are set through two mechanisms:

### 1. `env_file` directive

All application services use `env_file: ../.env` to load the root `.env` file. This provides SQL Server credentials and API keys.

### 2. `environment` directive (Orchestrator only)

The orchestrator gets additional variables for inter-service communication:

```yaml
armada-orchestrator:
  environment:
    PLATFORM: "local"
    RABBITMQ_URL: "amqp://armada-rabbitmq:5672"
    REDIS_HOST: "armada-redis"
    REDIS_PORT: "6379"
    PROXY_PROVIDER_URL: "http://armada-proxy-provider:5001"
    FINGERPRINT_PROVIDER_URL: "http://armada-fingerprint-provider:5005"
    BACKEND_URL: "http://armada-backend:8000"
```

These use Docker Compose service names as hostnames, which Docker's internal DNS resolves to the correct container.

---

## Local Development — Workbench mode

The workbench (`services/project/workbench/run_workbench.py`) loads environment variables from the `.env` file via `python-dotenv`:

```python
from load_env import *  # loads .env into os.environ
```

Since the workbench runs outside Docker, it uses `localhost` addresses (the defaults) to reach services started by Docker Compose with exposed ports. The workbench also generates values that would normally come from Kubernetes:

- **`RUN_ID`** — generated as `uuid.uuid4()` instead of being passed by the Orchestrator.
- **`POD_INDEX`** — hardcoded to `0` since the workbench always simulates a single agent.
