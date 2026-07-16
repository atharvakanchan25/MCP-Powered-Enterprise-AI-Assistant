<img width="1536" height="1024" alt="Workflow" src="https://github.com/user-attachments/assets/75b9f8c8-1dd1-478f-a861-36e4bdafe1dd" />

# MCP Enterprise AI Assistant

An AI-powered assistant that doesn't just chat — it actually *does things*. Ask it a question and it'll search the web, query your database, pull from your uploaded documents, send a Slack message, shoot an email, read a Google Sheet — all in one go, without you having to touch any of those tools yourself.

---

## What is this?

Most AI assistants answer questions. This one executes work.

It's built around the **Model Context Protocol (MCP)** — a standard way for AI agents to use external tools. You give it a query, and a multi-step LangGraph agent pipeline kicks in: it plans what to do, picks the right tools, runs them, searches your knowledge base, and synthesizes everything into a clear, cited answer.

Think of it as an AI coworker that has access to your stack.

---

## What it can do

- **Chat with memory** — it remembers past interactions and builds context about you over time
- **RAG over your documents** — upload PDFs, Word docs, PowerPoints, Excel files, or plain text and ask questions about them
- **Vision** — upload images and ask questions about what's in them (powered by GPT-4o)
- **Web search** — fetches live information from Google via SerpAPI
- **Slack** — send messages to channels or read recent messages
- **Email** — compose and send emails via SMTP
- **Google Sheets** — read data from or append rows to spreadsheets
- **PostgreSQL** — run safe read-only SELECT queries against your database
- **Report generation** — produces structured PDF reports from agent outputs
- **Admin panel** — manage users, monitor token usage, view audit logs

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER / BROWSER                                 │
│                         http://localhost:3000                               │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │  HTTP / REST
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        NEXT.JS 14 FRONTEND                                  │
│                                                                             │
│   ┌──────────┐  ┌───────────┐  ┌────────┐  ┌────────┐  ┌───────┐  ┌─────┐ │
│   │   Chat   │  │ Documents │  │ Vision │  │ Memory │  │ Admin │  │ ... │ │
│   └──────────┘  └───────────┘  └────────┘  └────────┘  └───────┘  └─────┘ │
│                                                                             │
│   Zustand (state)  ·  Axios (API client)  ·  Tailwind CSS                  │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │  HTTP/JSON  (JWT Bearer token)
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FASTAPI BACKEND  :8000                              │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Middleware Layer                                                    │   │
│  │  CORSMiddleware  ·  AuditMiddleware (request logging + X-Request-ID)│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  API Routes  /api/v1/                                                │   │
│  │                                                                      │   │
│  │  POST /auth/register    POST /auth/login    POST /auth/refresh       │   │
│  │  POST /agent/query      GET  /conversations  GET /conversations/{id} │   │
│  │  POST /documents/upload GET  /documents      DELETE /documents/{id}  │   │
│  │  POST /vision/analyze   GET  /memory         DELETE /memory/{id}     │   │
│  │  GET  /admin/users      GET  /admin/logs     GET  /admin/stats       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  GET /health   ·   GET /metrics (Prometheus)                                │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
          ┌──────────────┐  ┌──────────┐  ┌──────────────┐
          │  Agent       │  │  RAG     │  │  Auth /      │
          │  Orchestrator│  │  Service │  │  User Service│
          └──────┬───────┘  └────┬─────┘  └──────────────┘
                 │               │
                 ▼               ▼
```

### LangGraph Agent Pipeline

Every query to `POST /api/v1/agent/query` flows through this 6-node pipeline:

```
                        ┌─────────────────────────────────────────────────────┐
                        │              AgentState (shared context)            │
                        │  query · user_id · conversation_id · memories       │
                        │  plan · selected_tools · tool_results · rag_context │
                        │  citations · final_answer · token_usage · errors    │
                        └─────────────────────────────────────────────────────┘

  ┌───────┐
  │ START │
  └───┬───┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. PLANNER NODE                                                            │
