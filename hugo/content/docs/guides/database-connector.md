---
title: 3.1. Database Connector
linkTitle: 3.1. Database Connector
weight: 1
description: Read and write data to SQL Server from automation scripts using the DatabaseConnector
---

## Overview

The Database Connector provides direct SQL Server access from your automation scripts. Use it to read input data, write results, or perform any SQL operation your project requires.

```
ctx_script.py
  │
  │  select_from_db("SELECT ...")
  ▼
DatabaseConnector ──pymssql──► SQL Server (port 1433)
```

The connector uses parameterized queries to prevent SQL injection and manages connections automatically (one connection per query, opened and closed each time).

## Configuration

The connector reads its credentials from environment variables — there is no JSON configuration block for it:

| Variable | Description |
|---|---|
| `SQL_SERVER_NAME` | SQL Server hostname |
| `SQL_SERVER_USER` | Database username |
| `SQL_SERVER_PASSWORD` | Database password |
| `SQL_SERVER_DB` | Database name |

These are the same environment variables used by all Armada services. See [Environment Variables]({{< relref "/docs/reference/architecture/environment-variables" >}}) for the complete reference.

## Initialization

The `DatabaseConnector` is initialized in `ctx_agent_context.py` as part of `instantiate_default()`:

```python
from src.database_connector import DatabaseConnector

class AgentContext:
    def __init__(self, agent_message):
        self.agent_message = agent_message

    def instantiate_default(self):
        self.database = DatabaseConnector()
```

The connector is agent-scoped: it is created once and reused across all jobs (see [The Two-Tier Lifecycle]({{< relref "/docs/setting-up-project/python-files#the-two-tier-lifecycle" >}}) for more on agent-scoped vs. job-scoped resources). Credentials are lazy-loaded on the first query.

## Usage in ctx_script.py

### Reading data

Use `select_from_db()` to execute a SELECT query. It returns a list of tuples:

```python
async def ctx_script(job_ctx, agent_ctx):
    rows = agent_ctx.database.select_from_db(
        "SELECT TOP 1 uuid, email FROM dim_email ORDER BY NEWID()"
    )

    if rows:
        uuid_val, email = rows[0]
```

### Writing data

Use `post_to_db()` to execute INSERT, UPDATE, or DELETE queries:

```python
async def ctx_script(job_ctx, agent_ctx):
    agent_ctx.database.post_to_db(
        "INSERT INTO results (job_uuid, status) VALUES (%s, %s)",
        job_ctx.monitoring_client.job_uuid,
        "completed"
    )
```

### Parameterized queries

Always use `%s` placeholders for dynamic values. Arguments are passed as additional positional parameters:

```python
# Safe — parameterized
rows = agent_ctx.database.select_from_db(
    "SELECT * FROM users WHERE email = %s AND status = %s",
    "user@example.com",
    "active"
)

# UNSAFE — never do this
rows = agent_ctx.database.select_from_db(
    f"SELECT * FROM users WHERE email = '{email}'"  # SQL injection risk
)
```

### Select with autocommit

Use `select_with_commit_from_db()` when you need autocommit mode (e.g. for queries that require it or for large streaming result sets):

```python
rows = agent_ctx.database.select_with_commit_from_db(
    "SELECT * FROM large_table WHERE category = %s",
    "target"
)
```

## Complete Example

A script that reads input data from the database, performs automation, and writes results back:

```python
async def ctx_script(job_ctx, agent_ctx):
    try:
        # Read input
        rows = agent_ctx.database.select_from_db(
            "SELECT TOP 1 uuid, url FROM targets WHERE status = %s ORDER BY NEWID()",
            "pending"
        )
        if not rows:
            job_ctx.monitoring_client.record_failed_event("No targets available")
            return

        target_uuid, target_url = rows[0]
        job_ctx.monitoring_client.record_success_event(f"Target: {target_uuid}")

        # Mark as in progress
        agent_ctx.database.post_to_db(
            "UPDATE targets SET status = %s WHERE uuid = %s",
            "in_progress", target_uuid
        )

        # Perform automation
        tab = await agent_ctx.browser.get(target_url)
        # ... do work ...

        # Write result
        agent_ctx.database.post_to_db(
            "UPDATE targets SET status = %s WHERE uuid = %s",
            "completed", target_uuid
        )

        job_ctx.monitoring_client.record_finalsuccess_event("Done")

    except Exception as e:
        job_ctx.monitoring_client.record_failed_event(str(e))
```

## Methods Reference

| Method | Description | Returns |
|---|---|---|
| `select_from_db(query, *args)` | Execute a SELECT query | `list[tuple]` |
| `post_to_db(query, *args)` | Execute INSERT/UPDATE/DELETE with commit | `None` |
| `select_with_commit_from_db(query, *args)` | Execute a SELECT with autocommit enabled | `list[tuple]` |

## Disabling the Connector

Set `enabled` to `0` on the connector instance to disable all queries (methods return `None` silently):

```python
agent_ctx.database.enabled = 0
```

Or remove the `DatabaseConnector()` line from `ctx_agent_context.py` if your project does not need database access.

To manage the database schema or bulk-import data, see [Database Management]({{< relref "/docs/guides/database-management" >}}).
