---
title: 2.2. JSON Configuration
linkTitle: 2.2. JSON Configuration
weight: 2
description: Config template structure, $env_ environment substitution, config tune files, and all configuration fields
---

## config_template.json

The config template is the main configuration blueprint for your project. It is a JSON file with three top-level sections:

```json
{
  "run_message": { ... },
  "default_agent_message": { ... },
  "default_job_message": { ... }
}
```

- **`run_message`** — controls the infrastructure: how many agents, how many jobs, resource limits.
- **`default_agent_message`** — the default configuration received by every agent (browser, proxy, fingerprint, and any custom fields).
- **`default_job_message`** — the default configuration received by every job dispatched to agents.

---

## run_message — Infrastructure Settings

Controls how many agents and jobs are created, and their resource allocation.

```json
"run_message": {
  "image_name": "armada-agent",
  "image_version": "latest",
  "number_of_agents": 1,
  "number_of_jobs": 1,
  "agent_cpu": "500m",
  "agent_memory": "512Mi"
}
```

| Field | Type | Description |
|---|---|---|
| `image_name` | string | Docker image name for agent pods |
| `image_version` | string | Image tag (e.g. `"latest"`) |
| `number_of_agents` | int | Number of agent pods to deploy (parallelism) |
| `number_of_jobs` | int | Total number of job messages to dispatch to the queue |
| `agent_cpu` | string | CPU request per agent (Kubernetes notation, e.g. `"500m"`) |
| `agent_memory` | string | Memory request per agent (Kubernetes notation, e.g. `"512Mi"`) |

---

## default_agent_message — Agent Configuration

This is the default configuration every agent receives. It typically includes browser, proxy, and fingerprint settings. You can add any custom fields your script needs — they will be accessible through `agent_ctx.agent_message` in your code.

```json
"default_agent_message": {
  "config_fantomas": {
    "config_browser": {
      "fantomas_browser_options": [
        "--proxy-server=http://127.0.0.1:8081",
        "--ignore-certificate-errors",
        "--window-size=1500,1200",
        "--start-fullscreen"
      ],
      "fantomas_emulate_movement": 1,
      "fantomas_show_cursor": 0,
      "fantomas_emulate_keyboard": 1
    },
    "config_screen": {
      "screen_visible": "$env_SCREEN_VISIBLE",
      "screen_height": 1500,
      "screen_width": 2000
    }
  },
  "config_proxy": {
    "upstream_proxy_enabled": 1,
    "upstream_proxy_broker_type": "provider",
    "proxy_provider_name": "iproyal",
    "verify_ip": 0,
    "verify_quality": 0,
    "max_queries_number": 3
  },
  "config_fingerprint": {
    "antibot_vendor": "arkose",
    "website": "X",
    "collection_date_day": "01",
    "collection_date_month": "12",
    "collection_date_year": "2025"
  }
}
```

### config_fantomas (Browser Automation)

| Field | Description |
|---|---|
| `fantomas_browser_options` | Chrome command-line flags |
| `fantomas_emulate_movement` | Enable WindMouse human-like cursor movement (1/0) |
| `fantomas_show_cursor` | Render cursor on screen for debugging (1/0) |
| `fantomas_emulate_keyboard` | Enable randomized keystroke emulation (1/0) |
| `screen_visible` | Show Xvfb display (1 = visible, 0 = headless). Use `$env_SCREEN_VISIBLE` for runtime control |
| `screen_height` / `screen_width` | Virtual display resolution |

For details on WindMouse and keystroke emulation, see the [Fantomas Overview]({{< relref "/docs/fantomas/overview" >}}).

### config_proxy (Proxy Layer)

Controls the local mitmproxy and optional upstream proxy. Key fields: `upstream_proxy_enabled` (0/1), `upstream_proxy_broker_type` (`"provider"`/`"direct"`), `proxy_provider_name`, `proxy_location`, `verify_ip`, `verify_quality`, `quality_threshold`, `max_queries_number`.

For the complete field reference, proxy modes, addon system, and usage examples, see the [Proxy Provider guide]({{< relref "/docs/guides/proxy-provider" >}}).

### config_fingerprint (Fingerprint Forging)

Controls browser fingerprint retrieval. Key fields: `antibot_vendor`, `website`, `collection_date_day`/`_month`/`_year`.

For the complete field reference and usage examples, see the [Fingerprint Provider guide]({{< relref "/docs/guides/fingerprint-provider" >}}).

