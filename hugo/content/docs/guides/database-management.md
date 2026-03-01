---
title: 3.6. Database Management
linkTitle: 3.6. Database Management
weight: 6
description: Bulk data import from CSV files
---

## Overview

This guide covers bulk data import — a CLI tool to populate Armada's SQL Server tables from CSV files.

For the complete database schema (tables, columns, types, relationships), see the [Database Reference]({{< relref "/docs/reference/deployment/database" >}}).

For programmatic access from your automation scripts (SELECT, INSERT, UPDATE), see the [Database Connector]({{< relref "database-connector" >}}) guide.

---

## Bulk Data Import

The bulk import tool lets you populate tables from CSV files. It is located in `tools/bulk_data_to_sql_server/` and provides one script per table.

```
armada_proxies_template.csv
  │
  │  python bulk_armada_proxies.py armada_proxies_template.csv
  ▼
bulk_armada_proxies.py ──pymssql──► SQL Server (armada_proxies)
```

### Prerequisites

The tool reads its connection settings from the project root `.env` file — the same variables used by the Database Connector:

| Variable | Description |
|---|---|
| `SQL_SERVER_NAME` | SQL Server hostname |
| `SQL_SERVER_USER` | Database username |
| `SQL_SERVER_PASSWORD` | Database password |
| `SQL_SERVER_DB` | Database name |

Dependencies: `pymssql`, `python-dotenv`.

### Usage

Each table has a dedicated script and a CSV template:

```bash
cd tools/bulk_data_to_sql_server

python bulk_armada_proxies.py        armada_proxies_template.csv
python bulk_armada_jobs.py           armada_jobs_template.csv
python bulk_armada_runs.py           armada_runs_template.csv
python bulk_armada_events.py         armada_events_template.csv
python bulk_armada_fingerprints.py   armada_fingerprints_template.csv
python bulk_armada_output.py         armada_output_template.csv
```

Copy a template, fill it with your data, and pass its path to the corresponding script. The script reads the CSV, inserts every row, and prints the number of inserted rows.

### CSV examples

**armada_proxies:**

```csv
proxy_url,proxy_provider_name,proxy_type,proxy_rotation_strategy,proxy_location
http://user:pass@geo.iproyal.com:12321,iproyal,residential,sticky,Europe/Paris
http://user:pass@geo.iproyal.com:12322,iproyal,residential,rotating,Europe
http://user:pass@geo.iproyal.com:12323,iproyal,datacenter,sticky,
```

**armada_jobs:**

```csv
job_uuid,run_uuid,job_datetime,job_associated_agent,job_status
550e8400-e29b-41d4-a716-446655440000,660e8400-e29b-41d4-a716-446655440000,2026-02-24 10:30:00,agent-1,Success
```

**armada_runs:**

```csv
run_uuid,run_datetime
660e8400-e29b-41d4-a716-446655440000,2026-02-24 10:30:00
```

**armada_events:**

```csv
event_uuid,event_content,job_uuid,event_datetime,event_status
770e8400-e29b-41d4-a716-446655440000,page_loaded,550e8400-e29b-41d4-a716-446655440000,2026-02-24 10:30:00,Success
```

**armada_fingerprints:**

```csv
antibot_vendor,website,data,collecting_date
arkose,https://example.com,"{""ts"":""1708770600"",""ua"":""Mozilla/5.0 ..."",""bda"":""encrypted_payload""}",2026-02-24
```

**armada_output:**

```csv
run_uuid,data,timestamp
660e8400-e29b-41d4-a716-446655440000,{"key": "value"},2026-02-24 10:30:00
```

> **Note:** When a CSV value contains commas or double-quotes, wrap it in double-quotes and escape inner quotes by doubling them (`""`), as shown above for the `data` column.

Proxies imported into `armada_proxies` are served to agents by the [Proxy Provider]({{< relref "/docs/guides/proxy-provider" >}}). Fingerprints imported into `armada_fingerprints` are retrieved and forged by the [Fingerprint Provider]({{< relref "/docs/guides/fingerprint-provider" >}}).
