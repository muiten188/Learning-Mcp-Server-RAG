# MCP Platform frontend

This is the Angular 22 UI for the MCP Platform. It provides streamed chat with visible tool calls and retrieved document names, conversation history, document upload and status, a model picker, and MCP server status. The [platform README](../README.md) covers the backend and the wider architecture.

## Tech stack

| Layer              | Technology                            | Purpose                                                            |
| ------------------ | ------------------------------------- | ------------------------------------------------------------------ |
| Frontend framework | Angular 22                            | SPA, signals-based state, standalone components                    |
| AI chat state      | TanStack AI Angular                   | Streaming chat state with an adapter for the backend SSE format    |
| UI components      | Spartan UI brain                      | Accessible behavior for interactive controls                       |
| Styling            | Component CSS                         | Separate stylesheets for Angular components                        |
| Icons              | @lucide/angular                       | Consistent icon set                                                |
| Markdown           | ngx-markdown                          | Render assistant answers, including code blocks, tables, and lists |

`ChatStore` uses TanStack AI Angular for chat state. Its custom stream connection converts the backend's SSE events into TanStack AI stream chunks. Component CSS files style Angular views. Spartan UI brain supplies button, input, model select, and collapsible tool result behavior; Lucide supplies icons, and ngx-markdown renders assistant messages. The root README also mentions Zard UI as an alternative; this app uses Spartan UI.

## Run locally

Use Node.js 22.22.3+, 24.15+, or 26+. Start the platform backend on `http://localhost:8000` using the [platform setup guide](../IMPLEMENTATION.md), then run:

```powershell
cd frontend
npm ci
npm start
```

Open `http://localhost:4200`. The Angular development server uses [proxy.conf.json](proxy.conf.json) to forward `/api` requests to the backend. Without a running backend, the UI loads but API requests show errors.

| Command          | Purpose                                                     |
| ---------------- | ----------------------------------------------------------- |
| `npm start`      | Start the development server on port 4200                   |
| `npm run build`  | Build the production app into `dist/frontend/browser`       |
| `npm run format` | Format Angular source and configuration files with Prettier |

## App structure

```text
frontend/
├── public/
├── src/
│   ├── app/
│   │   ├── core/
│   │   │   ├── auth/
│   │   │   ├── config/                 # API base URL and endpoint paths
│   │   │   ├── http/
│   │   │   ├── layout/                 # App shell, header, and sidebar
│   │   │   └── mcp/                    # MCP status shared by header and settings
│   │   ├── features/
│   │   │   ├── chat/
│   │   │   │   ├── components/         # Chat controls, messages, and sidebar
│   │   │   │   ├── directives/
│   │   │   │   ├── models/
│   │   │   │   ├── pages/chat-page/    # TypeScript, HTML, and CSS
│   │   │   │   ├── pipes/
│   │   │   │   ├── services/           # Chat API and SSE stream
│   │   │   │   └── state/chat.store.ts
│   │   │   ├── documents/
│   │   │   │   ├── models/
│   │   │   │   ├── pages/documents-page/
│   │   │   │   └── services/
│   │   │   ├── settings/pages/settings-page/
│   │   │   ├── jobs/pages/jobs-page/
│   │   │   ├── knowledge-base/        # Redirects to documents
│   │   │   └── authentication/        # Placeholder
│   │   ├── app.config.ts
│   │   ├── app.routes.ts
│   │   └── app.ts
│   ├── environments/
│   ├── main.ts
│   └── styles.css                   # Global base styles
├── angular.json
├── package.json
├── Containerfile
└── README.md
```

The app layout owns the navigation shell. The chat feature owns its header controls, conversation sidebar, messages, composer, API service, stream reader, and TanStack-backed `ChatStore`. Documents owns its model, API service, and page. MCP status is shared by the header and settings page, so its service lives in `core/mcp`. Each component keeps its styles in a sibling CSS file; `styles.css` holds global base styles. Authentication is not enabled.

| Route             | Current screen                                                                |
| ----------------- | ----------------------------------------------------------------------------- |
| `/`               | Chat, conversation history, model picker, tool results, and stream debug view |
| `/documents`      | Upload text or Markdown documents and view ingestion status                   |
| `/knowledge-base` | Redirects to `/documents`                                                     |
| `/settings`       | MCP server status and available tools                                         |
| `/jobs`           | Placeholder page                                                              |

## API and streaming

The frontend calls relative `/api` paths defined in `core/config/api.paths.ts`. `ChatApiService` handles conversations and models, `DocumentsService` handles uploads and status, and `McpServersService` handles MCP connection status. `ChatStreamService` posts to `/api/chat` and reads server-sent events from the response stream. `ChatStore` converts tokens and completion events to TanStack AI stream chunks; retrieval and tool events remain in Angular signals for the chat UI. The backend endpoint list and event format are documented in the [platform README](../README.md#api-endpoints).

The `chat-markdown` component renders assistant content with ngx-markdown.

## Container build

[Containerfile](Containerfile) builds the Angular app with Node and serves it with Nginx. Build from this directory:

```powershell
docker build -f Containerfile -t mcp-platform-frontend .
```

[nginx.conf](nginx.conf) serves Angular routes with an `index.html` fallback and proxies `/api/` to `http://api:8000`. Run the container on a network where the backend resolves as `api`; API proxy buffering is disabled so chat tokens can stream. The platform's current `compose.yaml` starts PostgreSQL and Redis only, so it does not launch this frontend container.
