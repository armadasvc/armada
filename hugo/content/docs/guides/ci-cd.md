---
title: 3.5. CI/CD
linkTitle: 3.5. CI/CD
weight: 5
description: Release new service versions using Changesets, version bumps, and GitHub Actions workflows
---

## Overview

Armada uses [Changesets](https://github.com/changesets/changesets) to manage service versions and GitHub Actions to automatically build and publish Docker images when a version is bumped on `master`.

This guide covers everything you need as a developer to release a new version of a service.

## Prerequisites

- Node.js installed (for Changesets CLI)
- Push access to the `master` branch (or permission to merge PRs)
- Run `npm install` at the repository root at least once to install the Changesets CLI

## Services Managed by the Pipeline

| Service | Package Name | Docker Image |
|---------|-------------|--------------|
| agent | armada-agent | armada-agent |
| backend | armada-backend | armada-backend |
| orchestrator | armada-orchestrator | armada-orchestrator |
| frontend | armada-frontend | armada-frontend |
| meta | armada-meta | armada-meta |
| project | armada-project | armada-project |
| proxy-provider | armada-proxy-provider | armada-proxy-provider |
| fingerprint-provider | armada-fingerprint-provider | armada-fingerprint-provider |

See the [Services Reference]({{< relref "/docs/reference/services" >}}) for the documentation of each service.

## Releasing a New Version

### Step 1 — Create a Changeset

From the repository root, run:

```bash
npx changeset
```

The CLI will prompt you to:

1. **Select the affected service(s)** — use arrow keys and space to select one or more packages.
2. **Choose a bump type** for each selected package:
   - `patch` — bug fixes, minor tweaks (1.0.0 → 1.0.1)
   - `minor` — new features, backward-compatible changes (1.0.0 → 1.1.0)
   - `major` — breaking changes (1.0.0 → 2.0.0)
3. **Write a summary** — a short description of what changed (this goes into the changelog).

This creates a new markdown file inside the `.changeset/` directory. You can create multiple changesets before releasing — they will all be applied together.

{{% alert title="Tip" %}}
You can create a changeset at any point during development. It is common to add a changeset in the same commit or PR as the code change itself.
{{% /alert %}}

### Step 2 — Apply the Version Bump

When you are ready to release, run:

```bash
npx changeset version
```

This command:
- Reads all pending changeset files in `.changeset/`
- Bumps the `version` field in each affected `package.json`
- Updates (or creates) a `CHANGELOG.md` for each affected service
- Deletes the consumed changeset files

Review the changes to make sure the version bumps are correct.

### Step 3 — Commit and Push

```bash
git add .
git commit -m "bump: <service-name> vX.Y.Z"
git push origin master
```

Once pushed to `master`, the GitHub Actions pipeline automatically detects the version change and builds the new Docker image.

## What Happens After You Push

Two independent GitHub Actions workflows run on every push to `master`:

### Unit Tests (`unit-tests.yml`)

This workflow also runs on every **pull request** targeting `master`.

```
Push to master / Open PR
      │
      ▼
Setup Python 3.10 + system deps (FreeTDS, unixODBC)
      │
      ▼
Install pytest, pytest-asyncio, httpx
      │
      ▼
Install requirements for: agent, backend, orchestrator,
proxy-provider, fingerprint-provider + lib/fantomas
      │
      ▼
Run  pytest tests/unit -v
```

The `tests/unit/` directory mirrors the service structure:

| Directory | Covers |
|-----------|--------|
| `tests/unit/agent/` | fingerprint manager, proxy manager, database connector, monitoring client, … |
| `tests/unit/backend/` | routers (runs, jobs, events), WebSocket manager, DB layer |
| `tests/unit/orchestrator/` | Celery service, Redis service, Kubernetes service, bot router |
| `tests/unit/proxy_provider/` | proxy checks, proxy DB, proxy endpoint |
| `tests/unit/fingerprint_provider/` | forge, fingerprint, crypto, FP DB |
| `tests/unit/lib/` | screen, virtual cursor path, identity (fantomas) |

{{% alert title="Important" %}}
Unit tests **must pass** before a PR can be merged. If you add or modify service logic, run `pytest tests/unit -v` locally to catch failures early.
{{% /alert %}}

### Docker Publish (`docker-publish.yml`)

This workflow only triggers when a `services/**/package.json` file is modified (i.e. a version bump).

```
Push to master (with version change)
      │
      ▼
Detect modified services (compare package.json versions)
      │
      ▼
Build Docker image for each changed service
      │
      ▼
Push to Docker Hub (tagged with version + latest)
      │
      ▼
Create Git tag: <image-name>@<version>
```

You can monitor both workflows in the **Actions** tab of the GitHub repository.


## Checking Current Service Versions

A utility script `list-versions.js` is available at the repository root to list the name, version, and path of every package (services and libraries such as fantomas) in a single table.

From the repository root, run:

```bash
node list-versions.js
```

This recursively scans all directories (skipping `node_modules` and `.git`), reads every `package.json` it finds, and prints a formatted table:

```
┌─────────┬──────────────────────────────────┬─────────┬──────────────────────────────────────────┐
│ (index) │ name                             │ version │ path                                     │
├─────────┼──────────────────────────────────┼─────────┼──────────────────────────────────────────┤
│    0    │ 'armada-agent'                   │ '1.0.0' │ '/home/user/armada/services/agent'        │
│    1    │ 'armada-backend'                 │ '1.2.0' │ '/home/user/armada/services/backend'      │
│    2    │ 'fantomas'                       │ '0.5.0' │ '/home/user/armada/lib/fantomas'          │
│   ...   │ ...                              │  ...    │ ...                                      │
└─────────┴──────────────────────────────────┴─────────┴──────────────────────────────────────────┘
```

{{% alert title="Tip" %}}
Run `node list-versions.js` before and after `npx changeset version` to quickly verify which packages were bumped and to which version.
{{% /alert %}}

## Common Scenarios

### Bumping multiple services at once

Run `npx changeset` and select multiple packages when prompted. Each package can have a different bump type.

### Undoing a changeset before it is applied

Simply delete the generated markdown file inside `.changeset/`. It has not affected any version yet.

### Checking pending changesets

Look at the `.changeset/` directory. Any `.md` file (other than `README.md`) is a pending changeset waiting to be applied by `npx changeset version`.

## Credentials

The pipeline uses the following GitHub secrets (configured by an admin):

| Secret | Usage |
|--------|-------|
| `DOCKERHUB_USERNAME` | Docker Hub account |
| `DOCKERHUB_TOKEN` | Docker Hub access token |