│                                                                             │
│  • Receives: user query + available MCP tools + existing memories           │
│  • Calls GPT-4o with JSON mode                                              │
│  • Outputs: step-by-step plan, list of selected_tools, reasoning[]          │
│                                                                             │
│  Example output:                                                            │
│    plan: "1. Search web for X  2. Query DB for Y  3. Send Slack summary"   │
│    selected_tools: ["web_search", "postgresql", "slack"]                    │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  2. RESEARCH NODE                                                           │
│                                                                             │
│  • Checks if "web_search" is in selected_tools                              │
│  • If yes → calls MCPClient → WebSearchTool → SerpAPI → Google results     │
│  • If no  → passes through immediately (no-op)                              │
│  • Appends result to tool_results[]                                         │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  3. TOOL NODE                                                               │
│                                                                             │
│  • Iterates over selected_tools, skipping "web_search" and "rag_query"     │
│  • For each tool: calls GPT-4o to extract JSON arguments from the plan     │
│  • Dispatches to MCPClient → ToolRegistry → concrete MCPTool.execute()     │
│                                                                             │
│  Available MCP Tools:                                                       │
│  ┌─────────────────┬────────────────────────────────────────────────────┐  │
│  │ web_search      │ Google search via SerpAPI                          │  │
│  │ postgresql      │ Read-only SELECT queries on your Postgres DB       │  │
│  │ email           │ Send emails via SMTP (Gmail, etc.)                 │  │
│  │ google_sheets   │ Read from / append rows to Google Sheets           │  │
│  │ slack           │ Post messages or read channel history              │  │
│  └─────────────────┴────────────────────────────────────────────────────┘  │
│                                                                             │
│  Each tool extends MCPTool (abstract base):                                 │
│    name · description · parameters (JSON Schema) · execute() · safe_execute│
│  safe_execute() wraps execute() with error handling + duration tracking     │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  4. RAG NODE                                                                │
│                                                                             │
│  • Embeds the user query with text-embedding-3-small (OpenAI)              │
│  • Runs semantic_search() against Qdrant vector store                      │
│  • Returns top-K chunks: filename · page · score · excerpt                 │
│  • Populates rag_context[] and citations[] in state                        │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  5. MEMORY NODE                                                             │
│                                                                             │
│  • Surfaces existing user memories loaded at pipeline start                │
│  • Actual memory writes happen post-pipeline in the orchestrator           │
│  • MemoryService stores key/value facts per user, typed by:                │
│      AGENT · CONVERSATION · USER_PROFILE                                   │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  6. REPORT NODE                                                             │
│                                                                             │
│  • Collects: plan + tool_results + rag_context + reasoning                 │
│  • Calls GPT-4o to synthesize a final structured answer with citations     │
│  • Writes final_answer and token_usage to state                            │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
                               ┌───────┐
                               │  END  │
                               └───────┘

  Post-pipeline (Orchestrator):
  • Persists assistant Message + ToolCall traces to PostgreSQL
  • Stores query as a CONVERSATION memory via MemoryService
  • Records token usage via MonitoringService → request_logs table
```

### RAG Pipeline (Document Ingestion)

```
  User uploads file (PDF / DOCX / PPTX / XLSX / TXT / image)
         │
         ▼
  ┌─────────────────┐
  │  File Parser    │  pypdf · python-docx · python-pptx · openpyxl
  │  (app/rag/      │  → extracts raw text + page metadata
  │   parsers/)     │
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  Chunker        │  LangChain RecursiveCharacterTextSplitter
  │  (chunker.py)   │  chunk_size=512, overlap=64 tokens
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  Embedder       │  OpenAI text-embedding-3-small → 1536-dim vectors
  │  (embedder.py)  │
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  Qdrant         │  Upserts vectors with payload:
  │  Vector Store   │  { filename, page, chunk_index, excerpt, user_id }
  └─────────────────┘

  At query time:
  query → embed → Qdrant cosine search → top-K chunks → rag_context
