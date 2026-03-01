---
title: 4.1.9. Bootstrap Scripts
linkTitle: 4.1.9. Bootstrap Scripts
weight: 9
description: Cluster provisioning, Kubernetes secrets injection, and database initialization scripts
---

The `bootstrap/` directory contains three Python scripts that prepare a fresh environment for Armada. They are meant to be executed in order: secrets first, then cluster resources, then database.

## Prerequisites

Install the Python dependencies before running any script:

```bash
pip install -r bootstrap/requirements.txt
```

| Package | Version | Used by |
|---------|---------|---------|
| `kubernetes` | 35.0.0 | `bootstrap_secrets.py` |
| `pymssql` | 2.3.13 | `bootstrap_database.py` |

All scripts read configuration from the `.env` file at the project root.

## 1. bootstrap_secrets.py

Creates or updates Kubernetes secrets in a target namespace from values defined in `.env`.

### Secrets managed

| Secret name | Type | Keys consumed |
|-------------|------|---------------|
| `armada-docker-username-secret` | `Opaque` | `DOCKER_HUB_USERNAME` |
| `armada-docker-registry-secret` | `kubernetes.io/dockerconfigjson` | `DOCKER_HUB_USERNAME`, `DOCKER_HUB_PASSWORD`, `DOCKER_HUB_MAIL` |
| `armada-ipqs-secret` | `Opaque` | `IPQS_KEY` |
| `armada-sql-server-secret` | `Opaque` | `SQL_SERVER_USER`, `SQL_SERVER_PASSWORD`, `SQL_SERVER_DB`, `SQL_SERVER_NAME` |

If any required key is missing from `.env`, the corresponding secret is **skipped** (not treated as an error). The script prints a summary of how many secrets were applied versus skipped.

### Idempotent behaviour

The script checks whether each secret already exists in the namespace. Existing secrets are **replaced**; missing ones are **created**.

### Usage

Normally : 

```bash
python bootstrap/bootstrap_secrets.py
```

or if needed

```bash
python bootstrap/bootstrap_secrets.py --namespace default --env-file .env
```

| Flag | Default | Description |
|------|---------|-------------|
| `--namespace` | `default` | Kubernetes namespace to write secrets into |
| `--env-file` | — | Path to the `.env` file |

## 2. bootstrap_cluster_resources.py

Builds Docker images (when applicable), then installs the Armada Helm chart into the active Kubernetes cluster. The secrets created in step 1 must already exist, since the Helm chart Deployments reference them via `secretKeyRef` and `imagePullSecrets`.

### Installation modes

The script presents an interactive menu with three options:

| Mode | When to use | What it does |
|------|-------------|--------------|
| **Public** | Production / CI with official images | Runs `helm install` pointing to the pre-built `armadasvc` Docker Hub images. No local build step. |
| **Private** | Production with a custom registry | Builds all six service images, pushes them to your Docker Hub account, then runs `helm install` with `imagePullSecrets`. |
| **Minikube** | Local development | Builds images inside Minikube's Docker daemon (`eval $(minikube docker-env)`), sets `imagePullPolicy=Never`, then runs `helm install`. |

### Service images

Private and Minikube modes build one image per service:

| Source directory | Image name |
|------------------|------------|
| `services/agent` | `armada-agent` |
| `services/backend` | `armada-backend` |
| `services/fingerprint-provider` | `armada-fingerprint-provider` |
| `services/frontend` | `armada-frontend` |
| `services/orchestrator` | `armada-orchestrator` |
| `services/proxy-provider` | `armada-proxy-provider` |

### Required variables

It fetches from .env : 
- `DOCKER_HUB_USERNAME` — required for Private and Minikube modes.
- `DOCKER_HUB_PASSWORD` — required for Private mode (registry authentication).

### Example

```bash
python bootstrap/bootstrap_cluster_resources.py
# Follow the interactive prompt to choose a mode.
```

After completion the script prints a summary with useful verification commands (`kubectl get pods`, `helm list`, etc.).

## 3. bootstrap_database.py

Connects to SQL Server and creates the five tables Armada requires. Every `CREATE TABLE` statement is guarded with `IF NOT EXISTS`, making the script safe to run multiple times.

### Tables

For the complete database schema (tables, columns, types, relationships), see the [Database Reference]({{< relref "/docs/reference/deployment/database" >}})

### Usage

```bash
python bootstrap/bootstrap_database.py
```

## Complete recommended bootstrap sequence

```text
1. bootstrap_secrets.py             Inject secrets into the cluster
              │
              ▼
2. bootstrap_cluster_resources.py   Build images & helm install
              │
              ▼
3. bootstrap_database.py            Create SQL Server tables
```

Run the scripts in this order to go from an empty cluster to a fully provisioned Armada environment.
