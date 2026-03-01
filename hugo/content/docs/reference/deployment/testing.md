---
title: 4.3.4. Testing Strategy
linkTitle: 4.3.4. Testing Strategy
weight: 4
description: Two-tier testing strategy — unit tests with mocking patterns, E2E test projects via workbench, and CI pipeline configuration
---

## Strategy Overview

Armada uses a two-tier testing strategy:

| Tier | Scope | Runner | External Dependencies | CI |
|---|---|---|---|---|
| **Unit tests** | Individual functions and classes, all services | pytest + pytest-asyncio | None (fully mocked) | On every push and PR to `master` |
| **E2E test projects** | Full agent lifecycle through the workbench | Manual via `python -m workbench.run_workbench` | Redis, RabbitMQ, Chrome, Xvfb, SQL Server, proxy/fingerprint providers | Not automated |

Unit tests run in CI on every commit. E2E tests are run manually by operators before releases or when validating changes to the agent, Fantomas, or the project scaffold.

---

## Unit Tests

### Running

```bash
pytest tests/unit -v
```

All external dependencies (SQL Server, Redis, RabbitMQ, HTTP APIs) are mocked. Unit tests require no running infrastructure.

### Architecture

```
tests/unit/
├── conftest.py                      # Root: adds fantomas and agent to sys.path
├── pytest.ini                       # Config: asyncio_mode=auto, markers
├── backend/
│   ├── conftest.py                  # Adds backend to sys.path
│   ├── test_websocket_manager.py
│   ├── test_db.py
│   ├── test_runs_router.py
│   ├── test_jobs_router.py
│   └── test_events_router.py
├── orchestrator/
│   ├── conftest.py                  # Cleans `app` module cache, swaps sys.path
│   ├── test_celery_service.py
│   ├── test_redis_service.py
│   ├── test_bot_router.py
│   └── test_kubernetes_service.py
├── agent/
│   ├── test_load_agent_message.py
│   ├── test_fingerprint_manager.py
│   ├── test_database_connector.py
│   ├── test_proxy_manager.py
│   └── test_monitoring_client.py
├── fingerprint_provider/
│   ├── conftest.py                  # Sets SQL_SERVER_* env vars, adds path
│   ├── test_crypto.py
│   ├── test_fingerprint.py
│   ├── test_forge.py
│   └── test_fp_db.py
├── proxy_provider/
│   ├── conftest.py                  # Cleans `db`/`config` cache, swaps path
│   ├── test_proxy_endpoint.py
│   ├── test_checks.py
│   └── test_proxy_db.py
└── lib/
    ├── test_screen.py
    ├── test_virtual_cursor_path.py
    └── test_identity.py
```

---

## E2E Test Projects

E2E tests are structured as complete Armada projects — the same format users write for production workloads. They run through the full agent lifecycle: config loading, `$env_` substitution, CSV merging, `exec()` of `main.py`, Celery worker init/shutdown, and `ctx_script` execution.

### Running

```bash
cd tests/e2e/<project_name>
python -m workbench.run_workbench
```

The workbench simulates the agent runtime locally: it loads config files, resolves environment variables, creates a Celery app, `exec()`s `main.py` with injected `app` and `agent_message`, then manually triggers the worker lifecycle (`init_worker` → `run_job` → `shutdown_worker`).

### Projects

| Project | Description |
|---|---|
| `database_connector_e2e` | Validates the database connector's ability to execute SQL queries (SELECT, INSERT, UPDATE, DELETE), parameterized queries, and enable/disable toggling. |
| `fantomas_actions_e2e` | Exercises the Fantomas browser automation library's DOM interactions: file uploads, native and xdo input methods, element selection, clicking, checkbox toggling, waiting for elements, JavaScript injection, iframe handling, tab/window management, and cookie operations. |
| `fingerprint_provider_e2e` | Tests fingerprint generation with configurable parameters (e.g. custom User-Agents). |
| `monitoring_client_e2e` | Validates the monitoring client's integration with the backend API to track job lifecycle: run/job creation, success and failure event recording, job status transitions.|
| `playwright_e2e` | Tests Playwright-based browser automation on HTML forms |
| `proxy_provider_e2e` | Tests the proxy manager's mitmproxy-based proxy with upstream support: request/response modification through custom addons, header injection, User-Agent override, proxy switching mid-run, data counting, and modifier persistence across proxy switches. |
| `resource_reallocation_between_job_and_agent_e2e` | Tests change in resource allocation (fingerprint provider, database, and proxy access) with heavy resources implemented at job level |
| `selenium_e2e` | Tests Selenium WebDriver browser automation on HTML forms |

---

## CI Pipeline

### Unit Tests (`.github/workflows/unit-tests.yml`)

```
Trigger:  push to master + pull requests to master
Runner:   ubuntu-latest, Python 3.10
Installs: freetds-dev, unixodbc-dev (for pymssql)
          All service requirements.txt
          Fantomas as editable package (pip install -e lib/fantomas)
Command:  pytest tests/unit -v
```

---

## Design Decisions and Tradeoffs


### No Frontend Tests

The React frontend has no test suite (no Jest, Vitest, or Cypress).

**Why:** The frontend is a thin client — it uploads files, calls two API endpoints, and renders WebSocket events. The monitoring panel is a read-only display of server-pushed events with minimal client-side logic.

**Tradeoff:** UI regressions (layout, interaction bugs, WebSocket reconnection edge cases) are only caught by manual testing.