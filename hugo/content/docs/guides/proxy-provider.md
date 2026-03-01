---
title: 3.2. Proxy Provider
linkTitle: 3.2. Proxy Provider
weight: 2
description: Configure the mitmproxy layer, upstream proxy modes, traffic modifiers, data retrievers, and proxy rotation
---

## Overview

The proxy layer gives each agent a local mitmproxy instance (port 8081) that all browser traffic passes through. Optionally, this local proxy forwards traffic to an **upstream proxy** fetched from the Proxy Provider service, which serves verified proxies from a database.

Beyond routing, the proxy layer also supports **response modifiers**, **request modifiers**, and **data retrievers** — hooks that let you intercept and transform HTTP traffic in real time. For the Proxy Provider service API and deployment reference, see [Proxy Provider Service]({{< relref "/docs/reference/services/proxy-provider" >}}).

```
Browser ──► mitmproxy (localhost:8081) ──► Upstream Proxy ──► Internet
                │
                ├─ request modifiers
                ├─ response modifiers
                └─ data retrievers
```

## Configuration

Add a `config_proxy` block to `default_agent_message` in your `config_template.json` (see [JSON Configuration]({{< relref "/docs/setting-up-project/json-config" >}})):

```json
"default_agent_message": {
  "config_proxy": {
    "upstream_proxy_enabled": 1,
    "upstream_proxy_broker_type": "provider",
    "proxy_provider_name": "iproyal",
    "proxy_location": "",
    "proxy_type": "",
    "proxy_rotation_strategy": "",
    "verify_ip": 0,
    "verify_quality": 0,
    "verify_location": 0,
    "quality_threshold": 70,
    "max_queries_number": 3
  }
}
```

### Fields

| Field | Type | Description |
|---|---|---|
| `upstream_proxy_enabled` | int | `0` = no upstream proxy (local mitmproxy only), `1`= enable upstream proxy |
| `upstream_proxy_broker_type` | string | `"provider"` = fetch from Proxy Provider service, `"direct"` = use a hardcoded proxy URL |
| `proxy_provider_name` | string | Filter proxies by provider name (e.g. `"iproyal"`) |
| `proxy_location` | string | Filter by geographic location (e.g. `"Europe"`, `"US"`) |
| `proxy_type` | string | Filter by proxy type (`residential`, `mobile`) |
| `proxy_rotation_strategy` | string | Filter by rotation strategy (`sticky`, `rotating`) |
| `verify_ip` | int | `1` = resolve and return the proxy's outbound IP |
| `verify_quality` | int | `1` = run an IPQualityScore fraud check |
| `verify_location` | int | `1` = verify the proxy IP matches `proxy_location` |
| `quality_threshold` | int | Minimum quality score (0-100) to accept a proxy |
| `max_queries_number` | int | Max retry attempts if proxy checks fail |

## Initialization

The `ProxyManager` is initialized in `ctx_agent_context.py`:

```python
from src.proxy_manager import ProxyManager

class AgentContext:
    def __init__(self, agent_message):
        self.agent_message = agent_message

    def instantiate_default(self):
        self.proxy_manager = ProxyManager(
            self.agent_message["config_proxy"]
        ).launch_proxy()
```

On `launch_proxy()`, the manager:
1. Kills any existing process on port 8081
2. Fetches an upstream proxy from the Proxy Provider (if enabled)
3. Starts a local mitmproxy subprocess on port 8081

The browser is automatically configured to use this proxy via the `--proxy-server=http://127.0.0.1:8081` Chrome flag in `config_fantomas.config_browser`.

## Proxy Modes

### No upstream proxy

Set `upstream_proxy_enabled` to `0`. Traffic flows through the local mitmproxy only (useful for local development or when you just need traffic interception without IP masking):

```json
"config_proxy": {
  "upstream_proxy_enabled": 0
}
```

### Fetch from Proxy Provider

Set `upstream_proxy_enabled` to `1` and `upstream_proxy_broker_type` to `"provider"`. The manager queries the Proxy Provider service for a random proxy matching your filters:

```json
"config_proxy": {
  "upstream_proxy_enabled": 1,
  "upstream_proxy_broker_type": "provider",
  "proxy_provider_name": "iproyal",
  "proxy_location": "Europe",
  "verify_quality": 1,
  "quality_threshold": 70,
  "max_queries_number": 3
}
```

### How the request is built

When `upstream_proxy_broker_type` is `"provider"`, the `ProxyManager` builds a GET request to the Proxy Provider's `/fetch_proxy` endpoint. Only config fields with truthy values are included as query parameters — fields set to `0`, `""`, or `None` are omitted.

