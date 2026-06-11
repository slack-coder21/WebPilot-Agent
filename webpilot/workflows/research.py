from pathlib import Path
from typing import Callable

from webpilot.agents.arxiv_api import ArxivApiExtractor
from webpilot.agents.graph import ResearchAgentGraph
from webpilot.agents.llm_planner import LLMPlanner
from webpilot.agents.planner import RuleBasedPlanner
from webpilot.agents.reporter import MarkdownReporter
from webpilot.agents.verifier import ResultVerifier
from webpilot.models import TaskTraceEvent, WorkflowResult


class ResearchWorkflow:
    def __init__(
        self,
        output_dir: Path,
        planner_name: str = "rule",
        llm_provider: str | None = None,
        llm_model: str | None = None,
    ) -> None:
        self.output_dir = output_dir
        self.planner = (
            LLMPlanner(provider=llm_provider, model=llm_model)
            if planner_name == "llm"
            else RuleBasedPlanner()
        )
        self.graph = ResearchAgentGraph(
            output_dir=output_dir,
            planner=self.planner,
            arxiv_api=ArxivApiExtractor(),
            verifier=ResultVerifier(),
            reporter=MarkdownReporter(),
        )

    def run(
        self,
        task: str,
        site: str,
        limit: int,
        headless: bool = True,
        trace_callback: Callable[[TaskTraceEvent], None] | None = None,
    ) -> WorkflowResult:
        return self.graph.run(
            task=task,
            site=site,
            limit=limit,
            headless=headless,
            trace_callback=trace_callback,
        )
