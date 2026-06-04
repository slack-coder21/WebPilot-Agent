from typing import Any

from webpilot.skills import get_skill_registry

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover
    raise RuntimeError('MCP server requires: pip install -e ".[mcp]"') from exc


mcp = FastMCP("WebPilot Agent")


@mcp.tool()
def list_skills() -> list[dict[str, str]]:
    """List WebPilot agent skills exposed by this MCP server."""
    return get_skill_registry().list()


@mcp.tool()
def list_supported_sites() -> dict[str, list[str]]:
    """List supported research sites."""
    return get_skill_registry().run("list_supported_sites")


@mcp.tool()
def run_research_task(
    task: str,
    site: str = "arxiv",
    limit: int = 5,
    planner: str = "rule",
    llm_provider: str = "deepseek",
    llm_model: str | None = None,
    headless: bool = True,
) -> dict[str, Any]:
    """Run a browser research task and return structured results and artifact paths."""
    return get_skill_registry().run(
        "run_research_task",
        {
            "task": task,
            "site": site,
            "limit": limit,
            "planner": planner,
            "llm_provider": llm_provider,
            "llm_model": llm_model,
            "headless": headless,
        },
    )


@mcp.tool()
def ingest_research_results() -> dict[str, Any]:
    """Index previous WebPilot research results into Chroma."""
    return get_skill_registry().run("ingest_research_results")


@mcp.tool()
def tavily_search(query: str, max_results: int = 5, search_depth: str = "basic") -> dict[str, Any]:
    """Search the web with Tavily."""
    return get_skill_registry().run(
        "tavily_search",
        {"query": query, "max_results": max_results, "search_depth": search_depth},
    )


@mcp.tool()
def extract_webpage_text(url: str, use_tavily_extract: bool = True) -> dict[str, Any]:
    """Extract clean text from a webpage URL."""
    return get_skill_registry().run(
        "extract_webpage_text",
        {"url": url, "use_tavily_extract": use_tavily_extract},
    )


@mcp.tool()
def web_research_ingest(
    query: str,
    max_results: int = 5,
    search_depth: str = "basic",
    use_tavily_extract: bool = True,
) -> dict[str, Any]:
    """Search with Tavily, extract webpages, and index chunks into Chroma."""
    return get_skill_registry().run(
        "web_research_ingest",
        {
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "use_tavily_extract": use_tavily_extract,
        },
    )


@mcp.tool()
def ask_rag(
    question: str,
    llm_provider: str = "deepseek",
    llm_model: str | None = None,
    k: int = 5,
    use_llm: bool = True,
) -> dict[str, Any]:
    """Ask a retrieval-augmented question over indexed research outputs."""
    return get_skill_registry().run(
        "ask_rag",
        {
            "question": question,
            "llm_provider": llm_provider,
            "llm_model": llm_model,
            "k": k,
            "use_llm": use_llm,
        },
    )


@mcp.tool()
def semantic_ask_rag(
    question: str,
    llm_provider: str = "deepseek",
    llm_model: str | None = None,
    k: int = 5,
    use_llm: bool = True,
) -> dict[str, Any]:
    """Ask RAG over the current semantic Chroma collection."""
    return ask_rag(
        question=question,
        llm_provider=llm_provider,
        llm_model=llm_model,
        k=k,
        use_llm=use_llm,
    )


@mcp.tool()
def get_task_artifact(task_id: str, artifact_name: str = "report.md") -> dict[str, Any]:
    """Read a task artifact by task id and artifact filename."""
    return get_skill_registry().run(
        "get_task_artifact",
        {"task_id": task_id, "artifact_name": artifact_name},
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
