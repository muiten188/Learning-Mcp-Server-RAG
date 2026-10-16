# Phase 2 web app

This project implements the Phase 2 core from the [root README](../README.md): FastAPI hosts an HTTP MCP hub and Ollama chat loop, PostgreSQL stores conversations and vector documents, Celery indexes uploads through Redis, and Angular renders streamed chat, tool calls, retrieved document names, conversation history, per-server status, and document status. Five independently deployed MCP server containers are configured in `mcp_servers.container.json`; `mcp_servers.json` holds host-accessible URLs. The older `servers/tools.py` remains for the CLI prototype. Runtime server registration through the API is still outside this phase.

## Requirements

- Python 3.12 or newer
- Node 22.22.3+, 24.15+, or 26+
- Docker Compose or another way to run PostgreSQL with pgvector and Redis
- Ollama with `llama3.1` and `nomic-embed-text` pulled

## Run locally

From the project root, start infrastructure and pull models:

```powershell
docker compose up -d --build
docker compose exec ollama ollama pull llama3.1
docker compose exec ollama ollama pull nomic-embed-text
docker compose exec api alembic upgrade head
docker compose exec api python -m app.seed
```

For host-run backend development, instead start only the infrastructure and MCP services:

```powershell
docker compose up -d --build postgres redis ollama mcp-files mcp-weather mcp-database mcp-documents mcp-web
docker compose exec ollama ollama pull llama3.1
docker compose exec ollama ollama pull nomic-embed-text
```

In `backend`, create a virtual environment, install dependencies, migrate, import seed files, and run the API:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirement.txt
.venv\Scripts\alembic upgrade head
.venv\Scripts\python -m app.seed
.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

Run the worker in another terminal from `backend`:

```powershell
.venv\Scripts\celery -A app.workers.celery_app worker --loglevel=info --pool=solo
```

Run the UI in `frontend`:

```powershell
npm ci
npm start
```

Open `http://localhost:4200`. The API docs are at `http://localhost:8000/docs`. For Linux or macOS, activate the venv and use `python`, `alembic`, `uvicorn`, and `celery` without the Windows `.venv\Scripts\` prefix. Set values from `.env.example` in a root `.env` if your services differ from the defaults.

The backend only accepts UTF-8 `.txt` and `.md` uploads up to 2 MB. Embeddings use a 768-dimensional `nomic-embed-text` vector. Changing embedding models requires a schema and data migration.

## Verification

The backend is organized by feature under `backend/app/features/`; shared infrastructure lives in `core/` and external adapters in `integrations/`. Run `python -m pytest -q`, `ruff check app alembic tests`, `ruff format --check app alembic tests`, and `mypy app` from `backend`. The tests cover route stability, document validation, MCP tool discovery/call, and stream/chunk formatting. Live chat still requires PostgreSQL, Redis, and Ollama.
