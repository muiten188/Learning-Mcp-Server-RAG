# AGENTS.md — Python Backend Engineering Standards
## 1. Project Overview

This project is a production-oriented AI backend built with Python, FastAPI, PostgreSQL, pgvector, Redis, Celery, and Ollama.

The application supports:

- REST APIs and Server-Sent Events (SSE) streaming.
- AI model inference and tool calling.
- Model Context Protocol (MCP) integration.
- Retrieval-Augmented Generation (RAG).
- Document ingestion, chunking, and embedding.
- Asynchronous background job processing.
- Conversation and message persistence.
- External API and web crawler integrations.
### Technology Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12+ |
| API framework | FastAPI |
| ASGI server | Uvicorn |
| Validation | Pydantic v2 |
| Configuration | pydantic-settings |
| ORM | SQLAlchemy 2.x Async |
| Database migrations | Alembic |
| HTTP client | httpx |
| Job queue | Celery |
| Message broker | Redis |
| Database | PostgreSQL |
| Vector search | pgvector |
| AI inference | Ollama |
| Testing | pytest, pytest-asyncio, httpx |
| Linting and formatting | Ruff |
| Type checking | mypy |
| Containerization | Podman / Docker |

## 2. Architecture — Package by Feature

**Always follow Package by Feature architecture.**

Organize code by business capability rather than grouping all routers, services, models, and repositories into global folders.
### Recommended Project Structure

```text
backend/
├── AGENTS.md
├── pyproject.toml
├── alembic.ini
├── .env.example
├── migrations/
│   ├── env.py
│   └── versions/
├── src/
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── core/
│       │   ├── config.py
│       │   ├── database.py
│       │   ├── dependencies.py
│       │   ├── exceptions.py
│       │   ├── logging.py
│       │   └── security.py
│       ├── shared/
│       │   ├── schemas/
│       │   ├── utils/
│       │   └── interfaces/
│       ├── features/
│       │   ├── conversations/
│       │   │   ├── router.py
│       │   │   ├── service.py
│       │   │   ├── repository.py
│       │   │   ├── models.py
│       │   │   ├── schemas.py
│       │   │   └── dependencies.py
│       │   ├── documents/
│       │   │   ├── router.py
│       │   │   ├── service.py
│       │   │   ├── repository.py
│       │   │   ├── models.py
│       │   │   ├── schemas.py
│       │   │   └── tasks.py
│       │   ├── rag/
│       │   │   ├── service.py
│       │   │   ├── retriever.py
│       │   │   ├── chunker.py
│       │   │   └── embeddings.py
│       │   ├── agents/
│       │   │   ├── router.py
│       │   │   ├── service.py
│       │   │   ├── orchestrator.py
│       │   │   └── schemas.py
│       │   ├── mcp/
│       │   │   ├── router.py
│       │   │   ├── service.py
│       │   │   ├── client.py
│       │   │   ├── repository.py
│       │   │   ├── models.py
│       │   │   └── schemas.py
│       │   └── jobs/
│       │       ├── router.py
│       │       ├── service.py
│       │       ├── tasks.py
│       │       └── schemas.py
│       ├── integrations/
│       │   ├── ollama/
│       │   │   └── client.py
│       │   └── external_apis/
│       │       └── client.py
│       └── workers/
│           └── celery_app.py
└── tests/
    ├── conftest.py
    ├── unit/
    ├── integration/
    └── e2e/
```
### Architecture Rules

1. Each feature owns its router, service, repository, schemas, and models when needed.
2. Do not create global folders containing all application services or repositories.
3. Keep shared infrastructure in `core/`.
4. Put reusable utilities and abstractions in `shared/`.
5. Place external system adapters in `integrations/`.
6. Avoid circular imports and cross-feature access to internal implementation details.
7. Extract reusable components only when there is a real need.
8. Do not create unnecessary abstractions or excessive files.
9. Prefer explicit dependencies over global mutable state.
### Dependency Direction

