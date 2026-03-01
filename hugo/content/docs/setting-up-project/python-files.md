---
title: 2.4. Python Files
linkTitle: 2.4. Python Files
weight: 4
description: ctx_script, agent context, job context, two-tier lifecycle, addons, and replacing the browser library
---

## Overview

A project contains four types of Python files:

| File | Role |
|---|---|
| `ctx_script.py` | Your main automation logic |
| `ctx_agent_context.py` | Initializes resources shared across all jobs (browser, proxy, screen...) |
| `ctx_job_context.py` | Initializes resources created fresh for each job (monitoring, identity...) |
| `addon/` | Reusable Python modules importable from anywhere in the project |

All imports from files starting with `ctx` or from `addon/`, `workbench/`, folders are automatically inlined (bundled) before deployment. You don't need to worry about packaging — the frontend handles it.

---

## ctx_script.py — The Script Context

This is where your automation logic lives. It must define an async function named `ctx_script` that accepts two parameters:

```python
from ctx_agent_context import AgentContext
from ctx_job_context import JobContext

async def ctx_script(job_ctx: JobContext, agent_ctx: AgentContext):
    # Access the browser
    tab = await agent_ctx.browser.get("https://example.com")

    # Access job-specific data
    job_data = job_ctx.job_message

    # Report progress to dashboard
    job_ctx.monitoring_client.record_success_event("Step completed")
```

See the [Monitoring Client guide]({{< relref "/docs/guides/monitoring-client" >}}) for all reporting methods.

**What you have access to:**

- `agent_ctx` — everything initialized in `AgentContext`: `browser`, `screen`, `proxy_manager`, `fingerprint_manager`, `database`, and the raw `agent_message` dict.
- `job_ctx` — everything initialized in `JobContext`: `monitoring_client`, `identity`, and the raw `job_message` dict.

---

## ctx_agent_context.py — The Agent Context

This file defines the `AgentContext` class, which manages resources that live for the **entire agent lifetime** and are **shared across all jobs**.

```python
from fantomas import Screen, FantomasNoDriver
from src.database_connector import DatabaseConnector
from src.proxy_manager import ProxyManager
from src.fingerprint_manager import FingerprintManager

class AgentContext:

    def __init__(self, agent_message):
        self.agent_message = agent_message

    def instantiate_default(self):
        self.proxy_manager = ProxyManager(self.agent_message["config_proxy"]).launch_proxy()  # see Proxy Provider guide
        self.fingerprint_manager = FingerprintManager(self.agent_message["config_fingerprint"])  # see Fingerprint Provider guide
        self.database = DatabaseConnector()  # see Database Connector guide

    async def __aenter__(self):
        self.instantiate_default()
        self.screen = Screen(self.agent_message["config_fantomas"]["config_screen"]).launch_screen()
        self.browser = await FantomasNoDriver(self.agent_message["config_fantomas"]["config_browser"]).launch_browser()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.browser.stop()
        self.screen.stop_screen()
```

**How to customize:**
- Add or remove services in `instantiate_default()` depending on what your script needs.
- The `__aenter__` / `__aexit__` pattern lets you use `async with AgentContext(msg) as agent_ctx:` for automatic resource cleanup.
- Everything in `agent_message` comes from `default_agent_message` (after merge with CSV overrides).

Each built-in module has a dedicated guide: [Proxy Provider]({{< relref "/docs/guides/proxy-provider" >}}), [Fingerprint Provider]({{< relref "/docs/guides/fingerprint-provider" >}}), [Database Connector]({{< relref "/docs/guides/database-connector" >}}). For the browser API, see [Fantomas Overview]({{< relref "/docs/fantomas/overview" >}}).

---

## ctx_job_context.py — The Job Context

This file defines the `JobContext` class, which manages resources that are **created and destroyed for each individual job**.

```python
from fantomas import Identity
from src.monitoring_client import MonitoringClient
import uuid
import os

class JobContext():
    def __init__(self, job_message):
        self.job_message = job_message

    def instantiate_default(self):
        pod_index = os.getenv("POD_INDEX", 100)
        job_uuid = str(uuid.uuid4())
        self.monitoring_client = MonitoringClient(
            self.job_message["run_id"], pod_index, job_uuid
        ).create_job()

    async def __aenter__(self):
        self.instantiate_default()
        self.identity = Identity().launch_identity_creation()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass
```

**How to customize:**
- Add per-job initialization logic in `instantiate_default()`.
- The `monitoring_client` reports progress events back to the dashboard.
- Everything in `job_message` comes from `default_job_message` (after merge with CSV overrides).

---

## The Two-Tier Lifecycle

Resources in your project live in one of two scopes:

