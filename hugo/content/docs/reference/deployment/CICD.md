---
title: 4.3.5. CI/CD
linkTitle: 4.3.5. CI/CD
weight: 5
description: GitHub Actions workflows for unit tests and Docker image publishing, Changesets versioning, and pipeline flow
---

## Overview

Armada's CI/CD is built on two GitHub Actions workflows and a Changesets-based versioning system. The pipeline automatically detects which services changed, builds their Docker images, pushes them to Docker Hub, and tags the commit. Unit tests run on every push and pull request.

This page describes **how the pipeline works internally**. For instructions on how to release a new version as a developer, see the [CI/CD Guide]({{< relref "/docs/guides/ci-cd" >}}).

---

## Repository Tooling

### npm Workspaces

The root `package.json` declares the monorepo structure:

```json
{
  "workspaces": ["services/*", "lib/*"],
  "devDependencies": {
    "@changesets/cli": "^2.27.1"
  }
}
```

All packages under `services/` and `lib/` are managed as npm workspaces. Each service has its own `package.json` with a `name` and `version` field — these are the source of truth for image naming and tagging.

### Changesets

When a developer runs `npx changeset version`, Changesets reads pending `.md` files in `.changeset/`, bumps the `version` field in each affected `package.json`, updates the service's `CHANGELOG.md`, and deletes the consumed changeset files.

---

## Workflow: Docker Publish

**File:** `.github/workflows/docker-publish.yml`

### Trigger

| Event | Condition |
|---|---|
| `push` to `master` | Only when files matching `services/**/package.json` are modified |
| `workflow_dispatch` | Manual trigger — optionally specify a single service to rebuild |

The `run-name` is set dynamically: for push events it uses the commit message, for manual runs it uses the operator-provided `run_name` input.

### Step-by-Step Execution

#### 1. Detect Changed Services

**Auto mode (push):** the workflow runs `git diff --name-only HEAD~1 HEAD` and filters for paths matching `services/*/package.json`. For each changed file, it reads the `name` and `version` fields using Node.js:

```bash
NAME=$(node -p "require('./$file').name")
VERSION=$(node -p "require('./$file').version")
IMAGE_NAME=$(echo "$NAME" | sed 's/^@//; s/\//-/g')
```

The image name is derived from the npm package name by stripping the `@` prefix and replacing `/` with `-`. For example, `armada-agent` stays `armada-agent`.

**Manual mode (workflow_dispatch):** the operator provides a service path (e.g., `services/agent`). The workflow reads that single `package.json` directly.

Files inside `node_modules` are skipped. Deleted or moved services are logged and skipped.

The output is a JSON array of `{image, version, dir}` objects passed to subsequent steps via `$GITHUB_OUTPUT`.

#### 2. Build and Push Docker Images

For each detected service, the workflow:

1. Checks that a `Dockerfile` exists in the service directory (skips if missing).
2. Builds the image with two tags: `:latest` and `:{version}`.
3. Pushes both tags to Docker Hub under the `DOCKERHUB_USERNAME` namespace.

```bash
docker build -t $DOCKERHUB_USERNAME/$IMAGE_NAME:latest \
             -t $DOCKERHUB_USERNAME/$IMAGE_NAME:$VERSION \
             $DIR
docker push $DOCKERHUB_USERNAME/$IMAGE_NAME:latest
docker push $DOCKERHUB_USERNAME/$IMAGE_NAME:$VERSION
```

#### 3. Create Git Tags

After all builds succeed, the workflow creates annotated Git tags in the format `{image_name}@{version}` (e.g., `armada-agent@1.0.31`).


### Secrets Required

| Secret | Usage |
|---|---|
| `DOCKERHUB_USERNAME` | Docker Hub account for image push |
| `DOCKERHUB_TOKEN` | Docker Hub access token |

### Permissions

The workflow requires `contents: write` to push Git tags.

---

## Workflow: Unit Tests

**File:** `.github/workflows/unit-tests.yml`

### Trigger

Runs on every `push` to `master` and every `pull_request` targeting `master`.

### Environment Setup

| Layer | Details |
|---|---|
| Runner | `ubuntu-latest` |
| Python | 3.10 (via `setup-python@v5`) |
| System deps | `freetds-dev`, `unixodbc-dev` (required by `pymssql` for SQL Server connectivity) |

### Dependency Installation

The workflow installs each service's `requirements.txt` individually:

```bash
pip install -r services/agent/requirements.txt
pip install -r services/backend/requirements.txt
pip install -r services/orchestrator/requirements.txt
pip install -r services/proxy-provider/requirements.txt
pip install -r services/fingerprint-provider/requirements.txt
pip install -e lib/fantomas
```

The Fantomas library is installed in editable mode (`-e`) so that test imports resolve to the local source.

### Test Execution

```bash
pytest tests/unit -v
```

All unit tests run in a single pytest session. Path isolation between services sharing module names (`app`, `db`, `config`) is handled by per-service `conftest.py` files that manipulate `sys.path` and `sys.modules`.

---

## Pipeline Flow Diagram

```
Developer runs:  npx changeset        →  creates .changeset/*.md
                 npx changeset version →  bumps package.json + CHANGELOG.md
                 git push master       →  triggers workflows

                          ┌──────────────────────┐
                          │  push to master       │
                          └──────────┬───────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                                  ▼
          unit-tests.yml                    docker-publish.yml
          ──────────────                    ──────────────────
          pytest tests/unit -v              git diff HEAD~1 HEAD
                                                     │
                                            Detect changed package.json
                                                     │
                                            For each changed service:
                                              ├─ docker build (latest + version)
                                              ├─ docker push to Docker Hub
                                              └─ git tag {image}@{version}
```
