---
title: 4.2.6. Fingerprint Provider
linkTitle: 4.2.6. Fingerprint Provider
weight: 6
description: FastAPI microservice that retrieves and forges browser fingerprints from SQL Server, with Arkose BDA decryption and user agent transformation
---

# Fingerprint Provider

Internal microservice that serves browser fingerprints from a centralized database. It retrieves stored fingerprint data and, for supported antibot vendors, transforms it to match a desired user agent before returning it. For agent-side usage (configuration and script integration), see the [Fingerprint Provider guide]({{< relref "/docs/guides/fingerprint-provider" >}}).

## How It Works

1. Receives a fingerprint request with filters (antibot vendor, website, collection date)
2. Queries the SQL Server database for a random matching fingerprint
3. If the vendor is **Arkose**, decrypts the BDA payload, updates the user agent and timestamp, re-encrypts it, and returns the forged fingerprint. The Arkose vendor is dealt with the (now deprecated) Github repo [Unfuncaptcha-bda](https://github.com/unfuncaptcha/bda) - many thanks ! 
4. Otherwise, returns the raw fingerprint data

## API

### `GET /get-fingerprint`

**Request body (JSON):**

| Field | Type | Description |
|---|---|---|
| `antibot_vendor` | string | Antibot vendor name (e.g. `"arkose"`) |
| `website` | string | Target website identifier |
| `collection_date_day` | int \| null | Day component of the minimum collection date |
| `collection_date_month` | int \| null | Month component of the minimum collection date |
| `collection_date_year` | int \| null | Year component of the minimum collection date |

The three date fields together form a single date (`YYYY-MM-DD`). Only fingerprints collected **on or after** this date will be returned — older fingerprints are excluded. The date is split into separate fields to avoid format ambiguity. Setting all three to `null` removes the date filter, returning fingerprints from any date.
| `additional_data` | object | Vendor-specific data (e.g. `{"desired_ua": "..."}` for Arkose) |

**Response:** The transformed fingerprint payload (format depends on the vendor).

## Environment Variables

| Variable | Description |
|---|---|
| `SQL_SERVER_NAME` | SQL Server hostname |
| `SQL_SERVER_USER` | Database user |
| `SQL_SERVER_PASSWORD` | Database password |
| `SQL_SERVER_DB` | Database name |

## Project Structure

```
fingerprint-provider/
├── main.py            # FastAPI application and endpoint
├── config.py          # Environment variable loading and DB config
├── db.py              # Database connection, query building, and fetching
├── Dockerfile
├── requirements.txt
└── src/
    ├── crypto.py                  # AES-CBC encryption/decryption (BDA)
    ├── fingerprint.py             # ArkoseBrowserFingerprint class
    └── forge_arkose_fingerprint.py # Arkose fingerprint transformation logic
```

## Running Locally

```bash
pip install -r requirements.txt
python main.py
```

The service starts on port **5005**.

## Docker

```bash
docker build -t fingerprint-provider .
docker run -p 5005:5005 \
  -e SQL_SERVER_NAME=... \
  -e SQL_SERVER_USER=... \
  -e SQL_SERVER_PASSWORD=... \
  -e SQL_SERVER_DB=... \
  fingerprint-provider
```
