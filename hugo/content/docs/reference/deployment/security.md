---
title: 4.3.3. Security Considerations
linkTitle: 4.3.3. Security
weight: 3
description: Deployment boundary, rationale for no TLS/auth, exec() security model, RBAC scope, and hardening recommendations
---

## Deployment Boundary

Armada is designed to run inside a **private, trusted network** — either a local machine (Docker Compose) or an internal Kubernetes cluster with no ingress exposed to the public internet.

**Do not expose the cluster to the outside world.** The platform has no TLS termination, no user authentication, and executes arbitrary code by design. Exposing any Armada service to the internet would allow unauthenticated users to launch workloads, read configuration data, and execute code on your infrastructure.

---

## Design Choices and Rationale

### No TLS

All traffic stays within the cluster network (Kubernetes pod-to-pod via ClusterIP services, or Docker Compose bridge network). In both cases, traffic never leaves the host or the cluster's virtual network.

Adding TLS for internal service-to-service communication would require:
- A certificate authority (or integration with cert-manager)
- Certificate provisioning and rotation for 7 services
- TLS configuration in every FastAPI, Redis, and RabbitMQ client

For an internal platform where all services run within the same trust boundary, this adds operational complexity with limited security benefit. Kubernetes network policies or a service mesh (Istio, Linkerd) would be the appropriate layer to add encryption in transit if the cluster network itself cannot be trusted.

### No Authentication

Armada is an **operator tool**, not a multi-tenant SaaS product. It is operated by the same team that deploys and maintains the cluster. Adding an authentication layer (API keys, OAuth, RBAC) would add friction to an internal workflow without a clear threat to mitigate — the trust boundary is the network perimeter, not individual API calls.

If multi-user or multi-team access is ever needed, authentication should be introduced at the **ingress layer** (e.g., an API gateway or reverse proxy with SSO) rather than individually in each microservice. This keeps the internal architecture simple while enforcing access control at a single point.

### exec() for User Code

Agents execute user-provided Python code via `exec()` (see [Code Bundling and Execution]({{< relref "/docs/reference/architecture/code-bundling-execution" >}}) for why this approach was chosen over alternatives). This is the core mechanism that makes Armada flexible — users define their own automation logic, and the platform distributes and runs it.

`exec()` is inherently dangerous in untrusted contexts: it allows arbitrary code execution with the full privileges of the process. In Armada, this is an **intentional design decision**, not a vulnerability, because:

1. **The code author is the operator.** The person writing the script is the same person (or team) that owns the cluster. There is no separation between "platform user" and "platform administrator".
2. **Agents run in isolated ephemeral pods.** Each agent runs in its own Kubernetes pod as a non-root user (`celeryuser`, UID 1000). A compromised agent cannot directly affect other agents or platform services beyond its RBAC-scoped ServiceAccount. Besides pods are not long-lived services with persistent state. (TTL)
3. **Sandboxing exec() would defeat the purpose.** Restricting what code can do (no filesystem access, no network, no subprocess) would make the platform unusable for its intended workloads (OS-level interaction via xdotool).

The tradeoff is clear: Armada trusts the code it runs, because the code comes from its operators. If Armada were ever opened to untrusted users, `exec()` would need to be replaced with a sandboxed execution environment.

---

## Kubernetes RBAC Scope

The orchestrator's ServiceAccount is scoped to the minimum permissions required:

```yaml
Rules:
  - batch/jobs: create, delete
  - pods: create, get, list, watch, delete
  - configmaps: get, list
```

It cannot modify Deployments, Services, Secrets, or cluster-level resources. This limits the blast radius if the orchestrator is compromised — an attacker could create or delete Jobs and Pods, but cannot escalate to control the platform's own infrastructure.

---

## Recommendations to go further : 

If you need to move beyond a private, single-team deployment:

| Goal | Approach |
|---|---|
| Expose the dashboard externally | Place an authenticating reverse proxy (e.g., OAuth2 Proxy, Cloudflare Access) in front of the frontend and backend |
| Encrypt internal traffic | Deploy a service mesh (Istio/Linkerd) for mutual TLS, or use cert-manager with per-service certificates |
| Multi-tenant isolation | Add API-key or token-based auth to the orchestrator; introduce namespace-per-tenant for agent pods |
| Harden agent execution | Run agent pods with a sandboxed runtime (for eg gVisor) |
| Restrict network egress | Apply Kubernetes NetworkPolicies to limit which external hosts agents can reach |
| Audit trail | Log all orchestrator API calls and Kubernetes events to a centralized logging system |
