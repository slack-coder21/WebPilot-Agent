import json

from fastapi.testclient import TestClient

from webpilot.api import app
from webpilot.settings import get_app_settings


def test_health_exposes_capabilities() -> None:
    response = TestClient(app).get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["backend"] == "fastapi"
    assert payload["skills"] == "enabled"
    assert payload["mcp"] == "available"


def test_skills_endpoint_lists_web_ingestion_skill() -> None:
    response = TestClient(app).get("/api/skills")

    assert response.status_code == 200
    names = {skill["name"] for skill in response.json()["skills"]}
    assert "web_research_ingest" in names


def test_task_trace_endpoint_reads_structured_trace(tmp_path, monkeypatch) -> None:
    runs_dir = tmp_path / "runs"
    run_dir = runs_dir / "20260611-120000-trace-task"
    run_dir.mkdir(parents=True)
    (run_dir / "trace.json").write_text(
        json.dumps(
            [
                {
                    "step": 1,
                    "action": {"action": "goto", "url": "https://example.com"},
                    "observation_url": "about:blank",
                    "note": "opened search page",
                    "status": "ok",
                    "duration_ms": 42,
                }
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("WEBPILOT_RUNS_DIR", str(runs_dir))
    get_app_settings.cache_clear()

    try:
        response = TestClient(app).get("/api/tasks/trace-task/trace")
    finally:
        get_app_settings.cache_clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["action"]["action"] == "goto"
    assert payload[0]["status"] == "ok"
    assert payload[0]["duration_ms"] == 42


def test_async_task_rejects_unknown_site() -> None:
    response = TestClient(app).post(
        "/api/tasks/async",
        json={
            "task": "Search an unsupported site",
            "site": "unknown",
            "limit": 5,
            "planner": "rule",
            "llm_provider": "openai",
            "headless": True,
        },
    )

    assert response.status_code == 400
    assert "Unsupported site" in response.json()["detail"]


def test_async_task_status_returns_404_for_unknown_run() -> None:
    response = TestClient(app).get("/api/tasks/not-a-real-run/status")

    assert response.status_code == 404
