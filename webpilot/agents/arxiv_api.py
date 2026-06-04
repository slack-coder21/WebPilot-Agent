from urllib.parse import quote_plus
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from webpilot.models import ResearchItem


ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


class ArxivApiExtractor:
    def extract(self, query: str, limit: int) -> list[ResearchItem]:
        url = (
            "https://export.arxiv.org/api/query?"
            f"search_query=all:{quote_plus(query)}&start=0&max_results={limit}"
        )
        request = Request(url, headers={"User-Agent": "webpilot-agent/0.1"})
        with urlopen(request, timeout=30) as response:
            content = response.read()

        root = ElementTree.fromstring(content)
        items: list[ResearchItem] = []
        for entry in root.findall("atom:entry", ATOM_NS):
            title = _entry_text(entry, "atom:title")
            summary = _entry_text(entry, "atom:summary")
            authors = ", ".join(
                _entry_text(author, "atom:name") for author in entry.findall("atom:author", ATOM_NS)
            )
            link = _entry_text(entry, "atom:id")
            if title and link:
                items.append(
                    ResearchItem(
                        title=" ".join(title.split()),
                        url=link,
                        authors=authors,
                        summary=" ".join(summary.split()),
                        source="arxiv-api",
                    )
                )
        return items


def _entry_text(node: ElementTree.Element, path: str) -> str:
    child = node.find(path, ATOM_NS)
    return child.text.strip() if child is not None and child.text else ""