```text
Router
  ↓
Service / Use Case
  ↓
Repository / Integration
  ↓
Database / External System
```

- Routers must not directly execute database queries.
- Repositories must not contain HTTP response logic.
- Services must not depend on FastAPI request objects.
- Database models must not be returned directly as public API contracts.
- Feature-to-feature communication should use clear public service interfaces.

## 3. Python Coding Standards

Follow PEP 8 and modern Python conventions.
### Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Module | snake_case | `document_service.py` |
| Function | snake_case | `get_document_by_id()` |
| Variable | snake_case | `document_id` |
| Class | PascalCase | `DocumentService` |
| Constant | UPPER_SNAKE_CASE | `MAX_CHUNK_SIZE` |
| Private member | Leading underscore | `_build_query()` |
| Async function | Verb-based snake_case | `fetch_documents()` |
### General Rules

- Always use type hints for function parameters and return types.
- Prefer `str | None` over `Optional[str]`.
- Prefer built-in generic types such as `list[str]` and `dict[str, Any]`.
- Use `Enum` or `StrEnum` for constrained values.
- Use `dataclass` for simple internal data structures where appropriate.
- Prefer early returns to deeply nested conditions.
- Avoid magic numbers and hardcoded configuration.
- Avoid wildcard imports.
- Never use mutable default arguments.
- Avoid `print()` for application logging.
- Avoid broad `except Exception` unless at a well-defined boundary with appropriate handling.
- Do not suppress type-checker or linter errors without justification.
- Do not introduce dependencies without clear benefits.
### Type Hint Example

```python
async def get_document(
    document_id: int,
) -> Document | None:
    """Retrieve a document by its identifier."""
    ...
```

## 4. Documentation Standards

**Always add a docstring when creating a new public class, method, or function.**

Use Google-style docstrings consistently.
### Function Example

```python
async def search_documents(
    query: str,
    limit: int = 10,
) -> list[Document]:
    """Search documents matching a query.

    Args:
        query: Text used to search documents.
        limit: Maximum number of documents to return.

    Returns:
        A list of matching documents.

    Raises:
        SearchError: If the search operation fails.
    """
    ...
```
### Class Example

```python
class DocumentService:
    """Manage document operations and business rules."""
```
### Documentation Rules

- Document public interfaces and non-obvious behavior.
- Explain why complex logic exists, not merely what it does.
- Include `Args`, `Returns`, and `Raises` where useful.
- Do not generate redundant comments for self-explanatory code.
- Update docstrings when behavior changes.
- Keep documentation synchronized with implementation.

## 5. FastAPI Standards
### Router Responsibilities

Routers are responsible for:

- HTTP request handling.
- Input validation through Pydantic.
- Dependency injection.
- Calling application services.
- Declaring response schemas and HTTP status codes.

Routers must remain thin.
### Example

```python
@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
async def get_document(
    document_id: int,
    service: Annotated[
        DocumentService,
        Depends(get_document_service),
    ],
) -> DocumentResponse:
    """Retrieve a document by ID."""
    return await service.get_by_id(document_id)
```
### API Rules

- Use `/api/v1` prefixes for versioned endpoints.
- Use plural resource names such as `/documents`.
- Use proper HTTP methods and status codes.
- Use `response_model` for response validation.
- Define request and response schemas separately when appropriate.
- Never expose database entities directly.
- Implement centralized exception handlers.
- Document endpoints with OpenAPI metadata.
- Validate pagination, sorting, and filtering inputs.
- Use explicit authentication and authorization dependencies.
- Keep CPU-intensive or blocking work out of request handlers.

## 6. Pydantic Standards

Use Pydantic v2.
### Rules

