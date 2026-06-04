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
        results.append(
            {
                "id": task["id"],
                "items": len(result.items),
                "passed": len(result.items) >= task["min_items"],
                "report_path": result.report_path,
            }
        )
    return results
