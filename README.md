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

## How the agent works

Every query goes through a 6-node LangGraph pipeline:

```
planner → research → tool → rag → memory → report
```

1. **Planner** — reads your query and available tools, outputs a step-by-step plan and selects which tools to use
2. **Research** — runs a web search if needed
3. **Tool** — executes all other selected tools (Slack, email, Sheets, SQL, etc.) with LLM-extracted arguments
4. **RAG** — queries Qdrant for relevant chunks from your uploaded documents
5. **Memory** — surfaces existing memories about you for context
6. **Report** — synthesizes everything into a structured final answer with citations

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
