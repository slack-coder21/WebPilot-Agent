# WebPilot Agent

WebPilot Agent is a full-stack AI research-agent application for technical discovery workflows. It combines browser automation, FastAPI REST APIs, React TypeScript, OpenAI/DeepSeek LLM planning, Tavily web search, webpage extraction, LangChain RAG, ChromaDB vector search, plugin-style Agent Skills, and an MCP server.

## 中文简介

WebPilot Agent 是一个面向技术调研场景的全栈 AI Agent 项目。系统支持使用 Playwright 执行浏览器自动化调研，通过 OpenAI 或 DeepSeek 进行可选 LLM 规划，并使用 Tavily 搜索、网页正文抽取、LangChain 文本切分和 ChromaDB 构建外部知识摄取与 RAG 问答能力。项目还实现了插件式 Agent Skill Registry 和 MCP Server，可将搜索、抽取、索引、RAG 查询和任务产物读取暴露为外部 Agent Runtime 可调用的 tools。

核心能力：

- FastAPI RESTful API
- React + TypeScript 前端
- Playwright 浏览器自动化 Agent
- OpenAI / DeepSeek LLM Planner
- Tavily Search + 网页正文抽取
- LangChain RAG + ChromaDB
- 插件式 Agent Skills
- MCP Server / MCP tools

## Architecture Overview

| Area | Choice | Notes |
|---|---|---|
| Frontend/backend connection | FastAPI REST API | React calls `/api/tasks`, `/api/search/tavily`, `/api/rag/web-ingestions`, and `/api/rag/questions`. |
| LLM | OpenAI / DeepSeek | `LLMPlanner` uses `langchain-openai`; DeepSeek is called through an OpenAI-compatible `base_url`. |
| RAG | LangChain | Research results and extracted webpages are loaded as LangChain documents before retrieval. |
| Vector database | ChromaDB | Local persistent vector store under `vector_store/`. |
| Frontend language | React + TypeScript | Vite app in `frontend/`, with Chinese/English UI switching. |
| RESTful API | Yes | Resource-style endpoints for tasks, search, extraction, ingestion, artifacts, and RAG questions. |
| Skills | Plugin-style Skill Registry | Browser research, Tavily search, webpage extraction, RAG Q&A, indexing, and artifact retrieval are registered as reusable skills. |
| MCP | MCP Server | `webpilot.mcp_server` exposes WebPilot skills as MCP tools. |

## Capabilities

- Browser automation with Playwright.
- Structured page observations and constrained browser actions.
- Rule-based planner for deterministic execution.
- Optional LLM planner with OpenAI or DeepSeek.
- Site extractors for arXiv, GitHub, HuggingFace, and HuggingFace Papers.
- arXiv API fallback when browser extraction under-delivers.
- FastAPI REST backend for frontend and automation clients.
- Tavily web search, webpage text extraction, and Chroma web-ingestion pipeline.
- LangChain RAG over prior research outputs and indexed webpages.
- Chroma vector store for persistent local retrieval.
- React TypeScript dashboard for task execution, result review, web ingestion, indexing, and RAG Q&A.
- Plugin-style Agent Skill Registry shared by REST and MCP entrypoints.
- MCP server for external Agent runtimes.

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
docs/architecture.md
```

## Project Summary

WebPilot Agent provides an end-to-end AI research workflow: browser-based technical research, external web search and ingestion, structured extraction, vector indexing, retrieval-augmented Q&A, traceable artifacts, reusable Agent Skills, and MCP tool exposure for external Agent runtimes.
