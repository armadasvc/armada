---
title: 4.5. Docsy Documentation and landing page
linkTitle: 4.5. Docsy Documentation and landing page
weight: 5
description: Hugo + Docsy setup + React Landing
---

# Hugo Docsy Documentation & Landing page Guide

## Overview

This documentation site is built with [Hugo](https://gohugo.io/) using the [Docsy](https://www.docsy.dev/) theme, a Hugo theme designed for technical documentation.

## Local Development

Start the local server:

```bash
cd hugo
hugo server
```

Then open **http://localhost:1313/** in your browser. The site live-reloads on file changes.

## Project Structure

| Path | Purpose |
|---|---|
| `hugo.yaml` | Site configuration (title, theme, menus) |
| `content/docs/` | Documentation pages (Markdown) |
| `content/docs/<section>/_index.md` | Content|
| `static/` | Static assets (images, files) |
| `layouts/` | Custom layout overrides |

## Writing Content

Each page starts with a **front matter** block:

```yaml
---
title: Page Title
weight: 10
---
```

- `title` — displayed heading and sidebar label
- `weight` — controls ordering within a section (lower = higher)

## Key Docsy Features

- **Left sidebar navigation** — auto-generated from the `content/` folder hierarchy
- **Shortcodes** — reusable components (`alert`, `tabpane`, `cardpane`, etc.)
- **Versioning & multi-language** support built-in
- **Search** via Lunr.js or Algolia

## Integrate React Landing Page and Host to GitHub Pages


The `landing/` folder contains a vibecoded React app (Vite + React + Tailwind + shadcn) that serves as the project's landing page.

To rebuild and update the landing page:

```bash
cd hugo/landing
npm run build
```

Then copy-paste everything from `dist/` (⚠️ **except** `index.html`) into `hugo/static/`

Then go to `hugo/layouts/index.html` and adapat line 11 with hash of `hugo/static/index-xxxxx.js` and line 12 with hash of `hugo/static/index-xxxxx.css` 

Before building the Hugo site, if needed, change the baseURL by going to`hugo.yaml` and modify with your domain

```bash
baseURL: https://armada.services
```

Then build the Hugo site:

```bash
cd hugo
hugo
```

Copy-paste everything from `hugo/public` to `docs` in order to serve it on GH pages.

Finally you can setting up GitHub pages to serve directly the master branch using the `docs` folder as the publishing source. 