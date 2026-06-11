# WebPilot Agent Architecture

## 1. Frontend And Backend Connection

The project uses a separated frontend/backend architecture:

- Backend: FastAPI, entrypoint `webpilot/api.py`
- Frontend: React + TypeScript + Vite, entrypoint `frontend/src/App.tsx`
- Connection: the frontend calls REST APIs through `fetch` and subscribes to live task events through `EventSource`
- Local proxy: `frontend/vite.config.ts` proxies `/api` to `http://127.0.0.1:8000`

Core endpoints:

- `GET /api/health`
- `GET /api/sites`
- `GET /api/skills`
- `POST /api/search/tavily`
- `POST /api/web/extract`
- `POST /api/tasks`
- `POST /api/tasks/async`
- `GET /api/tasks/{run_id}/status`
- `GET /api/tasks/{run_id}/events`
- `GET /api/tasks/{task_id}/trace`
- `GET /api/tasks/{task_id}/artifacts/{artifact_name}`
- `POST /api/rag/ingestions`
- `POST /api/rag/web-ingestions`
- `POST /api/rag/questions`

## 2. LLM

The project supports OpenAI and DeepSeek:

- Unified model factory: `webpilot/llm.py`
- Configuration: `webpilot/settings.py`
- Planner integration: `webpilot/agents/llm_planner.py`

OpenAI is configured through `.env`:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`

DeepSeek is configured through `.env`:

- `DEEPSEEK_API_KEY`
- `DEEPSEEK_MODEL`
- `DEEPSEEK_BASE_URL=https://api.deepseek.com`

DeepSeek is integrated through an OpenAI-compatible API via `ChatOpenAI`. The project uses `python-dotenv` to load `.env` automatically and keeps secrets out of source control.

## 3. Agent Workflow

The browser research runtime is organized as a LangGraph `StateGraph`:

- State schema: `webpilot/agents/state.py`
- Graph implementation: `webpilot/agents/graph.py`
- Compatibility entrypoint: `webpilot/workflows/research.py`

Graph nodes:

- `plan`: ask the rule planner or LLM planner for the next constrained browser action.
- `act`: execute browser actions through Playwright and update page observation.
- `extract`: run the site-specific extractor and collect structured research items.
- `fallback`: use the arXiv API fallback when browser extraction under-delivers.
- `verify`: validate result count and required fields.
- `persist`: write `trace.json`, `results.json`, and `report.md`.

Conditional edges route from `plan` to `act`, `extract`, `fallback`, or `verify`, and route failed or under-filled extraction through fallback before final verification. Each emitted `TaskTraceEvent` is also sent to the async task runtime so the frontend can stream the trace with SSE.

## 4. RAG

The RAG layer is built with LangChain and ChromaDB:

- RAG service: `webpilot/rag.py`
- Prior task outputs from `runs/*/results.json` are loaded as LangChain documents
- Tavily search results can be extracted, split, and indexed into Chroma
- Chroma similarity search retrieves relevant context
- OpenAI or DeepSeek can generate answers from retrieved context

Task-output ingestion flow:

1. Browser Agent executes a research task
2. Structured results are written to `runs/`
3. `/api/rag/ingestions` indexes historical outputs
4. `/api/rag/questions` performs retrieval-augmented Q&A

External web ingestion flow:

1. Tavily Search returns external web results
2. Webpage text is extracted
3. LangChain text splitter creates chunks
4. Chunks are written into Chroma
5. RAG Q&A retrieves indexed webpage context

## 5. Vector Database

The project uses ChromaDB:

- Dependencies: `chromadb`, `langchain-chroma`
- Persistent directory: `vector_store/`
- Suitable for local development and reproducible demos

The default embedding backend is a deterministic local hash embedding provider, so the retrieval chain can run without external embedding credentials. For semantic embeddings, configure:

- `WEBPILOT_EMBEDDINGS_PROVIDER=openai`
- `WEBPILOT_EMBEDDING_MODEL=text-embedding-3-small`
- `OPENAI_API_KEY`

## 6. Frontend

The frontend uses React + TypeScript:

- TypeScript improves API typing and maintainability
- Vite provides a lightweight development workflow
- The page supports Chinese/English switching

Main UI sections:

- Agent task configuration
- Structured result display
- Live execution trace and run status
- External search and semantic indexing
- Chroma indexing
- RAG console
- OpenAI/DeepSeek provider switching
- Planner and model selection

## 7. Skills And MCP

The project uses a plugin-style Skill Registry:

- Registry entrypoint: `webpilot/skills/registry.py`
- Built-in skills: `webpilot/skills/builtins.py`
- FastAPI and MCP Server reuse the same skills

Registered skills:

- `list_supported_sites`
- `run_research_task`
- `ingest_research_results`
- `tavily_search`
- `extract_webpage_text`
- `web_research_ingest`
- `ask_rag`
- `get_task_artifact`

MCP:

- MCP Server: `webpilot/mcp_server.py`
- Command entrypoint: `webpilot-mcp`
- Exposed tools:
  - `list_skills`
  - `list_supported_sites`
  - `run_research_task`
  - `ingest_research_results`
  - `tavily_search`
  - `extract_webpage_text`
  - `web_research_ingest`
  - `ask_rag`
  - `semantic_ask_rag`
  - `get_task_artifact`

These MCP tools can be called by MCP-compatible external Agent runtimes.

## 8. RESTful API

The FastAPI backend exposes RESTful resources:

- `/api/tasks` for synchronous research tasks
- `/api/tasks/async` for background research tasks
- `/api/tasks/{run_id}/status` for background task state
- `/api/tasks/{run_id}/events` for SSE trace streaming
- `/api/tasks/{task_id}/trace` for structured trace artifacts
- `/api/tasks/{task_id}/artifacts/{artifact_name}` for task artifacts
- `/api/search/tavily` for external search
- `/api/web/extract` for webpage extraction
- `/api/rag/ingestions` for indexing task outputs
- `/api/rag/web-ingestions` for external web ingestion
- `/api/rag/questions` for RAG questions

The frontend uses standard HTTP methods:

- `GET` for status, sites, skills, and resources
- `POST` for task creation, search, extraction, indexing, and questions

## Project Description

WebPilot Agent is a full-stack AI research-agent application for technical discovery workflows. It uses FastAPI and React TypeScript for a separated frontend/backend architecture, Playwright for browser automation, OpenAI/DeepSeek for optional LLM planning, Tavily for external web search, LangChain for document processing and RAG, ChromaDB for vector retrieval, and MCP for exposing reusable tools to external Agent runtimes.
