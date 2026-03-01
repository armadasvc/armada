---
title: 1.3. Local Development
linkTitle: 1.3. Local Development 
weight: 4
description: Run Armada locally with Docker Compose using container mode or workbench mode
---

This guide walks you through running Armada on your own machine using Docker Compose. Local development is the recommended way to build and debug your projects before deploying to a Kubernetes cluster.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.12+ installed
- Access to a SQL Server instance (e.g. Azure SQL)

## 1. Clone and Configure

```bash
git clone https://github.com/armadasvc/armada
cd armada
```

Create a `.env` file at the project root by duplicating `.env.example` and filling in your values:

```dotenv
SQL_SERVER_USER=your_user
SQL_SERVER_PASSWORD=your_password
SQL_SERVER_DB=your_database
SQL_SERVER_NAME=your_server.database.windows.net

DOCKER_HUB_USERNAME=armadasvc
```

## 2. Bootstrap the Database

```bash
cd bootstrap
pip install -r requirements.txt
python bootstrap_database.py
cd ..
```

## 3. Create Your Project

Use the interactive project creation script to scaffold a new Armada project from the built-in template:

```bash
bash create-project.sh
```

and choose 1. New Project

A dialog will prompt you for:

| Field | Description |
|---|---|
| **Project name** | The name of your new project |
| **Destination folder** | Where the project folder will be created |

The script copies the project template (`services/project`) to the selected location and configures the workbench `agent_path` automatically.

Once created, the project folder opens automatically. You can start editing `ctx_script.py` to write your automation logic.

> **Tip** — See [Setting Up a Project](../setting-up-project/) for the full project structure reference.

## 4. Start All Services

```bash
cd local
docker compose up --build
```

Wait until all containers are healthy. You should see logs from the orchestrator, backend, and other services.

At this point the full platform is running locally. You now have **two ways** to launch and test your project, depending on what you need.

---

## Option A — Launch from the monitoring frontend ("Container mode")

Use the monitoring frontend when you want to run your project end-to-end, as it would run in production. This is the right choice for integration testing or when you need the full orchestration pipeline (multiple agents, multiple jobs, monitoring).

### Open the dashboard

Navigate to **http://localhost:3000** in your browser. You will see two tabs:

- **Launch** — Configure and submit automation runs
- **Monitor** — Track runs, jobs, and events in real time

### Submit a run

1. Open the **Launch** tab
2. Drag-and-drop your project folder into the upload area
3. If needed, browse and edit files using the built-in Monaco editor
4. Select the required configuration files from the dropdowns — in this case, as the default configtune is `config_distant.json` you should probably change it to `config_local.json` 
5. Click **Launch**
6. Switch to the **Monitor** tab to watch your run in real time

### Consume the run

In container mode, there is no Kubernetes cluster to spin up agent pods automatically. You need to start agent workers manually using the provided script:

```bash
cd local
bash agent.sh
```

A configuration dialog opens. Fill in the fields:

| Field | What to enter |
|---|---|
| **Queue name (RUN_ID)** | Paste the `run_id` returned by the frontend after clicking **Launch** |
| **Pod index (POD_INDEX)** | Leave at `0` for a single agent. Change to `1`, `2`, … to simulate additional pods |
| **Redis host / port** | Keep the defaults (`localhost` / `6379`) — they match the Docker Compose stack |
| **SQL fields** | Pre-filled from your `.env` file. Adjust only if needed |

Click **OK** to start a Celery worker that listens on the run's queue and begins processing jobs.

**Simulating multiple pods** — Open additional terminals and run `agent.sh` again with a different **Pod index** each time. Each worker acts as an independent agent pod, just like in a real Kubernetes deployment. This is useful for testing how your project distributes work across agents.

### Monitor your run

The **Monitor** panel provides three levels of drill-down:

```
Runs → Jobs → Events
```

- **Runs** — Paginated list of all runs. Click a run to see its jobs.
- **Jobs** — All jobs for the selected run with status indicators. Click a job to see its events.
- **Events** — Detailed event log for the selected job.

All updates are delivered in real time via WebSocket. No refresh needed.

---

## Option B — Launch from the Workbench

The **workbench** is a lightweight development mode that lets you run and test your `ctx_script.py` directly inside the project folder. It simulates the execution environment locally, so you can iterate quickly on small changes without deploying to Kubernetes or launching any orchestration pipeline. The workbench mode is able to run only one job in one agent.

Use it when you need to:

- Debug or tweak your `ctx_script.py` logic
- Test configuration changes (`config_template.json`, CSV overrides)
- Iterate rapidly on browser automation steps

### Run your script

```bash
# In the project folder, navigate to the workbench directory
cd workbench

# Execute your project
python run_workbench.py
```

This will basically run your script locally, ie : 

1. Load the agent library path (from `workbench/agent_path`). You should adapt the `agent_path` file with the path to the [agent microservice](../../reference/services/agent/) of your Armada project.
2. Read your project's `config/config_template.json` and mock locally the [environement substitution](../../setting-up-project/json-config/) with `config/config_local.json`
3. Apply CSV overrides by mocking locally the [CSV orverrides](../../setting-up-project/csv-config/) taking as input `config/data_agent.csv` and `config/data_job.csv` (first row only).
4. Generate a unique `run_id` for the run.
5. Execute `main.py`, which in turn calls your `ctx_script(job_ctx, agent_ctx)`.