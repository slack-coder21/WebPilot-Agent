from playwright.sync_api import Page

from webpilot.models import ResearchItem


class SiteExtractor:
    def extract(self, page: Page, limit: int) -> list[ResearchItem]:
        raise NotImplementedError


class ArxivExtractor:
    def extract(self, page: Page, limit: int) -> list[ResearchItem]:
        results = page.locator("li.arxiv-result")
        items: list[ResearchItem] = []
        count = min(results.count(), limit)
        for idx in range(count):
            result = results.nth(idx)
            title = _safe_text(result.locator("p.title"))
            authors = _safe_text(result.locator("p.authors")).replace("Authors:", "").strip()
            summary = _safe_text(result.locator("span.abstract-full")).replace("Abstract:", "").strip()
            url = ""
            links = result.locator("p.list-title a")
            if links.count():
                url = links.first.get_attribute("href") or ""
            if title:
                items.append(
                    ResearchItem(
                        title=title,
                        url=url,
                        authors=authors,
                        summary=summary,
                        source="arxiv",
                    )
                )
        return items


class GitHubExtractor:
    def extract(self, page: Page, limit: int) -> list[ResearchItem]:
        items: list[ResearchItem] = []
        repo_links = page.locator('a[href^="/"][href*="/"]')
        seen: set[str] = set()

        for idx in range(repo_links.count()):
            if len(items) >= limit:
                break
            link = repo_links.nth(idx)
            href = link.get_attribute("href") or ""
            title = _safe_text(link)
            if not _looks_like_repo_path(href) or href in seen:
                continue
            seen.add(href)
            items.append(
                ResearchItem(
                    title=title or href.strip("/"),
                    url=f"https://github.com{href}",
                    source="github",
                )
            )
        return items


class HuggingFaceExtractor:
    def extract(self, page: Page, limit: int) -> list[ResearchItem]:
        items: list[ResearchItem] = []
        links = page.locator('a[href^="/"][href*="/"]')
        seen: set[str] = set()
        skip_prefixes = ("/datasets/", "/spaces/", "/docs/", "/blog/", "/pricing", "/join")

        for idx in range(links.count()):
            if len(items) >= limit:
                break
            link = links.nth(idx)
            href = link.get_attribute("href") or ""
            title = _safe_text(link)
            if not _looks_like_hf_model_path(href) or href.startswith(skip_prefixes) or href in seen:
                continue
            seen.add(href)
            items.append(
                ResearchItem(
                    title=_first_line(title) or href.strip("/"),
                    url=f"https://huggingface.co{href}",
                    summary=title,
                    source="huggingface",
                )
            )
        return items


class PapersWithCodeExtractor:
    def extract(self, page: Page, limit: int) -> list[ResearchItem]:
        items: list[ResearchItem] = []
        links = page.locator('a[href^="/papers/"]')
        seen: set[str] = set()

        for idx in range(links.count()):
            if len(items) >= limit:
                break
            link = links.nth(idx)
            href = link.get_attribute("href") or ""
            title = _safe_text(link)
            if not _looks_like_hf_paper_path(href) or href in seen or not title:
                continue
            seen.add(href)
            items.append(
                ResearchItem(
                    title=_first_line(title),
                    url=f"https://huggingface.co{href}",
                    source="paperswithcode",
                )
            )
        return items


EXTRACTORS: dict[str, SiteExtractor] = {
    "arxiv": ArxivExtractor(),
    "github": GitHubExtractor(),
    "huggingface": HuggingFaceExtractor(),
    "paperswithcode": PapersWithCodeExtractor(),
}


def _safe_text(locator) -> str:
    try:
        if locator.count() == 0:
            return ""
        return " ".join(locator.first.inner_text(timeout=2000).split())
    except Exception:
        return ""


def _first_line(text: str) -> str:
    return next((line.strip() for line in text.splitlines() if line.strip()), text.strip())


def _looks_like_repo_path(href: str) -> bool:
    parts = [part for part in href.split("?")[0].strip("/").split("/") if part]
    if len(parts) != 2:
        return False
    owner, repo = parts
    blocked = {
        "features",
        "enterprise",
        "topics",
        "collections",
        "marketplace",
        "login",
        "signup",
        "search",
        "orgs",
        "settings",
    }
    return owner not in blocked and repo not in {"stargazers", "forks", "issues", "pulls"}


def _looks_like_hf_model_path(href: str) -> bool:
    parts = [part for part in href.split("?")[0].strip("/").split("/") if part]
    if len(parts) != 2:
        return False
    blocked = {"models", "datasets", "spaces", "docs", "blog", "settings", "new"}
    return parts[0] not in blocked


def _looks_like_hf_paper_path(href: str) -> bool:
    parts = [part for part in href.split("?")[0].strip("/").split("/") if part]
    return len(parts) == 2 and parts[0] == "papers" and parts[1] not in {"trending", "submit"}