```
Agent lifecycle (outer)        Job lifecycle (inner, repeated)
┌─────────────────────────┐    ┌─────────────────────┐
│  __aenter__             │    │  __aenter__          │
│    instantiate_default  │    │    instantiate_default│
│    create resources     │    │    create resources   │
│                         │    │                       │
│    ┌── job 0 ──┐        │    │  ctx_script(job, agent)│
│    ├── job 1 ──┤        │    │                       │
│    ├── job 2 ──┤        │    │  __aexit__            │
│    └── job N ──┘        │    │    teardown resources │
│                         │    └─────────────────────┘
│  __aexit__              │
│    teardown resources   │
└─────────────────────────┘
```

- **Agent context** — entered once, lives for the entire agent pod lifetime. Resources placed here are created once and **shared across all jobs**. Best for expensive resources (browser, screen, proxy, database).
- **Job context** — entered for each individual job. Resources placed here are **created and destroyed per job**. Best for lightweight, per-job resources (identity, monitoring).

### Default Resource Placement

| Resource | Context | Reason |
|---|---|---|
| `Screen` | Agent | Expensive — one virtual display reused across jobs |
| `FantomasNoDriver` (browser) | Agent | Expensive — one Chrome instance reused across jobs |
| `ProxyManager` | Agent | Starts a mitmproxy subprocess shared across jobs |
| `FingerprintManager` | Agent | One fingerprint config per agent |
| `DatabaseConnector` | Agent | One DB connection pool per agent |
| `Identity` | Job | Cheap — generates a fresh fake identity per job |
| `MonitoringClient` | Job | Creates a unique job record in the dashboard per job |

### Moving Resources Between Contexts

You are free to move any resource from one context to the other. The most common case is moving Screen and Browser into the job context so that each job gets a **fresh browser instance**.

| Move | When |
|---|---|
| Browser/Screen **to job** | You need full isolation between jobs (clean browser state, no cookie leakage) |
| Browser/Screen **in agent** (default) | You want performance — reusing a browser across jobs avoids startup cost |
| Identity **to agent** | You want one persistent persona per agent across all its jobs |
| Identity **in job** (default) | Each job needs a fresh, independent identity |
| ProxyManager **to job** | You want a different proxy for each job (rotate per job) |

The rule of thumb: **agent-scoped = shared and fast, job-scoped = isolated and fresh**.

{{% alert title="Note" %}}
When moving a resource to a different context, make sure its configuration comes from the correct message. For example, if you move browser to the job context, `config_fantomas` should be in `default_job_message` instead of `default_agent_message`.
{{% /alert %}}

---

## addon/ — Reusable Python Modules

The `addon/` folder is a place to put any Python files you want to import from elsewhere in your project (from `ctx_script.py`, context files, or other addons). It acts as a shared utility layer.

**Examples of what you might put here:**
- Helper functions and constants used across multiple scripts
- mitmproxy request/response modifiers for traffic interception
- Data extraction utilities
- Any reusable logic you want to keep separate from the main script

```python
# addon/my_helpers.py
def parse_response(data):
    ...

# ctx_script.py
from addon.my_helpers import parse_response

async def ctx_script(job_ctx, agent_ctx):
    result = parse_response(some_data)
```

All files in `addon/` are automatically bundled (inlined) by the frontend before deployment — you don't need to worry about packaging.

---

## requirements.txt — Extra Dependencies

If your script requires Python packages not included in the base agent image, list them here:

```
beautifulsoup4==4.12.2
lxml==5.1.0
```

At agent startup, these packages are installed before any script execution.

The base image already includes: `requests`, `mitmproxy`, `nodriver`, `pillow`, `numpy`, `redis`, `celery`, `pymssql`, and the `fantomas` library.

---

## Replacing Fantomas With Another Library

The context files are plain Python classes — you can replace Fantomas with any browser automation library.

**Using Selenium:**

```python
# ctx_agent_context.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class AgentContext:
    def __init__(self, agent_message):
        self.agent_message = agent_message

    def instantiate_default(self):
        pass

    async def __aenter__(self):
        self.instantiate_default()
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1500,1200")
        self.browser = webdriver.Chrome(options=options)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.browser.quit()
```

**Using Playwright:**

```python
# ctx_agent_context.py
from playwright.async_api import async_playwright

class AgentContext:
    def __init__(self, agent_message):
        self.agent_message = agent_message

    def instantiate_default(self):
        pass

    async def __aenter__(self):
        self.instantiate_default()
        self._playwright = await async_playwright().start()
        chromium = self._playwright.chromium
        self.browser = await chromium.launch(headless=True)
        self.page = await self.browser.new_page()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.browser.close()
        await self._playwright.stop()
```

If you use a library not included in the base image, add it to `requirements.txt`.

{{% alert title="Tip" %}}
You can mix approaches: keep Fantomas `Screen` for Xvfb management while using Playwright for the browser itself. The context classes are yours to compose however you want. See [Why Fantomas]({{< relref "/docs/fantomas/why-fantomas" >}}) to understand the anti-detection trade-offs before switching libraries.
{{% /alert %}}
