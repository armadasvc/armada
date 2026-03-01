---
title: 1.1. Key Concepts
linkTitle: 1.1. Key Concepts 
weight: 1
description: "Core building blocks of Armada: runs, agents, jobs, projects, orchestrator, and monitoring"
---

This tutorial walks you through the core ideas behind Armada. Before diving into configuration files and deployment commands, you need to understand **how the pieces fit together** and **why each one exists**.

---

## 1. The Big Picture

Armada is a distributed automation platform. The workflow is always the same:

```
You configure a web-automation project
        ↓
Armada orchestrator distributes the jobs
        ↓
Armada Agents execute it in parallel
```

At its core, Armada solves one problem: **taking a single automation script and running it at scale across many machines through Kubernetes** while you monitor everything from a dashboard.

---

## 2. 3 Key Notions : Runs, Agents, and Jobs

### 2.1. Overview

Before diving into the detailed concepts, you need to understand the three fundamental entities that Armada revolves around:

**A Run** is a single execution of your project. Every time you hit **Launch**, Armada creates a new run with a unique `run_id`. The run is the top-level container — it defines how many agents to spin up, how many jobs to process, and groups all activity under one identifier. Think of it as one "campaign" or "session".

**An Agent** is a worker that executes your automation script. Each agent is an isolated environment with its own browser, proxy, and identity. A run can have one agent or dozens — they all work in parallel, pulling tasks from the same queue.

**A Job** is a single unit of work. Jobs are distributed across agents automatically: whichever agent finishes first picks up the next available job.

The relationship is hierarchical:

```
Run (1 per launch)
 ├── Agent 0  ──→  processes Job 3, Job 7, Job 12, ...
 ├── Agent 1  ──→  processes Job 1, Job 4, Job 8, ...
 └── Agent 2  ──→  processes Job 0, Job 2, Job 5, ...
```

A run owns its agents and its jobs. Agents don't own jobs — they **consume** them from a shared queue. This is why 5 agents with 100 jobs doesn't mean 20 jobs each: a faster agent will naturally take more.

With these three notions in mind, everything else falls into place. The **project** defines what a run should look like. The **orchestrator** creates the run. **Redis** and **RabbitMQ** distribute the run's configuration and work. Let's start.

### 2.2. Runs — The Top-Level Container

A **run** is created every time you hit **Launch**. It is the top-level entity that groups everything together: agents, jobs, configuration, and monitoring data — all under a single unique `run_id`.

Each run is independent and self-contained. Launching the same project twice produces two separate runs with their own `run_id`, their own agents, and their own job queue. This means you can:

- **Compare runs** — see how changing a parameter affected results
- **Replay a project** — launch again without any leftover state from the previous run
- **Run concurrently** — multiple runs of the same project can execute at the same time without interfering with each other

```
Run a1b2c3d4
 ├── 3 agents (each with its own browser, proxy, identity)
 ├── 100 jobs (distributed via RabbitMQ)

Run e5f6g7h8   ← same project, different run
 ├── 5 agents
 ├── 200 jobs
```

### 2.3. Agents — The Workers

An agent is a Kubernetes pod (or a local Docker container) that runs your automation script. Each agent:

1. **Starts up** and reads its configuration from Redis
2. **Initializes heavy resources once** — browser, virtual display, proxy, fingerprint
3. **Connects to RabbitMQ** as a Celery worker
4. **Consumes jobs** from the queue, one at a time
5. **Shuts down** when the queue is empty

```
Agent Lifecycle
───────────────

Startup (once)                    Job Loop (repeated)
┌─────────────────────────┐      ┌──────────────────────────┐
│ Read config from Redis  │      │ Pick job from RabbitMQ   │
│ Launch Chrome browser   │ ──── │ Run ctx_script()         │
│ Start mitmproxy         │      │ Report result to backend │
│ Start virtual display   │      │ Acknowledge job          │
└─────────────────────────┘      └──────────────────────────┘
                                          │
                                    (queue empty?)
                                          │
                                    ┌─────┴──────┐
                                    │  Shut down  │
                                    └────────────┘
```

The key design principle: **heavy resources are initialized once, then reused across all jobs**. Starting a browser takes seconds — you don't want to pay that cost for every single job. For full details on the agent startup sequence, see [Agent Internals]({{< relref "/docs/reference/architecture/agent-internals" >}}).

### 2.4. Jobs — The Units of Work

A job is a single task that an agent processes. The relationship between agents and jobs is many-to-many through the queue:

- **5 agents, 100 jobs** → each agent processes ~20 jobs (depending on speed)
- **1 agent, 10 jobs** → that agent processes all 10 sequentially
- **10 agents, 10 jobs** → roughly 1 job per agent

Jobs are pulled from the RabbitMQ queue on a first-come-first-served basis. Faster agents naturally take on more work.

Inside your script, you access the job payload through `job_ctx.job_message`. This is where data from your `data_job.csv` overrides ends up — see [CSV Configuration]({{< relref "/docs/setting-up-project/csv-config" >}}) for how to define per-job overrides.

---

## 3. Key Components


### 3.1. The Project

Everything starts with a **project**. A project is a folder you create that contains everything you need to make your web-automation task to run

- **Py Files** — `ctx_script` for the logic, `ctx_agent_context` and `ctx_job_context` to instantiate ressources at agent and job level, and addon to add some functionalities at project level
- **JSON Configurations** — JSON files that describes the infrastructure (how many agents, how many jobs) and the default settings for each agent and job.
- **CSV override files** — optional spreadsheets that let you customize settings per-agent or per-job
- **Py Requirements** — to install depedencies at project level

For the complete project structure and file reference, see [Setting Up a Project — Key Concepts]({{< relref "/docs/setting-up-project/key-concepts" >}}).


### 3.2. The Orchestrator : Armada's Control Plane

When you hit **Launch** in the frontend, your project is sent to the **Orchestrator**. This is the brain of Armada. It does not run your script — it **prepares and distributes** everything so that agents can run it.

The orchestrator performs three critical operations:

- **CSV orverrides** : Orchestrator merges JSON files with CSV agent-specific overrides.
- **Push Agent config to redis** : Each agent's final merged configuration is stored in **Redis**. Redis acts as a **configuration distribution layer**. When an agent pod starts, it reads its own config from Redis using the run ID and its pod index. This is a read-once operation — the agent fetches its config at startup and never reads from Redis again.
- **Dispatch Jobs to RabbitMQ via Celery** : Each job message is sent to a **RabbitMQ queue** . Celery is the task framework that manages the dispatch and consumption of these messages. All agents for a given run consume from the **same queue**. This means jobs are automatically load-balanced: whichever agent finishes first picks up the next available job.

See the [Orchestrator service reference]({{< relref "/docs/reference/services/orchestrator" >}}) for the full API and configuration.


### 3.3. Monitoring Backend + Frontend

Every agent reports its progress back to the **Backend API**, which stores events in SQL Server and broadcasts them via **WebSocket** to the **Frontend dashboard**.

The monitoring model has three levels:

```
Run (one per launch)
 └── Job (one per task in the queue) - Agent is displayed as an attribute of job
      └── Event (one per progress step within a job)
```

These events appear in real time on the Monitor tab, with no page refresh needed. Learn how to report events from your scripts in the [Monitoring Client guide]({{< relref "/docs/guides/monitoring-client" >}}).
