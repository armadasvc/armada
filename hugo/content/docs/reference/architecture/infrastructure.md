---
title: 4.1.8. Resource Topology 
linkTitle: 4.1.8. Resource Topology
weight: 8
description: Kubernetes Helm chart, RBAC, secrets, agent Job spec, network topology, and Docker Compose local stack
---

## Kubernetes (Production)

### Helm Chart

The Helm chart (`deploy/`, apiVersion v2) deploys 7 resources as Deployments plus supporting RBAC and Secrets:

| Deployment | Image | Port | Notes |
|---|---|---|---|
| `armada-orchestrator` | `{hub}/armada-orchestrator:latest` | 8080 | `PLATFORM=distant` |
| `armada-backend` | `{hub}/armada-backend:latest` | 8000 | Liveness/readiness probes on `/docs` |
| `armada-frontend` | `{hub}/armada-frontend:latest` | 8080 | Liveness/readiness probes on `/` |
| `armada-proxy-provider` | `{hub}/armada-proxy-provider:latest` | 5001 | |
| `armada-fingerprint-provider` | `{hub}/armada-fingerprint-provider:latest` | 5005 | |
| `armada-redis` | `redis:7-alpine` | 6379 | |
| `armada-rabbitmq` | `rabbitmq:3-management-alpine` | 5672, 15672 | |

`{hub}` is the Docker registry prefix: `armadasvc` for the public Docker Hub images, or a custom value defined in your `.env` file for a private registry.

These are **long-running Deployments**. Agent pods are **not** deployed by the Helm chart — they are created dynamically by the orchestrator (see [Orchestrator Service]({{< relref "/docs/reference/services/orchestrator" >}})) as `batch/v1` Indexed Jobs at runtime. See [Bootstrap Scripts]({{< relref "/docs/reference/architecture/bootstrap-scripts" >}}) for how the cluster is initially provisioned.

### RBAC

The orchestrator needs permissions to create and manage Kubernetes Jobs:

```yaml
Role: armada-role
Rules:
  - apiGroups: ["batch"]
    resources: ["jobs"]
    verbs: ["create", "delete"]
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["create", "get", "list", "watch", "delete"]
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "list"]
```

```yaml
RoleBinding: armada-role-binding
Subjects:
  - kind: ServiceAccount
    name: default
    namespace: default
RoleRef:
  kind: Role
  name: armada-role
```

### Secrets

4 Kubernetes Secrets store sensitive credentials:

| Secret | Contents | Consumed by |
|---|---|---|
| `armada-sql-server-secret` | `SQL_SERVER_NAME`, `SQL_SERVER_DB`, `SQL_SERVER_USER`, `SQL_SERVER_PASSWORD` | Agent pods (via `valueFrom.secretKeyRef`), backend, providers |
| `armada-docker-registry-secret` | Docker config JSON | Agent pods (via `imagePullSecrets`) |
| `armada-docker-username-secret` | `DOCKER_HUB_USERNAME` | Orchestrator |
| `armada-ipqualityscore-secret` | `IPQS_KEY` | Proxy Provider |

### Agent Kubernetes Job Spec

When the orchestrator creates an agent Job, it uses these settings:

```yaml
apiVersion: batch/v1
kind: Job
spec:
  completionMode: Indexed       # Each pod gets a unique index
  completions: N                # One pod per agent
  parallelism: N                # All pods run simultaneously
  ttlSecondsAfterFinished: 1000000  # ~11.5 days before cleanup
  template:
    spec:
      restartPolicy: Never
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: kubernetes.io/hostname
        whenUnsatisfiable: ScheduleAnyway
      containers:
      - resources:
          requests:
            cpu: "{agent_cpu}"      # From config_template
            memory: "{agent_memory}" # From config_template
```

| Setting | Why |
|---|---|
| `completionMode: Indexed` | Assigns each pod a unique `batch.kubernetes.io/job-completion-index`, used as `POD_INDEX` |
| `completions = parallelism` | All agents start at once; Kubernetes handles scheduling |
| `topologySpreadConstraints` | Distributes pods across nodes to prevent overloading a single node |
| `imagePullPolicy: Never` (distribution mode = `minikube`) | Uses locally-built images without a registry |
| `imagePullPolicy: Always` (distribution mode = `kube`) | Pulls from Docker Hub using registry secret |

### Network Topology

```
                    Ingress
                       │
            ┌──────────┴──────────┐
            ▼                     ▼
       Frontend:8080        Backend:8000
                                  │
                            SQL Server
                            (external)

       Orchestrator:8080
       ├── Redis:6379        (ClusterIP)
       ├── RabbitMQ:5672     (ClusterIP)
       └── Kubernetes API    (in-cluster)

       Agent Pods (dynamic)
       ├── Redis:6379        (one-time read)
       ├── RabbitMQ:5672     (continuous)
       ├── Backend:8000      (monitoring)
       ├── ProxyProvider:5001
       ├── FingerprintProvider:5005
       └── SQL Server        (user queries)
```

---

## Local Developement (container mode with Docker Compose)

`local/docker-compose.yml` starts the same 7 services locally:

```
armada-redis             redis:7-alpine                         port 6379
armada-rabbitmq          rabbitmq:3-management-alpine           port 5672, 15672
armada-proxy-provider    build: ../services/proxy-provider      port 5001
armada-fingerprint-provider  build: ../services/fingerprint-provider  port 5005
armada-backend           build: ../services/backend             port 8000
armada-orchestrator      build: ../services/orchestrator        port 8080 (PLATFORM=local)
armada-frontend          build: ../services/frontend            port 3000→8080
```

Key differences from production:

| Aspect | Container mode | Kubernetes |
|---|---|---|
| Orchestrator `PLATFORM` | `local` | `distant` |
| Agent creation | None (workbench runs agent in-process, container run agent via `local/agent.sh` mocker) | Indexed Job with N pods |
| Service discovery | Docker DNS (`armada-redis`, `armada-backend`, etc.) | Kubernetes Services |
| Credentials | `.env` file via `env_file:` | Kubernetes Secrets |
| Image source | Built locally | Pulled from Docker Hub |

All application services share the root `.env` file. The orchestrator gets additional environment variables for inter-service URLs.

### Network Topology

```
       Host machine
       ├── localhost:3000  → Frontend container:8080
       ├── localhost:8000  → Backend container:8000
       ├── localhost:8080  → Orchestrator container:8080
       ├── localhost:5001  → ProxyProvider container:5001
       ├── localhost:5005  → FingerprintProvider container:5005
       ├── localhost:6379  → Redis container:6379
       └── localhost:5672  → RabbitMQ container:5672

       Workbench (bare Python on host)
       └── Connects to all services via localhost
```
