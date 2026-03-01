---
title: 4.1.5. Agent Internals
linkTitle: 4.1.5. Agent Internals
weight: 5
description: Agent Docker image contents, startup sequence, concurrency model, and available built-in modules
---

## Agent Container Contents

The agent Docker image (`services/agent/Dockerfile`) is based on `python:3.12-slim` and includes:

| Component | Purpose |
|---|---|
| Google Chrome | Real browser engine for automation |
| Xvfb | Virtual framebuffer (X11 display server) |
| xdotool | OS-level mouse/keyboard simulation |
| ImageMagick | Image processing utilities |
| mitmproxy | Local HTTPS proxy for traffic interception |
| lsof | Process management for proxy cleanup |
| CA certificates | TLS trust chain |

The container runs as a non-root user (`celeryuser`, UID 1000).

---

## Startup Sequence

```
entrypoint.sh
  │
  ├─ [optional] pip install requirements.txt (base64 decoded)
  │
  └─ exec celery -A main worker
       --queues=$RUN_ID
       --concurrency=1
       -n worker$POD_INDEX
       --prefetch-multiplier=1
            │
            ├─ Python imports main.py
            │    ├─ load_agent_message() from Redis
            │    ├─ Create Celery app
            │    └─ exec(agent_message["code"], {app, agent_message})  [details]
            │         └─ Project's main.py now loaded
            │
            └─ Celery signal: worker_process_init
                 └─ init_worker()
                      ├─ asyncio.new_event_loop()
                      └─ AgentContext.__aenter__()
                           ├─ ProxyManager.launch_proxy()
                           ├─ FingerprintManager (ready)
                           ├─ DatabaseConnector (connected)
                           ├─ Screen.launch_screen()
                           └─ Browser.launch()
```

For how the bundled code reaches the agent via Redis, see [Code Bundling and Execution]({{< relref "/docs/reference/architecture/code-bundling-execution" >}}). For how the agent message is constructed from config layers, see [Configuration Pipeline]({{< relref "/docs/reference/architecture/configuration-pipeline" >}}).

### Concurrency model

Each agent pod runs exactly **one** Celery worker process with `concurrency=1` and `prefetch-multiplier=1`. This means:

- One job at a time per pod
- One browser instance per pod
- No contention on the local mitmproxy (port 8081)
- Predictable resource usage

---

## Available Modules

Since your project code executes inside the agent container, it has direct access to several built-in modules through the `AgentContext` and `JobContext` objects. These modules are initialized automatically during the agent lifecycle (see [Startup Sequence](#startup-sequence) and [Context Managers](#context-managers) above) and are ready to use in your task code.

Each module has a dedicated guide covering configuration and usage:

- **ProxyManager** — Local mitmproxy layer for traffic interception, upstream proxy rotation, and addon system. See the [Proxy Provider guide]({{< relref "/docs/guides/proxy-provider" >}}).
- **FingerprintManager** — Fetches forged browser fingerprints from the Fingerprint Provider service. See the [Fingerprint Provider guide]({{< relref "/docs/guides/fingerprint-provider" >}}).
- **DatabaseConnector** — SQL Server connection wrapper for reading and writing data. See the [Database Connector guide]({{< relref "/docs/guides/database-connector" >}}).
- **MonitoringClient** — Reports run/job lifecycle events to the Backend API for real-time dashboard updates. See the [Monitoring Client guide]({{< relref "/docs/guides/monitoring-client" >}}).
