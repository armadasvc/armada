---
title: 2.3. CSV Configuration
linkTitle: 2.3. CSV Configuration
weight: 3
description: Per-agent and per-job overrides using CSV files, data formats, and deep merge behavior
---

## What Are CSV Overrides?

CSV files let you customize settings **per-agent** or **per-job** without modifying the JSON config template. They work as an override layer on top of the defaults defined in `config_template.json` (see [JSON Configuration]({{< relref "/docs/setting-up-project/json-config" >}})).

The central principle is:

> **The JSON decides _how many_ agents and jobs. The CSV decides _how each one differs_.**

---

## data_agent.csv — Per-Agent Overrides

Each row overrides the `default_agent_message` for a specific agent. The **first column must be `targetted_agent`** — it contains the agent index that the row targets. The orchestrator uses this column to match each row to the correct agent during the merge.

**Example — Different proxy provider per agent:**

```csv
targetted_agent,config_proxy
0,{"proxy_provider_name": "iproyal", "proxy_location": "Europe"}
1,{"proxy_provider_name": "oxylabs", "proxy_location": "US"}
```

- Agent 0 gets `proxy_provider_name=iproyal`, `proxy_location=Europe`
- Agent 1 gets `proxy_provider_name=oxylabs`, `proxy_location=US`
- All other keys inside `config_proxy` (e.g. `upstream_proxy_enabled`, `verify_ip`...) are preserved from the default

**Leave the file empty** (no rows, just headers or completely blank) if all agents should use the same default configuration.

---

## data_job.csv — Per-Job Overrides

Same mechanism as `data_agent.csv`, but for job messages. The **first column must be `targetted_job`** — it contains the job index that the row targets.

**Example — Different task per job:**

```csv
targetted_job,job_content,target_url
0,task_a,https://example.com/a
1,task_b,https://example.com/b
2,task_c,https://example.com/c
```

**Leave the file empty** if all jobs share the same default configuration.

---

## Data Format in CSV Cells

Each column header in the CSV corresponds to a **direct key** in the default message. The orchestrator parses each cell value according to the following rules:

### Plain text → string

Any cell value that does not start with `{` or `[` is kept as a **string**, regardless of its content.

| Cell value | Parsed as | Type |
|---|---|---|
| `hello` | `"hello"` | string |
| `123` | `"123"` | string |
| `true` | `"true"` | string |

This means if you need to override a top-level key with a simple value, just write it directly:

```csv
targetted_job,job_content
0,login_task
1,scrape_task
```

### JSON object → dictionary (for nested overrides)

To override fields inside a **nested object**, write a valid JSON object in the cell. The column header must be the parent key name.

```csv
targetted_agent,config_proxy
0,{"proxy_provider_name": "brightdata", "proxy_location": "US"}
```

The orchestrator deep-merges this into the existing `config_proxy` from the default — only the keys you specify are replaced, everything else is preserved.

You can override multiple nested sections by using multiple columns:

```csv
targetted_agent,config_proxy,config_fingerprint
0,{"proxy_provider_name": "brightdata"},{"website": "Y"}
```

### JSON array → list

Cell values starting with `[` are parsed as JSON arrays:

```csv
targetted_agent,config_fantomas
0,{"config_browser": {"fantomas_browser_options": ["--proxy-server=http://127.0.0.1:8081", "--no-sandbox"]}}
```

{{% alert title="Note" %}}
Lists are **replaced entirely**, not merged element by element. If you override `fantomas_browser_options`, you must provide the complete list of flags you want.
{{% /alert %}}

### Invalid JSON → fallback to string

If a cell starts with `{` or `[` but is not valid JSON, it falls back to a plain string without error.

---

## What to Expect

### The JSON count always prevails

The number of agents and jobs is always determined by `number_of_agents` and `number_of_jobs` in the [`run_message` section]({{< relref "/docs/setting-up-project/json-config#run_message--infrastructure-settings" >}}) of the config template — not by the number of CSV rows.

| Scenario | Result |
|---|---|
| `number_of_jobs=5`, CSV has 3 rows | 5 jobs produced. Jobs 0-2 get CSV overrides. Jobs 3-4 get the pure default. |
| `number_of_jobs=2`, CSV has 5 rows | 2 jobs produced. Only CSV rows 0-1 are used. Rows 2-4 are silently ignored. |
| `number_of_jobs=3`, CSV is empty | 3 jobs produced, all identical copies of the default. |
| `number_of_agents=1`, CSV has 0 rows | 1 agent config produced, identical to `default_agent_message`. |

The same logic applies symmetrically to agents.

### Overrides are merged, not replaced

CSV overrides are **deep-merged** onto the default messages. This means:

- Only the specific keys present in the CSV are replaced.
- Everything else in the default is preserved unchanged.

**Example:** if the default agent message has 10 fields and your CSV row only overrides 1 field, the other 9 fields remain untouched.

### Empty CSV = identical copies

If a CSV file is empty (no data rows), every agent or job receives an identical copy of the default message from the JSON config.

For the technical deep merge algorithm and internals, see [Configuration Pipeline]({{< relref "/docs/reference/architecture/configuration-pipeline" >}}).