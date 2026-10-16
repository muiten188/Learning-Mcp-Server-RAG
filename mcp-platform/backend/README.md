# MCP Platform backend

The backend is the FastAPI host for the web platform described in the [root README](../../README.md). It connects to Ollama and multiple MCP servers, streams chat responses and tool results to the frontend, stores conversations and documents in PostgreSQL with pgvector, and uses Celery and Redis to process document uploads.

## Technology stack

| Layer | Technology | Why it's here |
|---|---|---|
| ASGI server | Uvicorn | Runs the async FastAPI app and SSE chat streaming |
| API framework | FastAPI | Typed REST and SSE endpoints with OpenAPI documentation at `/api/docs` (`/docs` redirects there) |
| Validation | Pydantic | Request and response schemas and tool-call payload validation |
| Configuration | pydantic-settings | Typed settings from `mcp-platform/.env` for PostgreSQL, Redis, Ollama, and model selection |
| ORM | SQLAlchemy 2.x (async) | Declares conversation, message, tool-call, document, and chunk entities; repositories use ORM `select()` queries |
| Migrations | Alembic | Versions PostgreSQL tables and enables the pgvector extension |
| HTTP client | httpx | Async calls to Ollama and external APIs |
| Job queue | Celery + Redis | Runs document ingestion and embedding outside API requests |
| Database | PostgreSQL + pgvector | Stores relational data and performs vector similarity search for RAG |

Remote MCP servers are configured in [`mcp_servers.json`](../mcp_servers.json), selected by `MCP_SERVERS_FILE` (default `../mcp_servers.json`). Each entry has a unique `name`, a Streamable HTTP `url`, and an `enabled` flag. The containerized API uses [`mcp_servers.container.json`](../mcp_servers.container.json) with Compose service hostnames. Server configuration is not stored in the database. Webpage crawling runs as an MCP tool, not as a Celery job.

## Requirements

- Python 3.12 or newer
- Docker Compose or Podman Compose
- Ollama with the `llama3.1` and `nomic-embed-text` models

## Run locally (PowerShell)

From `mcp-platform`, build and start the complete stack. Each MCP server builds a separate image from its own source directory and requirements file:

```powershell
docker compose up -d --build
docker compose exec ollama ollama pull llama3.1
docker compose exec ollama ollama pull nomic-embed-text
docker compose exec api alembic upgrade head
docker compose exec api python -m app.seed
```

For Podman, replace `docker compose` with `podman compose` or `py -m podman_compose -f compose.yaml`. On Windows, start the Podman machine first if needed:

```powershell
podman machine start
```

The frontend is at `http://localhost:4200`, the API at `http://localhost:8000`, and Swagger at `/api/docs`. Each MCP server uses its own port, 8101–8105, inside its container and on host loopback. To stop without deleting data, run `docker compose down` or the equivalent Podman command.

