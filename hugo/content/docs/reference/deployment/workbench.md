---
title: 4.3.2. Workbench Mode under the hood
linkTitle: 4.3.2. Workbench Mode under the hood
weight: 2
description: How the workbench synthesizes agent and job messages from local config files and executes the full agent lifecycle without Kubernetes or Redis
---

## Overview

The workbench is a local execution harness that replicates the production agent lifecycle without Kubernetes, the orchestrator, or Redis. It lives as a `workbench/` folder inside each project directory and is responsible for **synthesizing** the same `agent_message` and `job_message` that the agent would receive in production — but from local files instead of infrastructure services.

The result is that a developer can run their `ctx_script.py` locally with the exact same code path that production uses, including `exec()` of `main.py`, Celery app creation, and the full `init_worker` → `run_job` → `shutdown_worker` lifecycle.

---

## How Agent Synthesis Works

When you run `python -m workbench.run_workbench` from a project directory, the workbench performs the following sequence to construct a fully functional agent locally.

### Step 1 — Environment Setup

**`load_env.py`** uses `python-dotenv` to load environment variables from the nearest `.env` file. This provides secrets like `SQL_SERVER_PASSWORD`, `PROXY_PROVIDER_URL`, etc., that the agent and context classes need at import time.

**`lib_loader.py`** reads the `workbench/agent_path` file (a plain text file containing the absolute path to `services/agent`, e.g., `/home/user/armada/services/agent`) and appends it to `sys.path`. This makes agent-internal modules (`src.proxy_manager`, `src.fingerprint_manager`, `src.database_connector`, `src.monitoring_client`) importable from within the project.

### Step 2 — Message Synthesis

**`get_messages.py`** builds the `agent_message` and `job_message` dictionaries that the agent would normally receive from Redis and RabbitMQ. The synthesis pipeline has four stages:

#### 2a. Load Template

Reads `config/config_template.json`, which contains the base configuration with two top-level keys:

```json
{
  "run_message": { ... },
  "default_agent_message": { ... },
  "default_job_message": { ... }
}
```

#### 2b. Resolve `$env_` Placeholders (environment substitution)

Reads `config/config_local.json` (a flat key-value map). Any string value in the template that starts with `$env_` is replaced with the corresponding value from this file (see [JSON Configuration — Environment Substitution]({{< relref "/docs/setting-up-project/json-config#environment-substitution" >}})).

For example, if the template contains `"screen_visible": "$env_SCREEN_VISIBLE"` and `config_local.json` contains `{"SCREEN_VISIBLE": 1}`, the resolved value becomes `"screen_visible": 1`.

The replacement is recursive — it walks through nested dictionaries and arrays.

#### 2c. Load CSV Overrides

Reads `config/data_agent.csv` and `config/data_job.csv`. Only the **first row** of each CSV is used. CSV values that look like JSON (starting with `{` or `[`) are parsed recursively into actual Python objects using `parse_value()`:

```
custom_agent_field,config_proxy
agent_override_value,{"proxy_provider_name": "override_provider"}
```

This row becomes:
```python
{"custom_agent_field": "agent_override_value", "config_proxy": {"proxy_provider_name": "override_provider"}}
```

#### 2d. Deep Merge

The CSV overrides are **recursively merged** onto the resolved defaults using `merge_dicts()`. If both the default and the override have a dict for the same key, the merge goes deeper. Otherwise, the override replaces the default.

The final output is a `[agent_message, job_message]` tuple.

### Step 3 — Run ID and Pod Index Injection

`run_workbench.py` generates a UUID as the `run_id` and sets `pod_index` to `0` on both messages:

```python
run_id = str(uuid.uuid4())
agent_message["run_id"] = run_id
job_message["run_id"] = run_id
agent_message["pod_index"] = 0
job_message["pod_index"] = 0
```

In production, the orchestrator assigns the `run_id` and Kubernetes assigns the `pod_index` via the `JOB_COMPLETION_INDEX` environment variable.

### Step 4 — Celery App Creation

The workbench creates a Celery application instance pointed at a local RabbitMQ broker:

```python
app = Celery('celery_app', broker="amqp://localhost")
```

This app object is injected into `main.py` exactly as the agent does in production.

### Step 5 — `exec()` of main.py

The workbench reads `main.py` as text and executes it with injected variables:

```python
namespace = {
    'app': app,
    'agent_message': agent_message,
    'job_message': job_message,
    '__name__': '__main__',
    '__file__': main_path,
}
exec(main_code, namespace)
```

This is the same `exec()` pattern the production agent uses (see [Code Bundling and Execution]({{< relref "/docs/reference/architecture/code-bundling-execution" >}})). After execution, the namespace contains the three lifecycle functions defined in `main.py`: `init_worker`, `run_job`, and `shutdown_worker`.

### Step 6 — Lifecycle Execution

The workbench manually calls the three lifecycle functions that Celery would normally trigger via signals:

```python
namespace['init_worker'](sender="local-test")    # → AgentContext.__aenter__()
namespace['run_job'](job_message)                 # → JobContext.__aenter__() → ctx_script()
namespace['shutdown_worker'](sender="local-test") # → AgentContext.__aexit__()
```

In production, `init_worker` is triggered by `worker_process_init`, `run_job` is a Celery task consumed from RabbitMQ, and `shutdown_worker` is triggered by `worker_process_shutdown`.

---

## Production vs. Workbench Comparison

| Aspect | Production (agent pod) | Workbench |
|---|---|---|
| Config source | Redis (`load_agent_message()`) — see [Run Lifecycle]({{< relref "/docs/reference/architecture/run-lifecycle" >}}) | `config/config_template.json` + `config_local.json` |
| Job source | RabbitMQ queue | Synthesized from `config/data_job.csv` |
| `$env_` resolution | Frontend resolves before sending to orchestrator | `get_messages.py` resolves from `config_local.json` |
| CSV merge | Frontend merges before sending to orchestrator | `get_messages.py` merges locally |
| `run_id` | Assigned by orchestrator | Generated as UUID |
| `pod_index` | Kubernetes `JOB_COMPLETION_INDEX` env var | Hardcoded to `0` |
| `main.py` execution | Agent's `exec()` with Celery signals | Workbench's `exec()` with manual calls |
| Broker | RabbitMQ (cluster URL from env) | Local RabbitMQ (`amqp://localhost`) |
| Agent modules | Bundled in Docker image | Loaded via `lib_loader.py` + `agent_path` |
| Number of jobs | Unlimited | 1 only |