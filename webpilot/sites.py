from dataclasses import dataclass
from urllib.parse import quote_plus


SUPPORTED_SITES = ("arxiv", "github", "huggingface", "paperswithcode")


@dataclass(frozen=True)
class SiteConfig:
    name: str
    host: str
    search_url_template: str

    def search_url(self, query: str) -> str:
        return self.search_url_template.format(query=quote_plus(query))


SITE_CONFIGS: dict[str, SiteConfig] = {
    "arxiv": SiteConfig(
        name="arxiv",
        host="arxiv.org",
        search_url_template="https://arxiv.org/search/?query={query}&searchtype=all&source=header",
    ),
    "github": SiteConfig(
        name="github",
        host="github.com",
        search_url_template="https://github.com/search?q={query}&type=repositories",
    ),
    "huggingface": SiteConfig(
        name="huggingface",
        host="huggingface.co",
        search_url_template="https://huggingface.co/models?search={query}",
    ),
    "paperswithcode": SiteConfig(
        name="paperswithcode",
        host="huggingface.co",
        search_url_template="https://huggingface.co/papers?q={query}",
    ),
}