For example, with this config:

```json
"config_proxy": {
  "upstream_proxy_enabled": 1,
  "upstream_proxy_broker_type": "provider",
  "proxy_provider_name": "iproyal",
  "proxy_location": "Europe",
  "proxy_type": "",
  "proxy_rotation_strategy": "",
  "verify_ip": 1,
  "verify_quality": 1,
  "verify_location": 0,
  "quality_threshold": 70,
  "max_queries_number": 3
}
```

The resulting HTTP request would be:

```
GET http://127.0.0.1:5001/fetch_proxy?proxy_provider_name=iproyal&proxy_location=Europe&verify_ip=1&verify_quality=1&quality_threshold=70&max_queries_number=3
```

Note that `proxy_type`, `proxy_rotation_strategy`, and `verify_location` are excluded because their values are falsy.

### How the response is built

The response from the Proxy Provider is **adaptive** — it only includes fields for the checks you actually requested. This keeps the response minimal and avoids unnecessary work on the server side.

**Always included:**

| Field | Description |
|---|---|
| `proxy_url` | The proxy address (e.g. `http://user:pass@host:port`) |
| `attempt` | Which retry attempt returned this proxy (starts at 1) |

**Conditionally included — only if the corresponding `verify_*` flag is set to `1`:**

| Field | Included when | Content |
|---|---|---|
| `verify_ip` | `verify_ip=1` | `{"ip": "1.2.3.4"}` or `{"ip": null}` if resolution failed |
| `verify_quality` | `verify_quality=1` | `{"fraud_score_inverted": 92, "quality_threshold": 70, "quality_pass": true}` |
| `verify_location` | `verify_location=1` | `{"actual_timezone": "Europe/Paris", "expected_location": "Europe", "location_match": true}` |

**Example — all checks enabled:**

```json
{
  "proxy_url": "http://user:pass@proxy.example.com:8080",
  "attempt": 1,
  "verify_ip": {
    "ip": "185.230.12.45"
  },
  "verify_quality": {
    "fraud_score_inverted": 92,
    "quality_threshold": 70,
    "quality_pass": true
  },
  "verify_location": {
    "actual_timezone": "Europe/Paris",
    "expected_location": "Europe",
    "location_match": true
  }
}
```

**Example — no checks enabled:**

```json
{
  "proxy_url": "http://user:pass@proxy.example.com:8080",
  "attempt": 1
}
```

If a check fails (e.g. quality score below threshold or location mismatch), the service automatically retries with a new proxy, up to `max_queries_number` attempts.

### Direct proxy URL

Set `upstream_proxy_broker_type` to `"direct"`. Instead of querying the service, the manager uses the URL from the `PROXY_PROVIDER_URL` environment variable (see [Environment Variables]({{< relref "/docs/reference/architecture/environment-variables" >}})) directly as the upstream proxy:

```json
"config_proxy": {
  "upstream_proxy_enabled": 1,
  "upstream_proxy_broker_type": "direct"
}
```

## Addon Registration and Proxy Lifecycle

The `ProxyManager` runs mitmproxy in a **separate subprocess** (via `billiard.Process`). When `launch_proxy()` is called, the current modifier and retriever arrays are copied into the child process. This has important implications for when addons can be registered.

### Registration must happen before launch

Addons (request modifiers, response modifiers, data retrievers) **must** be registered before calling `launch_proxy()`. Once the mitmproxy subprocess starts, it holds its own copy of the arrays — any addon added to the parent process afterward will not be seen by the running proxy.

```python
class AgentContext:
    def instantiate_default(self):
        # 1. Create the ProxyManager (no subprocess yet)
        self.proxy_manager = ProxyManager(self.agent_message["config_proxy"])

        # 2. Register addons while still in the parent process
        self.proxy_manager.add_request_modifier(my_request_modifier)
        self.proxy_manager.add_modifier(my_response_modifier)
        self.proxy_manager.add_retriever("my_queue", my_retriever)

        # 3. Launch — arrays are copied into the subprocess
        self.proxy_manager.launch_proxy()
```

### What happens after launch

| Action | Effect |
|---|---|
| Register addon **before** `launch_proxy()` | Addon is active in the proxy subprocess |
| Register addon **after** `launch_proxy()` | Addon is **ignored** — the running subprocess has its own copy |
| Register addon **after** launch, then call `switch_upstream_proxy()` | Addon becomes active — `switch_upstream_proxy()` kills the old subprocess and starts a new one with the current arrays |

### Proxy switching re-applies addons

