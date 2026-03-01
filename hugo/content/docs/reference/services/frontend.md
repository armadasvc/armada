---
title: 4.2.3. Frontend
linkTitle: 4.2.3. Frontend
weight: 3
description: React + Vite web application with Launch panel (file upload, Monaco editor, config processing) and Monitor panel (real-time WebSocket tracking)
---

# Armada Frontend

React web application for launching and monitoring Armada runs. It provides two main panels: a **Launch Panel** to configure and submit bot runs (see [Run Lifecycle — Phase 1]({{< relref "/docs/reference/architecture/run-lifecycle" >}}) for how the frontend processes configs), and a **Monitor Panel** to track runs, jobs, and events in real time via WebSocket.

## Tech Stack

- **React 18** with TypeScript
- **Vite** for development and bundling
- **Monaco Editor** for in-browser file editing
- **Nginx** as the production static server and reverse proxy
- **Docker** multi-stage build (Node 20 + Nginx Alpine)

## Project Structure

```
src/
├── App.tsx                        # Root component with tab navigation (Launch / Monitor)
├── components/
│   ├── Launcher/                  # Launch configuration modal (file selection, SSL check, submit)
│   ├── ConsultationDashboard/     # Real-time monitoring (Runs → Jobs → Events drill-down)
│   ├── FolderUploader.tsx         # Drag-and-drop folder upload
│   ├── FileTree.tsx               # File explorer sidebar
│   ├── JsonEditor.tsx             # Monaco-based code editor
│   ├── JsonTreeView.tsx           # Read-only JSON tree viewer
│   └── Header.tsx                 # Toolbar (view mode, download, format, launch)
├── hooks/
│   ├── useFileSystem.ts           # In-memory virtual file system
│   ├── useLauncher.ts             # Launch workflow (file validation, SSL, API call)
│   ├── useConsultationDashboard.ts# Runs/Jobs/Events fetching + WebSocket live updates
│   └── useJsonFile.ts             # JSON file utilities
├── types/
│   ├── launcher.ts                # Launch payload, config, and file mapping types
│   └── consultation.ts            # Run, Job, Event interfaces
└── utils/
    └── launcher/                  # Script bundling, config processing, SSL helpers
```

## Features

### Launch Panel

1. Upload a project folder (drag-and-drop)
2. Browse and edit files with Monaco Editor (syntax highlighting for JSON, Python, YAML, etc.)
3. Select required configuration files:
   - `config_template.json` — base configuration
   - `config_distant.json` — tuning overrides
   - `data_job.csv` — job data
   - `data_agent.csv` — agent data
4. Bundle `main.py` and submit everything to the orchestrator API + create run entry in armada_run table
5. Download individual files or the entire project as a ZIP

### Monitor Panel

- Paginated list of **Runs** with delete capability
- Drill-down from Run → **Jobs** → **Events**
- Real-time updates via WebSocket (`/tracking/ws/events/`):
  - New runs, new jobs, new events
  - Job status changes
  - Run deletions

## Getting Started

### Prerequisites

- Node.js 20+
- npm

### Development

```bash
npm install
npm run dev
```

The dev server starts on `http://localhost:5173` with a proxy that forwards `/tracking` requests to the backend at `http://localhost:8000`.

### Production Build

```bash
npm run build
```

Static files are output to `dist/`.

### Docker

```bash
docker build -t armada-frontend .
docker run -p 8080:8080 armada-frontend
```

### Kubernetes

```bash
kubectl port-forward svc/armada-frontend 8080:8080
```

## Nginx Reverse Proxy

In production, Nginx serves the SPA and proxies API calls:

| Route | Backend |
|---|---|
| `/tracking/` | `armada-backend:8000` (WebSocket support) |
| `/api/` | `armada-orchestrator:8080` |
| `/*` | SPA fallback (`index.html`) |
