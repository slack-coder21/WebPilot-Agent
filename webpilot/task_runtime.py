from __future__ import annotations

from copy import deepcopy
from threading import RLock, Thread
from uuid import uuid4

from webpilot.models import AsyncTaskState, TaskTraceEvent, WorkflowResult
from webpilot.settings import get_app_settings
from webpilot.workflows.research import ResearchWorkflow


class TaskRuntime:
    def __init__(self) -> None:
        self._lock = RLock()
        self._tasks: dict[str, AsyncTaskState] = {}

    def create(self, payload: dict) -> AsyncTaskState:
        run_id = uuid4().hex
        state = AsyncTaskState(run_id=run_id, status="queued")
        with self._lock:
            self._tasks[run_id] = state

        thread = Thread(target=self._run_task, args=(run_id, payload), daemon=True)
        thread.start()
        return self.get(run_id)

    def get(self, run_id: str) -> AsyncTaskState:
        with self._lock:
            if run_id not in self._tasks:
                raise KeyError(run_id)
            return deepcopy(self._tasks[run_id])

    def _run_task(self, run_id: str, payload: dict) -> None:
        self._set_status(run_id, "running")
        try:
            workflow = ResearchWorkflow(
                output_dir=get_app_settings().runs_dir,
                planner_name=str(payload.get("planner", "rule")),
                llm_provider=payload.get("llm_provider"),
                llm_model=payload.get("llm_model"),
            )
            result = workflow.run(
                task=str(payload["task"]),
                site=str(payload.get("site", "arxiv")),
                limit=int(payload.get("limit", 5)),
                headless=bool(payload.get("headless", True)),
                trace_callback=lambda event: self.add_trace(run_id, event),
            )
        except Exception as exc:
            self._set_error(run_id, str(exc))
            return

        self._set_result(run_id, result)

    def add_trace(self, run_id: str, event: TaskTraceEvent) -> None:
        with self._lock:
            if run_id in self._tasks:
                self._tasks[run_id].trace.append(event)

    def _set_status(self, run_id: str, status: str) -> None:
        with self._lock:
            if run_id in self._tasks:
                self._tasks[run_id].status = status  # type: ignore[assignment]

    def _set_error(self, run_id: str, error: str) -> None:
        with self._lock:
            if run_id in self._tasks:
                self._tasks[run_id].status = "failed"
                self._tasks[run_id].error = error

    def _set_result(self, run_id: str, result: WorkflowResult) -> None:
        with self._lock:
            if run_id in self._tasks:
                self._tasks[run_id].status = "completed"
                self._tasks[run_id].result = result


task_runtime = TaskRuntime()