---

## default_job_message — Job Configuration

This is the default payload every job receives. Add any fields your script needs at the job level — they will be accessible through `job_ctx.job_message` in your code.

```json
"default_job_message": {
  "job_content": "default_job_content"
}
```

You can add any arbitrary keys both in default_job_message and default_agent_message. They are all passed as-is to the agent.

---

## Environment Substitution

Environment substitution lets the same `config_template.json` work across different environments (local development vs. Kubernetes production) without modification. Values that need to change between environments are expressed as **`$env_` placeholders** and resolved at launch time.

### How It Works

Any string value in `config_template.json` that starts with `$env_` is a placeholder. At launch time, the system **recursively walks** the entire JSON tree — objects, arrays, nested structures — and replaces every `$env_` string with the corresponding value from the selected **config tune file** (`config_local.json` or `config_distant.json`).

The resolution rule is simple:

1. Strip the `$env_` prefix → the remainder is the **lookup key**.
2. Search for that key in the config tune file.
3. If found, replace the placeholder with the tune value. If not found, keep the original placeholder string unchanged.

### Example

In `config_template.json`:
```json
"screen_visible": "$env_SCREEN_VISIBLE"
```

In `config_local.json` (for local development):
```json
{
  "SCREEN_VISIBLE": 1
}
```

In `config_distant.json` (for Kubernetes production):
```json
{
  "SCREEN_VISIBLE": 0
}
```

**Result:** when launching in local mode (container or workbench), `screen_visible` becomes `1` (visible for debugging). When launching in distant mode, it becomes `0` (headless).

### Type Substitution

Although the placeholder itself is always a JSON string (`"$env_SCREEN_VISIBLE"`), the **replacement value** takes the type defined in the config tune file. In the example above, the integer `1` replaces the string placeholder — the resulting config contains a number, not a string.

This means tune files can inject any JSON-compatible type: strings, numbers, booleans, objects, or arrays.

### Where Substitution Happens

Environment substitution is performed in two places depending on the launch mode:

| Launch mode | Performed by | When |
|---|---|---|
| **Frontend** (distant mode or container mode) | `configProcessor.ts` → `replaceEnvValues()` | Before sending the config to the orchestrator |
| **Workbench** (workbench mode) | `get_messages.py` → `replace_env_values()` | When loading config from disk at startup (see [Workbench Mode]({{< relref "/docs/reference/deployment/workbench" >}})) |

Both implementations use the same recursive algorithm, so behavior is identical regardless of launch mode.

### Adding a New Placeholder

1. In `config_template.json`, use a `$env_`-prefixed string as the value for any field:

```json
"my_custom_field": "$env_MY_CUSTOM_VALUE"
```

2. Add the corresponding key (without the `$env_` prefix) to both config tune files:

In `config_local.json`:
```json
{
  "SCREEN_VISIBLE": 1,
  "MY_CUSTOM_VALUE": "local_value"
}
```

In `config_distant.json`:
```json
{
  "SCREEN_VISIBLE": 0,
  "MY_CUSTOM_VALUE": "production_value"
}
```

The placeholder name after `$env_` must match the key name in the config tune file exactly.

---

## Config Tune Files

Config tune files provide the environment-specific values that replace `$env_` placeholders.

### config_local.json — Local Development

Used when running via Docker Compose. Typically enables visible screens for debugging:

```json
{
  "SCREEN_VISIBLE": 1
}
```

### config_distant.json — Kubernetes Production

Used when deploying to a Kubernetes cluster. Typically disables visible screens:

```json
{
  "SCREEN_VISIBLE": 0
}
```

You choose which config tune file to use in the frontend before launching. The default is `config_distant.json`.

---

## Adding Custom Fields

Both `default_agent_message` and `default_job_message` accept arbitrary keys. To add a custom field:

1. Add it to the appropriate section in `config_template.json`:

```json
"default_agent_message": {
  "config_fantomas": { ... },
  "config_proxy": { ... },
  "my_custom_setting": "some_value"
}
```

2. Access it in your script:

```python
async def ctx_script(job_ctx, agent_ctx):
    my_setting = agent_ctx.agent_message["my_custom_setting"]
```

The same applies to `default_job_message` — any key you add is accessible via `job_ctx.job_message`. See [Python Files]({{< relref "/docs/setting-up-project/python-files" >}}) for the full `AgentContext` and `JobContext` APIs.
