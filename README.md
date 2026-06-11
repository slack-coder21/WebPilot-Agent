# WebPilot Agent

WebPilot Agent is a full-stack AI research-agent application for technical discovery workflows. It combines FastAPI, React TypeScript, Playwright browser automation, OpenAI/DeepSeek LLM planning, Tavily web search, LangChain RAG, ChromaDB vector search, plugin-style Agent Skills, traceable task artifacts, and an MCP server.

## 中文简介

WebPilot Agent 是一个面向技术调研场景的全栈 AI Agent 工程项目。系统支持创建调研任务、自动访问目标站点、抽取结构化结果、写入本地知识库、进行 RAG 问答，并把 Planner 决策、浏览器动作、fallback 和质量检查记录为可追踪的执行轨迹。

项目重点不是简单调用大模型，而是展示 Agent 工程中的编排、工具调用、状态记录、RAG、MCP 工具暴露、可观测性和前后端闭环。

## Core Capabilities

- Browser automation with Playwright.
- Rule-based planner and optional OpenAI/DeepSeek LLM planner.
- LangGraph `StateGraph` workflow for planner, browser, extraction, fallback, verification, and persistence nodes.
- Site extractors for arXiv, GitHub, HuggingFace, and Papers with Code.
- arXiv API fallback when browser extraction under-delivers.
- FastAPI REST backend for task execution, artifacts, RAG, and web ingestion.
- React TypeScript dashboard with Chinese/English UI switching.
- Tavily web search, webpage extraction, chunking, and Chroma indexing.
- LangChain RAG over previous research outputs and indexed webpages.
- Structured execution trace for each task step, action, status, note, and latency.
- Background task execution with SSE streaming for live Agent trace updates.
- Plugin-style Agent Skill Registry reused by REST and MCP entrypoints.
- MCP server exposing WebPilot skills to external Agent runtimes.

## Architecture Overview

| Area | Choice | Notes |
|---|---|---|
| Frontend | React + TypeScript + Vite | Dashboard in `frontend/`. |
| Backend | FastAPI | REST APIs in `webpilot/api.py`. |
| Browser automation | Playwright | Page observation and constrained browser actions. |
| Planning | Rule planner / LLM planner | OpenAI and DeepSeek are supported. |
| Agent workflow | LangGraph `StateGraph` | Nodes for plan, act, extract, fallback, verify, and persist. |
| RAG | LangChain | Research results and extracted webpages become documents. |
| Vector database | ChromaDB | Local persistent store under `vector_store/`. |
| Skills | Agent Skill Registry | Shared by FastAPI and MCP server. |
| MCP | FastMCP | `webpilot-mcp` exposes WebPilot tools. |
| Observability | Task trace artifacts + SSE | `trace.json`, `/api/tasks/{task_id}/trace`, and live `/api/tasks/{run_id}/events`. |

## Install

```powershell
conda activate webpilot-agent
pip install -e ".[dev,agent,rag,mcp,web]"
playwright install chromium
```

For the React frontend:

```powershell
cd frontend
npm install
```

## Environment

Create a local `.env` file from the template:

```powershell
Copy-Item .env.example .env
```

Then edit `.env`:

```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini

DEEPSEEK_API_KEY=
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com

TAVILY_API_KEY=

WEBPILOT_RUNS_DIR=runs
WEBPILOT_VECTOR_DIR=vector_store
WEBPILOT_LLM_PROVIDER=openai
WEBPILOT_EMBEDDINGS_PROVIDER=hash
WEBPILOT_EMBEDDING_MODEL=text-embedding-3-small
```

For semantic embeddings, set:

```env
WEBPILOT_EMBEDDINGS_PROVIDER=openai
OPENAI_API_KEY=...
WEBPILOT_EMBEDDING_MODEL=text-embedding-3-small
```

If no embedding provider is configured, the project uses a deterministic local hash embedding backend for local demos.

## Run

FastAPI backend:

```powershell
uvicorn webpilot.api:app --reload --host 127.0.0.1 --port 8000
```

React frontend:

```powershell
cd frontend
npm run dev
```

Open the frontend at:

```text
http://127.0.0.1:5173
```

The previous Streamlit MVP is still available:

```powershell
streamlit run app.py
```

## REST API

Health:

```http
GET /api/health
```

List registered skills:

