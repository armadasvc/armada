---
title: 2.1. Key Concepts
linkTitle: 2.1. Key Concepts 
weight: 1
description: Project folder structure, file categories, and how they are processed at launch time
---

## What Is a Project?

A **project** is a folder you create that contains everything needed to launch a run: automation scripts, configuration, data overrides, and optional dependencies.

When you hit **Launch** in the frontend, the entire project folder is processed, bundled, and distributed to agents. Each agent then executes your automation logic with the configuration you defined.

---

## Project Structure

A project folder follows this layout:

```
my-project/
├── config/
│   ├── config_template.json    # Main configuration blueprint
│   ├── config_local.json       # Environment values for local mode (container mode or workbench mode)
│   ├── config_distant.json     # Environment values for distant (Kubernetes) mode
│   ├── data_agent.csv          # Per-agent overrides
│   └── data_job.csv            # Per-job overrides
├── ctx_script.py               # Main automation logic
├── ctx_agent_context.py        # Agent lifecycle and resource setup
├── ctx_job_context.py          # Job lifecycle and monitoring setup
├── addon/                      # Reusable Python modules (optional)
│   ├── custom_utils.py
│   └── ...
└── requirements.txt            # Additional Python dependencies (optional)
```

---

## The Four Parts of a Project

A project is made of four categories of files:

### 1. JSON Configuration

The JSON files define **what** runs and **how**:

- `config_template.json` — the main blueprint describing infrastructure (how many agents, how many jobs, resource limits) and the default settings for each agent and job.
- `config_local.json` / `config_distant.json` — environment-specific values that get injected into the template at launch time via `$env_` placeholders.

See [JSON Configuration](../json-config/) for details.

### 2. CSV Override Files

The CSV files allow **per-agent** and **per-job** customization without modifying the JSON template:

- `data_agent.csv` — one row per agent, overriding specific fields from the default agent configuration.
- `data_job.csv` — one row per job, overriding specific fields from the default job payload.

See [CSV Configuration](../csv-config/) for details.

### 3. Python Files

The Python files define **the logic** and **the resource lifecycle**:

- `ctx_script.py` — your main automation logic.
- `ctx_agent_context.py` — initializes resources shared across all jobs (browser, proxy, screen...).
- `ctx_job_context.py` — initializes resources created fresh for each job (monitoring, identity...).
- `addon/` — optional reusable Python modules importable from anywhere in the project.

See [Python Files](../python-files/) for details.

### 4. Requirements (Optional)

- `requirements.txt` — extra Python packages not included in the base agent image. They are installed automatically at agent startup before any script execution.

---

## How It All Fits Together

When you hit **Launch** in the frontend:

```
1. Frontend reads config_template.json + config tune (local or distant)
   → replaces all $env_ placeholders (see Environment Substitution in JSON Configuration)
   → bundles your Python code (see Code Bundling and Execution)
   → injects bundled code + a generated run UUID

2. Frontend sends to orchestrator:
   config template (processed JSON), data_job.csv, data_agent.csv, requirements.txt

3. Orchestrator merges default_agent_message with data_agent.csv overrides
   → one config per agent, pushed to Redis

4. Orchestrator merges default_job_message with data_job.csv overrides
   → one message per job, dispatched to RabbitMQ

5. Orchestrator creates Kubernetes Jobs (distant mode)
   or uses existing Celery workers (container mode)

6. Each agent:
   → installs requirements.txt (if provided)
   → reads its config from Redis
   → starts consuming jobs from RabbitMQ
   → executes ctx_script(job_ctx, agent_ctx) for each job
```

For the complete three-layer merge process, see [Configuration Pipeline]({{< relref "/docs/reference/architecture/configuration-pipeline" >}}). For the end-to-end production run walkthrough, see [Run Lifecycle]({{< relref "/docs/reference/architecture/run-lifecycle" >}}).

---

## Quick Reference

| File | Required | Purpose |
|---|---|---|
| `config/config_template.json` | Yes | Main configuration blueprint with all settings |
| `config/config_local.json` | Yes | Environment values for local mode (container mode or workbench mode)|
| `config/config_distant.json` | Yes | Environment values for distant/Kubernetes mode |
| `config/data_agent.csv` | Yes | Per-agent config overrides (can be empty) |
| `config/data_job.csv` | Yes | Per-job config overrides (can be empty) |
| `ctx_script.py` | Yes | Main automation logic (`ctx_script` function) |
| `ctx_agent_context.py` | Yes | Agent lifecycle class (browser, proxy, etc.) |
| `ctx_job_context.py` | Yes | Job lifecycle class (monitoring, identity) |
| `addon/` | No | Reusable Python modules importable from anywhere in the project |
| `requirements.txt` | No | Extra Python packages to install at runtime |
