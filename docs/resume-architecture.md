# WebPilot Agent 简历版架构说明

## 1. 后端和前端连接

项目采用前后端分离架构：

- 后端：FastAPI，入口为 `webpilot/api.py`
- 前端：React + TypeScript + Vite，入口为 `frontend/src/App.tsx`
- 连接方式：前端通过 `fetch` 调用后端 REST API
- 本地代理：`frontend/vite.config.ts` 将 `/api` 代理到 `http://127.0.0.1:8000`

核心接口：

- `GET /api/health`
- `GET /api/sites`
- `GET /api/skills`
- `POST /api/search/tavily`
- `POST /api/web/extract`
- `POST /api/tasks`
- `GET /api/tasks/{task_id}/artifacts/{artifact_name}`
- `POST /api/rag/ingestions`
- `POST /api/rag/web-ingestions`
- `POST /api/rag/questions`

## 2. LLM

支持 OpenAI 和 DeepSeek：

- 统一封装在 `webpilot/llm.py`
- 配置读取在 `webpilot/settings.py`
- LLM Planner 在 `webpilot/agents/llm_planner.py`

OpenAI 使用 `.env` 配置：

- `OPENAI_API_KEY`
- `OPENAI_MODEL`

DeepSeek 使用 `.env` 配置：

- `DEEPSEEK_API_KEY`
- `DEEPSEEK_MODEL`
- `DEEPSEEK_BASE_URL=https://api.deepseek.com`

DeepSeek 通过 OpenAI-compatible API 方式接入 `ChatOpenAI`。项目通过 `python-dotenv` 自动读取 `.env`，避免将 API Key 写死在代码里。

## 3. RAG

项目加入 LangChain RAG：

- RAG 服务在 `webpilot/rag.py`
- 历史任务输出 `runs/*/results.json` 会被加载为 LangChain `Document`
- Tavily 搜索结果可通过网页正文抽取、文本切分后写入 Chroma
- 通过 Chroma 相似度检索召回相关调研结果
- 可选择使用 OpenAI/DeepSeek 基于召回上下文生成答案

RAG 流程：

1. 浏览器 Agent 执行调研任务
2. 结构化结果写入 `runs/`
3. 调用 `/api/rag/ingestions` 建立索引
4. 调用 `/api/rag/questions` 进行检索增强问答

外部网页摄取流程：

1. 调用 Tavily Search 获取网页结果
2. 抽取网页正文
3. 使用 LangChain text splitter 切分 chunk
4. 写入 Chroma 向量库
5. 通过 RAG 问答召回外部网页上下文

## 4. 向量知识库选取

选择 ChromaDB：

- 依赖：`chromadb`、`langchain-chroma`
- 持久化目录：`vector_store/`
- 适合本地 demo、简历项目展示和快速部署

当前 embedding 默认使用本地 deterministic hash embedding，不需要 API Key 就能跑通检索链路。后续可以替换为 OpenAI Embeddings 或其他 embedding 服务。

如需真正语义向量化，可设置：

- `WEBPILOT_EMBEDDINGS_PROVIDER=openai`
- `WEBPILOT_EMBEDDING_MODEL=text-embedding-3-small`
- `OPENAI_API_KEY`

## 5. 前端语言和界面优化

前端选择 React + TypeScript：

- 更符合前后端分离工程经验
- TypeScript 提升接口类型约束和可维护性
- Vite 提供轻量开发体验
- 页面支持中英文切换

界面包含：

- Agent 任务配置区
- 结构化结果展示区
- Chroma 索引按钮
- RAG 问答台
- OpenAI/DeepSeek provider 切换
- Planner 和模型选择

## 6. 用到哪些 Skill 和 MCP

项目已升级为插件式 Skill Registry：

- 入口：`webpilot/skills/registry.py`
- 内置 skills：`webpilot/skills/builtins.py`
- FastAPI 和 MCP Server 共用同一套 skills

当前注册的 skills：

- `list_supported_sites`
- `run_research_task`
- `ingest_research_results`
- `tavily_search`
- `extract_webpage_text`
- `web_research_ingest`
- `ask_rag`
- `get_task_artifact`

MCP：

- 已新增 MCP Server：`webpilot/mcp_server.py`
- 命令入口：`webpilot-mcp`
- 对外暴露 tools：
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

这些 MCP tools 可供支持 MCP 的外部 Agent Runtime 调用，例如 Claude Desktop、Cursor 或自定义 Agent Client。

简历建议写法：

> 设计插件式 Agent Skill Registry，将 Tavily 搜索、网页正文抽取、浏览器调研、RAG 问答、向量索引和任务产物读取封装为可复用 skills，并通过 MCP Server 暴露为标准 tools，支持外部 Agent Runtime 调用。

## 7. 是否用到 RESTful

是。

FastAPI 后端使用 RESTful 风格：

- `/api/tasks` 表示调研任务资源
- `/api/tasks/{task_id}/artifacts/{artifact_name}` 表示任务产物资源
- `/api/rag/ingestions` 表示向量索引构建资源
- `/api/rag/questions` 表示 RAG 问答请求资源

前端通过标准 HTTP 方法调用：

- `GET` 查询状态、站点、skills 和资源
- `POST` 创建任务、创建索引、提交问题

## 简历项目描述

WebPilot Agent：面向技术调研场景的全栈 AI Agent 应用。项目基于 FastAPI + React TypeScript 实现前后端分离，通过 RESTful API 调度 Playwright 浏览器自动化 Agent，支持 OpenAI/DeepSeek LLM Planner、结构化网页抽取、执行轨迹记录和 Markdown 报告生成；引入 Tavily Search、网页正文抽取、LangChain 文本切分、ChromaDB 向量知识库和 RAG 问答，对外部网页与历史调研结果进行本地持久化索引和检索增强问答；进一步设计插件式 Agent Skill Registry，并通过 MCP Server 将搜索、抽取、索引、RAG 查询和产物读取暴露为标准 tools，形成可复现、可追踪、可被外部 Agent 调用的 AI research workflow。
