import {
  Brain,
  Database,
  FileSearch,
  Globe2,
  Play,
  RefreshCw,
  Search,
} from "lucide-react";
import { FormEvent, useState } from "react";
import "./styles.css";

type Language = "zh" | "en";

type ResearchItem = {
  title: string;
  url: string;
  authors?: string;
  summary?: string;
  source?: string;
};

type WorkflowResult = {
  task_id: string;
  items: ResearchItem[];
  trace_path: string;
  results_path: string;
  report_path: string;
};

type RagAnswer = {
  question: string;
  answer: string;
  sources: Array<{ title: string; url: string; source: string; score?: number }>;
};

type WebIngestResult = {
  query: string;
  search_results: number;
  extracted_documents: number;
  indexed_chunks: number;
  vector_store: string;
  embedding_provider: string;
  results: Array<{ title: string; url: string; content: string; score?: number }>;
};

const sites = ["arxiv", "github", "huggingface", "paperswithcode"];

const text = {
  zh: {
    stack: "FastAPI · LangChain · Chroma · React · MCP",
    vectorStore: "Chroma 向量知识库",
    researchTask: "调研任务",
    task: "任务描述",
    site: "检索站点",
    limit: "返回数量",
    planner: "Planner",
    provider: "LLM 服务商",
    model: "模型选择",
    run: "运行 Agent",
    results: "结构化结果",
    emptyResults: "运行一个任务后，这里会展示浏览器调研结果。",
    items: "条结果",
    fallbackResult: "调研结果",
    webIngest: "外部搜索与语义索引",
    webQuery: "搜索问题",
    ingestWeb: "搜索、抽取并索引",
    webEmpty: "输入主题后，可通过 Tavily 搜索网页、抽取正文并写入 Chroma。",
    searchResults: "搜索结果",
    extractedDocs: "抽取文档",
    indexedChunks: "索引切片",
    embedding: "Embedding",
    rag: "RAG 问答台",
    ingest: "索引历史结果",
    ask: "提问",
    translate: "English",
    taskFailed: "任务运行失败",
    ingestOk: "已将 {count} 条调研文档写入 Chroma 向量库。",
    webIngestFailed: "外部搜索索引失败",
    ingestFailed: "索引构建失败",
    ragFailed: "RAG 问答失败",
    defaultModel: "使用默认模型",
    rulePlanner: "规则模式",
    llmPlanner: "LLM 模式",
    defaultTask: "在 arXiv 搜索 RAG evaluation，返回前 5 篇论文标题和链接",
    defaultWebQuery: "agentic RAG evaluation benchmark",
    defaultQuestion: "哪些已检索论文最适合用于 RAG evaluation？",
  },
  en: {
    stack: "FastAPI · LangChain · Chroma · React · MCP",
    vectorStore: "Chroma Vector Store",
    researchTask: "Research Task",
    task: "Task",
    site: "Search Site",
    limit: "Result Limit",
    planner: "Planner",
    provider: "LLM Provider",
    model: "Model",
    run: "Run Agent",
    results: "Structured Results",
    emptyResults: "Run a task to collect browser research results.",
    items: "items",
    fallbackResult: "Research result",
    webIngest: "External Search & Semantic Indexing",
    webQuery: "Search Query",
    ingestWeb: "Search, Extract, Index",
    webEmpty: "Enter a topic to search with Tavily, extract webpage text, and index it into Chroma.",
    searchResults: "Search results",
    extractedDocs: "Extracted docs",
    indexedChunks: "Indexed chunks",
    embedding: "Embedding",
    rag: "RAG Console",
    ingest: "Index Runs",
    ask: "Ask",
    translate: "中文",
    taskFailed: "Task failed",
    ingestOk: "Indexed {count} research documents into Chroma.",
    webIngestFailed: "Web ingestion failed",
    ingestFailed: "Ingestion failed",
    ragFailed: "RAG query failed",
    defaultModel: "Use default model",
    rulePlanner: "Rule mode",
    llmPlanner: "LLM mode",
    defaultTask: "Search arXiv for RAG evaluation and return the top 5 paper titles and links",
    defaultWebQuery: "agentic RAG evaluation benchmark",
    defaultQuestion: "Which retrieved papers are most relevant for RAG evaluation?",
  },
};

const siteLabels: Record<Language, Record<string, string>> = {
  zh: {
    arxiv: "arXiv 论文",
    github: "GitHub 仓库",
    huggingface: "HuggingFace 模型",
    paperswithcode: "论文 / Papers with Code",
  },
  en: {
    arxiv: "arXiv Papers",
    github: "GitHub Repositories",
    huggingface: "HuggingFace Models",
    paperswithcode: "Papers / Papers with Code",
  },
};

