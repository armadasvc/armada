---
title: 4.1.3. Configuration Pipeline
linkTitle: 4.1.3. Configuration Pipeline
weight: 3
description: Three-layer configuration pipeline — config template, $env_ substitution, CSV deep merge, and UUID/code injection
---

## Overview

Armada uses a three-layer configuration pipeline. Each layer adds specificity:

```
Layer 1: config_template.json     ← Defaults + $env_ placeholders
             ↓
Layer 2: config_tune.json         ← Environment-specific values ($env_ resolution)
             ↓
Layer 3: data_agent.csv / data_job.csv  ← Per-instance overrides (deep merge)
             ↓
         Final agent_message / job_message
```

This design separates **what** the agent does (template) from **where** it runs (tune) from **how each instance differs** (CSV overrides).

---

## Layer 1 — Config Template

The config template (`config/config_template.json`) defines the full structure of a run. It has three top-level keys:

```json
{
  "run_message": { ... },
  "default_agent_message": { ... },
  "default_job_message": { ... }
}
```

- **`run_message`** — infrastructure settings (number of agents/jobs, image, resource limits). Consumed by the orchestrator, not forwarded to agents.
- **`default_agent_message`** — the default config for every agent (browser, proxy, fingerprint, custom fields). This is the base that CSV overrides are merged into.
- **`default_job_message`** — the default payload for every job. Arbitrary keys are forwarded as-is to the `job_message` dict inside `ctx_script`.

For detailed field descriptions and usage examples, see [JSON Configuration]({{< relref "/docs/setting-up-project/json-config" >}}).

---

## Layer 2 — Environment Substitution (`$env_`)

Any string value in the config template that starts with `$env_` is treated as a placeholder. The system recursively walks the config tree and replaces each placeholder with the corresponding value from the active config tune file (`config_local.json` or `config_distant.json`).

```
Input:   "screen_visible": "$env_SCREEN_VISIBLE"
Tune:    { "SCREEN_VISIBLE": 0 }
Output:  "screen_visible": 0
```

| Mode | Where substitution happens |
|---|---|
| Production / Container | Frontend (`configProcessor.ts`) — before the POST to orchestrator |
| Workbench | `get_messages.py` — `replace_env_values()` reads config files from disk |

For the full mechanism (type substitution, how to add placeholders, tune file details), see [JSON Configuration — Environment Substitution]({{< relref "/docs/setting-up-project/json-config#environment-substitution" >}}).

---

## Layer 3 — CSV Overrides (Deep Merge)

CSV files allow **per-instance** customization of agent and job messages. Each row in the CSV targets one specific agent or job by its index. For a complete user guide to CSV overrides, see [CSV Configuration]({{< relref "/docs/setting-up-project/csv-config" >}}).

### data_agent.csv

Each row overrides keys in `default_agent_message` for one agent:

```csv
config_proxy
"{""proxy_location"": ""US""}"
"{""proxy_location"": ""FR""}"
```

- Row 0 → agent 0: set `config_proxy.proxy_location` to `"US"`
- Row 1 → agent 1: set `config_proxy.proxy_location` to `"FR"`
- Agent 2+ (if any) keep the default

### data_job.csv

Same concept for jobs:

```csv
job_content
"scrape page A"
"scrape page B"
"scrape page C"
```

### CSV parsing internals

1. **Read CSV** — standard `csv.DictReader`, column headers become dict keys
2. **Recursive JSON parsing** — any cell that looks like JSON (`{...}` or `[...]`) is parsed recursively:
   ```python
   def parse_value(value):
       if value.startswith("{") and value.endswith("}"):
           parsed = json.loads(value)
           return {k: parse_value(v) for k, v in parsed.items()}
       return value
   ```
3. **Index tagging** — each parsed row gets `targetted_agent: i` or `targetted_job: i` appended
4. **Deep merge** — the orchestrator's `merge_messages()` function creates `N` copies of the default message and merges the targeted row into the corresponding copy

### Deep merge algorithm

```python
def merge_dicts(default, override):
    for key, value in override.items():
        if isinstance(value, dict) and key in default and isinstance(default[key], dict):
            merge_dicts(default[key], value)  # Recurse into nested dicts
        else:
            default[key] = value  # Overwrite scalars and lists
    return default
```

Rules:
- **Dict + Dict** → recursive merge
- **Dict + scalar** → scalar wins (override replaces entire subtree)
- **Scalar + scalar** → override wins
- **Missing key** → added to default

### Merge example

```
default_agent_message:
  config_proxy:
    upstream_proxy_enabled: 2
    proxy_location: ""
    verify_ip: 0

data_agent.csv row 0:
  config_proxy: {"proxy_location": "US", "verify_ip": 1}

Result for agent 0:
  config_proxy:
    upstream_proxy_enabled: 2    ← kept from default
    proxy_location: "US"         ← overridden by CSV
    verify_ip: 1                 ← overridden by CSV
```

---

## UUID and Code Injection

After environment substitution and before the POST to the orchestrator, the frontend injects two additional fields:

1. **`run_id`** — a UUID v4, injected into `run_message`, `default_agent_message`, and `default_job_message`
2. **`code`** — the bundled Python string, injected into `default_agent_message`

```python
# After injection, default_agent_message looks like:
{
  "code": "from ctx_agent_context import AgentContext\n...(full bundled script)...",
  "run_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "config_fantomas": { ... },
  "config_proxy": { ... },
  "config_fingerprint": { ... }
}
```

The code is embedded inside `default_agent_message` so that after deep merge, every agent's message carries the same code string. The agent then extracts and `exec()`s it at startup. See [Code Bundling and Execution]({{< relref "/docs/reference/architecture/code-bundling-execution" >}}) for the bundler internals and `exec()` mechanism.
