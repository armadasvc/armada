---
title: 4.1.1. Overview
linkTitle: 4.1.1. Overview
weight: 1
description: High-level architecture diagram, three execution modes, data stores, and service communication map
---

## High-Level Architecture

```
                         ┌──────────────────┐
                         │     Frontend      │
                         │  React + Vite     │
                         │  (port 3000/8080) │
                         └────────┬─────────┘
                                  │  HTTP + WebSocket
                                  ▼
              ┌───────────────────────────────────────┐
              │              Backend API               │
              │           FastAPI (port 8000)           │
              │   Runs / Jobs / Events CRUD + WS       │
              └──────────────────┬────────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   SQL Server     │
                        │  (Azure SQL)     │
                        └─────────────────┘

              ┌───────────────────────────────────────┐
              │           Orchestrator                 │
              │         FastAPI (port 8080)             │
              └──┬──────────┬────────────┬────────────┘
                 │          │            │
                 ▼          ▼            ▼
          ┌──────────┐ ┌────────┐ ┌──────────────────┐
          │  Redis   │ │RabbitMQ│ │ Kubernetes API    │
          │ (config) │ │ (jobs) │ │ (batch/v1 Jobs)   │
          └──────────┘ └────────┘ └────────┬─────────┘
                                           │
                          ┌────────────────┼────────────────┐
                          ▼                ▼                ▼
                    ┌──────────┐    ┌──────────┐    ┌──────────┐
                    │ Agent 0  │    │ Agent 1  │    │ Agent N  │
                    │ (Pod)    │    │ (Pod)    │    │ (Pod)    │
                    └──┬───────┘    └──┬───────┘    └──┬───────┘
                       │               │               │
                  ┌────┴────┐    ┌────┴────┐    ┌────┴────┐
                  │Fantomas │    │Fantomas │    │Fantomas │
                  │+mitmprxy│    │+mitmprxy│    │+mitmprxy│
                  └─────────┘    └─────────┘    └─────────┘
                       │               │               │
              ┌────────┴───────────────┴───────────────┴────────┐
              │                                                  │
              ▼                                                  ▼
     ┌──────────────────┐                             ┌───────────────────┐
     │  Proxy Provider   │                             │Fingerprint Provider│
     │ FastAPI (port 5001)│                             │FastAPI (port 5005) │
     └──────────────────┘                             └───────────────────┘
```

---

## Three Execution Modes

Armada supports three execution modes that share the same agent code but differ in infrastructure, message delivery, and how agents are created:

| Aspect | Distant mode (Kubernetes) | Container mode (Docker Compose) | [Workbench mode]({{< relref "/docs/reference/deployment/workbench" >}}) (In-process)|
|---|---|---|---|
| Trigger | Frontend → Orchestrator on the cluster | Frontend → Orchestrator running locally | Workbench script started from the command line |
| Agent creation | Orchestrator creates a `batch/v1` Indexed Job; Kubernetes schedules N pods | Orchestrator starts agent containers via Docker Compose | Single agent runs in-process |
| Config delivery | Redis (key = `{run_id}{pod_index}`) | Redis (key = `{run_id}{pod_index}`) | Config files read directly from disk |
| Job delivery | RabbitMQ via Celery `send_task` | RabbitMQ via Celery `send_task` | Direct function call to `run_job(job_message)` |
| Code injection | Bundled Python string stored in Redis, executed via `exec()` | Bundled Python string stored in Redis, executed via `exec()` | `main.py` read from disk, executed via `exec()` |
| Infrastructure | Kubernetes cluster, Helm chart, Docker images | Docker Compose for all services and data stores | Docker Compose for microservices but no use of RabbitMQ or Redis |

--- 

## Data Stores and Their Roles

### Redis — Ephemeral Agent Config Store

Redis holds agent configuration messages for the duration of a run. Each key is `{run_id}{agent_index}`, and the value is the serialized JSON of the consolidated agent message (including the bundled Python code). The agent pod fetches its config from Redis at startup and never reads it again. See [Configuration Pipeline]({{< relref "/docs/reference/architecture/configuration-pipeline" >}}) for how agent messages are consolidated.

### RabbitMQ — Job Message Broker

RabbitMQ carries job messages from the orchestrator to agent workers. Each run gets its own queue (named after the `run_id`). Agents subscribe to that queue as Celery workers and consume one job at a time (`concurrency=1`, `prefetch-multiplier=1`).

The orchestrator monitors the queue in a background thread. When the queue is empty **and** no tasks are actively running, it sends a shutdown signal to all workers on that queue.

### SQL Server — Persistent State

SQL Server stores six tables:

| Table | Purpose |
|---|---|
| `armada_runs` | Tracks run UUIDs and start times |
| `armada_jobs` | Tracks individual jobs with status and agent assignment |
| `armada_events` | Tracks granular events within a job |
| `armada_proxies` | Pool of proxy URLs with provider/location metadata |
| `armada_fingerprints` | Encrypted browser fingerprints per antibot vendor |
| `armada_output` | Standard output tagged with run_uuid |

See the [Database Reference]({{< relref "/docs/reference/deployment/database" >}}) for complete schema definitions.

---

## Service Communication Map

```
Frontend ──HTTP POST /bot/start──▶ Orchestrator
Frontend ──HTTP REST──────────────▶ Backend API
Frontend ──WebSocket /ws/events/──▶ Backend API

Orchestrator ──Redis SET──────────▶ Redis
Orchestrator ──Celery send_task───▶ RabbitMQ
Orchestrator ──batch/v1 create────▶ Kubernetes API

Agent ──Redis GET─────────────────▶ Redis       (at startup only)
Agent ──Celery consume────────────▶ RabbitMQ    (continuous)
Agent ──HTTP POST/PATCH───────────▶ Backend API (monitoring events)
Agent ──HTTP GET──────────────────▶ Proxy Provider
Agent ──HTTP GET──────────────────▶ Fingerprint Provider
Agent ──pymssql───────────────────▶ SQL Server  (user queries)
```

For agent-side usage of these services, see the guides: [Proxy Provider]({{< relref "/docs/guides/proxy-provider" >}}), [Fingerprint Provider]({{< relref "/docs/guides/fingerprint-provider" >}}), [Database Connector]({{< relref "/docs/guides/database-connector" >}}), [Monitoring Client]({{< relref "/docs/guides/monitoring-client" >}}).
