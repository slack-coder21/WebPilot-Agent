import json
import re
from datetime import datetime
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError

from webpilot.agents.arxiv_api import ArxivApiExtractor
from webpilot.agents.extractor import EXTRACTORS
from webpilot.agents.llm_planner import LLMPlanner
from webpilot.agents.planner import RuleBasedPlanner, _extract_query
from webpilot.agents.reporter import MarkdownReporter
from webpilot.agents.verifier import ResultVerifier
from webpilot.browser.actions import execute_action
from webpilot.browser.client import browser_page
from webpilot.browser.observer import observe_page
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
        self.arxiv_api = ArxivApiExtractor()
        self.verifier = ResultVerifier()
        self.reporter = MarkdownReporter()

    def run(self, task: str, site: str, limit: int, headless: bool = True) -> WorkflowResult:
        task_id = _slugify(task)
        run_dir = self.output_dir / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{task_id}"
        run_dir.mkdir(parents=True, exist_ok=True)

        trace: list[TaskTraceEvent] = []
        items = []
        observation = None
        with browser_page(headless=headless) as page:
            for step in range(1, 6):
                action = self.planner.next_action(task=task, site=site, observation=observation)
                if action.action == "extract":
                    items = EXTRACTORS[site].extract(page, limit=limit)
                    trace.append(
                        TaskTraceEvent(
                            step=step,
                            action=action,
                            observation_url=page.url,
                            note=f"extracted {len(items)} items",
                        )
                    )
                    break

                if observation is None:
                    observation_url = "about:blank"
                else:
                    observation_url = observation.url
                try:
                    note = execute_action(page, action, observation or _blank_observation())
                    page.wait_for_load_state("domcontentloaded", timeout=10000)
                    page.wait_for_timeout(1000)
                    observation = observe_page(page)
                except PlaywrightError as exc:
                    note = f"browser action failed: {exc}"
                    trace.append(
                        TaskTraceEvent(
                            step=step,
                            action=action,
                            observation_url=observation_url,
                            note=note[:500],
                        )
                    )
                    break
                trace.append(
                    TaskTraceEvent(
                        step=step,
                        action=action,
                        observation_url=observation_url,
                        note=note,
                    )
                )

        if site == "arxiv" and len(items) < limit:
            try:
                api_items = self.arxiv_api.extract(_extract_query(task), limit=limit)
                if api_items:
                    items = api_items
                    trace.append(
                        TaskTraceEvent(
                            step=len(trace) + 1,
                            action=_fallback_action(),
                            observation_url="https://export.arxiv.org/api/query",
                            note=f"fallback extracted {len(items)} items from arxiv api",
                        )
                    )
            except Exception as exc:
                trace.append(
                    TaskTraceEvent(
                        step=len(trace) + 1,
                        action=_fallback_action(),
                        observation_url="https://export.arxiv.org/api/query",
                        note=f"fallback failed: {exc}",
                    )
                )

        ok, verification_note = self.verifier.verify(items, min_items=limit)
        if not ok:
            verification_note = f"failed: {verification_note}"

        trace_path = run_dir / "trace.json"
        results_path = run_dir / "results.json"
        report_path = run_dir / "report.md"
        trace_path.write_text(
            json.dumps([event.model_dump() for event in trace], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        results_path.write_text(
            json.dumps([item.model_dump(mode="json") for item in items], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        report_path.write_text(
            self.reporter.render(task=task, items=items, verification_note=verification_note),
            encoding="utf-8",
        )

        return WorkflowResult(
            task_id=task_id,
            items=items,
            trace_path=str(trace_path),
            results_path=str(results_path),
            report_path=str(report_path),
        )


def _slugify(task: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", task).strip("-").lower()
    return slug[:48] or "task"


def _blank_observation():
    from webpilot.models import PageObservation

    return PageObservation(url="about:blank", title="", visible_text="", interactive_elements=[])


def _fallback_action():
    from webpilot.models import BrowserAction

    return BrowserAction(action="extract", value="arxiv_api_fallback")
