from webpilot.agents.planner import RuleBasedPlanner


def test_planner_starts_with_arxiv_search() -> None:
    planner = RuleBasedPlanner()
    action = planner.next_action("在 arXiv 搜索 RAG evaluation，返回前 5 篇论文标题和链接", "arxiv", None)
    assert action.action == "goto"
    assert "arxiv.org/search" in action.url


def test_planner_supports_research_sites() -> None:
    planner = RuleBasedPlanner()
    sites = {
        "github": "github.com/search",
        "huggingface": "huggingface.co/models",
        "paperswithcode": "huggingface.co/papers",
    }
    for site, expected_url in sites.items():
        action = planner.next_action("search RAG evaluation", site, None)
        assert action.action == "goto"
        assert expected_url in action.url
