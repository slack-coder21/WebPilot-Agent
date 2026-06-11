import json
import yaml
from pathlib import Path

from webpilot.workflows.research import ResearchWorkflow


def run_eval(task_file: Path, output_dir: Path, headless: bool = True) -> list[dict]:
    tasks = yaml.safe_load(task_file.read_text(encoding="utf-8"))
    workflow = ResearchWorkflow(output_dir=output_dir)
    results = []
    for task in tasks:
        result = workflow.run(
            task=task["task"],
            site=task["site"],
            limit=task["min_items"],
            headless=headless,
        )
        trace_metrics = _trace_metrics(Path(result.trace_path))
        expected_fields = task.get("expected_fields", [])
        results.append(
            {
                "id": task["id"],
                "items": len(result.items),
                "passed": len(result.items) >= task["min_items"],
                "expected_fields_present": _has_expected_fields(result.items, expected_fields),
                "steps": trace_metrics["steps"],
                "errors": trace_metrics["errors"],
                "fallbacks": trace_metrics["fallbacks"],
                "duration_ms": trace_metrics["duration_ms"],
                "report_path": result.report_path,
            }
        )
    return results


def summarize_eval_results(results: list[dict]) -> dict:
    if not results:
        return {
            "tasks": 0,
            "completion_rate": 0.0,
            "average_steps": 0.0,
            "average_duration_ms": 0.0,
            "tool_error_rate": 0.0,
            "fallbacks": 0,
        }

    task_count = len(results)
    passed = sum(1 for result in results if result["passed"])
    total_steps = sum(int(result.get("steps", 0)) for result in results)
    total_errors = sum(int(result.get("errors", 0)) for result in results)
    return {
        "tasks": task_count,
        "completion_rate": passed / task_count,
        "average_steps": total_steps / task_count,
        "average_duration_ms": sum(int(result.get("duration_ms", 0)) for result in results)
        / task_count,
        "tool_error_rate": total_errors / max(total_steps, 1),
        "fallbacks": sum(int(result.get("fallbacks", 0)) for result in results),
    }


def _trace_metrics(trace_path: Path) -> dict[str, int]:
    try:
        events = json.loads(trace_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        events = []

    return {
        "steps": len(events),
        "errors": sum(1 for event in events if event.get("status") == "error"),
        "fallbacks": sum(1 for event in events if event.get("status") == "fallback"),
        "duration_ms": sum(int(event.get("duration_ms") or 0) for event in events),
    }


def _has_expected_fields(items, expected_fields: list[str]) -> bool:
    if not expected_fields:
        return True
    for item in items:
        payload = item.model_dump(mode="json")
        if not all(payload.get(field) for field in expected_fields):
            return False
    return True