- Use `BaseModel` for request and response schemas.
- Use `Field` for validation constraints.
- Use `ConfigDict(from_attributes=True)` when converting ORM models.
- Use `field_validator` and `model_validator` when necessary.
- Never use deprecated Pydantic v1 APIs.
- Avoid returning sensitive fields in response schemas.
- Prefer separate Create, Update, and Response models.
### Example

```python
class DocumentCreate(BaseModel):
    """Input schema for document creation."""

    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)


class DocumentResponse(BaseModel):
    """Public document representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
```

## 7. Configuration Management

Use `pydantic-settings`.
### Rules

- Never hardcode secrets, credentials, or environment-specific URLs.
- Read configuration from environment variables or `.env`.
- Commit `.env.example`, never real secrets.
- Validate required configuration at startup.
- Use cached settings instances where appropriate.
- Separate application configuration from business logic.
### Example

```python
class Settings(BaseSettings):
    """Application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    database_url: str
    redis_url: str
    ollama_url: str
    default_model: str = "llama3.1"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
```

## 8. Async and Concurrency Standards

Use async-first programming for I/O-bound operations.
### Rules

- Use `async def` for asynchronous database, HTTP, and streaming operations.
- Never call blocking I/O inside the event loop.
- Use `httpx.AsyncClient` for asynchronous HTTP requests.
- Reuse HTTP clients through application lifespan where appropriate.
- Use explicit timeouts for external requests.
- Propagate cancellation correctly.
- Do not share `AsyncSession` instances across concurrent tasks.
- Use `asyncio.TaskGroup` for related concurrent operations when appropriate.
- Apply concurrency limits to protect external services.
- Use Celery for durable, long-running background jobs.
### Important

Do not use `async def` automatically for CPU-bound operations.

Celery tasks are normally synchronous entry points, even when the FastAPI application uses asynchronous services.

Never call `asyncio.run()` from an already running event loop.

## 9. SQLAlchemy 2.x Async Standards

Use SQLAlchemy 2.x style exclusively.
### Rules

- Use `AsyncSession`.
- Use `async_sessionmaker`.
- Use `select()` rather than legacy `session.query()`.
- Prefer `Mapped` and `mapped_column`.
- Avoid implicit lazy loading in async code.
- Use `selectinload()` or explicit eager loading when appropriate.
- Use parameterized queries.
- Manage transactions at service/use-case boundaries.
- Do not commit transactions inside every repository method.
- Keep sessions short-lived.
- Never share one session across requests or Celery tasks.
### Model Example

```python
class Document(Base):
    """Persisted document entity."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
```
### Repository Example

```python
class DocumentRepository:
    """Access document persistence operations."""

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def get_by_id(
        self,
        document_id: int,
    ) -> Document | None:
        """Find a document by ID."""
        result = await self._session.execute(
            select(Document).where(
                Document.id == document_id
            )
        )
        return result.scalar_one_or_none()
```

## 10. Alembic Migration Standards

- All schema changes require Alembic migrations.
- Never use `Base.metadata.create_all()` as the production migration strategy.
- Review autogenerated migrations before applying them.
- Never silently delete existing data.
- Prefer backward-compatible migrations for rolling deployments.
- Add indexes for frequently queried fields.
- Enable PostgreSQL extensions through migrations.
### pgvector Extension

```python
def upgrade() -> None:
    op.execute(
        "CREATE EXTENSION IF NOT EXISTS vector"
    )
```

Verify that the PostgreSQL environment supports the extension before deploying.

## 11. PostgreSQL and pgvector Standards

Use PostgreSQL for relational data and pgvector for embedding similarity search.
### Rules

- Store document metadata separately from chunks.
- Track embedding model and dimension.
- Use a consistent embedding model within a compatible vector index.
- Validate embedding dimensions before insertion.
- Choose cosine, inner-product, or L2 distance intentionally.
- Add vector indexes when dataset size and query patterns justify them.
- Apply access-control filters during retrieval.
- Use batch inserts for large ingestion workloads.
- Avoid loading large document collections into application memory.
### RAG Pipeline

