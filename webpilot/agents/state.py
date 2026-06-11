from pathlib import Path
from typing import Any, Callable, Literal, TypedDict

from webpilot.models import BrowserAction, PageObservation, ResearchItem, TaskTraceEvent, WorkflowResult


GraphRoute = Literal["plan", "act", "extract", "fallback", "verify"]


class ResearchAgentState(TypedDict, total=False):
    task: str
    site: str
    limit: int
    headless: bool
    task_id: str
    run_dir: Path
    step: int
    max_steps: int
    observation: PageObservation | None
    action: BrowserAction | None
    items: list[ResearchItem]
    trace: list[TaskTraceEvent]
    verification_note: str
    result: WorkflowResult
    error: str | None
    route: GraphRoute
    trace_callback: Callable[[TaskTraceEvent], None] | None
    page: Any
