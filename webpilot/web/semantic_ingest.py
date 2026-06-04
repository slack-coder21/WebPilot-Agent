from pydantic import BaseModel

from webpilot.rag import ResearchRagService
from webpilot.web.extractor import WebpageDocument, extract_webpage_text
from webpilot.web.tavily_search import TavilySearchResult, tavily_search


class WebIngestResult(BaseModel):
    query: str
    search_results: int
    extracted_documents: int
    indexed_chunks: int
    vector_store: str = "chroma"
    embedding_provider: str
    results: list[TavilySearchResult]


def ingest_search_results(
    query: str,
    max_results: int = 5,
    search_depth: str = "basic",
    use_tavily_extract: bool = True,
) -> WebIngestResult:
    results = tavily_search(query=query, max_results=max_results, search_depth=search_depth)
    documents: list[WebpageDocument] = []

    for result in results:
        try:
            document = extract_webpage_text(
                result.url,
                use_tavily_extract=use_tavily_extract,
            )
        except Exception:
            continue
        if document.text:
            if not document.title:
                document.title = result.title
            documents.append(document)

    service = ResearchRagService()
    indexed_chunks = service.ingest_web_documents(documents)
    return WebIngestResult(
        query=query,
        search_results=len(results),
        extracted_documents=len(documents),
        indexed_chunks=indexed_chunks,
        embedding_provider=service.embedding_provider,
        results=results,
    )