```text
Document Upload
      ↓
Validation
      ↓
Celery Ingestion Job
      ↓
Text Extraction
      ↓
Chunking
      ↓
Embedding Generation
      ↓
PostgreSQL + pgvector
      ↓
Similarity Retrieval
      ↓
Context Construction
      ↓
LLM Generation
      ↓
SSE Response
```
### RAG Quality Rules

- Preserve document and chunk provenance.
- Store document ID, chunk index, and source metadata.
- Make chunk size and overlap configurable.
- Deduplicate documents where practical.
- Version embeddings when changing embedding models.
- Limit retrieved context to the model's context budget.
- Treat retrieved content as untrusted data.
- Never allow retrieved documents to override system instructions.

## 12. Celery and Redis Standards

Use Celery for durable background processing.
### Suitable Jobs

- Document ingestion.
- Text extraction.
- Embedding generation.
- Web crawling.
- Document reindexing.
- Scheduled maintenance.
### Rules

- Celery tasks must be idempotent where practical.
- Pass identifiers rather than large objects to tasks.
- Create database sessions inside worker execution.
- Configure retry policies with exponential backoff.
- Configure task time limits where appropriate.
- Use separate queues for workloads with different resource requirements.
- Persist important job status in PostgreSQL.
- Use Redis for broker and transient coordination.
- Never rely on Redis alone as the permanent source of job history.
- Acknowledge the tradeoffs of late acknowledgments and task redelivery.
- Avoid retrying permanent validation errors.
- Use a scheduler such as Celery Beat for recurring jobs.
### Task Example

```python
@celery_app.task(
    bind=True,
    autoretry_for=(TransientIngestionError,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def ingest_document(
    self,
    document_id: int,
) -> None:
    """Process a document in the background."""
    run_document_ingestion(document_id)
```

`run_document_ingestion()` must manage its own worker-safe resources, sessions, and event-loop lifecycle if async database access is required.

## 13. HTTPX and External API Standards

- Use `httpx.AsyncClient` for async integrations.
- Reuse clients when appropriate.
- Configure connection, read, and overall operation time budgets.
- Retry only safe or idempotent operations.
- Handle HTTP errors explicitly.
- Never log API keys or authorization headers.
- Validate external response payloads with Pydantic.
- Use bounded concurrency for crawlers.
- Apply SSRF protections to user-supplied URLs.
- Do not allow external requests to access internal network resources unless explicitly authorized.

## 14. Ollama and AI Integration Standards
### Rules

- Isolate Ollama communication in `integrations/ollama/`.
- Do not call Ollama directly from FastAPI routers.
- Keep model selection configurable.
- Support streaming and non-streaming generation.
- Validate tool-call payloads before execution.
- Set explicit inference timeouts and cancellation behavior.
- Track token usage when available.
- Avoid logging sensitive prompts and model responses by default.
- Limit context size and output tokens.
- Handle unavailable models and connection failures gracefully.
### Agent Orchestration

The agent orchestration layer is responsible for:

1. Receiving user input.
2. Loading conversation context.
3. Retrieving relevant RAG context.
4. Selecting available tools.
5. Validating tool arguments.
6. Executing authorized tools.
7. Processing tool results.
8. Producing a final or streamed response.
### Tool Execution Security

- Never execute arbitrary shell commands based only on LLM output.
- Maintain explicit tool allowlists.
- Validate tool arguments with Pydantic.
- Enforce permissions before executing tools.
- Apply tool execution timeouts.
- Limit recursive tool calls and iteration counts.
- Record tool execution status without exposing secrets.
- Treat tool results as untrusted input.

## 15. MCP Integration Standards

- Keep MCP client logic separate from agent orchestration.
- Discover tools using supported MCP protocol operations.
- Validate tool input schemas.
- Support connection lifecycle management.
- Handle server disconnections and timeouts.
- Do not assume all MCP servers are trusted.
- Require authorization for sensitive tool operations.
- Avoid exposing credentials to MCP servers unnecessarily.
- Log tool name, execution duration, and outcome.
- Never allow tool descriptions to override application security rules.

