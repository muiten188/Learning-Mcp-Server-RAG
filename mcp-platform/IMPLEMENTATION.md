# Phase 2 web app

This project implements the Phase 2 core from the copied [README.md](README.md): FastAPI hosts an MCP stdio client and Ollama chat loop, PostgreSQL stores conversations and vector documents, Celery indexes uploads through Redis, and Angular renders streamed chat, tool calls, retrieved document names, conversation history, server status, and document status. The Phase 1 tool server and `data/*.txt` are copied into this project. Phase 3 server registration and model switching are outside this phase, though the API lists installed Ollama models and the chat UI can choose one.

## Requirements

- Python 3.11 or newer
- Node 22.22.3+, 24.15+, or 26+
- Docker Compose or another way to run PostgreSQL with pgvector and Redis
- Ollama with `llama3.1` and `nomic-embed-text` pulled

## Run locally

From the project root, start infrastructure and pull models:

```powershell
docker compose up -d
ollama pull llama3.1
ollama pull nomic-embed-text
```

In `backend`, create a virtual environment, install dependencies, migrate, import the copied seed files, and run the API:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[test]"
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

`python -m pytest -q` in `backend` passes the MCP tool discovery/call and stream/chunk tests. The Angular production build succeeds with Node 24.15. Database, Redis, and Ollama were not available in the development environment, so a full live chat was not exercised here.
