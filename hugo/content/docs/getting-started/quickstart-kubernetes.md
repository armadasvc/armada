---
title: 1.2. Quick-Start / Installation
linkTitle: 1.2. Quick-Start / Installation
weight: 2
description: Step-by-step guide to deploy Armada on a Kubernetes cluster
---

## Prerequisites

- A running Kubernetes cluster
- `kubectl` configured and connected to your cluster
- Helm 3+ installed
- Python 3.12+ installed
- Access to a SQL Server instance (e.g. Azure SQL)

## 1. Clone and Configure

```bash
git clone https://github.com/armadasvc/armada
cd armada
```

Create a `.env` file at the project root:

```dotenv
SQL_SERVER_USER=your_user
SQL_SERVER_PASSWORD=your_password
SQL_SERVER_DB=your_database
SQL_SERVER_NAME=your_server.database.windows.net

DOCKER_HUB_USERNAME=armadasvc
DOCKER_HUB_MAIL=your_email #Optional - only if you self-host your image on DockerHub Registry
DOCKER_HUB_PASSWORD=your_password #Optional - only if you self-host your image on DockerHub Registry
IPQS_KEY=your_ip_qualityscore.com #Optional if you do not verify IP Quality

```

## 2. Bootstrap the Database

```bash
cd bootstrap
pip install -r requirements.txt
python bootstrap_database.py
cd ..
```

This creates the required tables (`armada_runs`, `armada_jobs`, `armada_events`, `armada_proxies`, `armada_fingerprints`, `armada_output`) if they don't already exist.

## 3. Create Your Project

Use the interactive project creation script to scaffold a new Armada project from the built-in template:

```bash
bash create-project.sh
```

and choose 1. New Project

A dialog will prompt you for:

| Field | Description |
|---|---|
| **Project name** | The name of your new project |
| **Destination folder** | Where the project folder will be created |

The script copies the project template (`services/project`) to the selected location and configures the workbench `agent_path` automatically.

Once created, the project folder opens automatically. You can start editing `ctx_script.py` to write your automation logic.

> **Tip** — See [Setting Up a Project](../setting-up-project/) for the full project structure reference.

## 4. Create Kubernetes Secrets

The secrets store your SQL Server credentials and Docker Hub configuration so pods can access them at runtime.

```bash
cd bootstrap
python bootstrap_secrets.py --namespace default
cd ..
```

Verify the secrets were created:

```bash
kubectl get secrets | grep armada
```

You should see:

```
armada-docker-registry-secret
armada-docker-username-secret
armada-sql-server-secret
```

## 5. Deploy to the Cluster

Run the interactive deployment script:

```bash
cd bootstrap
python bootstrap_cluster_resources.py
```

The script presents three options:

| Option | Description |
|---|---|
| **1. Public images** | Fastest — uses pre-built images from the `armadasvc` Docker Hub account. No build step required. |
| **2. Private registry** | Builds all 6 Docker images from `services/`, pushes them to your Docker Hub account (uses `DOCKER_HUB_USERNAME` from `.env`), and deploys with `imagePullSecrets`. |
| **3. Minikube (dev mode)** | Builds images directly inside the Minikube Docker daemon — no registry push needed. Requires `minikube start` beforehand. |

For a first deployment, **select option 1** to get up and running without building anything.

The script handles the full Helm install automatically. Once complete, you will see a summary with verification commands.

## 6. Verify the Deployment

Check that all 7 deployments are running:

```bash
kubectl get deploy | grep armada
```

Expected output:

```
armada-backend                1/1     1            1           2m
armada-fingerprint-provider   1/1     1            1           2m
armada-frontend               1/1     1            1           2m
armada-orchestrator           1/1     1            1           2m
armada-proxy-provider         1/1     1            1           2m
armada-rabbitmq               1/1     1            1           2m
armada-redis                  1/1     1            1           2m
```

Check that all pods are healthy:

```bash
kubectl get pods | grep armada
```

## 7. Access the Web UI

Forward the frontend service to your local machine:

```bash
kubectl port-forward svc/armada-frontend 8080:8080
```

Open **http://localhost:8080** in your browser.

You will see two tabs:

- **Launch** — Configure and submit automation runs
- **Monitor** — Track runs, jobs, and events in real time

---

## 8. Submit via the Web UI

1. Open the **Launch** tab
2. Drag-and-drop your project folder into the upload area
3. Click **Launch**
4. Switch to the **Monitor** tab to watch your run in real time


## 9. Monitor Your Run

The **Monitor** panel provides three levels of drill-down:

```
Runs → Jobs → Events
```

- **Runs** — Paginated list of all runs. Click a run to see its jobs.
- **Jobs** — All jobs for the selected run with status indicators. Click a job to see its events.
- **Events** — Detailed event log for the selected job.

All updates are delivered in real time via WebSocket. No refresh needed.


## Uninstalling

```bash
helm uninstall armada
```

This removes all Armada deployments, services, and RBAC resources. Agent Job pods from past runs are not removed — clean them up manually if needed:

```bash
kubectl delete jobs -l managed-by=armada
```