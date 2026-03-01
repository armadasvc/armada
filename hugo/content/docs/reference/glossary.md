---
title: 4.4. Glossary
linkTitle: 4.4. Glossary
weight: 4
description: Definitions of all Armada terms — platform, services, domain concepts, configuration files, script files, and agent sub-components
---

## Platform

| Term | Definition |
|---|---|
| **Armada** | Kubernetes-native orchestration platform for distributed web automation. See [Architecture Overview]({{< relref "/docs/reference/architecture/overview" >}}). |
| **[Fantomas]({{< relref "/docs/fantomas/overview" >}})** | Armada's custom anti-detection browser automation library built on nodriver. Provides human-like cursor movement, keystroke emulation, and Display-server-level input via xdotool. Located at `lib/fantomas/`. |

## Services

| Term | Definition |
|---|---|
| **[Orchestrator]({{< relref "/docs/reference/services/orchestrator" >}})** (`armada-orchestrator`) | Central control plane (FastAPI, port 8080). Receives launch requests, merges configurations, pushes agent configs to Redis, dispatches jobs to RabbitMQ via Celery, and creates Kubernetes Jobs in distant mode. |
| **[Backend API]({{< relref "/docs/reference/services/backend" >}})** (`armada-backend`) | Monitoring and tracking API (FastAPI, port 8000). Stores run/job/event data in SQL Server and broadcasts real-time updates via WebSocket. |
| **[Frontend]({{< relref "/docs/reference/services/frontend" >}})** (`armada-frontend`) | Two-panel React web application (port 3000 local / 8080 production). Provides the Launch panel (file upload, code editor, config processing) and the Monitor panel (real-time run/job/event tracking). |
| **[Agent]({{< relref "/docs/reference/services/agent" >}})** (`armada-agent`) | Celery worker (Kubernetes pod or local Docker container) that executes user-provided Python automation code. By default, initializes a browser, proxy, and display once, then consumes jobs from RabbitMQ in a loop. |
| **[Proxy Provider]({{< relref "/docs/reference/services/proxy-provider" >}})** (`armada-proxy-provider`) | FastAPI service (port 5001) that selects and verifies proxies from the SQL Server inventory using filtering, IP verification, quality scoring, and location checks. |
| **[Fingerprint Provider]({{< relref "/docs/reference/services/fingerprint-provider" >}})** (`armada-fingerprint-provider`) | FastAPI service (port 5005) that retrieves and forges browser fingerprints from the SQL Server inventory. For the moment, supports AES-256-CBC encryption/decryption for Arkose fingerprints. |
| **[armada-meta]({{< relref "/docs/reference/services/meta" >}})** | Central versioning metadata package for the Armada monorepo. Acts as the single source of truth for the global platform version under the Changesets tooling. |

## Domain Concepts

