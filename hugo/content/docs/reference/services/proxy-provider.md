---
title: 4.2.5. Proxy Provider
linkTitle: 4.2.5. Proxy Provider
weight: 5
description: FastAPI microservice that serves filtered proxies from SQL Server with optional IP, quality, and geolocation verification
---

# Proxy Provider

Internal microservice that serves verified proxies from a SQL Server database. It exposes a single REST endpoint that returns a random proxy matching the requested criteria, with optional IP, quality, and geolocation verification. For agent-side usage (configuration, addon system, proxy switching), see the [Proxy Provider guide]({{< relref "/docs/guides/proxy-provider" >}}).

## Stack

- **Python 3.12** / **FastAPI** / **Uvicorn**
- **pymssql** (SQL Server driver)
- **IPQualityScore API** (optional, for fraud scoring)
- **ip-api.com** (geolocation check)
- **ipify.org** (IP resolution)

## API

### `GET /fetch_proxy`

Returns a random proxy URL from the `armada_proxies` table.

#### Query Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `proxy_provider_name` | string | `null` | Filter by provider name |
| `proxy_rotation_strategy` | string | `null` | Filter by rotation strategy |
| `proxy_type` | string | `null` | Filter by proxy type |
| `proxy_location` | string | `null` | Filter by location |
| `verify_ip` | bool | `null` | Resolve and return the proxy's outbound IP |
| `verify_quality` | bool | `null` | Run an IPQualityScore fraud check |
| `verify_location` | bool | `null` | Verify the proxy IP matches `proxy_location` |
| `quality_threshold` | int | `70` | Minimum quality score (0-100) to pass |
| `max_queries_number` | int | `2` | Max retry attempts if checks fail |

#### Response Example

```json
{
  "proxy_url": "http://user:pass@host:port",
  "attempt": 1,
  "verify_ip": { "ip": "203.0.113.42" },
  "verify_quality": {
    "fraud_score_inverted": 85,
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

## Configuration

Environment variables:

| Variable | Required | Description |
|---|---|---|
| `SQL_SERVER_NAME` | Yes | SQL Server hostname |
| `SQL_SERVER_USER` | Yes | SQL Server username |
| `SQL_SERVER_PASSWORD` | Yes | SQL Server password |
| `SQL_SERVER_DB` | Yes | Database name |
| `IPQS_KEY` | No | IPQualityScore API key (quality checks disabled if absent) |

## Run Locally

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 5001
```

## Docker

```bash
docker build -t armada-proxy-provider .
docker run -p 5001:5001 --env-file .env armada-proxy-provider
```

The container runs as a non-root user (`appuser`) on port **5001**.
