import re

from webpilot.models import BrowserAction, PageObservation
from webpilot.sites import SITE_CONFIGS


class RuleBasedPlanner:
    """Deterministic planner for MVP demos and tests.

    The class mirrors the interface a future LLM planner should implement:
    observe task state, return one constrained BrowserAction.
    """

    def next_action(self, task: str, site: str, observation: PageObservation | None) -> BrowserAction:
        if site not in SITE_CONFIGS:
            raise ValueError(f"Unsupported site: {site}")

        site_config = SITE_CONFIGS[site]
        if observation is None or site_config.host not in observation.url:
            query = _extract_query(task)
            return BrowserAction(action="goto", url=site_config.search_url(query))

        return BrowserAction(action="extract")


def _extract_query(task: str) -> str:
    # Keep the first version deterministic. This intentionally avoids relying on a model.
    stop_words = [
        "arxiv",
        "github",
        "huggingface",
        "papers with code",
        "paperswithcode",
        "search",
        "find",
        "return",
        "top",
        "title",
        "titles",
        "link",
        "links",
        "repo",
        "repos",
        "repository",
        "repositories",
        "model",
        "models",
    ]
    query = task
    for word in stop_words:
        query = re.sub(re.escape(word), " ", query, flags=re.IGNORECASE)
    for token in [
        "在",
        "搜索",
        "查找",
        "返回",
        "前",
        "个",
        "项",
        "篇",
        "论文",
        "标题",
        "链接",
        "模型",
        "仓库",
        "和",
    ]:
        query = query.replace(token, " ")
    query = re.sub(r"\b\d+\b", " ", query)
    query = " ".join(query.replace("，", " ").replace("。", " ").split())
    return query or task
