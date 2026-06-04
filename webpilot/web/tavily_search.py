from pydantic import BaseModel

from webpilot.settings import get_web_search_settings


class TavilySearchResult(BaseModel):
    title: str
    url: str
    content: str = ""
    score: float | None = None


def tavily_search(
    query: str,
    max_results: int = 5,
    search_depth: str = "basic",
) -> list[TavilySearchResult]:
    settings = get_web_search_settings()
    if not settings.tavily_api_key:
        raise RuntimeError("Tavily search requires TAVILY_API_KEY in .env")

    try:
        from tavily import TavilyClient
    except ImportError as exc:
        raise RuntimeError('Tavily search requires: pip install -e ".[web]"') from exc

    client = TavilyClient(api_key=settings.tavily_api_key)
    response = client.search(
        query=query,
        max_results=max_results,
        search_depth=search_depth,
        include_answer=False,
        include_raw_content=False,
    )
    results = response.get("results", []) if isinstance(response, dict) else []
    return [
        TavilySearchResult(
            title=str(item.get("title", "")),
            url=str(item.get("url", "")),
            content=str(item.get("content", "")),
            score=item.get("score"),
        )
        for item in results
        if item.get("url")
    ]
