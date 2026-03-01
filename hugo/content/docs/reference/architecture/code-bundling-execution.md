---
title: 4.1.4. Code Bundling and Execution
linkTitle: 4.1.4. Code Bundling and Execution
weight: 4
description: Frontend script bundler, code injection into config, Redis transport, agent-side exec(), and requirements.txt handling
---

## The Problem

Armada uses a single, generic Docker image for the agent (`armada-agent`). This image contains the Python runtime, Chrome, Xvfb, mitmproxy, and all base libraries — but **no project-specific code**. The user's automation logic (`ctx_script.py`, `ctx_agent_context.py`, `addon/` modules, etc.) must be delivered at runtime without rebuilding the image.

## The Solution: Bundle, Transport, `exec()`

```
Frontend                    Orchestrator              Redis                  Agent Pod
   │                            │                      │                       │
   ├─ Bundle main.py ─────────▶ │                      │                       │
   │  (inline ctx_*, addon/*)   │                      │                       │
   │                            │                      │                       │
   ├─ Inject code into config ─▶│                      │                       │
   │                            ├─ Redis SET ─────────▶│                       │
   │                            │  (agent_message      │                       │
   │                            │   with "code" field) │                       │
   │                            │                      │                       │
   │                            │                      │◀── Redis GET ─────────┤
   │                            │                      │    (on pod startup)   │
   │                            │                      │                       │
   │                            │                      │                       │ exec(code, {app,agent_message})
   │                            │                      │                       │
```

---

## Step 1 — Frontend Script Bundler

The bundler (`services/frontend/src/utils/launcher/scriptBundler.ts`) takes `main.py` and recursively inlines specific imports into a single Python string.

### Inlining rules

A `from X import Y` statement is inlined if `X` matches one of these criteria:

| Criterion | Example |
|---|---|
| File is in the `addon/` directory | `from addon.my_modifier import modify_response` |
| Filename starts with `ctx` | `from ctx_script import ctx_script` (see [Python Files]({{< relref "/docs/setting-up-project/python-files" >}})) |

All other imports (standard library, pip packages, `celery`, `asyncio`, etc.) are left as-is because they are available in the agent's Docker image.

### Recursion

The bundler is recursive. If `ctx_agent_context.py` itself imports from `addon/some_helper.py`, that helper is also inlined. A `Set<string>` of already-processed files prevents infinite loops and duplicate inlining.

---

## Step 2 — Code Injection into Config

After bundling, the frontend injects the Python string into the config under `default_agent_message.code`:

```typescript
// services/frontend/src/utils/launcher/configProcessor.ts
function addUuidAndCodeToConfig(config, code) {
  config.default_agent_message.code = code
  config.default_agent_message.run_id = uuidv4()
  config.default_job_message.run_id = runId
  config.run_message.run_id = runId
  return config
}
```

The code travels as a JSON string field through the entire pipeline:
1. Frontend → Orchestrator (HTTP POST, inside JSON body)
2. Orchestrator → Redis (Redis SET, inside serialized agent message)
3. Redis → Agent (Redis GET at pod startup)

---

## Step 3 — Agent-Side `exec()`

The agent's own `main.py` (`services/agent/main.py`) is minimal:

```python
from src.load_agent_message import load_agent_message
from celery import Celery
import os

agent_message = load_agent_message()

app = Celery('celery_app')
app.conf.update(broker_url=os.getenv("RABBITMQ_URL", "amqp://localhost:5672"))

exec(agent_message["code"], {'app': app, 'agent_message': agent_message})
```

### What `exec()` does

`exec(code, namespace)` executes the Python string `code` inside the provided `namespace` dict. The namespace serves as both the global and local scope for the executed code. This means:

- The project's `main.py` can reference `app` (the Celery instance) without importing it
- The project's `main.py` can reference `agent_message` (the full config dict) without importing it
- Any functions, classes, or variables defined by the executed code are accessible via the namespace

### What the project's `main.py` defines

After `exec()`, the project's code has registered:

1. **`init_worker`** — Celery `worker_process_init` signal handler that creates `AgentContext`
2. **`shutdown_worker`** — Celery `worker_process_shutdown` signal handler that tears down `AgentContext`
3. **`run_job`** — Celery task `tasks.consume_message` that processes a single job message

The Celery worker (started by `entrypoint.sh`) then calls these through its normal signal and task dispatch mechanisms.

---

## Step 4 — Extra Dependencies (`requirements.txt`)

If the user includes a `requirements.txt` in their project, the frontend sends it as a separate form part. The orchestrator base64-encodes the file content and passes it as the `REQUIREMENTS_TXT` environment variable on the Kubernetes pod.

At pod startup, `entrypoint.sh` decodes and installs the packages before starting the Celery worker:

```bash
if [ -n "$REQUIREMENTS_TXT" ]; then
  echo "$REQUIREMENTS_TXT" | base64 -d > /tmp/requirements.txt
  pip install -r /tmp/requirements.txt
fi
```

This allows projects to use pip packages that are not in the base agent image. See [Python Files — requirements.txt]({{< relref "/docs/setting-up-project/python-files#requirementstxt--extra-dependencies" >}}) for what the base image already includes.

---

## Why `exec()` Instead of Alternatives

| Alternative | Why it was not chosen |
|---|---|
| Rebuild Docker image per project | Slow, requires Docker daemon access, scales poorly |
| Mount code as ConfigMap/volume | Kubernetes ConfigMaps have a 1MB size limit; volume mounts add complexity |
| Download code from a file server | Adds another service to maintain; Redis already stores the config |
| `importlib` dynamic import | Requires files on disk; `exec()` works directly from a string |

The `exec()` approach enables a **single immutable agent image** to run arbitrary project code. The trade-off is that all user code must be bundleable into a single Python string (no binary assets, no complex package structures). Do not expose the cluster to the outside world, see [Security](../deployment/security)

---

## Workbench mode Variant

In the local workbench mode, the same `exec()` pattern is used, but the code comes from disk instead of Redis:

```python
# services/project/workbench/run_workbench.py
with open('main.py', 'r') as f:
    main_code = f.read()

namespace = {
    'app': app,
    'agent_message': agent_message,
    'job_message': job_message,
}
exec(main_code, namespace)

# Then call the functions directly
namespace['init_worker'](sender="local-test")
namespace['run_job'](job_message)
namespace['shutdown_worker'](sender="local-test")
```

The only difference is that the workbench does not go through Celery's signal mechanism — it calls `init_worker`, `run_job`, and `shutdown_worker` as regular functions.
