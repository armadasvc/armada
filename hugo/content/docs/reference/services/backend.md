---
title: 4.2.4. Backend
linkTitle: 4.2.4. Backend
weight: 4
description: FastAPI REST API and WebSocket service for run/job/event CRUD, real-time monitoring, and SQL Server persistence
---

# Armada Backend

FastAPI service that exposes the REST API and WebSocket layer for the Armada platform. It manages **runs**, **jobs**, and **events**, persisting them in SQL Server and broadcasting changes to connected clients in real time.

## Tech Stack

- **Python 3.12** / **FastAPI** + **Uvicorn**
- **pymssql** — SQL Server driver (sync calls wrapped with `asyncio.to_thread`)
- **WebSocket** — built-in FastAPI support for real-time broadcasting
- **Docker** — production-ready image (`python:3.12-slim`)

## Project Structure

```
app/
├── main.py             # FastAPI entry point, CORS & router registration
├── config.py           # Environment variable loading
├── db.py               # Async Database wrapper around pymssql
├── ws.py               # WebSocket manager (connect / disconnect / broadcast)
├── routers/
│   ├── runs.py         # /api/runs   — CRUD for runs
│   ├── jobs.py         # /api/jobs   — CRUD for jobs
│   └── events.py       # /api/events — CRUD for events + WS endpoint
└── schemas/
    ├── runs.py         # Pydantic models for runs
    ├── jobs.py         # Pydantic models for jobs
    └── events.py       # Pydantic models for events
```

## Base URL

```
http://localhost:8000
```

All endpoints are also available via the Nginx reverse proxy at `/tracking/`.

## REST API

### Runs

#### `GET /api/runs/`

List runs (paginated).

**Query params:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | int | 1 | Page number |
| `page_size` | int | 10 | Items per page (max 100) |

#### `POST /api/runs/`

Create a run. Idempotent (`IF NOT EXISTS`).

#### `DELETE /api/runs/{run_uuid}`

Delete a run with cascading delete (events → jobs → run).

### Jobs

#### `GET /api/jobs/`

List jobs (paginated).

**Query params:**

| Parameter | Type | Description |
|---|---|---|
| `run_uuid` | string | Filter by run UUID |

#### `POST /api/jobs/`

Create a job (auto-generates UUID).

#### `PATCH /api/jobs/status`

Update job status.

### Events

#### `GET /api/events/`

List events, sorted by datetime DESC.

**Query params:**

| Parameter | Type | Description |
|---|---|---|
| `job_uuid` | string | Filter by job UUID |

#### `POST /api/events/`

Create an event (auto-generates UUID).

#### `PATCH /api/events/status`

Update event status.

## WebSocket

### `WS /ws/events/`

Full-duplex connection for real-time event streaming. Every REST mutation broadcasts to all connected WebSocket clients.

**Message format:**

```json
{
  "type": "create_run | create_job | update_job | create_event | update_event | delete_run",
  "data": { ... }
}
```

**Message types:**

| Type | Description |
|---|---|
| `new_run` | A new run was created |
| `new_job` | A new job was created |
| `new_event` | A new event was created |
| `update_job_status` | A job status was updated |
| `update_event_status` | An event status was updated |
| `delete_run` | A run was deleted (cascading) |

These events are triggered by the agent's [Monitoring Client]({{< relref "/docs/guides/monitoring-client" >}}).

## Data Model

The backend operates on three tables: `armada_runs`, `armada_jobs`, and `armada_events` (hierarchy: Run 1:N Job 1:N Event). The `DELETE /api/runs/{run_uuid}` endpoint performs a manual cascading delete: events → jobs → run.

For the complete schema definition of all five tables, see the [Database Reference]({{< relref "/docs/reference/deployment/database" >}}).

## Environment Variables

| Variable              | Description                |
|-----------------------|----------------------------|
| `SQL_SERVER_NAME`     | SQL Server hostname        |
| `SQL_SERVER_USER`     | Database user              |
| `SQL_SERVER_PASSWORD` | Database password          |
| `SQL_SERVER_DB`       | Database name              |

These can be set via a `.env` file (loaded automatically by `python-dotenv`).

## Getting Started

### Local

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker

```bash
docker build -t armada-backend .
docker run -p 8000:8000 \
  -e SQL_SERVER_NAME=... \
  -e SQL_SERVER_USER=... \
  -e SQL_SERVER_PASSWORD=... \
  -e SQL_SERVER_DB=... \
  armada-backend
```