```

### Data Layer

```
  ┌──────────────────────────────────────────────────────────────────┐
  │                        PostgreSQL                                │
  │                                                                  │
  │  users          id · email · username · hashed_password · role  │
  │                 is_active · is_verified                          │
  │                                                                  │
  │  conversations  id · title · status · user_id                   │
  │                                                                  │
  │  messages       id · role · content · token_count · conv_id     │
  │                 role ∈ {user, assistant, system, tool}           │
  │                                                                  │
  │  tool_calls     id · tool_name · input_args · output · error    │
  │                 duration_ms · message_id                         │
  │                                                                  │
  │  memories       id · key · value · relevance_score              │
  │                 user_id · conversation_id                        │
  │                                                                  │
  │  documents      id · filename · content_type · status           │
  │                 chunk_count · storage_path · owner_id            │
  │                                                                  │
  │  audit_logs     id · action · resource_type · ip_address        │
  │                 user_id · meta                                   │
  │                                                                  │
  │  request_logs   id · path · method · status_code · duration_ms  │
  │                 prompt_tokens · completion_tokens · user_id      │
  └──────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────────────┐
  │                          Redis                                   │
  │  • Response caching (TTL = 300s by default)                      │
  │  • Session / token management                                    │
  └──────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────────────┐
  │                          Qdrant                                  │
  │  • Collection: mcp_documents                                     │
  │  • 1536-dim vectors (text-embedding-3-small)                     │
  │  • Cosine similarity search                                      │
  │  • Payload: filename · page · chunk_index · excerpt · user_id   │
  └──────────────────────────────────────────────────────────────────┘
```

### MCP Tool Layer

```
  MCPTool (abstract base)
  ├── name: str
  ├── description: str
  ├── parameters: dict  (JSON Schema — exposed to LLM for arg extraction)
  ├── execute(**kwargs) → ToolResult          ← implement this
  └── safe_execute(**kwargs) → ToolResult     ← wraps execute() with try/except + timing

  ToolResult
  └── tool_name · success · output · error · duration_ms · metadata

  ToolRegistry (singleton)
  ├── register(tool)
  ├── get(name) → MCPTool
  ├── all_tools() → list[MCPTool]
  ├── discover(query) → keyword match on name/description
  └── to_openai_functions() → OpenAI function-calling schema list

  MCPClient
  ├── list_tools() → OpenAI function schemas (fed to planner LLM)
  ├── discover(query) → tool name list
  └── execute(tool_name, **kwargs) → ToolResult
```

### Security & Observability

```
  Auth
  ├── JWT access tokens (HS256, 30 min expiry)
  ├── Refresh tokens (7 day expiry)
  ├── Passwords hashed with bcrypt (passlib)
  └── Role-based access: admin · manager · user · viewer

  Middleware
  ├── CORSMiddleware — configurable allowed origins
  └── AuditMiddleware — logs every request: method · path · status · duration
                        injects X-Request-ID and X-Response-Time headers

  Monitoring
  ├── Prometheus metrics exposed at GET /metrics
  ├── prometheus-fastapi-instrumentator — auto-instruments all routes
  └── MonitoringService — writes per-request token usage to request_logs

  Logging
  └── structlog — structured JSON logs with context binding
