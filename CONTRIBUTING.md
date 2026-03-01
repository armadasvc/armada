# Contributing to Armada

Thanks for your interest in contributing to Armada! This document outlines how to get started.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Set up the local development environment:

```bash
# Bootstrap the database
cd bootstrap
pip install -r requirements.txt
python bootstrap_database.py
python bootstrap_secrets.py
python bootstrap_cluster_resources.py
cd ..

# Create a project
bash create-project.sh

# Start all services
cd local
docker compose up --build
```

The dashboard should be available at `http://localhost:3000`.

## Making Changes

1. Create a branch from `master` for your changes
2. Make your changes, keeping commits focused and atomic
3. Run the tests before submitting:

```bash
pytest tests/
```

4. Open a pull request against `master`

## Project Structure

Armada is a monorepo with several services:

- `services/orchestrator` — FastAPI job orchestrator
- `services/agent` — Celery worker agents
- `services/frontend` — React/TypeScript dashboard
- `services/proxy-provider` — Proxy management
- `services/fingerprint-provider` — Anti-detection engine
- `lib/fantomas` — Browser automation library

## Guidelines

- Keep pull requests small and focused on a single concern
- Follow the existing code style in each service (Python for backend, TypeScript for frontend)
- Add tests for new functionality when applicable
- Update documentation if your changes affect user-facing behavior

## Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub with:

- A clear description of the problem or suggestion
- Steps to reproduce (for bugs)
- Expected vs actual behavior

## License

By contributing, you agree that your contributions will be licensed under the [GNU Affero General Public License v3](LICENSE).
