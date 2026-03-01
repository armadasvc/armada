---
title: 4.2.7. Meta
linkTitle: 4.2.7. Meta
weight: 7
description: Central versioning metadata package that tracks the global Armada platform version via Changesets
---

# armada-meta

Central versioning metadata package for the Armada monorepo.

## Purpose

This package acts as the **single source of truth for the global version** of the Armada platform. It is referenced by the npm workspaces setup and the [Changesets](https://github.com/changesets/changesets) tooling to coordinate version bumps across all services.

When a changeset is applied on armada-meta (`npx changeset` and `npx changeset version`), `armada-meta` tracks the overall release version independently from the individual services (`backend`, `orchestrator`, `frontend`, etc.), giving a unified version number to tag releases against.

## Usage

This package is not meant to be run directly. It is consumed automatically by the workspace and changeset pipeline defined in the root `package.json`.