| Term | Definition |
|---|---|
| **[Project]({{< relref "/docs/setting-up-project/key-concepts" >}})** | User-defined folder containing all files needed for a run: automation scripts, configuration template, CSV overrides, and optional `requirements.txt`. |
| **Run** | Single execution instance triggered from the Launch panel. Identified by a UUID (`run_id`). Comprises multiple agents and jobs. See [Key Concepts]({{< relref "/docs/getting-started/key_concepts" >}}). |
| **Job** | Single unit of work pulled from the RabbitMQ queue by an agent. Jobs are distributed first-come-first-served across agents. See [Key Concepts]({{< relref "/docs/getting-started/key_concepts" >}}). |
| **Event** | Granular progress step within a job, reported by the agent to the Backend API. Statuses: Running, Success, or Failed. See [Monitoring Client]({{< relref "/docs/guides/monitoring-client" >}}). |
| **Agent Lifecycle** | Startup-to-shutdown cycle of an agent: read config from Redis, initialize heavy resources (browser, proxy, display), consume jobs from RabbitMQ, execute `ctx_script()` for each job, shut down when the queue is empty. See [Run Lifecycle]({{< relref "/docs/reference/architecture/run-lifecycle" >}}). Resources like browser, proxy, display can also be instantianted at job level. |
| **CSV overrides** | Process by which the orchestrator deep-merges `config_template.json` defaults with CSV overrides (`data_agent.csv`, `data_job.csv`) to produce per-agent and per-job configurations. See [CSV Configuration]({{< relref "/docs/setting-up-project/csv-config" >}}). |
| **[Deep-Merge]({{< relref "/docs/reference/architecture/configuration-pipeline" >}})** | Recursive dictionary merge used to overlay CSV override values onto default configuration. Dot-separated CSV column headers (e.g., `config_proxy.proxy_location`) target nested keys. |
| **[Script Bundler]({{< relref "/docs/reference/architecture/code-bundling-execution" >}})** | Frontend logic that finds `main.py`, recursively inlines imports from `addon/`, `workbench/`, and `ctx*` files before sending to the orchestrator. |
| **[Environment Substitution]({{< relref "/docs/setting-up-project/json-config#environment-substitution" >}})** | Frontend-side process that scans `config_template.json` for `$env_` placeholders and replaces them with the corresponding values from the active config tune file (`config_local.json` or `config_distant.json`) at launch time. This allows a single template to target multiple environments without manual editing. |
| **`$env_` Placeholders** | String values in config templates starting with `$env_` that are replaced at launch time by corresponding keys from the config tune file. Enables environment substitution. See [JSON Configuration]({{< relref "/docs/setting-up-project/json-config" >}}). |
| **Config Tune File** | Environment-specific JSON file (`config_local.json` or `config_distant.json`) whose values replace `$env_` placeholders in the template at launch time. |
| **Local Mode** (`PLATFORM=local`) | Development mode using Docker Compose. The orchestrator skips Kubernetes. It can be both "Container mode" or "Workbench mode". |
| **[Workbench Mode]({{< relref "/docs/reference/deployment/workbench" >}})** | Lightweight local development mode that runs `ctx_script.py` directly inside the project folder, simulating the execution environment without orchestrator pipeline. |
| **Container Mode** | Sub-mode of Local Mode. All services run in Docker Compose containers and agents are started manually via `local/agent.sh`. Used for integration testing with the full orchestrator and monitoring pipeline. See [Quickstart Local]({{< relref "/docs/getting-started/quickstart-local" >}}). |
| **Distant Mode** (`PLATFORM=distant`) | Production mode on Kubernetes. The orchestrator creates `batch/v1` Indexed Jobs that spawn agent pods. See [Quickstart Kubernetes]({{< relref "/docs/getting-started/quickstart-kubernetes" >}}). |
| **Distribution Mode** | Sub-mode within distant mode: `kube` (production cluster with Docker Hub image pull) or `minikube`. It changes pull policy to faster use of minikube for testing|
| **Launch Panel** | First tab of the frontend UI. Provides file upload, Monaco editor, config selection, and the Launch button. |
| **Monitor Panel** | Second tab of the frontend UI. Displays three-level drill-down (Runs, Jobs, Events) with real-time WebSocket updates. |
| **[Code Injection (`exec()` pattern)]({{< relref "/docs/reference/architecture/code-bundling-execution" >}})** | Mechanism by which user Python code is transported as a string through the pipeline (bundled in frontend → injected into config → stored in Redis → retrieved by agent → executed via `exec()`). Enables a single immutable agent Docker image to run arbitrary project code. |
| **Fingerprint Forging** | Process of taking a stored encrypted browser fingerprint, decrypting it, modifying the user agent and timestamp to match the current agent, and re-encrypting it — producing a fingerprint that passes antibot checks as if generated natively. See [Fingerprint Provider guide]({{< relref "/docs/guides/fingerprint-provider" >}}). |
| **IPQualityScore (IPQS)** | Third-party API used by the Proxy Provider to score proxy quality. Returns a fraud score (0–100); Armada inverts this to a "quality score" and rejects proxies below `quality_threshold` (default 70). |
| **Cascading Delete** | When a run is deleted, events are deleted first, then jobs, then the run record itself. See [Database Reference]({{< relref "/docs/reference/deployment/database" >}}). |

## Configuration Files