`switch_upstream_proxy()` internally calls `exit_local_proxy()` followed by `launch_proxy()`. The new subprocess is created with the **current** state of the modifier and retriever arrays. This means:

- All previously registered addons are preserved across switches.
- Any addon added after the initial launch but before a switch will be picked up by the new subprocess.

```python
async def ctx_script(job_ctx, agent_ctx):
    # Proxy is already running with initial addons

    # This modifier won't be active yet (subprocess already running)
    agent_ctx.proxy_manager.add_request_modifier(extra_modifier)

    # After switch, ALL addons (initial + extra_modifier) are active
    agent_ctx.proxy_manager.switch_upstream_proxy()
```

### Pickling constraint

Since the subprocess receives addons via serialization, all modifier and retriever functions **must be picklable**. In practice this means they must be defined at **module level** — not as lambdas, closures, or nested functions.

```python
# Good — module-level function, picklable
def remove_csp_header(flow):
    if "content-security-policy" in flow.response.headers:
        del flow.response.headers["content-security-policy"]

# Bad — lambda, not picklable
remove_csp = lambda flow: flow.response.headers.pop("content-security-policy", None)

# Bad — closure, not picklable
def make_modifier(header_name):
    def modifier(flow):
        del flow.response.headers[header_name]
    return modifier
```

A recommended pattern is to place each addon in its own file inside the `addon/` directory (see [Reusable Python Modules]({{< relref "/docs/setting-up-project/python-files#addon--reusable-python-modules" >}})) and import them where needed:

```
project/
└── addon/
    ├── request_modifier_add_custom_header.py
    ├── response_modifier_remove_csp.py
    └── retriever_capture_api.py
```

```python
from addon.request_modifier_add_custom_header import request_modifier_add_custom_header
from addon.response_modifier_remove_csp import response_modifier_remove_csp
from addon.retriever_capture_api import retriever_capture_api
```

## Usage in ctx_script.py

### Switching proxy mid-run

To get a fresh upstream proxy during a job (e.g. after a block), call `switch_upstream_proxy()`:

```python
async def ctx_script(job_ctx, agent_ctx):
    # ... some automation ...

    # IP got blocked, rotate to a new proxy
    agent_ctx.proxy_manager.switch_upstream_proxy()

    # Continue with a new IP
```

This stops the current mitmproxy process, fetches a new upstream proxy, and restarts mitmproxy. All previously registered addons remain active.

### Adding response modifiers

Response modifiers intercept and alter HTTP responses passing through the proxy. They receive a `flow` object with access to `flow.response.headers`, `flow.response.content`, etc.

```python
def remove_csp_header(flow):
    if flow.response and "content-security-policy" in flow.response.headers:
        del flow.response.headers["content-security-policy"]

agent_ctx.proxy_manager.add_modifier(remove_csp_header)
```

### Adding request modifiers

Request modifiers intercept outgoing requests. They receive a `flow` object with access to `flow.request.headers`, `flow.request.url`, etc.

```python
def add_custom_header(flow):
    flow.request.headers["X-Custom"] = "my-value"

agent_ctx.proxy_manager.add_request_modifier(add_custom_header)
```

### Adding data retrievers

Retrievers extract data from responses and store it in a named queue you can read later. They receive `flow` and `queue` as arguments:

```python
def capture_api_response(flow, queue):
    if "/api/data" in flow.request.url and flow.response:
        queue.put(flow.response.text)

agent_ctx.proxy_manager.add_retriever("api_data", capture_api_response)
```

Then in your script, retrieve the captured data:

```python
async def ctx_script(job_ctx, agent_ctx):
    # Navigate to a page that triggers the API call
    tab = await agent_ctx.browser.get("https://example.com")

    # Retrieve the last captured value from the queue
    data = agent_ctx.proxy_manager.retrieve("api_data")
```

### Execution order inside the proxy

When a response arrives, the `ProxyAddOn` processes hooks in this order:

1. **Data counting** — cumulative `Content-Length` tracking
2. **Retrievers** — data extraction into queues
3. **Response modifiers** — header/body transformations

This means retrievers see the **original** response before any modifier alters it.

For requests, **request modifiers** run before the request is forwarded upstream.

### Monitoring bandwidth

The proxy tracks total data transferred. Access it with:

```python
total_bytes = agent_ctx.proxy_manager.get_data_count()
```

## Disabling the Proxy Layer

If your project does not need any proxy (no upstream, no traffic interception), remove the `ProxyManager` from `ctx_agent_context.py` and remove `--proxy-server=http://127.0.0.1:8081` from the browser options in `config_template.json`.
