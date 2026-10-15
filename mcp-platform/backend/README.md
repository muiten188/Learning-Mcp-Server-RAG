# MCP Platform backend

The backend is the FastAPI host for the web platform described in the [root README](../../README.md). It connects to Ollama and the MCP tool server, streams chat responses and tool results to the frontend, stores conversations and documents in PostgreSQL with pgvector, and uses Celery and Redis to process document uploads.

## Requirements

- Python 3.12 or newer
- Podman with `podman-compose` available as a Python module
- Ollama with the `llama3.1` and `nomic-embed-text` models

## Run locally (PowerShell)

From `mcp-platform`, start PostgreSQL and Redis defined in `compose.yaml`:

```powershell
podman machine start # Windows, if the machine is stopped
py -m podman_compose -f compose.yaml up -d
ollama pull llama3.1
ollama pull nomic-embed-text
```

The Compose file starts the database and Redis only. Run the API and worker separately. From `mcp-platform/backend`, create the Python environment, apply migrations, optionally import the text files in `../data`, and start the API:

```powershell
cd backend
py -m venv .venv
.venv\Scripts\python -m pip install -r requirement.txt
.venv\Scripts\alembic upgrade head
.venv\Scripts\python -m app.seed
.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

In another terminal, also from `mcp-platform/backend`, start the Celery worker:

```powershell
.venv\Scripts\celery -A app.workers.celery_app worker --loglevel=info --pool=solo
```

The API is at `http://localhost:8000`, with health check at `/health` and interactive API documentation at `/api/docs` (`/docs` redirects there). To stop the infrastructure without deleting the PostgreSQL volume, run `py -m podman_compose -f compose.yaml down` from `mcp-platform`.

The frontend's **API docs** sidebar link opens the same Swagger UI through the Angular dev proxy. Upload a UTF-8 `.txt` or `.md` file with `POST /api/documents`. If documents remain pending, use `POST /api/documents/embed-pending` (or **Embed pending** on the Documents page) to queue all pending documents. The endpoint returns the queued count and Celery job IDs; `GET /api/documents` shows when embedding has completed. Keep the Celery worker running for queued tasks to become `ready` and populate `document_chunks`.

Default service URLs are PostgreSQL on `localhost:5432`, Redis on `localhost:6379`, and Ollama on `localhost:11434`. Settings can be overridden in `mcp-platform/.env`; see [`.env.example`](../.env.example).

Run backend tests from `mcp-platform/backend` with `.venv\Scripts\python -m pytest -q`.

## Code layout

`app/main.py` creates the FastAPI app and includes feature routers. Business code is grouped under `app/features/`:

| Feature | Responsibility |
|---|---|
| `chat/` | SSE chat endpoint and tool-calling loop |
| `conversations/` | Conversation models, persistence, and history API |
| `documents/` | Upload validation, document models, ingestion, and Celery task |
| `rag/` | Text chunking and vector retrieval |
| `mcp/` | MCP client, tool discovery, and server status |
| `models/` | Ollama model listing |
| `jobs/` | Background job status |

Shared configuration, database sessions, and model registry are in `app/core/`. The Ollama API client is in `app/integrations/ollama/`; shared Celery setup is in `app/workers/`. `app/seed.py` remains the seed import command, and `alembic/` holds migrations. MCP tool declarations live in `../servers/tools.py`.

Run code quality checks from `backend` with `.venv\Scripts\ruff check app alembic tests`, `.venv\Scripts\ruff format --check app alembic tests`, and `.venv\Scripts\mypy app`.
