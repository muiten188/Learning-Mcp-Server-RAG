# Independently deployed MCP servers

Each directory contains one Streamable HTTP MCP server and its own Python dependencies. [`Containerfile`](Containerfile) builds an image for exactly one server using the `SERVICE` and `PORT` build arguments. The five services are `files`, `weather`, `database`, `documents`, and `web`. Their default ports are 8101, 8102, 8103, 8104, and 8105 respectively, both on the host and inside their containers. FastAPI uses port 8000.

From `mcp-platform`, run `docker compose up -d --build` (or the equivalent Podman Compose command). The API connects to service names on the Compose network using [`mcp_servers.container.json`](../mcp_servers.container.json). A backend running on the host uses [`mcp_servers.json`](../mcp_servers.json) and loopback ports 8101–8105. Only the backend calls `/mcp`; the frontend never connects to an MCP server directly.

| Server | Dependencies and access |
|---|---|
| `files` | MCP SDK; read/write only the shared `workspace` mount |
| `weather` | MCP SDK and Open-Meteo over HTTP; current conditions and forecast |
| `database` | MCP SDK and PostgreSQL; fixed read-only SQLAlchemy count queries |
| `documents` | MCP SDK and the backend document API; list/status/queue workflows |
| `web` | MCP SDK and HTTP client; reads one requested page |

To add a server, create `<name>/server.py` and `<name>/requirements.txt`, choose a unique default port and expose Streamable HTTP at `/mcp`, add a Compose service using the shared Containerfile with `SERVICE` and `PORT`, then add its URL to both registry files. Tool names are qualified by the hub as `<server>__<tool>`, avoiding collisions. Each server can be deployed and scaled without rebuilding the others. Keep service URLs reachable only on trusted networks; the Compose file publishes debug ports on host loopback.

## Develop and debug in IntelliJ IDEA

Open the repository in IntelliJ IDEA. Install/enable Python support and select `mcp-platform/backend/.venv/Scripts/python.exe` as the interpreter; the backend `requirement.txt` includes the dependencies used by these servers. If the virtual environment does not exist, create it from `mcp-platform/backend` and install `requirement.txt` first.

For a complete containerized development run, open IntelliJ's terminal in `mcp-platform` and run `docker compose up -d --build`. You can also right-click `compose.yaml` and run it as a Docker Compose configuration. Use `podman compose up -d --build` in the terminal when using Podman. The five MCP endpoints are published on `http://127.0.0.1:8101/mcp` through `:8105/mcp`; the API uses service names inside Compose. Build or restart one server with `docker compose up -d --build mcp-files`, substituting its service name.

To set breakpoints in a locally running MCP server, stop that server's Compose service first so its published port is free. In **Run > Edit Configurations**, add a **Python** configuration for each script below. Set **Script path** to the listed file, **Working directory** to `mcp-platform`, and **Python interpreter** to the backend virtual environment. Set the listed environment variables and click **Debug**. The servers use their distinct ports by default. The optional per-server variables `MCP_FILES_PORT`, `MCP_WEATHER_PORT`, `MCP_DATABASE_PORT`, `MCP_DOCUMENTS_PORT`, and `MCP_WEB_PORT` are listed in [`.env.example`](../.env.example); `MCP_PORT` remains a fallback override for one process.

If you copy `.env.example` to `mcp-platform/.env`, add that file to each IntelliJ Python configuration's **Environment variables** field, or enter the variables directly. Python does not load `.env` into `os.environ` automatically. Compose uses the fixed ports in `compose.yaml`; if you change a server port, also update its Compose mapping and URL in both registry files.

| Configuration | Script path under `mcp-platform` | Environment variables |
|---|---|---|
| Files MCP | `mcp_servers/files/server.py` | `MCP_WORKSPACE=<absolute path to mcp-platform/workspace>` |
| Weather MCP | `mcp_servers/weather/server.py` | None |
| Database MCP | `mcp_servers/database/server.py` | `DATABASE_URL=postgresql+asyncpg://mcp:mcp@127.0.0.1:5432/mcp` |
| Documents MCP | `mcp_servers/documents/server.py` | `BACKEND_API_URL=http://127.0.0.1:8000` (already the default) |
| Web MCP | `mcp_servers/web/server.py` | None |

For a fully host-run debug session, start only supporting containers with `docker compose up -d postgres redis ollama`, then run the API and worker on the host as described in the [backend guide](../backend/README.md). Run the MCP configurations above in IntelliJ. The host-run API reads [`mcp_servers.json`](../mcp_servers.json), which already points to ports 8101–8105. Start the database migration before calling database or document tools. If only one server is under debug, keep the other four MCP services in Compose and stop just the conflicting service; run the API on the host so its registry can reach both the Compose-published ports and the local debug process.
