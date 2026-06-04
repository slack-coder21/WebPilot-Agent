import hashlib
import json
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel, Field

from webpilot.llm import build_chat_model
from webpilot.settings import get_app_settings


class RetrievedSource(BaseModel):
    title: str
    url: str
    source: str = ""
    score: float | None = None


class RagAnswer(BaseModel):
    question: str
    answer: str
    sources: list[RetrievedSource] = Field(default_factory=list)


class HashEmbeddings:
    """Small deterministic embedding backend for local demos without API keys."""

    def __init__(self, dimensions: int = 256) -> None:
        self.dimensions = dimensions

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            vector[index] += 1.0
        norm = sum(value * value for value in vector) ** 0.5 or 1.0
        return [value / norm for value in vector]


class ResearchRagService:
    def __init__(self, persist_dir: Path | None = None) -> None:
        settings = get_app_settings()
        self.persist_dir = persist_dir or settings.vector_dir
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.embedding_provider = settings.default_embedding_provider
        self.embedding_model = settings.embedding_model
        self.collection_name = _collection_name(self.embedding_provider)

    def ingest_runs(self, runs_dir: Path | None = None) -> int:
        documents = list(_load_run_documents(runs_dir or get_app_settings().runs_dir))
        if not documents:
            return 0
        vector_store = self._vector_store()
        vector_store.add_documents(documents)
        return len(documents)

    def ingest_web_documents(self, documents) -> int:
        chunks = _split_web_documents(documents)
        if not chunks:
            return 0
        vector_store = self._vector_store()
        vector_store.add_documents(chunks)
        return len(chunks)

    def ask(
        self,
        question: str,
        provider: str = "openai",
        model: str | None = None,
        k: int = 5,
        use_llm: bool = True,
    ) -> RagAnswer:
        vector_store = self._vector_store()
        docs_with_scores = vector_store.similarity_search_with_relevance_scores(question, k=k)
        docs = [doc for doc, _score in docs_with_scores]
        sources = [
            RetrievedSource(
                title=doc.metadata.get("title", ""),
                url=doc.metadata.get("url", ""),
                source=doc.metadata.get("source", ""),
                score=score,
            )
            for doc, score in docs_with_scores
        ]

        if use_llm and docs:
            try:
                answer = self._generate_answer(question, docs, provider=provider, model=model)
            except Exception as exc:
                answer = f"Retrieved relevant sources, but LLM generation failed: {exc}"
        elif docs:
            answer = "\n".join(f"- {doc.metadata.get('title', 'Untitled')}" for doc in docs)
        else:
            answer = "No relevant context found. Ingest research results or web pages first."

        return RagAnswer(question=question, answer=answer, sources=sources)

    def _vector_store(self):
        try:
            from langchain_chroma import Chroma
        except ImportError as exc:
            raise RuntimeError('RAG support requires: pip install -e ".[rag]"') from exc

        return Chroma(
            collection_name=self.collection_name,
            embedding_function=_build_embedding_function(
                provider=self.embedding_provider,
                model=self.embedding_model,
            ),
            persist_directory=str(self.persist_dir),
        )

    def _generate_answer(self, question: str, docs, provider: str, model: str | None) -> str:
        context = "\n\n".join(
            f"Title: {doc.metadata.get('title', '')}\n"
            f"URL: {doc.metadata.get('url', '')}\n"
            f"Content: {doc.page_content}"
            for doc in docs
        )
        prompt = (
            "Answer the research question using only the retrieved context. "
            "If the context is insufficient, say what is missing. Include source titles when useful.\n\n"
            f"Question: {question}\n\nContext:\n{context}"
        )
        response = build_chat_model(provider=provider, model=model).invoke(prompt)
        return response.content if isinstance(response.content, str) else str(response.content)


def _load_run_documents(runs_dir: Path) -> Iterable:
    try:
        from langchain_core.documents import Document
    except ImportError as exc:
        raise RuntimeError('RAG support requires: pip install -e ".[rag]"') from exc

    if not runs_dir.exists():
        return

    for results_path in runs_dir.glob("*/results.json"):
        try:
            payload = json.loads(results_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        for item in payload:
            title = item.get("title", "")
            url = str(item.get("url", ""))
            summary = item.get("summary", "")
            authors = item.get("authors", "")
            source = item.get("source", "")
            content = "\n".join(part for part in [title, authors, summary, url] if part)
            if not content:
                continue
            yield Document(
                page_content=content,
                metadata={
                    "title": title,
                    "url": url,
                    "source": source,
                    "run": results_path.parent.name,
                },
            )


def _build_embedding_function(provider: str, model: str):
    provider = provider.lower()
    if provider == "openai":
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError as exc:
            raise RuntimeError('OpenAI embeddings require: pip install -e ".[agent]"') from exc
        return OpenAIEmbeddings(model=model)
    if provider in {"hash", "local"}:
        return HashEmbeddings()
    raise RuntimeError(f"Unsupported embedding provider: {provider}")


def _collection_name(provider: str) -> str:
    provider = provider.lower()
    if provider in {"hash", "local"}:
        return "webpilot_research"
    return f"webpilot_research_{provider}"


def _split_web_documents(documents) -> list:
    try:
        from langchain_core.documents import Document
    except ImportError as exc:
        raise RuntimeError('RAG support requires: pip install -e ".[rag]"') from exc

    raw_documents = [
        Document(
            page_content=document.text,
            metadata={
                "title": document.title,
                "url": document.url,
                "source": document.source,
                "kind": "webpage",
            },
        )
        for document in documents
        if getattr(document, "text", "")
    ]
    if not raw_documents:
        return []

    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError:
        return _simple_split_documents(raw_documents)

    splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=160)
    return splitter.split_documents(raw_documents)


def _simple_split_documents(documents) -> list:
    try:
        from langchain_core.documents import Document
    except ImportError as exc:
        raise RuntimeError('RAG support requires: pip install -e ".[rag]"') from exc

    chunks = []
    for document in documents:
        text = document.page_content
        for index in range(0, len(text), 1000):
            chunk = text[index : index + 1200]
            if chunk.strip():
                metadata = dict(document.metadata)
                metadata["chunk_index"] = index // 1000
                chunks.append(Document(page_content=chunk, metadata=metadata))
    return chunks