## 16. SSE Streaming Standards

Use Server-Sent Events for server-to-client AI response streaming.
### Rules

- Use `text/event-stream`.
- Emit structured event types.
- Keep event payloads JSON-serializable.
- Handle client disconnects.
- Stop unnecessary upstream inference when clients disconnect.
- Avoid buffering the entire response before streaming.
- Do not perform blocking work inside streaming generators.
- Use keepalive comments where required by proxies.
- Configure reverse proxies to avoid unwanted buffering.
- Distinguish transport failures from model-generation failures.
### Suggested Event Types

```text
event: message_start
data: {"message_id": "123"}

event: token
data: {"content": "Hello"}

event: tool_start
data: {"tool": "search_documents"}

event: tool_end
data: {"tool": "search_documents"}

event: message_end
data: {"status": "completed"}
```

Use JSON serialization for payload construction rather than manual string concatenation.

## 17. Error Handling Standards
### Rules

- Create domain-specific exception classes.
- Map domain exceptions to HTTP errors at the API boundary.
- Do not expose database errors or internal stack traces to clients.
- Preserve original exception context with `raise ... from exc`.
- Log unexpected errors with stack traces.
- Use consistent API error response schemas.
- Do not silently swallow exceptions.
- Distinguish validation, authorization, infrastructure, and business errors.

## 18. Logging and Observability

Use Python's `logging` module with structured logging where practical.
### Rules

- Use appropriate log levels.
- Include request IDs and job IDs.
- Record important state transitions.
- Measure external API and database operation durations.
- Never log passwords, tokens, secrets, or sensitive document content.
- Avoid duplicate exception logging across layers.
- Use UTC timestamps.
- Add health and readiness endpoints.
- Ensure observability works across API and Celery processes.

## 19. Security Standards

- Validate all external input.
- Use parameterized SQL queries.
- Apply authentication and authorization at API boundaries.
- Enforce document ownership and tenant isolation.
- Limit file upload sizes and allowed formats.
- Sanitize filenames and avoid path traversal.
- Never trust file extensions alone.
- Protect against SSRF in crawler and URL-fetching features.
- Keep secrets out of Git.
- Restrict MCP tool execution permissions.
- Apply rate limiting where appropriate.
- Use least-privilege database accounts.
- Treat LLM output and RAG content as untrusted.
- Avoid exposing internal errors or infrastructure details.

## 20. Testing Standards

Use pytest and pytest-asyncio.
### Test Categories

- Unit tests for business logic.
- Integration tests for repositories and PostgreSQL.
- API tests using httpx ASGI transport.
- Celery task tests.
- RAG retrieval and chunking tests.
- MCP tool validation tests.
- SSE streaming tests.
### Rules

- Add tests for new business logic.
- Add regression tests when fixing bugs.
- Test both successful and failure paths.
- Mock external APIs and Ollama in unit tests.
- Use a real PostgreSQL/pgvector instance for database integration tests.
- Avoid relying exclusively on SQLite for PostgreSQL-specific behavior.
- Do not require live external services for unit tests.
- Keep tests deterministic.
- Test transaction rollback and resource cleanup.
- Test async cancellation where relevant.
### Naming

```text
test_document_service.py
test_document_repository.py
test_rag_retriever.py
test_agent_orchestrator.py
test_mcp_client.py
```

## 21. Code Quality Standards

Use Ruff for formatting and linting, and mypy for static type checking.
### Commands

```bash
ruff check .
ruff format --check .
mypy app
pytest
```
### Rules

