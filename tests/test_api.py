from fastapi.testclient import TestClient

from webpilot.api import app


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
