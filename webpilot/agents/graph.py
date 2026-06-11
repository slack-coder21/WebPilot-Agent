import json
import re
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Callable

from playwright.sync_api import Error as PlaywrightError

from webpilot.agents.arxiv_api import ArxivApiExtractor
from webpilot.agents.extractor import EXTRACTORS
from webpilot.agents.planner import _extract_query
from webpilot.agents.reporter import MarkdownReporter
from webpilot.agents.state import GraphRoute, ResearchAgentState
from webpilot.agents.verifier import ResultVerifier
from webpilot.browser.actions import execute_action
from webpilot.browser.client import browser_page
from webpilot.browser.observer import observe_page
from webpilot.models import BrowserAction, PageObservation, TaskTraceEvent, WorkflowResult

try:
    from langgraph.graph import END, StateGraph
except ImportError as exc:  # pragma: no cover - dependency is installed in the agent extra
    raise RuntimeError('LangGraph workflow requires: pip install -e ".[agent]"') from exc


class ResearchAgentGraph:
    def __init__(
        self,
        output_dir: Path,
        planner,
        arxiv_api: ArxivApiExtractor | None = None,
        verifier: ResultVerifier | None = None,
        reporter: MarkdownReporter | None = None,
    ) -> None:
        self.output_dir = output_dir
        self.planner = planner
        self.arxiv_api = arxiv_api or ArxivApiExtractor()
        self.verifier = verifier or ResultVerifier()
        self.reporter = reporter or MarkdownReporter()
        self._compiled = self._build_graph()

    def run(
        self,
        task: str,
        site: str,
        limit: int,
        headless: bool = True,
        trace_callback: Callable[[TaskTraceEvent], None] | None = None,
    ) -> WorkflowResult:
        task_id = _slugify(task)
        run_dir = self.output_dir / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{task_id}"
        run_dir.mkdir(parents=True, exist_ok=True)
        initial_state: ResearchAgentState = {
            "task": task,
            "site": site,
            "limit": limit,
            "headless": headless,
            "task_id": task_id,
            "run_dir": run_dir,
            "step": 0,
            "max_steps": 5,
            "observation": None,
            "items": [],
            "trace": [],
            "error": None,
            "route": "plan",
            "trace_callback": trace_callback,
        }

        with browser_page(headless=headless) as page:
            final_state = self._compiled.invoke({**initial_state, "page": page})

        return final_state["result"]

    def _build_graph(self):
        graph = StateGraph(ResearchAgentState)
        graph.add_node("plan", self._plan_node)
        graph.add_node("act", self._browser_action_node)
        graph.add_node("extract", self._extract_node)
        graph.add_node("fallback", self._fallback_node)
        graph.add_node("verify", self._verify_node)
        graph.add_node("persist", self._persist_node)

        graph.set_entry_point("plan")
        graph.add_conditional_edges("plan", _route, {"act": "act", "extract": "extract", "fallback": "fallback", "verify": "verify"})
        graph.add_conditional_edges("act", _route, {"plan": "plan", "fallback": "fallback", "verify": "verify"})
        graph.add_conditional_edges("extract", _route, {"fallback": "fallback", "verify": "verify"})
        graph.add_edge("fallback", "verify")
        graph.add_edge("verify", "persist")
        graph.add_edge("persist", END)
        return graph.compile()

    def _plan_node(self, state: ResearchAgentState) -> dict:
        if state["step"] >= state["max_steps"]:
            return {"route": _route_after_collection(state)}

        action = self.planner.next_action(
            task=state["task"],
            site=state["site"],
            observation=state.get("observation"),
        )
        step = state["step"] + 1
        if action.action == "extract":
            route: GraphRoute = "extract"
        elif action.action == "finish":
            route = _route_after_collection(state)
        else:
            route = "act"
        return {"action": action, "step": step, "route": route}

    def _browser_action_node(self, state: ResearchAgentState) -> dict:
        page = state["page"]
        action = state["action"]
        observation = state.get("observation") or _blank_observation()
        observation_url = observation.url if state.get("observation") else "about:blank"
        started_at = perf_counter()
        try:
            note = execute_action(page, action, observation)
            page.wait_for_load_state("domcontentloaded", timeout=10000)
            page.wait_for_timeout(1000)
            next_observation = observe_page(page)
        except (PlaywrightError, ValueError, RuntimeError) as exc:
            event = TaskTraceEvent(
                step=state["step"],
                action=action,
                observation_url=observation_url,
                note=f"browser action failed: {exc}"[:500],
                status="error",
                duration_ms=_elapsed_ms(started_at),
            )
            return {
                **_trace_update(state, event),
                "error": str(exc),
                "route": _route_after_collection(state),
            }

        event = TaskTraceEvent(
            step=state["step"],
            action=action,
            observation_url=observation_url,
            note=note,
            duration_ms=_elapsed_ms(started_at),
        )
        route: GraphRoute = "plan" if state["step"] < state["max_steps"] else _route_after_collection(state)
        return {**_trace_update(state, event), "observation": next_observation, "route": route}

    def _extract_node(self, state: ResearchAgentState) -> dict:
        page = state["page"]
        action = state["action"]
        started_at = perf_counter()
        try:
            items = EXTRACTORS[state["site"]].extract(page, limit=state["limit"])
            event = TaskTraceEvent(
                step=state["step"],
                action=action,
                observation_url=page.url,
                note=f"extracted {len(items)} items",
                duration_ms=_elapsed_ms(started_at),
            )
            return {**_trace_update(state, event), "items": items, "route": _route_after_collection({**state, "items": items})}
        except Exception as exc:
            event = TaskTraceEvent(
                step=state["step"],
                action=action,
                observation_url=page.url,
                note=f"extract failed: {exc}"[:500],
                status="error",
                duration_ms=_elapsed_ms(started_at),
            )
            return {**_trace_update(state, event), "error": str(exc), "route": _route_after_collection(state)}

    def _fallback_node(self, state: ResearchAgentState) -> dict:
        if state["site"] != "arxiv" or len(state.get("items", [])) >= state["limit"]:
            return {}

        started_at = perf_counter()
        try:
            api_items = self.arxiv_api.extract(_extract_query(state["task"]), limit=state["limit"])
            if not api_items:
                return {}
            event = TaskTraceEvent(
                step=len(state.get("trace", [])) + 1,
                action=_fallback_action(),
                observation_url="https://export.arxiv.org/api/query",
                note=f"fallback extracted {len(api_items)} items from arxiv api",
                status="fallback",
                duration_ms=_elapsed_ms(started_at),
            )
            return {**_trace_update(state, event), "items": api_items}
        except Exception as exc:
            event = TaskTraceEvent(
                step=len(state.get("trace", [])) + 1,
                action=_fallback_action(),
                observation_url="https://export.arxiv.org/api/query",
                note=f"fallback failed: {exc}",
                status="error",
                duration_ms=_elapsed_ms(started_at),
            )
            return {**_trace_update(state, event), "error": str(exc)}

    def _verify_node(self, state: ResearchAgentState) -> dict:
        started_at = perf_counter()
        ok, verification_note = self.verifier.verify(state.get("items", []), min_items=state["limit"])
        if not ok:
            verification_note = f"failed: {verification_note}"
        event = TaskTraceEvent(
            step=len(state.get("trace", [])) + 1,
            action=_finish_action(),
            observation_url="local://quality-check",
            note=verification_note,
            status="ok" if ok else "error",
            duration_ms=_elapsed_ms(started_at),
        )
        return {**_trace_update(state, event), "verification_note": verification_note}

    def _persist_node(self, state: ResearchAgentState) -> dict:
        run_dir = state["run_dir"]
        trace_path = run_dir / "trace.json"
        results_path = run_dir / "results.json"
        report_path = run_dir / "report.md"
        trace_path.write_text(
            json.dumps([event.model_dump() for event in state.get("trace", [])], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        results_path.write_text(
            json.dumps(
                [item.model_dump(mode="json") for item in state.get("items", [])],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        report_path.write_text(
            self.reporter.render(
                task=state["task"],
                items=state.get("items", []),
                verification_note=state.get("verification_note", "not verified"),
            ),
            encoding="utf-8",
        )
        result = WorkflowResult(
            task_id=state["task_id"],
            items=state.get("items", []),
            trace_path=str(trace_path),
            results_path=str(results_path),
            report_path=str(report_path),
        )
        return {"result": result}


def _route(state: ResearchAgentState) -> GraphRoute:
    return state["route"]


def _route_after_collection(state: ResearchAgentState) -> GraphRoute:
    if state["site"] == "arxiv" and len(state.get("items", [])) < state["limit"]:
        return "fallback"
    return "verify"


def _trace_update(state: ResearchAgentState, event: TaskTraceEvent) -> dict:
    callback = state.get("trace_callback")
    if callback:
        callback(event)
    return {"trace": [*state.get("trace", []), event]}


def _slugify(task: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", task).strip("-").lower()
    return slug[:48] or "task"


def _blank_observation() -> PageObservation:
    return PageObservation(url="about:blank", title="", visible_text="", interactive_elements=[])


def _fallback_action() -> BrowserAction:
    return BrowserAction(action="extract", value="arxiv_api_fallback")


def _finish_action() -> BrowserAction:
    return BrowserAction(action="finish", value="quality_check")


def _elapsed_ms(started_at: float) -> int:
    return int((perf_counter() - started_at) * 1000)
