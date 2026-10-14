# MCP Learning Project

A minimal, educational project that demonstrates how the **Model Context Protocol (MCP)** works end-to-end. It connects a local Llama 3.1 LLM (via Ollama) to an MCP tool server, with simple file-based RAG for knowledge grounding.

> **Goal:** Learn the MCP architecture by tracing every step — from user input, through the LLM, to tool execution and back.

**Project phases**

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | 🧪 **TEST / prototype** — CLI chat host + one MCP server (stdio) + keyword RAG | ✅ Done (test only) |
| 2 | Web platform: FastAPI backend, PostgreSQL + pgvector, Angular chat UI — **can be a new project** | 🚧 Planned — see [Web Platform](#web-platform-phase-2) |
| 3 | Runtime model switching + multi-server MCP hub | 🚧 Planned — see [Model switching](#feature-switch-model-from-the-ui) and [Multi-server MCP](#feature-multi-server-mcp-hub) |
| 4 | Containerised deployment with Podman (7 containers) | 🚧 Planned — see [Deployment with Podman](#deployment-with-podman-phase-4) |

> 🧪 **Phase 1 is a test.** It exists to prove the idea and learn how MCP works end to end (LLM ↔ tool loop ↔ MCP server ↔ RAG). It is a throw-away prototype: keep it small, don't over-engineer it.
>
> 🚀 **From Phase 2 onwards we can start a new project if needed.** Use what Phase 1 teaches us (tool-loop design, tool schemas, what worked or failed with `llama3.1`, RAG quality) to decide what to carry over. Reusing the Phase 1 code is optional, not required.

---

## Architecture (Phase 1 — CLI test)

```mermaid
sequenceDiagram
    participant U as User
    participant C as client.py Chat Host
    participant R as rag.py
    participant L as Ollama Llama 3.1
    participant S as server.py MCP Server
    participant A as Open-Meteo API

    U->>C: "How is the weather in Hanoi?"
    C->>R: retrieve(query)
    R-->>C: context from matching docs
    C->>L: messages + tool schemas + context
    L-->>C: tool_call get_weather city=Hanoi
    C->>S: session.call_tool get_weather
    S->>A: HTTP geocode + forecast
    A-->>S: JSON weather data
    S-->>C: Weather in Hanoi 32C ...
    C->>L: tool result generate final answer
    L-->>C: The weather in Hanoi is 32C
    C-->>U: Print answer
```

### How the pieces fit together

| Component | Role | File |
|-----------|------|------|
| **Host** | The user-facing application — our CLI chat loop | `client.py` |
| **Client** | MCP protocol connector (`ClientSession`) that manages a 1:1 session with the server | Inside `client.py` |
| **Server** | Exposes tools, resources, and prompts over MCP | `server.py` |
| **Tool** | A callable function the LLM can invoke (e.g. `create_file`, `get_weather`, `crawl_webpage`) | Defined in `server.py` |
| **Resource** | Read-only data the server exposes (like a GET endpoint) — `docs://list` | `server.py` (optional) |
| **Prompt** | A reusable message template — `summarize_file` | `server.py` (optional) |
| **Transport** | stdio — client launches server as subprocess, talks through stdin/stdout | Configured in `client.py` |
| **RAG** | Loads text files and injects relevant ones into the LLM system prompt | `rag.py` |

---

## How to run (Phase 1 — CLI test)

### 1. Install Ollama

Download from [ollama.com](https://ollama.com/) and install it. Then pull the model:

```bash
ollama pull llama3.1
```

> **Why `llama3.1`?** Plain `llama3` has weak/no native tool-calling support in Ollama. `llama3.1` was trained with tool-calling capabilities, so the LLM can return structured `tool_calls` instead of just text.

Verify it works:

```bash
ollama run llama3.1 "Say hello in one sentence."
```

### 2. Set up the Python environment and run

```bash
cd mcp-learning

# Create and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the chat (launches the MCP server automatically)
python client.py

# Or run without debug output:
# python client.py --quiet
```

You will see debug output showing every step of the flow:

```
  [MCP] Launching server: python server.py
  [MCP] Session initialised
  [MCP] Connected — 4 tools available: create_file, get_weather, list_files, read_file
  [RAG] Loaded 3 documents: ['about_mcp.txt', 'company_faq.txt', 'python_tips.txt']

  MCP Learning Chat  (type 'quit' to exit)

You: create a file called notes.txt with content hello world
  [RAG] Injected context into system prompt
  [LLM] Calling Ollama (llama3.1), round 1...
  [LLM] Chose tool: create_file({"filename": "notes.txt", "content": "hello world"})
  [MCP] Result: Created file: notes.txt (11 bytes)
  [LLM] Calling Ollama (llama3.1), round 2...

A: I created notes.txt with the content "hello world" in your workspace.
```

---

## Things to try

| User input | What happens |
|------------|--------------|
| `create an empty file` | LLM picks `create_file` tool |
| `create a file notes.txt with content hello` | `create_file` with specific args |
| `how is weather today in Hanoi` | LLM picks `get_weather`, calls Open-Meteo |
| `what is MCP?` | No tool call — answered from RAG context |
| `what is the ennov?` | RAG injects `ennov.txt` (link `https://en.ennov.com/`) → LLM picks `crawl_webpage` tool to crawl the site → summarizes Ennov |
| `list my files` | LLM picks `list_files` |
| `read notes.txt` | LLM picks `read_file` |

### 🔍 How RAG + Crawler work together (Ennov Example)

When you ask `"what is the ennov?"`:
1. **RAG Retrieval:** `rag.py` matches the keyword `ennov` and retrieves [`data/ennov.txt`](file:///c:/Data-PC-Home/Projects/AI/New%20folder/mcp-learning/data/ennov.txt), which contains:
   ```
   Ennov là một công ty:
   link trang web: https://en.ennov.com/
   ```
2. **Context Injection:** `client.py` injects this text into the system prompt.
3. **Tool Selection:** The LLM observes the website link in context and recognizes that more information is needed. It issues a tool call:
   ```json
   crawl_webpage({"url": "https://en.ennov.com/"})
   ```
4. **MCP Execution:** `server.py` fetches `https://en.ennov.com/`, cleans the HTML, extracts readable text, and returns it over the MCP stdio protocol.
5. **Final Answer:** Ollama reads the crawled content and formulates a complete response explaining what Ennov does (Life Sciences software solutions for regulatory, clinical, quality, etc.).

---

## MCP concepts explained

### Server
A lightweight program that exposes capabilities (tools, resources, prompts) through the MCP protocol. In this project, `server.py` is our MCP server. It does not know anything about the LLM — it just exposes functions and waits for calls.

### Client
A protocol-level connector that maintains a 1:1 session with a server. It handles message framing, capability negotiation, and transport. In our code, this is the `ClientSession` object in `client.py`.

### Host
The user-facing application that contains one or more MCP clients. The host decides which servers to connect to and orchestrates tool calls with the LLM. Our host is the CLI chat loop in `client.py`.

### Tool
A function the server exposes that the LLM can choose to call. Tools have a name, description, and a JSON Schema for their inputs. The LLM reads these schemas to decide when and how to call a tool.

### Resource
Read-only data the server exposes, identified by a URI (e.g. `docs://list`). Resources are like GET endpoints — clients can read them but not modify them. Useful for exposing configuration, documentation, or status.

### Prompt
A reusable message template the server suggests. Prompts help clients construct good requests. For example, our `summarize_file` prompt generates a message asking the LLM to summarize a specific file.

### stdio transport
The client launches the server as a subprocess and communicates through stdin/stdout using JSON-RPC messages. This is the simplest transport — no network setup, no ports, no authentication. The alternative is HTTP+SSE for remote servers.

---

## How to add a new tool

Adding a tool is a 3-step process:

### Step 1: Define the function in `server.py`

```python
@mcp.tool()
def my_new_tool(arg1: str, arg2: int = 42) -> str:
    """
    Describe what this tool does — the LLM reads this docstring
    to decide when to use it.

    Args:
        arg1: Explain what this argument is for.
        arg2: Optional argument with a default value.

    Returns:
        A human-readable result string.
    """
    # Your logic here
    return f"Did something with {arg1} and {arg2}"
```

### Step 2: Restart the server

The client launches the server on startup, so just restart `client.py`. The new tool will automatically appear in `list_tools()`.

### Step 3: Test it

Ask the LLM something that should trigger your tool. Check the debug output to confirm the LLM chose it:

```
  [LLM] Chose tool: my_new_tool({"arg1": "hello", "arg2": 10})
  [MCP] Result: Did something with hello and 10
```

> **Tip:** Good docstrings and argument names are critical. The LLM uses them to decide which tool to call and what arguments to pass. Be explicit about what each argument expects.

---

## Debugging with MCP Inspector

MCP Inspector is a web-based tool that lets you interact with your MCP server directly (without the LLM), which is great for testing tools in isolation.

```bash
npx @modelcontextprotocol/inspector python server.py
```

This opens a browser UI where you can:
- See all registered tools, resources, and prompts
- Call tools with custom arguments and see the results
- Inspect the JSON-RPC messages going back and forth

---

# Web Platform (Phase 2)

> 🚀 **New project (if needed).** Phase 1 was only a test. If the test shows the CLI code isn't a good base (e.g. the tool loop is tangled with the CLI, or one `server.py` is too limiting), start Phase 2 as a **fresh project** — for example `mcp-platform/` — and port over only the pieces that proved useful. The structure below is written as a clean layout and doesn't depend on the Phase 1 folder.
>
> **What to carry over from the Phase 1 test:** the tool-calling loop logic, the MCP tool definitions (`create_file`, `get_weather`, `crawl_webpage`, …), the RAG seed files in `data/`, and the notes on which models handle tool calls well.

Phase 2 turns the CLI host into a **web application**: a FastAPI server hosts the MCP client(s), stores conversations and RAG data in PostgreSQL, and an Angular chat UI (ChatGPT-style) talks to it over HTTP + streaming.

> **Why a web server?** In MCP terms, the FastAPI app becomes the **Host**. Browsers can't speak stdio or hold MCP sessions, so the backend owns the MCP clients, the LLM calls, and the tool loop. The browser only sends messages and renders streamed events.

## Target architecture

```mermaid
flowchart LR
    subgraph Browser
        UI[Angular 22 Chat UI]
    end

    subgraph Backend[FastAPI Host - Uvicorn]
        API[REST + SSE endpoints]
        CHAT[Chat orchestrator<br/>tool loop]
        HUB[MCP Hub<br/>multi-server clients]
        RAG[RAG service]
    end

    subgraph Workers
        CEL[Celery workers]
        RED[(Redis<br/>broker + results)]
    end

    DB[(PostgreSQL<br/>+ pgvector)]
    OLL[Ollama<br/>llama3.1 / qwen2.5 / mistral]

    subgraph MCPServers[MCP Servers]
        S1[files server]
        S2[weather server]
        S3[database server]
    end

    UI -- HTTP / SSE --> API
    API --> CHAT
    CHAT --> RAG
    CHAT --> HUB
    CHAT -- httpx --> OLL
    RAG --> DB
    API --> DB
    API -- enqueue --> RED
    RED --> CEL
    CEL --> DB
    CEL -- embeddings --> OLL
    HUB -- stdio / HTTP --> S1
    HUB -- stdio / HTTP --> S2
    HUB -- stdio / HTTP --> S3
```

## Tech stack

| Layer | Technology | Why it's here |
|-------|-----------|---------------|
| **ASGI server** | Uvicorn | Runs the FastAPI app (async, supports SSE streaming) |
| **API framework** | FastAPI | Typed REST/SSE endpoints, automatic OpenAPI docs at `/docs` |
| **Validation** | Pydantic | Request/response schemas, tool-call payload validation |
| **Configuration** | pydantic-settings | Typed settings from `.env` (DB URL, Ollama URL, Redis URL, default model) |
| **ORM** | SQLAlchemy 2.x (async) | Models for conversations, messages, documents, MCP servers |
| **Migrations** | Alembic | Versioned schema changes (including enabling `pgvector`) |
| **HTTP client** | httpx | Async calls to Ollama and external APIs (Open-Meteo, crawler) |
| **Job queue** | Celery + Redis | Long-running jobs: document ingestion, embedding, web crawling |
| **Database** | PostgreSQL + pgvector | Relational data + vector similarity search for RAG |
| **Frontend framework** | Angular 22 | SPA, signals-based state, standalone components |
| **AI chat state** | TanStack AI | Streaming chat state/hooks (see the note in [Frontend](#frontend)) |
| **UI components** | Spartan UI *or* Zard UI | Accessible, unstyled/shadcn-style Angular components |
| **Styling** | Tailwind CSS | Utility-first styling, dark mode |
| **Icons** | Lucide Angular | Consistent icon set |
| **Markdown** | ngx-markdown | Render assistant answers (code blocks, tables, lists) |

## Project structure (Phase 2)

```
mcp-learning/
├── README.md
├── docker-compose.yml           ← postgres (pgvector), redis
├── mcp_servers.json             ← registry of MCP servers (seed config)
├── servers/                     ← MCP servers (moved from server.py)
│   ├── files_server.py
│   ├── weather_server.py
│   └── database_server.py
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   └── app/
│       ├── main.py              ← FastAPI app factory, lifespan (start/stop MCP hub)
│       ├── core/
│       │   ├── config.py        ← pydantic-settings
│       │   └── db.py            ← async engine + session
│       ├── models/              ← SQLAlchemy models
│       ├── schemas/             ← Pydantic schemas
│       ├── api/
│       │   ├── chat.py          ← POST /api/chat (SSE stream)
│       │   ├── conversations.py
│       │   ├── models.py        ← GET /api/models (Ollama models)
│       │   ├── mcp_servers.py   ← CRUD + health for MCP servers
│       │   └── documents.py     ← upload docs for RAG
│       ├── services/
│       │   ├── llm.py           ← Ollama client (httpx)
│       │   ├── mcp_hub.py       ← multi-server MCP manager
│       │   ├── orchestrator.py  ← the tool loop (from client.py)
│       │   └── rag.py           ← pgvector retrieval
│       └── workers/
│           ├── celery_app.py
│           └── tasks.py         ← ingest_document, crawl_and_index
├── frontend/                    ← Angular 22 app
│   └── src/app/
│       ├── core/                ← api client, settings store
│       ├── features/
│       │   ├── chat/            ← sidebar, message list, composer, tool-call cards
│       │   ├── servers/         ← MCP server management page
│       │   └── documents/       ← RAG document manager
│       └── shared/ui/           ← Spartan/Zard wrappers
└── data/                        ← seed RAG text files (imported into pgvector)
```

---

## Backend

### Responsibilities

1. **Host the MCP client(s)** — start them at app startup (FastAPI `lifespan`), keep sessions alive, close on shutdown.
2. **Run the tool loop** — the same flow as `client.py`, but per request and streamed to the browser.
3. **Persist everything** — conversations, messages, tool calls, documents, embeddings.
4. **Offload slow work** — embedding and crawling run in Celery workers, not in the request.

### Configuration (`pydantic-settings`)

```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str = "postgresql+asyncpg://mcp:mcp@localhost:5432/mcp"
    redis_url: str = "redis://localhost:6379/0"
    ollama_base_url: str = "http://localhost:11434"
    default_model: str = "llama3.1"
    embedding_model: str = "nomic-embed-text"
    embedding_dim: int = 768
    mcp_servers_file: str = "mcp_servers.json"

settings = Settings()
```

### API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/chat` | Send a message; response is a **Server-Sent Events** stream (tokens, tool calls, tool results) |
| `GET` | `/api/conversations` | List conversations for the sidebar |
| `GET` | `/api/conversations/{id}` | Load full message history |
| `DELETE` | `/api/conversations/{id}` | Delete a conversation |
| `GET` | `/api/models` | List models installed in Ollama (for the model picker) |
| `GET` | `/api/mcp-servers` | List registered MCP servers + status + tools |
| `POST` | `/api/mcp-servers` | Register a new MCP server |
| `PATCH` | `/api/mcp-servers/{id}` | Enable/disable a server |
| `DELETE` | `/api/mcp-servers/{id}` | Remove a server |
| `POST` | `/api/documents` | Upload a document → enqueues an ingestion job |
| `GET` | `/api/jobs/{id}` | Poll status of a Celery job |
| `GET` | `/health` | Liveness check |

### Streaming event format (SSE)

The UI needs to show *what the LLM is doing*, not just the final text — that's the whole point of this learning project. Each SSE event has a `type`:

```
event: rag
data: {"documents": ["ennov.txt"]}

event: tool_call
data: {"id": "call_1", "server": "weather", "name": "get_weather", "arguments": {"city": "Hanoi"}}

event: tool_result
data: {"id": "call_1", "content": "Weather in Hanoi 32C ...", "is_error": false}

event: token
data: {"text": "The weather in "}

event: done
data: {"message_id": "…", "model": "llama3.1"}
```

### Request flow in the backend

```mermaid
sequenceDiagram
    participant UI as Angular UI
    participant API as FastAPI /api/chat
    participant ORC as Orchestrator
    participant RAG as RAG service
    participant DB as PostgreSQL
    participant LLM as Ollama
    participant HUB as MCP Hub
    participant SRV as MCP Server

    UI->>API: POST /api/chat {conversation_id, model, message}
    API->>DB: save user message
    API->>ORC: run(conversation, model)
    ORC->>RAG: retrieve(query) (pgvector)
    RAG->>DB: SELECT ... ORDER BY embedding <=> query
    RAG-->>ORC: top-k chunks
    ORC-->>UI: SSE rag
    loop until no more tool calls
        ORC->>LLM: messages + tools from hub
        LLM-->>ORC: tool_call or text
        ORC-->>UI: SSE tool_call
        ORC->>HUB: call_tool(server__tool, args)
        HUB->>SRV: session.call_tool
        SRV-->>HUB: result
        HUB-->>ORC: result
        ORC-->>UI: SSE tool_result
    end
    ORC-->>UI: SSE token stream (final answer)
    ORC->>DB: save assistant message + tool calls
    ORC-->>UI: SSE done
```

### Celery jobs (Redis broker)

Anything slow or retryable goes to a worker:

| Task | What it does |
|------|--------------|
| `ingest_document(document_id)` | Read file → split into chunks → embed each chunk via Ollama → insert into `document_chunks` |
| `crawl_and_index(url)` | Crawl a page (httpx) → clean text → ingest as a document |
| `reindex_all()` | Re-embed everything after changing the embedding model |

```bash
# run a worker
celery -A app.workers.celery_app worker --loglevel=info
# on Windows add:  --pool=solo
```

> **Windows note:** Celery's default prefork pool does not work well on Windows. Use `--pool=solo` (or `--pool=threads`) for local development.

### Migrations (Alembic)

```bash
cd backend
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

The first migration must enable the extension **before** creating vector columns:

```python
# in the migration's upgrade()
op.execute("CREATE EXTENSION IF NOT EXISTS vector")
```

---

## Database (PostgreSQL + pgvector)

pgvector stores embeddings next to your normal data, so RAG retrieval is a single SQL query — no separate vector database to run.

### Local setup with Docker

```yaml
# docker-compose.yml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: mcp
      POSTGRES_PASSWORD: mcp
      POSTGRES_DB: mcp
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]

  redis:
    image: redis:7
    ports: ["6379:6379"]

volumes:
  pgdata:
```

### Schema

```mermaid
erDiagram
    CONVERSATION ||--o{ MESSAGE : has
    MESSAGE ||--o{ TOOL_CALL : triggers
    DOCUMENT ||--o{ DOCUMENT_CHUNK : split_into
    MCP_SERVER ||--o{ TOOL_CALL : executes

    CONVERSATION {
        uuid id PK
        text title
        text model
        timestamptz created_at
    }
    MESSAGE {
        uuid id PK
        uuid conversation_id FK
        text role
        text content
        timestamptz created_at
    }
    TOOL_CALL {
        uuid id PK
        uuid message_id FK
        uuid mcp_server_id FK
        text tool_name
        jsonb arguments
        text result
        boolean is_error
    }
    MCP_SERVER {
        uuid id PK
        text name
        text transport
        jsonb config
        boolean enabled
    }
    DOCUMENT {
        uuid id PK
        text filename
        text source_url
        text status
        timestamptz created_at
    }
    DOCUMENT_CHUNK {
        uuid id PK
        uuid document_id FK
        int chunk_index
        text content
        vector embedding
    }
```

### RAG retrieval query

```python
from sqlalchemy import select
from pgvector.sqlalchemy import Vector

# in models/document_chunk.py
# embedding: Mapped[list[float]] = mapped_column(Vector(768))

async def retrieve(session, query_embedding: list[float], k: int = 4):
    stmt = (
        select(DocumentChunk)
        .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(k)
    )
    return (await session.scalars(stmt)).all()
```

Add an index once you have more than a few thousand chunks:

```sql
CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);
```

> **Embedding model:** pull one with `ollama pull nomic-embed-text` (768 dimensions). If you change the model, the vector size may change — update `embedding_dim`, add a migration, and run `reindex_all()`.

This replaces the keyword matching in `rag.py` (see "What to try next", item 3).

---

## Frontend

### Stack

**Angular 22 + TanStack AI + Spartan UI (or Zard UI) + Tailwind CSS + Lucide Angular + ngx-markdown**

> ⚠️ **Verify before committing to TanStack AI.** TanStack AI is a newer library and its framework support has focused on React/Solid-style hooks first. Check that an **Angular adapter** exists and supports custom (non-OpenAI) SSE streams like ours. If it doesn't, the fallback is small and keeps the same architecture: an Angular `ChatService` that consumes the SSE stream with `fetch` + `ReadableStream` and stores messages in **signals**.

### Spartan UI vs Zard UI

| | Spartan UI | Zard UI |
|---|---|---|
| Style | Headless primitives ("brain") + styled layer ("helm") | shadcn/ui-style, copy components into your repo |
| Accessibility | Strong (built on Angular CDK) | Good |
| Customisation | High — you own the helm layer | High — you own the code |
| Best for | Long-lived apps that need robust a11y | Fast start with a ChatGPT/shadcn look |

**Suggestion:** start with **Spartan UI** for its accessibility primitives (dialog, select, dropdown, tabs). Both work with Tailwind, so switching later is not painful.

### UI design (ChatGPT-style)

Layout suggestion — familiar, and it fits everything this project needs to show:

```
┌──────────────────┬──────────────────────────────────────────────────┐
│  ＋ New chat     │  [ llama3.1 ▾ ]                    [ MCP: 3/3 ● ] │ ← top bar
│                  ├──────────────────────────────────────────────────┤
│  Today           │                                                  │
│   · Weather Hanoi│        You:  how is the weather in Hanoi?        │
│   · Notes file   │                                                  │
│  Yesterday       │   ┌─ 🔧 weather · get_weather ───────────────┐   │
│   · What is MCP  │   │ args:   { "city": "Hanoi" }              │   │
│                  │   │ result: Weather in Hanoi 32C ...   ▾     │   │
│                  │   └──────────────────────────────────────────┘   │
│                  │   A:  The weather in Hanoi is 32°C ...           │
│  ───────────     │                                                  │
│  ⚙ Servers       ├──────────────────────────────────────────────────┤
│  📄 Documents    │  [ Message...                         ] [ Send ] │
└──────────────────┴──────────────────────────────────────────────────┘
```

**What makes it more than a ChatGPT clone — it's a *learning* UI:**

- **Tool-call cards** inline in the conversation: server name, tool name, arguments, result (collapsible). This is the MCP flow made visible.
- **RAG badge** on a message: shows which documents were injected into the prompt.
- **Debug drawer** (toggle): raw SSE events and the exact messages sent to the LLM — the web version of the CLI's `[LLM]` / `[MCP]` debug output.
- **Model picker** in the top bar and **MCP status pill** (how many servers are connected).

### Pages & components

| Route | Content |
|-------|---------|
| `/chat/:id?` | Sidebar (conversation list), message list, composer, top bar (model picker, MCP status) |
| `/servers` | List/add/enable/disable MCP servers, view each server's tools and health |
| `/documents` | Upload documents for RAG, see ingestion job status, delete |
| `/settings` | Default model, temperature, theme (dark/light) |

Key components: `ChatSidebar`, `MessageList`, `MessageBubble` (uses `ngx-markdown`), `ToolCallCard`, `Composer`, `ModelPicker`, `McpStatusPill`, `DebugDrawer`.

### Rendering assistant answers

```ts
// message-bubble.component.ts (standalone)
import { MarkdownComponent } from 'ngx-markdown';
// template: <markdown [data]="message().content" />
```

Add `ngx-markdown`'s syntax highlighting (Prism or highlight.js) so code blocks in answers look right.

### Icons

```ts
import { LucideAngularModule, Send, Plus, Wrench, Server, FileText } from 'lucide-angular';
```

### Frontend setup

```bash
cd frontend
npm install -g @angular/cli
ng new frontend --style=css --routing --ssr=false
npm install tailwindcss @tailwindcss/postcss postcss
npm install lucide-angular ngx-markdown marked
# UI kit: follow the Spartan UI (spartan.ng) or Zard UI (zardui.com) install guide
ng serve   # http://localhost:4200
```

Proxy `/api` to the backend during development (`proxy.conf.json`):

```json
{ "/api": { "target": "http://localhost:8000", "secure": false } }
```

---

## Feature: switch model from the UI

> Try a different model — swap `llama3.1` for `qwen2.5` or `mistral` and see how tool-calling behaviour changes.

In Phase 1 this meant editing the `MODEL` variable. In Phase 2 the user picks the model **per conversation** from a dropdown, with no restart.

### How it works

1. `GET /api/models` calls Ollama's `/api/tags` (via httpx) and returns the installed models.
2. The UI shows them in the `ModelPicker`.
3. `POST /api/chat` includes `model`; the orchestrator passes it straight to Ollama.
4. The model name is saved on the conversation (and on each assistant message) so you can compare behaviour later.

```python
# backend/app/api/models.py
@router.get("/api/models")
async def list_models(llm: LlmClient = Depends(get_llm)):
    tags = await llm.list_models()          # GET {ollama}/api/tags
    return [{"name": m["name"], "size": m["size"]} for m in tags["models"]]
```

```python
# backend/app/schemas/chat.py
class ChatRequest(BaseModel):
    conversation_id: UUID | None = None
    model: str = settings.default_model
    message: str
```

### Pull models

```bash
ollama pull qwen2.5
ollama pull mistral
```

### Things to watch when comparing models

| Aspect | What to compare |
|--------|-----------------|
| **Tool-calling support** | Not every model supports tools in Ollama. If a model doesn't, Ollama returns an error — show a friendly "this model can't use tools" message and disable the MCP tools for that chat. |
| **Argument quality** | Does it pass the right `city` / `filename`? Does it invent arguments? |
| **Tool choice** | Does it call a tool when it should — and *not* call one when it shouldn't (e.g. `what is MCP?`)? |
| **Multi-tool tasks** | Can it chain `list_files` → `read_file`? |
| **Speed / memory** | Tokens per second, RAM/VRAM use on your machine |

**Learning idea:** add a *Compare* button that sends the same prompt to two models and shows both answers + tool calls side by side.

---

## Feature: multi-server MCP hub

> Build a multi-server setup — connect the client to multiple MCP servers (e.g. one for files, one for weather, one for databases) and let the LLM choose across all of them.

In Phase 1 there was one server (`server.py`). In Phase 2 the backend runs an **MCP Hub** that holds one `ClientSession` per server and presents all their tools to the LLM as a single list.

### Splitting the server

| Server | Tools | Transport |
|--------|-------|-----------|
| `files` | `create_file`, `read_file`, `list_files` | stdio |
| `weather` | `get_weather` | stdio |
| `database` | `query_documents`, `list_tables` (read-only SQL) | stdio (or HTTP) |

Each server stays unaware of the LLM and of the other servers — the Hub does all the coordination.

### Server registry (`mcp_servers.json`)

```json
{
  "servers": [
    { "name": "files",    "transport": "stdio", "command": "python", "args": ["servers/files_server.py"] },
    { "name": "weather",  "transport": "stdio", "command": "python", "args": ["servers/weather_server.py"] },
    { "name": "database", "transport": "stdio", "command": "python", "args": ["servers/database_server.py"] }
  ]
}
```

This file seeds the `mcp_servers` table on first start; after that the UI (`/servers`) manages them.

### Hub design

```mermaid
flowchart TB
    LLM[LLM sees one flat tool list]
    HUB[MCP Hub]
    LLM -- "files__create_file<br/>weather__get_weather<br/>database__list_tables" --> HUB
    HUB -- "strip prefix, route" --> A[files session]
    HUB --> B[weather session]
    HUB --> C[database session]
```

**Key idea — namespacing.** Two servers might both expose a tool called `search`. The Hub prefixes each tool with its server name (`weather__get_weather`) when giving schemas to the LLM, then splits the prefix off to route the call.

```python
# backend/app/services/mcp_hub.py
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SEP = "__"

class McpHub:
    def __init__(self):
        self._stack = AsyncExitStack()
        self._sessions: dict[str, ClientSession] = {}

    async def connect(self, name: str, command: str, args: list[str]):
        params = StdioServerParameters(command=command, args=args)
        read, write = await self._stack.enter_async_context(stdio_client(params))
        session = await self._stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        self._sessions[name] = session

    async def list_tools(self) -> list[dict]:
        """All tools from all servers, in Ollama's tool-schema format."""
        tools = []
        for server, session in self._sessions.items():
            for t in (await session.list_tools()).tools:
                tools.append({
                    "type": "function",
                    "function": {
                        "name": f"{server}{SEP}{t.name}",
                        "description": f"[{server}] {t.description}",
                        "parameters": t.inputSchema,
                    },
                })
        return tools

    async def call_tool(self, namespaced: str, arguments: dict):
        server, tool = namespaced.split(SEP, 1)
        return await self._sessions[server].call_tool(tool, arguments)

    async def close(self):
        await self._stack.aclose()
```

### Things to handle

- **A server fails to start or crashes** — mark it `unavailable`, keep the others working, show it in the UI status pill.
- **Too many tools confuse small models** — local models get worse as the tool list grows. Allow enabling/disabling servers *per conversation*, or pick the top-N relevant tools per request.
- **Safety** — the `files` server must stay sandboxed to `workspace/`; the `database` server must be read-only.
- **Lifecycle** — connect all servers in FastAPI's `lifespan`, close them on shutdown (the `AsyncExitStack` above handles this).

### Try it

| User input | Expected behaviour |
|------------|--------------------|
| `weather in Hanoi, then save it to weather.txt` | LLM chains `weather__get_weather` → `files__create_file` across **two servers** |
| `which tables do I have?` | LLM picks `database__list_tables` |
| Disable the `weather` server in the UI, ask for the weather | LLM can't call it — observe how each model responds |

---

## How to run (Phase 2 — Web)

```bash
# 1. Infrastructure (PostgreSQL + pgvector, Redis)
docker compose up -d

# 2. Models
ollama pull llama3.1
ollama pull nomic-embed-text

# 3. Backend
cd backend
pip install -e .
alembic upgrade head
uvicorn app.main:app --reload --port 8000       # API docs: http://localhost:8000/docs

# 4. Worker (new terminal)
celery -A app.workers.celery_app worker --loglevel=info --pool=solo

# 5. Frontend (new terminal)
cd frontend
npm install
ng serve                                         # http://localhost:4200
```

### Suggested build order

1. Docker Compose + Alembic schema (conversations, messages)
2. Move the tool loop from `client.py` into `orchestrator.py`; expose `POST /api/chat` with SSE
3. Minimal Angular chat page (send message, render streamed tokens with `ngx-markdown`)
4. Tool-call cards + RAG badge (make the MCP flow visible)
5. `GET /api/models` + model picker
6. Split `server.py` into 3 servers + build the MCP Hub + `/servers` page
7. pgvector RAG + Celery ingestion + `/documents` page
8. Debug drawer, conversation history polish, dark mode

---

# Deployment with Podman (Phase 4)

Phase 4 packages the whole platform as containers and runs it with **Podman** — rootless, daemonless, and compatible with Docker-style Compose files. The same setup works on a Windows/macOS dev machine (via `podman machine`) and on a Linux server (with systemd Quadlets).

## Container breakdown

| # | Container | Image / base | Responsibility | Exposed |
|---|-----------|--------------|----------------|---------|
| 1 | `frontend` | `nginx:alpine` (multi-stage: Node build → Nginx) | Nginx serves the Angular build and reverse-proxies `/api` to `api` | **80** (public) |
| 2 | `api` | `python:3.12-slim` | FastAPI (Uvicorn): chat, RAG, and job-management APIs; hosts the MCP Hub | 8000 (internal) |
| 3 | `worker` | same image as `api` | Celery worker: RAG ingestion, chunking, embedding jobs | — |
| 4 | `scheduler` | same image as `api` | Celery Beat: triggers scheduled RAG updates (re-crawl, re-index) | — |
| 5 | `postgres` | `pgvector/pgvector:pg16` | Stores users, conversations, documents, and vectors | 5432 (internal) |
| 6 | `redis` | `redis:7-alpine` | Message broker + result backend for Celery | 6379 (internal) |
| 7 | `flower` *(optional)* | same image as `api` | Web dashboard for monitoring Celery jobs | 5555 (localhost only) |

> `api`, `worker`, `scheduler` and `flower` all use **one backend image** with different commands. One build, four roles.

### Deployment diagram

```mermaid
flowchart LR
    USER[Browser] -->|:80| FE[frontend<br/>Nginx + Angular]

    subgraph NET[Podman network: mcpnet]
        FE -->|/api proxy| API[api<br/>FastAPI + MCP Hub]
        API --> PG[(postgres<br/>pgvector)]
        API --> RED[(redis)]
        WRK[worker<br/>Celery] --> RED
        WRK --> PG
        SCH[scheduler<br/>Celery Beat] --> RED
        FLW[flower<br/>optional] --> RED
    end

    API -->|host.containers.internal:11434| OLL[Ollama<br/>on the host]
    WRK -->|embeddings| OLL
```

Only `frontend` (and optionally `flower`) publish ports. Everything else is reachable only inside the Podman network.

### What runs where

- **Ollama stays on the host** (not in a container). It needs direct GPU access and already manages its own model files. Containers reach it at `http://host.containers.internal:11434`. A containerised Ollama is possible later, but GPU passthrough under rootless Podman takes extra setup.
- **MCP servers run inside the `api` container** as stdio subprocesses (spawned by the MCP Hub). That means the `api` image must contain `servers/` and the Python dependencies they need. The `worker` does not need them.
- **Scheduler must be a single instance.** Running two Beat containers would trigger every scheduled job twice.

## Project structure additions

```
mcp-learning/
├── deploy/
│   ├── compose.yaml              ← all 7 containers
│   ├── .env.example              ← copy to .env (never commit .env)
│   └── quadlet/                  ← systemd units for Linux servers (optional)
├── backend/
│   └── Containerfile             ← shared by api / worker / scheduler / flower
└── frontend/
    ├── Containerfile             ← Node build stage + Nginx runtime stage
    └── nginx.conf
```

## Images

### Backend (`backend/Containerfile`)

```dockerfile
FROM docker.io/library/python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv

# dependencies first (better layer caching)
COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir .

# application code, MCP servers, seed data
COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./
COPY servers ./servers
COPY mcp_servers.json ./
COPY data ./data

# run as a non-root user
RUN useradd --create-home appuser \
    && mkdir -p /srv/workspace /srv/uploads \
    && chown -R appuser /srv
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

> Build from the **repository root** so `servers/` and `data/` are inside the build context: `podman build -f backend/Containerfile -t mcp-backend .`

### Frontend (`frontend/Containerfile`)

```dockerfile
# ---- build stage ----
FROM docker.io/library/node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npx ng build --configuration production

# ---- runtime stage ----
FROM docker.io/library/nginx:alpine
# adjust the folder name to match your Angular output path
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### Nginx config (`frontend/nginx.conf`)

The important part is **disabling buffering for `/api`** — otherwise Nginx holds back the SSE stream and the chat answer arrives all at once instead of token by token.

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    # Angular SPA: unknown routes fall back to index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API + SSE streaming
    location /api/ {
        proxy_pass http://api:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_buffering off;          # required for SSE
        proxy_cache off;
        proxy_read_timeout 3600s;     # long LLM responses
        chunked_transfer_encoding on;
    }

    location = /health { proxy_pass http://api:8000/health; }
}
```

## Compose file (`deploy/compose.yaml`)

```yaml
name: mcp-platform

x-backend-env: &backend-env
  DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
  REDIS_URL: redis://redis:6379/0
  OLLAMA_BASE_URL: ${OLLAMA_BASE_URL:-http://host.containers.internal:11434}
  DEFAULT_MODEL: ${DEFAULT_MODEL:-llama3.1}
  EMBEDDING_MODEL: ${EMBEDDING_MODEL:-nomic-embed-text}
  SECRET_KEY: ${SECRET_KEY}

services:
  postgres:
    image: docker.io/pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 3s
      retries: 10
    restart: unless-stopped

  redis:
    image: docker.io/library/redis:7-alpine
    command: ["redis-server", "--appendonly", "yes"]
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10
    restart: unless-stopped

  api:
    build:
      context: ..
      dockerfile: backend/Containerfile
    # run migrations, then start the server
    command: >
      sh -c "alembic upgrade head &&
             uvicorn app.main:app --host 0.0.0.0 --port 8000"
    environment: *backend-env
    volumes:
      - workspace:/srv/workspace
      - uploads:/srv/uploads
    depends_on:
      postgres: { condition: service_healthy }
      redis:    { condition: service_healthy }
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 10s
      timeout: 5s
      retries: 10
    restart: unless-stopped

  worker:
    build:
      context: ..
      dockerfile: backend/Containerfile
    command: ["celery", "-A", "app.workers.celery_app", "worker", "--loglevel=info", "--concurrency=2"]
    environment: *backend-env
    volumes:
      - uploads:/srv/uploads
    depends_on:
      api:   { condition: service_healthy }   # migrations have finished
      redis: { condition: service_healthy }
    restart: unless-stopped

  scheduler:
    build:
      context: ..
      dockerfile: backend/Containerfile
    command: ["celery", "-A", "app.workers.celery_app", "beat", "--loglevel=info",
              "--schedule=/tmp/celerybeat-schedule"]
    environment: *backend-env
    depends_on:
      api:   { condition: service_healthy }
      redis: { condition: service_healthy }
    restart: unless-stopped            # keep at exactly ONE replica

  frontend:
    build:
      context: ../frontend
      dockerfile: Containerfile
    ports:
      - "80:80"                    # host port 80 -> Nginx port 80 (see rootless note below)
    depends_on:
      api: { condition: service_healthy }
    restart: unless-stopped

  flower:
    profiles: ["monitoring"]           # only starts with --profile monitoring
    build:
      context: ..
      dockerfile: backend/Containerfile
    command: ["celery", "-A", "app.workers.celery_app", "flower", "--port=5555"]
    environment:
      <<: *backend-env
      FLOWER_BASIC_AUTH: ${FLOWER_USER:-admin}:${FLOWER_PASSWORD}
    ports:
      - "127.0.0.1:5555:5555"          # localhost only
    depends_on:
      redis: { condition: service_healthy }
    restart: unless-stopped

volumes:
  pgdata:
  redisdata:
  workspace:
  uploads:
```

> **Network:** Compose puts all services on one default network where they resolve each other by service name (`postgres`, `redis`, `api`). That is why the URLs above use those names instead of `localhost`.

> **Shared volume note:** `uploads` is mounted in both `api` (which receives the file) and `worker` (which reads and embeds it). Without a shared volume, the worker can't find uploaded documents.

### Environment file (`deploy/.env.example`)

```bash
POSTGRES_USER=mcp
POSTGRES_PASSWORD=change-me
POSTGRES_DB=mcp

SECRET_KEY=change-me-long-random-string     # e.g. python -c "import secrets; print(secrets.token_urlsafe(48))"

OLLAMA_BASE_URL=http://host.containers.internal:11434
DEFAULT_MODEL=llama3.1
EMBEDDING_MODEL=nomic-embed-text

FLOWER_USER=admin
FLOWER_PASSWORD=change-me
```

```bash
cp deploy/.env.example deploy/.env      # then edit the secrets
```

## Scheduled RAG updates (Celery Beat)

The `scheduler` container runs Celery Beat, which only **enqueues** tasks on a timetable — the `worker` executes them.

```python
# backend/app/workers/celery_app.py
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery("mcp", broker=settings.redis_url, backend=settings.redis_url,
                    include=["app.workers.tasks"])

celery_app.conf.timezone = "UTC"
celery_app.conf.beat_schedule = {
    "refresh-crawled-sources-nightly": {
        "task": "app.workers.tasks.refresh_crawled_sources",
        "schedule": crontab(hour=2, minute=0),
    },
    "embed-pending-chunks": {
        "task": "app.workers.tasks.embed_pending_chunks",
        "schedule": 300.0,          # every 5 minutes
    },
    "cleanup-orphan-chunks-weekly": {
        "task": "app.workers.tasks.cleanup_orphan_chunks",
        "schedule": crontab(hour=3, minute=30, day_of_week="sun"),
    },
}
```

| Scheduled task | Purpose |
|----------------|---------|
| `refresh_crawled_sources` | Re-crawl documents that came from a URL and re-embed them if the content changed |
| `embed_pending_chunks` | Pick up chunks that failed or were queued while Ollama was down |
| `cleanup_orphan_chunks` | Remove chunks whose parent document was deleted |

Make tasks **idempotent** (safe to run twice) — Celery guarantees at-least-once delivery, not exactly-once.

## Running with Podman

### One-time setup

```bash
# Linux: install podman + a compose provider
sudo dnf install podman podman-compose        # Fedora/RHEL
sudo apt install podman podman-compose        # Debian/Ubuntu

# Windows / macOS: Podman Desktop, or the CLI + a VM
podman machine init --cpus 4 --memory 8192
podman machine start
```

`podman compose` is a thin wrapper that uses either `docker-compose` or `podman-compose` — either works with the file above.

### Start everything

```bash
cd deploy

# build images and start the 6 core containers
podman compose up -d --build

# include the optional Flower dashboard
podman compose --profile monitoring up -d

# watch the status and logs
podman compose ps
podman compose logs -f api worker
```

Open the app at **http://localhost** (port 80) and Flower (if enabled) at **http://localhost:5555**.

### Everyday commands

| Task | Command |
|------|---------|
| Stop everything (keep data) | `podman compose down` |
| Stop and **delete all data** | `podman compose down -v` |
| Rebuild after code changes | `podman compose up -d --build api worker scheduler` |
| Shell inside the API container | `podman compose exec api sh` |
| Run a migration manually | `podman compose exec api alembic upgrade head` |
| Database shell | `podman compose exec postgres psql -U mcp -d mcp` |
| Scale workers (not the scheduler!) | `podman compose up -d --scale worker=3` |

### Make Ollama reachable from containers

Ollama listens on `127.0.0.1` by default, which containers can't reach through `host.containers.internal`. Bind it to all interfaces:

```bash
# Linux (systemd): add to the service environment
OLLAMA_HOST=0.0.0.0:11434
# Windows: set the user environment variable OLLAMA_HOST=0.0.0.0:11434, then restart Ollama
```

> ⚠️ Binding to `0.0.0.0` exposes Ollama on your whole network. On a server, firewall port 11434 so only the host and containers can reach it.

## Rootless Podman gotchas

| Issue | Fix |
|-------|-----|
| **SELinux (Fedora/RHEL) denies bind mounts** | Add `:Z` to bind-mounted paths (e.g. `./data:/srv/data:Z`). Named volumes don't need it. |
| **Can't publish port 80 (rootless)** | Rootless Podman can't bind ports below 1024 by default. Run once: `sudo sysctl -w net.ipv4.ip_unprivileged_port_start=80`, and persist it with `echo "net.ipv4.ip_unprivileged_port_start=80" \| sudo tee /etc/sysctl.d/99-podman-port80.conf`. On Windows/macOS, port 80 may need a rootful machine: `podman machine set --rootful`. Fallback: publish `8080:80` instead. |
| **Images pulled from the wrong registry** | Use fully qualified names (`docker.io/library/...`) as in the examples |
| **`host.containers.internal` not resolving** | Use the host's LAN IP in `OLLAMA_BASE_URL`, or `--add-host` |
| **Containers stop when you log out (Linux)** | `loginctl enable-linger $USER` |
| **Windows: slow bind mounts** | Keep source/data inside the Podman machine, or use named volumes |
| **pgvector extension missing** | Make sure the first Alembic migration runs `CREATE EXTENSION IF NOT EXISTS vector` |

## Running as a service on Linux (Quadlet)

For a server, let **systemd** manage the containers so they start on boot and restart on failure. Quadlet turns small `.container` files into systemd services.

```ini
# ~/.config/containers/systemd/mcp-api.container
[Unit]
Description=MCP platform API
After=mcp-postgres.service mcp-redis.service
Requires=mcp-postgres.service mcp-redis.service

[Container]
Image=localhost/mcp-backend:latest
Network=mcpnet.network
EnvironmentFile=%h/mcp-learning/deploy/.env
Volume=mcp-workspace.volume:/srv/workspace
Volume=mcp-uploads.volume:/srv/uploads
Exec=sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"

[Service]
Restart=always

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user start mcp-api.service
systemctl --user enable mcp-api.service
journalctl --user -u mcp-api -f
```

Create one `.container` file per service (plus `.network` and `.volume` files). Alternatively, `podman generate kube` can export a running setup to a Kubernetes YAML that `podman kube play` runs as a single pod.

## Production checklist

- [ ] Change every `change-me` secret in `.env`; keep `.env` out of git
- [ ] Put **TLS** in front of `frontend` (Caddy, Traefik, or a host-level Nginx) — don't expose plain HTTP
- [ ] Do not publish `postgres`, `redis` or `api` ports; only `frontend` is public
- [ ] Protect Flower with basic auth (above) or don't run it in production
- [ ] Back up the `pgdata` volume: `podman compose exec postgres pg_dump -U mcp mcp > backup.sql`
- [ ] Pin image versions (e.g. `postgres:16`, not `latest`) and rebuild on a schedule for security updates
- [ ] Keep the `files` MCP server sandboxed to `/srv/workspace`, and the `database` MCP server read-only
- [ ] Set CORS to your real domain if the frontend and API ever live on different origins
- [ ] Rotate logs (`--log-opt max-size=10m`) so `worker` output doesn't fill the disk
- [ ] Test the restore path, not only the backup

## Troubleshooting

| Symptom | Likely cause |
|---------|--------------|
| Chat answer arrives all at once, not streamed | Nginx buffering — check `proxy_buffering off` on `/api/` |
| `api` can't reach Ollama | `OLLAMA_HOST` not bound to `0.0.0.0`, or wrong `OLLAMA_BASE_URL` |
| Uploaded document stays `pending` forever | `worker` not running, or `uploads` volume not shared between `api` and `worker` |
| Scheduled jobs run twice | More than one `scheduler` container running |
| `api` restarts in a loop | Postgres not healthy yet, or the migration failed — read `podman compose logs api` |
| `relation ... does not exist` | Migrations did not run — `podman compose exec api alembic upgrade head` |
| MCP tools missing in the UI | MCP server subprocess failed to start inside `api` — check the API logs and that `servers/` was copied into the image |

---

## Project structure (Phase 1 — CLI test)

```
mcp-learning/
├── README.md            ← You are here
├── requirements.txt     ← Python dependencies
├── data/                ← Text files used for RAG
│   ├── about_mcp.txt
│   ├── company_faq.txt
│   ├── ennov.txt
│   └── python_tips.txt
├── workspace/           ← Sandbox: files created by tools go here
├── server.py            ← MCP server (tools, resources, prompts)
├── client.py            ← Chat host (LLM + MCP client + tool loop)
└── rag.py               ← Simple keyword-based RAG
```

---

## What to try next

1. **Add SSE/HTTP transport** — Run the MCP server as a standalone web service instead of a subprocess. Change `mcp.run(transport="sse", port=8080)` in `server.py` and connect to it from the client using `SSEServerParameters`. *(In Phase 2, the Hub can mix stdio and HTTP servers.)*

2. **Add a new API tool** — Try wrapping another free API (e.g. a dictionary API, a joke API, or a currency converter) as an MCP tool.

3. **Swap RAG for embeddings** — Replace the keyword matching in `rag.py` with real embeddings using `sentence-transformers` and cosine similarity. Compare the retrieval quality. *(Phase 2 does this with Ollama embeddings + pgvector — see [Database](#database-postgresql--pgvector).)*

4. **Add conversation memory** — Right now the conversation history grows unboundedly. Implement a sliding window or summarisation to keep it within the model's context limit. *(Phase 2 stores history in PostgreSQL, so the window can be applied when building the prompt.)*

5. **Try a different model** — Swap `llama3.1` for `qwen2.5` or `mistral` in the `MODEL` variable and see how tool-calling behaviour changes. *(Phase 2: [pick the model from the UI](#feature-switch-model-from-the-ui).)*

6. **Build a multi-server setup** — Connect the client to multiple MCP servers (e.g. one for files, one for weather, one for databases) and let the LLM choose across all of them. *(Phase 2: [MCP Hub](#feature-multi-server-mcp-hub).)*

7. **Add authentication** — Implement a simple API key check in the server to learn how MCP handles security in production setups. *(Phase 2: add login/JWT to FastAPI so each user only sees their own conversations.)*

8. **Compare models side by side** — Send one prompt to two models and diff their tool calls and answers.

9. **Per-conversation tool selection** — Let users turn individual MCP servers on/off for a chat, and measure how tool-list size affects small local models.
