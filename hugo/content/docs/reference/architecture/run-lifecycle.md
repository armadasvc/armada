---
title: 4.1.2. Run Lifecycle
linkTitle: 4.1.2. Run Lifecycle
weight: 2
description: End-to-end walkthrough of a production run — frontend preparation, orchestrator processing, agent startup, job execution, monitoring, and shutdown
---

## Production Run — End-to-End

A production run involves every component of the platform. This section follows the exact sequence of operations.

### Phase 1 — Frontend Prepares the Payload

When the user clicks **Launch**, the frontend performs four operations before any network call:

**1. Script bundling.** The bundler reads `main.py` and recursively inlines every `from X import Y` where `X` is in the `addon/` folder or where the filename starts with `ctx`. The result is a single Python string with all user code concatenated. Imports from standard libraries or pip packages are left untouched. See [Code Bundling and Execution]({{< relref "/docs/reference/architecture/code-bundling-execution" >}}) for the complete bundling rules.

```
main.py
  ├── from ctx_agent_context import AgentContext   → inlined
  ├── from ctx_job_context import JobContext         → inlined
  ├── from ctx_script import ctx_script              → inlined
  ├── from addon.my_modifier import modifier         → inlined
  └── from celery.signals import ...                 → left as-is (stdlib/pip)
```

**2. Environment substitution.** Every string in `config_template.json` that starts with `$env_` is replaced by the corresponding value from the config tune file (`config_local.json` or `config_distant.json`). See [JSON Configuration — Environment Substitution]({{< relref "/docs/setting-up-project/json-config#environment-substitution" >}}) for the full mechanism.

**3. UUID and code injection.** The frontend generates a `run_id` (UUID v4) and injects both the `run_id` and the bundled Python code into the config:

```json
{
  "run_message":          { "run_id": "a1b2c3d4-..." },
  "default_agent_message": { "code": "...bundled python...", "run_id": "a1b2c3d4-..." },
  "default_job_message":   { "run_id": "a1b2c3d4-..." }
}
```

**4. FormData POST.** The frontend sends a `multipart/form-data` request to the orchestrator at `POST /bot/start` with five parts:

| Part name | Content |
|---|---|
| `configtemplate` | The fully processed JSON config (with env values resolved, UUID and code injected) |
| `configtune` | The raw config tune JSON |
| `data_job` | CSV file with per-job overrides |
| `data_agent` | CSV file with per-agent overrides |
| `requirements_txt` | Optional — extra pip dependencies |

---

### Phase 2 — Orchestrator Processes the Request

The orchestrator's `POST /bot/start` handler executes five steps synchronously:

**Step 1 — Parse inputs.**

```python
configtemplate_content = json.loads(configtemplate.file.read())
list_of_json_output_job = parse_csv_to_list(data_job)
list_of_json_output_agent = parse_csv_to_list(data_agent)
```

CSV parsing deserializes each row into a dict, recursively parsing any JSON-shaped cell values. Each row is tagged with its index:

```python
# Row 0 of data_agent.csv → {"proxy_location": "US", "targetted_agent": 0}
# Row 1 of data_agent.csv → {"proxy_location": "FR", "targetted_agent": 1}
```

**Step 2 — Deep merge.** For each agent index `i` in `[0, number_of_agents)`, the orchestrator deep-merges the CSV override row onto a copy of `default_agent_message`. The same logic applies to job messages. See [Configuration Pipeline — CSV Deep Merge]({{< relref "/docs/reference/architecture/configuration-pipeline#layer-3--csv-overrides-deep-merge" >}}) for the algorithm details.

**Step 3 — Push to Redis.** Each consolidated agent message (which now contains the bundled code, the run_id, and all config) is serialized to JSON and stored in Redis:

```python
redis.set(f"{run_id}{agent_index}", json.dumps(agent_message))
# Key example: "a1b2c3d4-...0", "a1b2c3d4-...1", etc.
```

**Step 4 — Create Kubernetes Job** (production mode only). The orchestrator uses the `kubernetes-client` to create a `batch/v1` Job:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: armada-agent-{run_id}
spec:
  completionMode: Indexed
  completions: N        # one per agent
  parallelism: N        # all at once
  ttlSecondsAfterFinished: 1000000
  template:
    spec:
      containers:
      - name: armada-agent
        image: {hub}/armada-agent:{version}
        env:
          - name: RUN_ID
            value: "{run_id}"
          - name: POD_INDEX
            valueFrom:
              fieldRef:
                fieldPath: "metadata.annotations['batch.kubernetes.io/job-completion-index']"
          - name: SQL_SERVER_*
            valueFrom:
              secretKeyRef: armada-sql-server-secret
          # ... Redis, RabbitMQ, service URLs
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: kubernetes.io/hostname
        whenUnsatisfiable: ScheduleAnyway
