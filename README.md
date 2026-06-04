# WebPilot Agent

WebPilot Agent is an AI research-agent application for technical discovery workflows. It combines browser automation, a RESTful FastAPI backend, optional OpenAI/DeepSeek planning, LangChain RAG, Chroma vector search, and a React TypeScript frontend.

## 中文简介

WebPilot Agent 是一个面向技术调研场景的全栈 AI Agent 项目。它支持使用 Playwright 进行浏览器自动化调研，通过 OpenAI/DeepSeek 进行可选 LLM 规划，使用 Tavily 搜索和网页正文抽取进行外部知识摄取，并基于 LangChain + Chroma 构建 RAG 问答能力。项目还实现了插件式 Agent Skill Registry 和 MCP Server，可将搜索、抽取、索引、RAG 查询和任务产物读取暴露为外部 Agent Runtime 可调用的 tools。

适合展示的关键词：

- FastAPI RESTful API
- React + TypeScript 前端
- Playwright 浏览器自动化 Agent
- OpenAI / DeepSeek LLM Planner
- Tavily Search + 网页正文抽取
- LangChain RAG + ChromaDB
- 插件式 Agent Skills
- MCP Server / MCP tools

## Resume-Oriented Architecture

| Area | Choice | Notes |
|---|---|---|
| Frontend/backend connection | FastAPI REST API | React calls `/api/tasks`, `/api/rag/ingestions`, and `/api/rag/questions`. |
| LLM | OpenAI / DeepSeek | `LLMPlanner` uses `langchain-openai`; DeepSeek is called through an OpenAI-compatible `base_url`. |
| RAG | LangChain | Research results are loaded as LangChain `Document` objects and retrieved before answer generation. |
| Vector database | ChromaDB | Local persistent vector store under `vector_store/`; simple to run and demo. |
| Frontend language | React + TypeScript | Vite app in `frontend/`, replacing the Streamlit-only MVP for a production-style UI. |
| RESTful | Yes | Resource-style endpoints for tasks, artifacts, RAG ingestion, and RAG questions. |
| Skills | Plugin-style Skill Registry | Browser research, Tavily search, webpage extraction, RAG Q&A, indexing, and artifact retrieval are registered as reusable skills. |
| MCP | MCP Server | `webpilot.mcp_server` exposes WebPilot skills as MCP tools. |

## Capabilities

- Browser automation with Playwright.
- Structured page observations and constrained browser actions.
- Rule-based planner for deterministic demos.
- Optional LLM planner with OpenAI or DeepSeek.
- Site extractors for arXiv, GitHub, HuggingFace, and HuggingFace Papers.
- arXiv API fallback when browser extraction under-delivers.
- FastAPI REST backend for frontend and automation clients.
- LangChain RAG over prior research outputs.
- Chroma vector store for persistent local retrieval.
- React TypeScript dashboard for task execution, result review, indexing, and RAG Q&A.
- Plugin-style Agent Skill Registry shared by REST and MCP entrypoints.
- MCP server for external Agent runtimes.
- Tavily web search, webpage text extraction, and Chroma web-ingestion pipeline.

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

`.env` is ignored by Git, so API keys stay local.

For true semantic embeddings, set:

```env
WEBPILOT_EMBEDDINGS_PROVIDER=openai
OPENAI_API_KEY=...
WEBPILOT_EMBEDDING_MODEL=text-embedding-3-small
```

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

Search the web with Tavily:

```http
POST /api/search/tavily
Content-Type: application/json

{
  "query": "agentic RAG evaluation",
  "max_results": 5
}
```

Extract webpage text:

```http
POST /api/web/extract
Content-Type: application/json

{
  "url": "https://example.com/article"
}
```

Search, extract, split, and index web pages into Chroma:

```http
POST /api/rag/web-ingestions
Content-Type: application/json

{
  "query": "agentic RAG evaluation",
  "max_results": 5
}
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

Index research outputs into Chroma:

```http
POST /api/rag/ingestions
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

## Output

Each run writes:

```text
runs/
  <timestamp>-<task_slug>/
    trace.json
    results.json
    report.md
```

## Project Structure

```text
webpilot/
  api.py            # FastAPI REST backend
  llm.py            # OpenAI/DeepSeek chat model factory
  mcp_server.py     # MCP tools for external Agent runtimes
  rag.py            # LangChain + Chroma RAG service
  skills/           # plugin-style Agent Skill Registry
  web/              # Tavily search, webpage extraction, web ingestion
  agents/           # planner, extractor, verifier, reporter
  browser/          # Playwright client, observations, action executor
  workflows/        # end-to-end research workflow
frontend/
  src/App.tsx       # React TypeScript dashboard
tests/              # unit tests
examples/           # sample tasks
```

## Resume Bullet

Designed and upgraded WebPilot Agent, a full-stack AI research-agent application using FastAPI REST APIs, React TypeScript, Playwright browser automation, OpenAI/DeepSeek LLM planning, Tavily web search, webpage extraction, LangChain RAG, ChromaDB vector search, plugin-style Agent Skills, and an MCP server; implemented structured task execution, external web ingestion, traceable research outputs, local vector indexing, retrieval-augmented Q&A, and MCP tool exposure for external Agent runtimes.
