from contextlib import contextmanager
from pathlib import Path

from webpilot.agents import graph as graph_module
from webpilot.agents.graph import ResearchAgentGraph
from webpilot.agents.reporter import MarkdownReporter
from webpilot.agents.verifier import ResultVerifier
from webpilot.models import BrowserAction, PageObservation, ResearchItem


class FakePlanner:
    def next_action(self, task: str, site: str, observation: PageObservation | None) -> BrowserAction:
        if observation is None:
            return BrowserAction(action="goto", url="https://example.com/search?q=rag")
        return BrowserAction(action="extract")


class FakeExtractor:
    def extract(self, page, limit: int) -> list[ResearchItem]:
        return [
            ResearchItem(
                title="RAG evaluation benchmark",
                url="https://example.com/paper",
                source="example",
            )
        ][:limit]


class FakePage:
    url = "about:blank"

    def wait_for_load_state(self, *args, **kwargs) -> None:
        return None

    def wait_for_timeout(self, *args, **kwargs) -> None:
        return None


@contextmanager
def fake_browser_page(headless: bool = True):
    yield FakePage()


def fake_execute_action(page: FakePage, action: BrowserAction, observation: PageObservation) -> str:
    if action.url:
        page.url = action.url
    return f"goto {page.url}"


def fake_observe_page(page: FakePage) -> PageObservation:
    return PageObservation(url=page.url, title="Example", visible_text="", interactive_elements=[])


def test_research_agent_graph_runs_nodes_and_persists_artifacts(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(graph_module, "browser_page", fake_browser_page)
    monkeypatch.setattr(graph_module, "execute_action", fake_execute_action)
    monkeypatch.setattr(graph_module, "observe_page", fake_observe_page)
    monkeypatch.setitem(graph_module.EXTRACTORS, "arxiv", FakeExtractor())

    graph = ResearchAgentGraph(
        output_dir=tmp_path,
        planner=FakePlanner(),
        verifier=ResultVerifier(),
        reporter=MarkdownReporter(),
    )
    streamed_events = []

    result = graph.run(
        task="Search arXiv for RAG evaluation",
        site="arxiv",
        limit=1,
        headless=True,
        trace_callback=streamed_events.append,
    )

    assert result.items[0].title == "RAG evaluation benchmark"
    assert len(streamed_events) == 3
    assert streamed_events[-1].action.action == "finish"
    assert Path(result.trace_path).exists()
