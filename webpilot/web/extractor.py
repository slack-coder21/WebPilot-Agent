from bs4 import BeautifulSoup
from pydantic import BaseModel

from webpilot.settings import get_web_search_settings


class WebpageDocument(BaseModel):
    url: str
    title: str = ""
    text: str
    source: str = "web"


def extract_webpage_text(url: str, use_tavily_extract: bool = True, timeout: int = 20) -> WebpageDocument:
    if use_tavily_extract:
        document = _extract_with_tavily(url)
        if document and document.text:
            return document
    return _extract_with_requests(url, timeout=timeout)


def _extract_with_tavily(url: str) -> WebpageDocument | None:
    settings = get_web_search_settings()
    if not settings.tavily_api_key:
        return None

    try:
        from tavily import TavilyClient
    except ImportError:
        return None

    client = TavilyClient(api_key=settings.tavily_api_key)
    payload = client.extract(url)
    item = _first_extract_result(payload)
    if not item:
        return None

    text = str(item.get("raw_content") or item.get("content") or "").strip()
    if not text:
        return None

    return WebpageDocument(
        url=str(item.get("url") or url),
        title=str(item.get("title") or ""),
        text=text,
        source="tavily_extract",
    )


def _first_extract_result(payload) -> dict | None:
    if isinstance(payload, dict):
        if isinstance(payload.get("results"), list) and payload["results"]:
            first = payload["results"][0]
            return first if isinstance(first, dict) else None
        if payload.get("raw_content") or payload.get("content"):
            return payload
    return None


def _extract_with_requests(url: str, timeout: int) -> WebpageDocument:
    try:
        import requests
    except ImportError as exc:
        raise RuntimeError("Webpage extraction requires requests") from exc

    response = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": "WebPilotAgent/0.2 (+https://example.local)"},
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "aside"]):
        tag.decompose()

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    paragraphs = [
        element.get_text(" ", strip=True)
        for element in soup.find_all(["h1", "h2", "h3", "p", "li"])
    ]
    text = "\n".join(part for part in paragraphs if part)
    if not text:
        text = soup.get_text("\n", strip=True)

    return WebpageDocument(url=url, title=title, text=text[:120_000], source="requests_bs4")