| Term | Definition |
|---|---|
| **[`config_template.json`]({{< relref "/docs/setting-up-project/json-config" >}})** | Main configuration blueprint with three sections: `run_message`, `default_agent_message`, and `default_job_message`. |
| **`run_message`** | Config section controlling infrastructure: number of agents, number of jobs, Docker image name/version, and per-agent CPU/memory limits. See [JSON Configuration]({{< relref "/docs/setting-up-project/json-config#run_message--infrastructure-settings" >}}). |
| **`default_agent_message`** | Config section providing default settings for every agent: browser config (Fantomas), proxy config, fingerprint config, and user-defined fields. See [JSON Configuration]({{< relref "/docs/setting-up-project/json-config#default_agent_message--agent-configuration" >}}). These resources can also be at job level, in which case their are configured in default_job_message|
| **`default_job_message`** | Config section providing the default payload for every job. Contains arbitrary user-defined fields accessible via `job_ctx.job_message`. See [JSON Configuration]({{< relref "/docs/setting-up-project/json-config#default_job_message--job-configuration" >}}). It can also instantiate resources at job-level|
| **`config_local.json`** | Environment values file for local mode. |
| **`config_distant.json`** | Environment values file for distant (Kubernetes) mode. |
| **[`data_agent.csv`]({{< relref "/docs/setting-up-project/csv-config" >}})** | CSV file providing per-agent overrides. Each row targets a specific agent by index and is deep-merged onto `default_agent_message`. |
| **[`data_job.csv`]({{< relref "/docs/setting-up-project/csv-config" >}})** | CSV file providing per-job overrides. Each row targets a specific job by index and is deep-merged onto `default_job_message`. |

## User-Defined Script Files

| Term | Definition |
|---|---|
| **`main.py`** | Entry-point Python script in a project. Defines the Celery task, worker lifecycle hooks, and calls `ctx_script()`. |
| **[`ctx_script.py`]({{< relref "/docs/setting-up-project/python-files#ctx_scriptpy--the-script-context" >}})** | Main automation logic file. Contains the `ctx_script(job_ctx, agent_ctx)` async function executed by the agent for each job. |
| **[`ctx_agent_context.py`]({{< relref "/docs/setting-up-project/python-files#ctx_agent_contextpy--the-agent-context" >}})** | Defines the `AgentContext` class managing agent lifecycle: screen, browser, proxy, fingerprint, and database initialization/teardown. |
| **[`ctx_job_context.py`]({{< relref "/docs/setting-up-project/python-files#ctx_job_contextpy--the-job-context" >}})** | Defines the `JobContext` class managing per-job lifecycle: monitoring client, identity generation, and job message access. |
| **[`addon/` folder]({{< relref "/docs/setting-up-project/python-files#addon--reusable-python-modules" >}})** | Optional folder inside a project for reusable Python modules. All imports from `addon/` are automatically inlined by the Script Bundler before deployment. |
| **`requirements.txt`** | Optional file listing extra Python dependencies installed at agent startup (base64-encoded and passed as an env var). See [Python Files]({{< relref "/docs/setting-up-project/python-files#requirementstxt--extra-dependencies" >}}). |
| **`AgentContext`** | Python async context manager that initializes heavy agent resources: `Screen`, `FantomasNoDriver`, `ProxyManager`, `FingerprintManager`, `DatabaseConnector`. See [Python Files]({{< relref "/docs/setting-up-project/python-files#ctx_agent_contextpy--the-agent-context" >}}). |
| **`JobContext`** | Python async context manager that initializes per-job resources: for eg `Identity`. See [Python Files]({{< relref "/docs/setting-up-project/python-files#ctx_job_contextpy--the-job-context" >}}). |


## Agent Sub-Components

| Term | Definition |
|---|---|
| **[`ProxyManager`]({{< relref "/docs/guides/proxy-provider" >}})** | Manages a local mitmproxy subprocess on port 8081. Supports upstream proxy chaining, pluggable response/request modifiers, data retrievers, and hot-swappable upstream proxies. |
| **[`FingerprintManager`]({{< relref "/docs/guides/fingerprint-provider" >}})** | Fetches forged browser fingerprints from the Fingerprint Provider API, configurable by antibot vendor, website, and collection date. |
| **[`MonitoringClient`]({{< relref "/docs/guides/monitoring-client" >}})** | Reports execution progress to the Backend API via HTTP. Methods: `create_job()`, `record_success_event()`, `record_finalsuccess_event()`, `record_failed_event()`. Recommandation to be instantiated at job-level so the instantiation does not appear in the ctx_script|
| **[`DatabaseConnector`]({{< relref "/docs/guides/database-connector" >}})** | Provides direct SQL Server access for user scripts. Methods: `post_to_db()`, `select_from_db()`, `select_with_commit_from_db()`. |
