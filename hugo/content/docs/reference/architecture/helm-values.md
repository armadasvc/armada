---
title: 4.1.7. Helm Values
linkTitle: 4.1.7. Helm Values
weight: 7
description: Reference for all Helm values — image references, pull policies, registry secrets, and values that become environment variables
---

Helm values are template parameters resolved at deploy time into the final Kubernetes YAML.
Some end up inside `env:` blocks and become container environment variables (see
[Environment Variables]({{< relref "environment-variables" >}})); others control the manifest
itself (image paths, pull policies, registry auth) and never reach the process environment.

---

## How Values Are Defined

Values come from two sources, merged in order of precedence:

1. **`deploy/values.yaml`** — the default values file checked into the repository. Currently contains:
   ```yaml
   imagePullPolicy: Always
   ```
2. **`--set` flags** passed to `helm install` or `helm upgrade` at the command line. These override
   or add values at deploy time:
   ```bash
   helm install armada ./deploy \
     --set dockerHubName=myregistry \
     --set distrib=kube \
     --set imagePullSecrets[0].name=armada-docker-registry-secret
   ```

Values provided via `--set` take precedence over those in `values.yaml`. Together, these two sources
form the complete set of parameters available to every Go template expression (`{{ .Values.* }}`) in
`deploy/templates/`.

---

## Values That Become Environment Variables

Some Helm values are placed directly inside `env:` blocks in deployment templates. After Helm renders
the template, Kubernetes injects them as environment variables into the container. The application code
reads them with `os.getenv()` like any other environment variable.

```yaml
# From deploy/templates/orchestrator/orchestrator-deployment.yaml
env:
  - name: DISTRIB
    value: {{ .Values.distrib }}        # Rendered to "kube" or "minikube"
  - name: PLATFORM
    value: "distant"                     # Hardcoded in the template (not a Helm value)
```

| Value path | Becomes env var | In which pod | Example value |
|---|---|---|---|
| `{{ .Values.distrib }}` | `DISTRIB` | Orchestrator | `kube` / `minikube` |

Note that most `env:` entries in the Orchestrator template are **hardcoded strings** (like `PLATFORM`,
`RABBITMQ_URL`, `REDIS_HOST`), not Helm value references. They are written directly in the template
and do not vary between deployments.

---

## Values That Control the Manifest (Not Environment Variables)

These values configure the Kubernetes resource spec itself — they never appear in an `env:` block and
are not visible to the application process.

### Image references

Every deployment template builds its container image path from `dockerHubName`:

```yaml
image: {{ .Values.dockerHubName }}/armada-orchestrator:latest
image: {{ .Values.dockerHubName }}/armada-backend:latest
image: {{ .Values.dockerHubName }}/armada-proxy-provider:latest
image: {{ .Values.dockerHubName }}/armada-fingerprint-provider:latest
```

This determines **which Docker registry and username** Kubernetes pulls images from.

### Image pull policy

```yaml
imagePullPolicy: {{ .Values.imagePullPolicy }}
```

Controls when Kubernetes re-pulls the image. Set to `Always` in `values.yaml` so that every pod restart
fetches the latest `latest` tag from the registry.

### Image pull secrets

```yaml
{{- with .Values.imagePullSecrets }}
      imagePullSecrets:
{{- toYaml . | nindent 8 }}
{{- end }}
```

Attaches Docker registry credentials to the pod so that Kubernetes can authenticate when pulling images
from a private Docker Hub repository. The secret itself (`armada-docker-registry-secret`) is created by
`bootstrap_secrets.py` — the Helm value only **references** it by name.

---

## All Values at a Glance

| Value path | Default | Example | Becomes env var? | Used in |
|---|---|---|---|---|
| `{{ .Values.imagePullPolicy }}` | `Always` | `Always` | No — controls pod spec | All deployment templates |
| `{{ .Values.dockerHubName }}` | *(none — must be set)* | `myregistry` | No — controls image path | All deployment templates |
| `{{ .Values.distrib }}` | *(none — must be set)* | `kube` / `minikube` | Yes → `DISTRIB` | Orchestrator |
| `{{ .Values.imagePullSecrets }}` | *(none — must be set)* | `[{name: armada-docker-registry-secret}]` | No — controls registry auth | All deployment templates |
