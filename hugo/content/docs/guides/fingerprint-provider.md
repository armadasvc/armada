---
title: 3.3. Fingerprint Provider
linkTitle: 3.3. Fingerprint Provider
weight: 3
description: Fetch and forge browser fingerprints for antibot bypass using the FingerprintManager
---

## Overview

The Fingerprint Provider lets your agent fetch realistic browser fingerprints at runtime. This is useful when automating websites protected by antibot solutions (e.g. Arkose) that analyze browser fingerprints to detect bots.

The agent calls the Fingerprint Provider service, which returns a fingerprint matching your filters. For the service API and internal architecture, see [Fingerprint Provider Service]({{< relref "/docs/reference/services/fingerprint-provider" >}}). 

The only vendors supported at that time is fingerprint compatible with an ancient version of Arkose antifingerprinting script (from jan. 2025), the fingerprint is automatically transformed to match the agent's current user agent.

```
Agent (ctx_script.py)
  │
  │  get_fingerprint(additional_data)
  ▼
FingerprintManager ──HTTP GET──► Fingerprint Provider (port 5005)
                                       │
                                       ▼
                                 SQL Server (armada_fingerprints)
```

## Configuration

Add a `config_fingerprint` block to `default_agent_message` in your `config_template.json` (see [JSON Configuration]({{< relref "/docs/setting-up-project/json-config" >}})):

```json
"default_agent_message": {
  "config_fingerprint": {
    "antibot_vendor": "arkose",
    "website": "X",
    "collection_date_day": "01",
    "collection_date_month": "12",
    "collection_date_year": "2025"
  }
}
```

### Fields

| Field | Type | Description |
|---|---|---|
| `antibot_vendor` | string | Antibot vendor name (e.g. `"arkose"`) |
| `website` | string | Target website identifier used to filter fingerprints |
| `collection_date_day` | string \| null | Day component of the minimum collection date (e.g. `"01"`) |
| `collection_date_month` | string \| null | Month component of the minimum collection date (e.g. `"12"`) |
| `collection_date_year` | string \| null | Year component of the minimum collection date (e.g. `"2025"`) |

The three date fields together form a single date (`YYYY-MM-DD`). Only fingerprints collected **on or after** this date will be returned — older fingerprints are excluded. The date is split into separate fields to avoid format ambiguity. Setting all three to `null` removes the date filter, returning fingerprints from any date.

## Initialization

The `FingerprintManager` is initialized in `ctx_agent_context.py` as part of `instantiate_default()`:

```python
from src.fingerprint_manager import FingerprintManager

class AgentContext:
    def __init__(self, agent_message):
        self.agent_message = agent_message

    def instantiate_default(self):
        self.fingerprint_manager = FingerprintManager(
            self.agent_message["config_fingerprint"]
        )
```

The manager is agent-scoped: it is created once and reused across all jobs (see [The Two-Tier Lifecycle]({{< relref "/docs/setting-up-project/python-files#the-two-tier-lifecycle" >}})).

## Usage in ctx_script.py

### Basic usage

Call `get_fingerprint()` to retrieve a fingerprint:

```python
async def ctx_script(job_ctx, agent_ctx):
    fingerprint = agent_ctx.fingerprint_manager.get_fingerprint()
```

### Passing additional data

For Arkose fingerprints, you typically need to pass the desired user agent so the BDA payload is re-encrypted to match:

```python
async def ctx_script(job_ctx, agent_ctx):
    fingerprint = agent_ctx.fingerprint_manager.get_fingerprint(
        additional_data={"desired_ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)..."}
    )
```

The `additional_data` dict is vendor-specific. For Arkose, the key `desired_ua` tells the provider which user agent to forge the fingerprint for.

### Using the fingerprint

The returned value is a string. For Arkose, it is a JSON-encoded payload you can inject into your antibot-solving logic:

```python
async def ctx_script(job_ctx, agent_ctx):
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    fingerprint = agent_ctx.fingerprint_manager.get_fingerprint(
        additional_data={"desired_ua": ua}
    )

    # Use the fingerprint in your Arkose solving flow
    # fingerprint is a JSON string ready to be sent as BDA
```

## Disabling the Fingerprint Provider

If your project does not need fingerprints, remove or comment out the `FingerprintManager` line in `ctx_agent_context.py`:

```python
def instantiate_default(self):
    self.proxy_manager = ProxyManager(self.agent_message["config_proxy"]).launch_proxy()
    # self.fingerprint_manager = FingerprintManager(self.agent_message["config_fingerprint"])
    self.database = DatabaseConnector()
```