For IntelliJ Python run/debug configurations for each MCP server, see the [MCP server development guide](../mcp_servers/README.md#develop-and-debug-in-intellij-idea). Local server processes use the same distinct default ports as their containers. The optional per-server port variables are in [`.env.example`](../.env.example); `MCP_PORT` remains a fallback override for an individual process.

To run the API and worker on the host while the infrastructure and MCP containers run in Compose, start only `postgres`, `redis`, `ollama`, and the `mcp-*` services. The default `mcp_servers.json` uses the published loopback ports. Then from `backend`:

```powershell
cd backend
py -m venv .venv
.venv\Scripts\python -m pip install -r requirement.txt
.venv\Scripts\alembic upgrade head
.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

In another terminal, also from `mcp-platform/backend`, start the Celery worker:

```powershell
.venv\Scripts\celery -A app.workers.celery_app worker --loglevel=info --pool=solo
```

The API health check is `/health`; interactive documentation is at `/api/docs` (`/docs` redirects there).

The frontend's **API docs** sidebar link opens the same Swagger UI through the Angular dev proxy. Upload a UTF-8 `.txt` or `.md` file with `POST /api/documents`. If documents remain pending, use `POST /api/documents/embed-pending` (or **Embed pending** on the Documents page) to queue all pending documents. The endpoint returns the queued count and Celery job IDs; `GET /api/documents` shows when embedding has completed. Keep the Celery worker running for queued tasks to become `ready` and populate `document_chunks`.

Default service URLs are PostgreSQL on `localhost:5432`, Redis on `localhost:6379`, and Ollama on `localhost:11434`. Settings can be overridden in `mcp-platform/.env`; see [`.env.example`](../.env.example).

Run backend tests from `mcp-platform/backend` with `.venv\Scripts\python -m pytest -q`.

## Code layout

`app/main.py` creates the FastAPI app and includes feature routers. Business code is grouped under `app/features/`:

```text
backend/
├── alembic/                 Database migrations
├── app/
│   ├── core/                Configuration, database engine, and sessions
│   ├── features/
│   │   ├── chat/            Chat API and orchestration
│   │   ├── conversations/   Conversation persistence and API
│   │   ├── documents/       Uploads, ingestion, and document API
│   │   ├── jobs/            Background job status API
│   │   ├── mcp/             MCP client, tools, and server API
│   │   ├── models/          Ollama model listing API
│   │   └── rag/             Chunking and vector retrieval
│   ├── integrations/
│   │   └── ollama/          Ollama API client
│   ├── workers/             Celery app and compatibility task imports
│   ├── main.py              FastAPI application
│   ├── models.py            Compatibility model imports
│   └── seed.py              Seed import command
└── tests/                   Backend tests
```

| Feature | Responsibility |
|---|---|
| `chat/` | SSE chat endpoint; Ollama chooses from discovered MCP tools and the backend executes validated calls |
| `conversations/` | Conversation models, persistence, and history API |
| `documents/` | Upload validation, document models, ingestion, and Celery task |
| `rag/` | Text chunking and vector retrieval |
| `mcp/` | MCP client, tool discovery, and server status |
| `models/` | Ollama model listing |
| `jobs/` | Background job status |

Shared configuration, database sessions, and model registry are in `app/core/`. The Ollama API client is in `app/integrations/ollama/`; shared Celery setup is in `app/workers/`. `app/seed.py` remains the seed import command, and `alembic/` holds migrations. The backend contains only the MCP client hub; server applications live under [`../mcp_servers/`](../mcp_servers/). `../servers/tools.py` remains available for the earlier CLI prototype.

RAG retrieval returns named `RetrievedChunk` values with `filename` and `content`. MCP calls return `ToolResult` values with `content` and `is_error`. Ollama responses are validated into typed message and response models at the HTTP boundary.

For each chat request, the hub opens Streamable HTTP sessions with enabled servers, discovers tools independently, and sends Ollama qualified names such as `weather__get_weather`. The model may respond without a tool call or request one or more tools. The backend accepts only discovered names, validates JSON arguments, routes calls to their owning server, and returns results to the model. Tool calls are capped at five rounds. An unavailable server is reported as disconnected while healthy servers remain usable. Sessions close at the end of each request; the server containers keep running.

To add another server, give it its own directory and requirements file under `mcp_servers/`, expose an `/mcp` Streamable HTTP endpoint, add a Compose service, and register its URL in both registry files. `GET /api/mcp-servers` reports each server's state and tool names. The files server only touches the shared `workspace` mount; the database server exposes read-only counts; the document server calls the backend document API; the weather server provides current conditions and a three-day forecast; the web server reads one requested page.

Each MCP server can be built, restarted, and scaled independently. The hub makes HTTP connections per request and does not launch subprocesses. The static registry is edited in a file and is not managed through the API.

### Models and migrations

All persisted entities inherit `app.core.base.Base`, which supplies a generated UUID `id`, `created_at`, `updated_at`, and nullable UUID `created_by` and `updated_by` fields. Actor IDs remain null until authentication supplies a user identity. The shared timestamps use UTC. Existing API response fields keep their current names.

Define new tables and columns in `app/features/<feature>/models.py` and import each new model module in `alembic/env.py`. Alembic uses `Base.metadata` to compare those models with the live PostgreSQL schema. From `backend`, generate and review a versioned migration with `.venv\Scripts\alembic revision --autogenerate -m "describe change"`, then apply it with `.venv\Scripts\alembic upgrade head`. Keep previously applied revisions unchanged; `0002_audit_fields` upgrades databases created with `0001_initial`.

### Database connection pooling

`app/core/db.py` explicitly uses SQLAlchemy's `AsyncAdaptedQueuePool` for the async PostgreSQL engine. Each `SessionLocal()` call creates a new session; it checks out a connection when needed and returns it when closed. `pool_pre_ping` checks reused connections. Alembic migrations use `NullPool` separately.

Set `DB_POOL_SIZE` (default `5`), `DB_MAX_OVERFLOW` (default `10`), and `DB_POOL_TIMEOUT` (default `30` seconds) in `mcp-platform/.env`. Each API or Celery worker process has its own pool, so account for all processes when sizing PostgreSQL connections.

Run code quality checks from `backend` with `.venv\Scripts\ruff check app alembic tests`, `.venv\Scripts\ruff format --check app alembic tests`, and `.venv\Scripts\mypy app`.