```http
GET /api/skills
```

Run a research task:

```http
POST /api/tasks
Content-Type: application/json

{
  "task": "Search arXiv for RAG evaluation and return the top 5 paper titles and links",
  "site": "arxiv",
  "limit": 5,
  "planner": "rule",
  "llm_provider": "openai",
  "headless": true
}
```

Run a research task asynchronously:

```http
POST /api/tasks/async
Content-Type: application/json

{
  "task": "Search arXiv for RAG evaluation and return the top 5 paper titles and links",
  "site": "arxiv",
  "limit": 5,
  "planner": "rule",
  "llm_provider": "openai",
  "headless": true
}
```

The response contains:

```json
{
  "run_id": "2b0c3b4a0f1c4b9d8b0f7d7a4f5c1e1a",
  "status": "queued",
  "events_url": "/api/tasks/{run_id}/events",
  "status_url": "/api/tasks/{run_id}/status"
}
```

Subscribe to live Agent events:

```http
GET /api/tasks/{run_id}/events
Accept: text/event-stream
```

Query async task status:

```http
GET /api/tasks/{run_id}/status
```

Read structured task trace:

```http
GET /api/tasks/{task_id}/trace
```

Read raw artifacts:

```http
GET /api/tasks/{task_id}/artifacts/trace.json
GET /api/tasks/{task_id}/artifacts/results.json
GET /api/tasks/{task_id}/artifacts/report.md
```

Search, extract, split, and index webpages into Chroma:

```http
POST /api/rag/web-ingestions
Content-Type: application/json

{
  "query": "agentic RAG evaluation",
  "max_results": 5
}
```

Ask a RAG question:

```http
POST /api/rag/questions
Content-Type: application/json

{
  "question": "Which retrieved papers are relevant for RAG evaluation?",
  "llm_provider": "deepseek",
  "k": 5,
  "use_llm": true
}
```

## CLI

Rule planner:

```powershell
webpilot run --task "Search arXiv for RAG evaluation and return the top 5 paper titles and links" --site arxiv --limit 5
```

OpenAI planner:

```powershell
webpilot run --planner llm --llm-provider openai --task "Search GitHub for LangGraph examples" --site github --limit 5
```

DeepSeek planner:

```powershell
webpilot run --planner llm --llm-provider deepseek --task "Search HuggingFace for RAG embedding models" --site huggingface --limit 5
```

## MCP Server

Run the MCP server:

```powershell
webpilot-mcp
```

Or:

```powershell
python -m webpilot.mcp_server
```

Exposed MCP tools:

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

These tools reuse the same plugin-style skills used by the FastAPI backend.

## Task Artifacts

Each run writes:

```text
runs/
  <timestamp>-<task_slug>/
    trace.json
    results.json
    report.md
```

The trace records each step with:

- `step`
- `action`
- `observation_url`
- `note`
- `status`
- `duration_ms`

## Evaluation

The evaluation module can run fixed research tasks from `webpilot/evals/tasks.yaml` and report:

- task completion rate
- expected field coverage
- execution steps
- average latency
- browser/tool error rate
- fallback count

Recommended next step: run the same evaluation set with both rule planner and LLM planner, then compare completion rate, average steps, error rate, and report quality.

## Project Structure

```text
webpilot/
  api.py            # FastAPI REST backend
  llm.py            # OpenAI/DeepSeek chat model factory
  mcp_server.py     # MCP tools for external Agent runtimes
  models.py         # Pydantic request/result/trace models
  rag.py            # LangChain + Chroma RAG service
  skills/           # plugin-style Agent Skill Registry
  web/              # Tavily search, webpage extraction, web ingestion
  agents/           # LangGraph state graph, planner, extractor, verifier, reporter
  browser/          # Playwright client, observations, action executor
  evals/            # task evaluation set and runner
  workflows/        # end-to-end research workflow
frontend/
  src/App.tsx       # React TypeScript dashboard
tests/              # unit tests
examples/           # sample tasks
docs/architecture.md
```

## Roadmap

- Add LangGraph checkpointing and resumable task state.
- Add human-in-the-loop approval for risky browser actions.
- Expand the evaluation set to 20-30 technical research tasks.
- Add stronger RAG evaluation, citation coverage, and reranking.
- Add Docker Compose for one-command local deployment.
