from webpilot.evals.evaluator import summarize_eval_results


def test_summarize_eval_results_reports_core_metrics() -> None:
    summary = summarize_eval_results(
        [
            {"passed": True, "steps": 4, "errors": 0, "fallbacks": 1, "duration_ms": 100},
            {"passed": False, "steps": 2, "errors": 1, "fallbacks": 0, "duration_ms": 50},
        ]
    )

    assert summary["tasks"] == 2
    assert summary["completion_rate"] == 0.5
    assert summary["average_steps"] == 3
    assert summary["tool_error_rate"] == 1 / 6
    assert summary["fallbacks"] == 1
