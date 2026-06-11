from time import sleep

from webpilot.models import BrowserAction, TaskTraceEvent, WorkflowResult
from webpilot.task_runtime import TaskRuntime


def test_task_runtime_captures_trace_and_result(monkeypatch) -> None:
    class FakeWorkflow:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def run(self, *args, trace_callback=None, **kwargs) -> WorkflowResult:
            if trace_callback:
                trace_callback(
                    TaskTraceEvent(
                        step=1,
                        action=BrowserAction(action="goto", url="https://example.com"),
                        observation_url="about:blank",
                        note="opened example",
                        duration_ms=12,
                    )
                )
            return WorkflowResult(
                task_id="fake-task",
                items=[],
                trace_path="runs/fake/trace.json",
                results_path="runs/fake/results.json",
                report_path="runs/fake/report.md",
            )

    monkeypatch.setattr("webpilot.task_runtime.ResearchWorkflow", FakeWorkflow)
    runtime = TaskRuntime()

    created = runtime.create(
        {
            "task": "Search example",
            "site": "arxiv",
            "limit": 5,
            "planner": "rule",
            "llm_provider": "openai",
            "headless": True,
        }
    )

    state = created
    for _ in range(20):
        state = runtime.get(created.run_id)
        if state.status == "completed":
            break
        sleep(0.01)

    assert state.status == "completed"
    assert state.result is not None
    assert state.result.task_id == "fake-task"
    assert state.trace[0].action.action == "goto"
