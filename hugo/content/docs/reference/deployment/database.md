---
title: 4.3.1. Database
linkTitle: 4.3.1. Database
weight: 1
description: SQL Server schema, table definitions, service-to-table matrix, bulk import tools, and database conventions
---


# Database Reference

Armada uses **Microsoft SQL Server** as its persistent data store, accessed through the **pymssql** library (`v2.3.13`). There is no ORM — all queries are raw SQL with parameterized placeholders (`%s`).

---

## Connection Credentials

Every service reads the same four environment variables:

| Variable | Description | Example |
|---|---|---|
| `SQL_SERVER_NAME` | Server hostname | `myserver.database.windows.net` |
| `SQL_SERVER_USER` | Login name | `myadmin` |
| `SQL_SERVER_PASSWORD` | Login password | `••••••` |
| `SQL_SERVER_DB` | Database name | `my_db` |

These are stored in the root `.env` file and injected into Kubernetes pods via the `armada-sql-server-secret` secret.

---

## Schema

All tables are created by `bootstrap/bootstrap_database.py` using idempotent `IF NOT EXISTS` DDL (see [Bootstrap Scripts]({{< relref "/docs/reference/architecture/bootstrap-scripts" >}})). There is **no migration framework** — schema changes must be applied manually or by editing the bootstrap script.

> **Note:** No primary keys, foreign keys, or indexes are defined. Uniqueness and referential integrity are enforced at the application level.

### armada_runs

Tracks each orchestrator run.

| Column | Type | Description |
|---|---|---|
| `run_uuid` | `VARCHAR(255)` | UUID v4 identifying the run |
| `run_datetime` | `DATETIME` | Timestamp when the run started |

### armada_jobs

Tracks individual jobs spawned within a run.

| Column | Type | Description | Allowed values |
|---|---|---|---|
| `job_uuid` | `VARCHAR(255)` | UUID v4 identifying the job | |
| `run_uuid` | `VARCHAR(255)` | References `armada_runs.run_uuid` | |
| `job_datetime` | `DATETIME` | Timestamp when the job started | |
| `job_associated_agent` | `VARCHAR(255)` | Identifier of the agent that executed the job | |
| `job_status` | `VARCHAR(255)` | Current status of the job | `Running`, `Success`, `Failed` |

### armada_events

Tracks granular events emitted during a job.

| Column | Type | Description | Allowed values |
|---|---|---|---|
| `event_uuid` | `VARCHAR(255)` | UUID v4 identifying the event | |
| `event_content` | `VARCHAR(255)` | Free-text event description | |
| `job_uuid` | `VARCHAR(255)` | References `armada_jobs.job_uuid` | |
| `event_datetime` | `DATETIME` | Timestamp of the event | |
| `event_status` | `VARCHAR(255)` | Status of the event | `Success`, `Failed` |

### armada_proxies

Stores the pool of available proxies.

| Column | Type | Description | Allowed values |
|---|---|---|---|
| `proxy_url` | `VARCHAR(255)` | Full proxy URL | `http://USER:PASS@HOST:PORT` |
| `proxy_provider_name` | `VARCHAR(255)` | Provider name | e.g. `iproyal`, `brightdata`, `oxylabs` |
| `proxy_type` | `VARCHAR(255)` | Proxy category | `datacenter`, `residential`, `mobile` |
| `proxy_rotation_strategy` | `VARCHAR(255)` | Rotation mode | `sticky`, `rotating` |
| `proxy_location` | `VARCHAR(255)` | [IANA timezone](https://data.iana.org/time-zones/tzdb/zone1970.tab) identifier (can be empty) | e.g. `Europe/Paris`, `Europe`, `US` |

Filtering on `proxy_location` uses a **contains** match: setting the filter value to `Europe` selects proxies in both `Europe/Vienna` and `Europe/Paris`. Use a more specific value (e.g. `Europe/Paris`) to target a single timezone.

### armada_output

Stores the output data produced by agent runs.

| Column | Type | Description |
|---|---|---|
| `run_uuid` | `VARCHAR(255)` | UUID v4 referencing the run |
| `data` | `VARCHAR(MAX)` | Output data (plain text or JSON string) |
| `timestamp` | `DATETIME` | Timestamp of the output record |

### armada_fingerprints

Stores collected browser fingerprints as JSON blobs.

| Column | Type | Description |
|---|---|---|
| `antibot_vendor` | `VARCHAR(255)` | Vendor name (e.g. `arkose`, `datadome`) |
| `website` | `VARCHAR(255)` | Target website identifier |
| `data` | `VARCHAR(MAX)` | JSON string — format depends on vendor (see below) |
| `collecting_date` | `DATE` | Collection date (`YYYY-MM-DD`) |

**`data` field format by vendor:**

- **arkose**: `{"ts":"<timestamp>","ua":"<user_agent>","bda":"<bda_payload>"}`
- Other vendors: free-form JSON.

### Data type reference

| SQL Server type | Format | Example |
|---|---|---|
| `DATE` | `YYYY-MM-DD` | `2026-02-24` |
| `DATETIME` | `YYYY-MM-DD HH:MM:SS` | `2026-02-24 10:30:00` |
| `VARCHAR(255)` | Plain text | `my_value` |
| `VARCHAR(MAX)` | Plain text / JSON string | `{"key":"value"}` |

Empty values are stored as `NULL` for date and datetime columns.

### Entity Relationships

```
armada_runs
  └── 1:N ── armada_jobs  (via run_uuid)
                └── 1:N ── armada_events  (via job_uuid)

armada_runs
  └── 1:N ── armada_output  (via run_uuid)

armada_proxies        (standalone lookup table)
armada_fingerprints   (standalone lookup table)
```

These relationships are not enforced by foreign keys — they are maintained by application code. The backend's `DELETE /api/runs/{run_uuid}` endpoint performs a manual cascade: events → jobs → run.



## Bulk Data Import

Armada provides CLI scripts to populate tables from CSV files. See the [Database Management guide]({{< relref "/docs/guides/database-management" >}}) for usage instructions and CSV examples.

---


## Conventions & Design Decisions

| Convention | Detail |
|---|---|
| **No connection pooling** | Every operation opens and closes its own `pymssql` connection. |
| **Parameterized queries** | All SQL uses `%s` placeholders — no string substitution. |
| **No ORM** | Raw SQL throughout the entire codebase. |
| **No migrations** | Schema is managed via the idempotent bootstrap script only. |
| **Async wrapping** | The backend wraps synchronous `pymssql` calls with `asyncio.to_thread()` for FastAPI compatibility. |
| **Consistent credentials** | All services use the same 4 env vars, loaded identically. |

---

## Dependencies

All services pin the same version:

```
pymssql==2.3.13
```

Found in `requirements.txt` of: `services/agent`, `services/backend`, `services/proxy-provider`, `services/fingerprint-provider`, and `bootstrap`.