- Keep functions focused.
- Prefer composition over inheritance.
- Follow SOLID principles where they improve maintainability.
- Avoid premature abstraction.
- Avoid excessive nesting.
- Remove unused imports and dead code.
- Prefer standard-library solutions when suitable.
- Do not optimize without a measurable reason.
- Do not modify unrelated code during a focused task.

## 22. Containerization Standards

The application must support Podman and Docker.
### Recommended Services

```text
frontend
api
worker
beat
postgres
redis
ollama
```
### Rules

- Use environment variables for service configuration.
- Do not store secrets in container images.
- Use health checks for critical services.
- Persist PostgreSQL and Ollama data in volumes.
- Run application containers as non-root where practical.
- Use multi-stage builds where beneficial.
- Keep images small and reproducible.
- Do not depend on localhost for communication between separate containers.
- Use service DNS names inside container networks.
- Support graceful shutdown of API and worker processes.
- Run database migrations as an explicit deployment step.

## 23. Agent Code Generation Rules

These rules apply whenever an AI coding agent creates or modifies code.
### Before Writing Code

1. Inspect existing architecture and conventions.
2. Identify the correct feature package.
3. Reuse existing implementations where possible.
4. Understand dependencies and potential side effects.
5. Prefer the smallest maintainable change.
### When Creating a New Feature

- Follow Package by Feature.
- Create only the files actually required.
- Separate router, service, repository, schemas, and models when their responsibilities exist.
- Add dependency injection where appropriate.
- Add type hints.
- Add Google-style docstrings to public classes and functions.
- Add validation.
- Add error handling.
- Add tests for important behavior.
- Add migrations when database schemas change.
### When Modifying Existing Code

- Preserve backward compatibility unless explicitly instructed otherwise.
- Do not refactor unrelated modules.
- Do not rename public APIs without a reason.
- Update relevant tests.
- Update documentation when behavior changes.
- Do not change database schemas without a migration.
- Do not add new dependencies without justification.
### When Fixing Bugs

1. Identify the root cause.
2. Implement the smallest correct fix.
3. Add a regression test.
4. Verify existing behavior.
5. Explain the cause and resolution.
### When Refactoring

- Preserve existing functionality.
- Improve readability and maintainability.
- Avoid unnecessary abstractions.
- Keep public contracts stable.
- Prefer incremental changes.
### Prohibited Patterns

- Business logic inside routers.
- Direct database access inside API handlers.
- Blocking I/O inside async request handlers.
- Shared mutable global database sessions.
- Hardcoded secrets or environment URLs.
- Bare `except:` clauses.
- Silent exception suppression.
- Unvalidated tool execution.
- Returning ORM models directly from API endpoints.
- Running heavy ingestion jobs inside FastAPI request handlers.
- Unnecessary new dependencies.
- Large unrelated refactors.

## 24. Agent Response Standards

When generating or modifying code, the coding agent should:

1. Briefly explain the intended implementation.
2. Follow existing project conventions.
3. Show or apply complete, working changes.
4. Identify newly added or modified files.
5. Explain significant design decisions.
6. Report tests and validation performed.
7. Clearly state any tests that were not executed.
8. Mention important risks or compatibility considerations.

Do not claim that tests passed unless they were actually executed.

Do not invent APIs, library methods, or configuration options.

If requirements are ambiguous and materially affect correctness, ask for clarification before making destructive or difficult-to-reverse changes.

## 25. Definition of Done

A task is complete when:

- The requested behavior is implemented.
- Code follows Package by Feature.
- Type hints are present.
- Public APIs have appropriate docstrings.
- Input validation is implemented.
- Errors are handled correctly.
- Async and database resource lifecycles are safe.
- Relevant tests are added or updated.
- Migrations are included when required.
- Formatting and linting are checked.
- Security and compatibility concerns are addressed.
- No unrelated changes are introduced.
- Any unverified assumptions or checks are clearly reported.

**Primary engineering principle: Build simple, maintainable, secure, and testable Python services. Prefer correctness and clear architecture over unnecessary complexity.**
