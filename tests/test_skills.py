from webpilot.skills import get_skill_registry


def test_registry_lists_builtin_skills() -> None:
    names = {skill["name"] for skill in get_skill_registry().list()}

    assert "run_research_task" in names
    assert "tavily_search" in names
    assert "extract_webpage_text" in names
    assert "web_research_ingest" in names
    assert "ask_rag" in names


def test_list_supported_sites_skill() -> None:
    payload = get_skill_registry().run("list_supported_sites")

    assert "arxiv" in payload["sites"]
    assert "github" in payload["sites"]
