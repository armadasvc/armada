---
title: 3.4. Monitoring Client
linkTitle: 3.4. Monitoring Client
weight: 4
description: Report job lifecycle events to the dashboard using the MonitoringClient API
---

## Overview

The Monitoring Client reports job lifecycle events to the Backend API (see [Backend Service]({{< relref "/docs/reference/services/backend" >}})), which stores them in the database and broadcasts them to the frontend dashboard via WebSocket. This lets you track in real time which jobs are running, which succeeded, and which failed.

```
ctx_script.py
  │
  │  record_success_event("Step done")
  ▼
MonitoringClient ──HTTP POST──► Backend API (port 8000)
                                      │
                                      ├──► SQL Server (armada_runs, armada_jobs, armada_events)
                                      └──► WebSocket ──► Frontend Dashboard
```

## Lifecycle

The monitoring client tracks three levels:

| Level | Description |
|---|---|
| **Run** | A single launch from the frontend. One run can have many agents and jobs (see [Key Concepts]({{< relref "/docs/getting-started/key_concepts" >}})). |
| **Job** | A single unit of work processed by an agent. Each job has a unique UUID. |
| **Event** | A granular step within a job (e.g. "Login succeeded", "Form submitted"). |

## Initialization

The `MonitoringClient` is initialized in `ctx_job_context.py` — it is **job-scoped**, meaning a fresh client is created for each job (see [Job Context]({{< relref "/docs/setting-up-project/python-files#ctx_job_contextpy--the-job-context" >}})):

```python
from src.monitoring_client import MonitoringClient
import uuid
import os

class JobContext:
    def __init__(self, job_message):
        self.job_message = job_message

    def instantiate_default(self):
        pod_index = os.getenv("POD_INDEX", 100)
        job_uuid = str(uuid.uuid4())
        self.monitoring_client = MonitoringClient(
            self.job_message["run_id"], pod_index, job_uuid
        ).create_job()
```

`create_job()` immediately the job with the backend, setting the initial job status to `"Running"`.

## Usage in ctx_script.py

### Recording progress events

Use `record_success_event()` to log intermediate progress steps. These appear on the dashboard as green events:

```python
async def ctx_script(job_ctx, agent_ctx):
    tab = await agent_ctx.browser.get("https://example.com/login")
    job_ctx.monitoring_client.record_success_event("Page loaded")

    # ... perform login ...
    job_ctx.monitoring_client.record_success_event("Login successful")

    # ... perform action ...
    job_ctx.monitoring_client.record_success_event("Form submitted")
```

### Marking a job as succeeded

When the job is fully complete, call `record_finalsuccess_event()`. This creates a success event **and** updates the job status to `"Success"`:

```python
async def ctx_script(job_ctx, agent_ctx):
    # ... automation logic ...

    job_ctx.monitoring_client.record_finalsuccess_event("Job completed")
```

### Marking a job as failed

When an error occurs, call `record_failed_event()`. This creates a failure event **and** updates the job status to `"Failed"`:

```python
async def ctx_script(job_ctx, agent_ctx):
    try:
        # ... automation logic ...
        job_ctx.monitoring_client.record_finalsuccess_event("Job completed")
    except Exception as e:
        job_ctx.monitoring_client.record_failed_event(f"Error: {str(e)}")
```

## Complete Example

A typical script with full monitoring:

```python
async def ctx_script(job_ctx, agent_ctx):
    try:
        tab = await agent_ctx.browser.get("https://example.com")
        job_ctx.monitoring_client.record_success_event("Page loaded")

        # Step 1
        await tab.find("input[name=email]").send_keys("user@example.com")
        job_ctx.monitoring_client.record_success_event("Email entered")

        # Step 2
        await tab.find("button[type=submit]").click()
        job_ctx.monitoring_client.record_success_event("Form submitted")

        # Final
        job_ctx.monitoring_client.record_finalsuccess_event("Job completed")

    except Exception as e:
        job_ctx.monitoring_client.record_failed_event(str(e))
```

## Methods Reference

| Method | Effect |
|---|---|
| `create_job()` | Registers the job with status `"Running"`.|
| `record_success_event(content)` | Creates an event with status `"Success"`. Job status stays `"Running"`. |
| `record_finalsuccess_event(content)` | Creates a `"Success"` event **and** sets job status to `"Success"`. |
| `record_failed_event(content)` | Creates a `"Failed"` event **and** sets job status to `"Failed"`. |