```

### Full Component Map

```
mcp-assistant/
│
├── app/
│   ├── main.py                  FastAPI app factory, lifespan, middleware setup
│   │
│   ├── api/v1/                  HTTP route handlers
│   │   ├── auth.py              register · login · refresh · me
│   │   ├── agent.py             POST /query → run_agent()
│   │   ├── conversations.py     CRUD for conversations + messages
│   │   ├── documents.py         upload · list · delete · status
│   │   ├── vision.py            image upload → GPT-4o vision analysis
│   │   └── admin.py             users · audit logs · token stats
│   │
│   ├── agents/
│   │   ├── state.py             AgentState TypedDict (shared pipeline context)
│   │   ├── nodes.py             6 async node functions (planner→report)
│   │   └── workflow.py          LangGraph StateGraph wiring + compiled singleton
│   │
│   ├── mcp/
│   │   ├── base.py              MCPTool ABC + ToolResult dataclass
│   │   ├── registry.py          ToolRegistry singleton
│   │   ├── client.py            MCPClient (list/discover/execute)
│   │   ├── __init__.py          register_all_tools() called at startup
│   │   └── tools/
│   │       ├── web_search.py    SerpAPI Google search
│   │       ├── postgresql.py    Read-only SQL execution
│   │       ├── email_tool.py    SMTP email sending
│   │       ├── google_sheets.py Sheets read/append via service account
│   │       └── slack.py         Slack post/read via Bot Token
│   │
│   ├── rag/
│   │   ├── parsers/             PDF · DOCX · PPTX · XLSX · TXT parsers
│   │   ├── chunker.py           RecursiveCharacterTextSplitter wrapper
│   │   ├── embedder.py          OpenAI text-embedding-3-small
│   │   ├── vector_store.py      Qdrant upsert/search
│   │   └── storage.py           Local file storage for uploads
│   │
│   ├── services/
│   │   ├── agent/
│   │   │   ├── orchestrator.py  run_agent(): loads memory → invokes workflow → persists results
│   │   │   └── memory.py        MemoryService: store/recall/get_user_profile
│   │   ├── rag/
│   │   │   ├── ingestion.py     Full doc ingestion pipeline (parse→chunk→embed→store)
│   │   │   ├── query.py         semantic_search() used by rag_node
│   │   │   └── vision.py        GPT-4o image analysis
│   │   ├── cache/
│   │   │   └── redis_cache.py   get/set/delete with TTL
│   │   ├── reports/
│   │   │   └── generator.py     ReportLab PDF generation from agent output
│   │   ├── auth.py              JWT creation/verification, user auth logic
│   │   ├── audit.py             AuditLog writes
│   │   └── monitoring.py        MonitoringService: record_request() → request_logs
│   │
│   ├── models/
│   │   ├── user.py              User · UserRole
│   │   ├── conversation.py      Conversation · Message · MessageRole
│   │   └── domain.py            Document · Memory · ToolCall · AuditLog · RequestLog
│   │
│   ├── core/
│   │   ├── config.py            Pydantic Settings (reads .env)
│   │   ├── security.py          JWT helpers, password hashing
│   │   ├── logging.py           structlog setup
│   │   └── exceptions.py        Custom exception classes + FastAPI handlers
│   │
│   ├── db/
│   │   ├── session.py           SQLAlchemy async engine + session factory
│   │   └── redis.py             Redis async client
│   │
│   ├── middleware/
│   │   └── audit.py             AuditMiddleware (request/response logging)
│   │
│   └── repositories/
│       ├── base.py              Generic async CRUD repository
│       └── user.py              UserRepository (email/username lookups)
│
├── frontend/src/
│   ├── app/
│   │   ├── chat/page.tsx        Chat interface with message history
│   │   ├── documents/page.tsx   File upload + document list
│   │   ├── vision/page.tsx      Image upload + GPT-4o analysis
│   │   ├── memory/page.tsx      View + delete stored memories
│   │   ├── settings/page.tsx    User profile + API key config
│   │   └── admin/page.tsx       User management + audit logs + token stats
│   ├── components/Sidebar.tsx   Navigation sidebar
│   ├── hooks/useAuth.ts         Auth state + JWT refresh logic
│   └── lib/api.ts               Axios instance with auth interceptors
│
├── alembic/                     Database migration scripts
├── tests/                       pytest suite (auth · RAG · parsers · vision)
├── docker-compose.yml           api · postgres · redis · qdrant
└── Dockerfile                   Multi-stage Python image
```

---

## Tech stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) — async Python API
- [LangGraph](https://langchain-ai.github.io/langgraph/) — multi-node agent workflow (planner → research → tools → RAG → memory → report)
- [LangChain](https://www.langchain.com/) + [OpenAI](https://openai.com/) — LLM calls and embeddings (GPT-4o, text-embedding-3-small)
- [Qdrant](https://qdrant.tech/) — vector store for semantic search
- [PostgreSQL](https://www.postgresql.org/) — relational storage for users, conversations, memories, tool call traces
- [Redis](https://redis.io/) — caching and session management
- [Alembic](https://alembic.sqlalchemy.org/) — database migrations
- [ReportLab](https://www.reportlab.com/) — PDF generation
- [Prometheus](https://prometheus.io/) — metrics and monitoring

**Frontend**
- [Next.js 14](https://nextjs.org/) (App Router) + TypeScript
- [Tailwind CSS](https://tailwindcss.com/)
- Pages: Chat, Documents, Memory, Vision, Settings, Admin

---

## Project structure

```
mcp-assistant/
├── app/
│   ├── agents/          # LangGraph nodes, state, workflow
│   ├── api/v1/          # FastAPI routes (auth, agent, documents, vision, conversations, admin)
│   ├── core/            # Config, security, logging, exceptions
│   ├── mcp/             # MCP tool registry + 5 tool implementations
│   ├── rag/             # Document parsers, chunker, embedder, vector store
│   ├── services/        # Agent orchestrator, memory, RAG, reports, monitoring
│   ├── models/          # SQLAlchemy ORM models
│   └── main.py
├── frontend/            # Next.js app
├── tests/               # pytest test suite
├── alembic/             # DB migrations
├── docker-compose.yml
└── Dockerfile
```

---

## Getting started

### Prerequisites

- Docker & Docker Compose
- An OpenAI API key
- (Optional) SerpAPI key, Slack bot token, SMTP credentials, Google service account

### 1. Clone and configure

```bash
git clone https://github.com/your-username/mcp-assistant.git
cd mcp-assistant
cp .env.example .env
```

Open `.env` and fill in at minimum:

```env
SECRET_KEY=your-random-secret-key-at-least-32-chars
OPENAI_API_KEY=sk-your-openai-key-here
```

Everything else has sane defaults for local dev. Tool integrations (Slack, email, etc.) are all optional — the agent gracefully skips tools that aren't configured.

### 2. Start the stack

```bash
docker compose up --build
```

This spins up 4 services: the FastAPI backend, PostgreSQL, Redis, and Qdrant.

### 3. Run migrations

```bash
docker compose exec api alembic upgrade head
```

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

### 5. Open it

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API docs | http://localhost:8000/docs |
| Metrics | http://localhost:8000/metrics |
| Qdrant UI | http://localhost:6333/dashboard |

---

## Running tests

```bash
pytest tests/ -v
```

The CI pipeline (GitHub Actions) runs tests against real Postgres and Redis services, then builds and pushes a Docker image on merge to `main`.

---

## Environment variables

See [`.env.example`](.env.example) for the full list. Key ones:

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | Required. Powers all LLM calls and embeddings |
| `SECRET_KEY` | Required. JWT signing secret |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `QDRANT_HOST` | Qdrant host (default: `qdrant`) |
| `SERPAPI_KEY` | Enables web search tool |
| `SLACK_BOT_TOKEN` | Enables Slack tool |
| `SMTP_HOST/USER/PASSWORD` | Enables email tool |
| `GOOGLE_CREDENTIALS_JSON` | Path to service account JSON for Google Sheets |

---

## Why I built this

I wanted to explore what a real production-grade MCP agent system looks like end-to-end — not a tutorial, but something with proper auth, a real database, a vector store, document ingestion, multiple tool integrations, a frontend, tests, CI, and Docker. This is that thing.

It's also a reference architecture for anyone building enterprise AI assistants: the separation between the MCP tool layer, the LangGraph agent workflow, the RAG pipeline, and the API is intentional and meant to be extended cleanly.

---

## Adding new tools

1. Create a new file in `app/mcp/tools/` extending `MCPTool`
2. Implement `name`, `description`, `parameters`, and `execute()`
3. Register it in `app/mcp/__init__.py` via `register_all_tools()`

The agent will automatically discover and use it.

---

## License

MIT
