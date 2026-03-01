---
title: 3.7. Standard Output
linkTitle: 3.7. Standard Output
weight: 7
description: Write structured output data to SQL Server, tagged by run, using the StandardOutput class
---

## Overview

The Standard Output lets your automation script write arbitrary JSON data to the `armada_output` table, tagged with the current run UUID. Use it to persist results, extracted data, or any structured output that you want to retrieve later.

```
ctx_script.py
  │
  │  send({"email": "user@example.com", "status": "ok"})
  ▼
StandardOutput ──DatabaseConnector──► SQL Server (armada_output)
```

Each row stores the run UUID, the JSON-serialized data, and a UTC timestamp.

## Initialization

Create a `StandardOutput` instance with the current run ID — typically in `ctx_agent_context.py`.

The class internally creates its own `DatabaseConnector` that can be use for flexible use (inputting / outputting)
## Usage in ctx_script.py

Call `send()` with a dictionary. The dictionary is JSON-serialized and inserted into `armada_output`:

```python
async def ctx_script(job_ctx, agent_ctx):
    # ... automation logic ...

    job_ctx.standard_output.send({
        "email": "user@example.com",
        "status": "registered",
        "confirmation_id": "ABC-123"
    })
```

You can call `send()` multiple times — each call inserts a new row.