const providerLabels: Record<string, string> = {
  openai: "OpenAI",
  deepseek: "DeepSeek",
};

const modelOptions: Record<string, Array<{ label: string; value: string }>> = {
  openai: [
    { label: "GPT-4.1 Mini", value: "gpt-4.1-mini" },
    { label: "GPT-4.1", value: "gpt-4.1" },
    { label: "GPT-4o Mini", value: "gpt-4o-mini" },
  ],
  deepseek: [
    { label: "DeepSeek Chat", value: "deepseek-chat" },
    { label: "DeepSeek Reasoner", value: "deepseek-reasoner" },
  ],
};

export default function App() {
  const [language, setLanguage] = useState<Language>("zh");
  const t = text[language];
  const [task, setTask] = useState(text.zh.defaultTask);
  const [site, setSite] = useState("arxiv");
  const [limit, setLimit] = useState(5);
  const [planner, setPlanner] = useState("rule");
  const [provider, setProvider] = useState("deepseek");
  const [model, setModel] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<WorkflowResult | null>(null);
  const [webQuery, setWebQuery] = useState(text.zh.defaultWebQuery);
  const [webResult, setWebResult] = useState<WebIngestResult | null>(null);
  const [ragQuestion, setRagQuestion] = useState(text.zh.defaultQuestion);
  const [ragAnswer, setRagAnswer] = useState<RagAnswer | null>(null);
  const [notice, setNotice] = useState("");

  function toggleLanguage() {
    const nextLanguage: Language = language === "zh" ? "en" : "zh";
    const previous = text[language];
    const next = text[nextLanguage];
    setLanguage(nextLanguage);
    if (task === previous.defaultTask) setTask(next.defaultTask);
    if (webQuery === previous.defaultWebQuery) setWebQuery(next.defaultWebQuery);
    if (ragQuestion === previous.defaultQuestion) setRagQuestion(next.defaultQuestion);
  }

  async function runTask(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setNotice("");
    try {
      const response = await fetch("/api/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task,
          site,
          limit,
          planner,
          llm_provider: provider,
          llm_model: model || null,
          headless: true,
        }),
      });
      if (!response.ok) throw new Error(await response.text());
      setResult(await response.json());
    } catch (error) {
      setNotice(error instanceof Error ? error.message : t.taskFailed);
    } finally {
      setBusy(false);
    }
  }

  async function ingestWeb(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setNotice("");
    try {
      const response = await fetch("/api/rag/web-ingestions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: webQuery,
          max_results: 5,
          search_depth: "basic",
          use_tavily_extract: true,
        }),
      });
      if (!response.ok) throw new Error(await response.text());
      setWebResult(await response.json());
    } catch (error) {
      setNotice(error instanceof Error ? error.message : t.webIngestFailed);
    } finally {
      setBusy(false);
    }
  }

  async function ingestRuns() {
    setBusy(true);
    setNotice("");
    try {
      const response = await fetch("/api/rag/ingestions", { method: "POST" });
      if (!response.ok) throw new Error(await response.text());
      const payload = await response.json();
      setNotice(t.ingestOk.replace("{count}", String(payload.documents)));
    } catch (error) {
      setNotice(error instanceof Error ? error.message : t.ingestFailed);
    } finally {
      setBusy(false);
    }
  }

  async function askRag(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setNotice("");
    try {
      const response = await fetch("/api/rag/questions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: ragQuestion,
          llm_provider: provider,
          llm_model: model || null,
          k: 5,
          use_llm: planner === "llm",
        }),
      });
      if (!response.ok) throw new Error(await response.text());
      setRagAnswer(await response.json());
    } catch (error) {
      setNotice(error instanceof Error ? error.message : t.ragFailed);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="shell">
      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">{t.stack}</p>
            <h1>WebPilot Agent</h1>
          </div>
          <div className="top-actions">
            <button className="secondary compact" type="button" onClick={toggleLanguage}>
              <Globe2 size={18} />
              {t.translate}
            </button>
            <div className="status">
              <Database size={18} />
              {t.vectorStore}
            </div>
          </div>
        </header>

        <div className="grid">
          <form className="panel command-panel" onSubmit={runTask}>
            <div className="panel-title">
              <FileSearch size={20} />
              <h2>{t.researchTask}</h2>
            </div>
            <label>
              {t.task}
              <textarea value={task} onChange={(event) => setTask(event.target.value)} />
            </label>
            <div className="field-row">
              <label>
                {t.site}
                <select value={site} onChange={(event) => setSite(event.target.value)}>
                  {sites.map((item) => (
                    <option key={item} value={item}>
                      {siteLabels[language][item]}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                {t.limit}
                <input
                  type="number"
                  min={1}
                  max={10}
                  value={limit}
                  onChange={(event) => setLimit(Number(event.target.value))}
                />
              </label>
            </div>
            <div className="field-row">
              <label>
                {t.planner}
                <select value={planner} onChange={(event) => setPlanner(event.target.value)}>
                  <option value="rule">{t.rulePlanner}</option>
                  <option value="llm">{t.llmPlanner}</option>
                </select>
              </label>
              <label>
                {t.provider}
                <select
                  value={provider}
                  onChange={(event) => {
                    setProvider(event.target.value);
                    setModel("");
                  }}
                >
                  <option value="openai">{providerLabels.openai}</option>
                  <option value="deepseek">{providerLabels.deepseek}</option>
                </select>
              </label>
            </div>
            <label>
              {t.model}
              <select value={model} onChange={(event) => setModel(event.target.value)}>
                <option value="">{t.defaultModel}</option>
                {modelOptions[provider].map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <button className="primary" disabled={busy} type="submit">
              {busy ? <RefreshCw size={18} /> : <Play size={18} />}
              {t.run}
            </button>
          </form>

          <section className="panel results-panel">
            <div className="panel-title">
              <Search size={20} />
              <h2>{t.results}</h2>
            </div>
            {notice && <div className="notice">{notice}</div>}
            {!result && <p className="empty">{t.emptyResults}</p>}
            {result && (
              <>
                <div className="metrics">
                  <span>
                    {result.items.length} {t.items}
                  </span>
                  <span>{result.task_id}</span>
                </div>
                <div className="result-list">
                  {result.items.map((item, index) => (
                    <article className="result-card" key={`${item.url}-${index}`}>
                      <a href={item.url} target="_blank" rel="noreferrer">
                        {item.title}
                      </a>
                      <p>{item.authors || item.source || t.fallbackResult}</p>
                    </article>
                  ))}
                </div>
              </>
            )}
          </section>
        </div>

        <section className="panel web-panel">
          <div className="panel-title">
            <Globe2 size={20} />
            <h2>{t.webIngest}</h2>
          </div>
          <form onSubmit={ingestWeb} className="rag-form">
            <input
              aria-label={t.webQuery}
              value={webQuery}
              onChange={(event) => setWebQuery(event.target.value)}
            />
            <button className="primary" disabled={busy} type="submit">
              {busy ? <RefreshCw size={18} /> : <Search size={18} />}
              {t.ingestWeb}
            </button>
          </form>
          {!webResult && <p className="empty web-empty">{t.webEmpty}</p>}
          {webResult && (
            <div className="answer">
              <div className="metrics">
                <span>
                  {t.searchResults}: {webResult.search_results}
                </span>
                <span>
                  {t.extractedDocs}: {webResult.extracted_documents}
                </span>
                <span>
                  {t.indexedChunks}: {webResult.indexed_chunks}
                </span>
                <span>
                  {t.embedding}: {webResult.embedding_provider}
                </span>
              </div>
              <div className="source-list">
                {webResult.results.map((source, index) => (
                  <a key={`${source.url}-${index}`} href={source.url} target="_blank" rel="noreferrer">
                    {source.title || source.url}
                  </a>
                ))}
              </div>
            </div>
          )}
        </section>

        <section className="panel rag-panel">
          <div className="panel-title">
            <Brain size={20} />
            <h2>{t.rag}</h2>
          </div>
          <button className="secondary" onClick={ingestRuns} disabled={busy}>
            <Database size={18} />
            {t.ingest}
          </button>
          <form onSubmit={askRag} className="rag-form">
            <input value={ragQuestion} onChange={(event) => setRagQuestion(event.target.value)} />
            <button className="primary" disabled={busy} type="submit">
              <Brain size={18} />
              {t.ask}
            </button>
          </form>
          {ragAnswer && (
            <div className="answer">
              <p>{ragAnswer.answer}</p>
              <div className="source-list">
                {ragAnswer.sources.map((source, index) => (
                  <a key={`${source.url}-${index}`} href={source.url} target="_blank" rel="noreferrer">
                    {source.title || source.url}
                  </a>
                ))}
              </div>
            </div>
          )}
        </section>
      </section>
    </main>
  );
}
