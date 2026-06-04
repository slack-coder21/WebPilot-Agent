from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


ActionType = Literal["goto", "click", "type", "select", "scroll", "wait", "extract", "finish"]
PathLike = str


class InteractiveElement(BaseModel):
    element_id: str
    tag: str
    text: str = ""
    selector: str
    placeholder: str = ""
    role: str = ""


class PageObservation(BaseModel):
    url: str
    title: str
    visible_text: str
    interactive_elements: list[InteractiveElement] = Field(default_factory=list)


class BrowserAction(BaseModel):
    action: ActionType
    target_id: str | None = None
    value: str | None = None
    url: str | None = None


class ResearchItem(BaseModel):
    title: str
    url: HttpUrl | str
    authors: str = ""
    summary: str = ""
    source: str = ""


class TaskTraceEvent(BaseModel):
    step: int
    action: BrowserAction
    observation_url: str
    note: str = ""


class WorkflowResult(BaseModel):
    task_id: str
    items: list[ResearchItem]
    trace_path: PathLike
    results_path: PathLike
    report_path: PathLike