```

Key points:
- `completionMode: Indexed` gives each pod a unique index via `batch.kubernetes.io/job-completion-index`
- `POD_INDEX` is derived from this annotation
- Topology spread distributes pods across nodes
- `imagePullPolicy` is `Never` on Minikube, `Always` in production

**Step 5 — Dispatch jobs via Celery.** For each consolidated job message, the orchestrator sends a Celery task to RabbitMQ:

```python
celery_app.send_task(
    "tasks.consume_message",
    args=[job_message],
    queue=run_id
)
```

A background thread then monitors the queue every 15 seconds. When the queue is empty and no tasks are active, it shuts down all workers listening on that queue.

---

### Phase 3 — Agent Pod Starts

Each agent pod runs the same image (`armada-agent`). The entrypoint is `entrypoint.sh`:

```bash
# 1. Install extra pip dependencies if provided
if [ -n "$REQUIREMENTS_TXT" ]; then
  echo "$REQUIREMENTS_TXT" | base64 -d > /tmp/requirements.txt
  pip install -r /tmp/requirements.txt
fi

# 2. Start Celery worker
exec python -m celery -A main worker \
  --queues="$RUN_ID" \
  --concurrency=1 \
  -n worker"$POD_INDEX" \
  --prefetch-multiplier=1
```

`celery -A main` imports `main.py`, which does three things:

```python
# services/agent/main.py
agent_message = load_agent_message()      # Fetch from Redis
app = Celery('celery_app', broker=RABBITMQ_URL)
exec(agent_message["code"], {'app': app, 'agent_message': agent_message})
```

The `exec()` call loads the project's bundled `main.py` into the agent process. From this point, the project's code takes over and defines Celery signals and tasks.

---

### Phase 4 — Worker Initialization

The project's `main.py` (now running inside `exec()`) registers three things:

```python
@worker_process_init.connect
def init_worker(sender, **kwargs):
    # Runs once per worker process
    event_loop = asyncio.new_event_loop()
    agent_ctx = await AgentContext(agent_message).__aenter__()
    # → ProxyManager, FingerprintManager, DatabaseConnector
    # → Screen (Xvfb), FantomasNoDriver (Chrome)

@worker_process_shutdown.connect
def shutdown_worker(sender, **kwargs):
    # Runs when the worker process terminates
    agent_ctx.__aexit__(None, None, None)
    # → browser.stop(), screen.stop_screen()

@app.task(name='tasks.consume_message', queue=agent_message["run_id"])
def run_job(job_message):
    # Runs for each job consumed from RabbitMQ
    event_loop.run_until_complete(process_message(job_message, agent_ctx))
```

The `AgentContext` initializes heavy resources **once** — browser, display server, proxy, database connection. These persist across all jobs processed by this agent. See [Python Files]({{< relref "/docs/setting-up-project/python-files" >}}) for the `AgentContext` and `JobContext` class reference.

---

### Phase 5 — Job Execution

For each job message consumed from RabbitMQ:

```python
async def process_message(job_message, agent_ctx):
    async with JobContext(job_message) as job_ctx:
        await ctx_script(job_ctx, agent_ctx)
```

`JobContext.__aenter__` creates:
- A new `job_uuid` (UUID v4)
- A `MonitoringClient` that registers the run and job with the backend API (`POST /api/runs/`, `POST /api/jobs/`)
- An `Identity` object (fake person via Fantomas)

`ctx_script` is the user's automation function (see [Python Files — ctx_script.py]({{< relref "/docs/setting-up-project/python-files#ctx_scriptpy--the-script-context" >}})). It has access to:
- `agent_ctx.browser` — Chrome browser instance
- `agent_ctx.proxy_manager` — local mitmproxy with optional upstream
- `agent_ctx.fingerprint_manager` — fingerprint forging
- `agent_ctx.database` — SQL Server connector
- `job_ctx.monitoring_client` — event reporting
- `job_ctx.identity` — generated identity

---

### Phase 6 — Monitoring and Real-Time Updates

Throughout execution, the agent reports events to the backend:

```
Agent → POST /api/events/ → Backend → WebSocket broadcast → Frontend
Agent → PATCH /api/jobs/status → Backend → WebSocket broadcast → Frontend
```

The backend API stores every mutation in SQL Server and immediately broadcasts it to all connected WebSocket clients. The frontend's monitor panel updates in real time. See the [Monitoring Client guide]({{< relref "/docs/guides/monitoring-client" >}}) for the user-facing reporting API.

---

### Phase 7 — Shutdown

When the orchestrator's monitoring thread detects an empty queue with no active tasks:

1. It calls `celery_app.control.shutdown(destination=[worker])` for each worker on the run's queue
2. Celery triggers the `worker_process_shutdown` signal
3. `AgentContext.__aexit__` stops the browser and virtual display
4. The pod terminates
5. Kubernetes garbage-collects the pod after `ttlSecondsAfterFinished` (approximately 11.5 days)

---

## Local Workbench Run

The workbench (`services/project/workbench/run_workbench.py`) replicates the same execution flow without Kubernetes or Redis. It synthesizes `agent_message` and `job_message` from local config files, then calls `init_worker`, `run_job`, and `shutdown_worker` directly as functions instead of relying on Celery signals and RabbitMQ message delivery.

For the complete workbench synthesis pipeline, see [Workbench Mode under the hood]({{< relref "/docs/reference/deployment/workbench" >}}).