from pathlib import Path
from typing import Any

from webpilot.models import WorkflowResult
from webpilot.rag import ResearchRagService
from webpilot.settings import get_app_settings
from webpilot.sites import SUPPORTED_SITES
from webpilot.skills.base import AgentSkill
from webpilot.skills.registry import SkillRegistry
from webpilot.web import extract_webpage_text, ingest_search_results, tavily_search
from webpilot.workflows.research import ResearchWorkflow


class ListSupportedSitesSkill(AgentSkill):
    name = "list_supported_sites"
    description = "List research sites supported by WebPilot."

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"sites": list(SUPPORTED_SITES)}


class RunResearchTaskSkill(AgentSkill):
    name = "run_research_task"
    description = "Run a browser research task and return structured results plus artifact paths."

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        site = payload.get("site", "arxiv")
        if site not in SUPPORTED_SITES:
            raise ValueError(f"Unsupported site: {site}")

        planner = payload.get("planner", "rule")
        if planner not in {"rule", "llm"}:
            raise ValueError("planner must be 'rule' or 'llm'")

        llm_provider = payload.get("llm_provider", "openai")
        if llm_provider not in {"openai", "deepseek"}:
            raise ValueError("llm_provider must be 'openai' or 'deepseek'")

        settings = get_app_settings()
        workflow = ResearchWorkflow(
            output_dir=settings.runs_dir,
            planner_name=planner,
            llm_provider=llm_provider,
            llm_model=payload.get("llm_model"),
        )
        result: WorkflowResult = workflow.run(
            task=str(payload["task"]),
            site=site,
            limit=int(payload.get("limit", 5)),
            headless=bool(payload.get("headless", True)),
        )
        return result.model_dump(mode="json")


class IngestResearchResultsSkill(AgentSkill):
    name = "ingest_research_results"
    description = "Index previous research results from runs/ into the Chroma vector store."

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        service = ResearchRagService()
        documents = service.ingest_runs()
        return {"documents": documents, "vector_store": "chroma"}


class TavilySearchSkill(AgentSkill):
    name = "tavily_search"
    description = "Search the web with Tavily and return ranked external results."

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        results = tavily_search(
            query=str(payload["query"]),
            max_results=int(payload.get("max_results", 5)),
            search_depth=str(payload.get("search_depth", "basic")),
        )
        return {"results": [result.model_dump(mode="json") for result in results]}


class ExtractWebpageTextSkill(AgentSkill):
    name = "extract_webpage_text"
    description = "Extract clean article-like text from a webpage URL."

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        document = extract_webpage_text(
            url=str(payload["url"]),
            use_tavily_extract=bool(payload.get("use_tavily_extract", True)),
        )
        return document.model_dump(mode="json")


class WebResearchIngestSkill(AgentSkill):
    name = "web_research_ingest"
    description = "Search with Tavily, extract webpages, split text, and index chunks into Chroma."

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = ingest_search_results(
            query=str(payload["query"]),
            max_results=int(payload.get("max_results", 5)),
            search_depth=str(payload.get("search_depth", "basic")),
            use_tavily_extract=bool(payload.get("use_tavily_extract", True)),
        )
        return result.model_dump(mode="json")


class AskRagSkill(AgentSkill):
    name = "ask_rag"
    description = "Ask a retrieval-augmented question over indexed research results."

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        llm_provider = payload.get("llm_provider", "openai")
        if llm_provider not in {"openai", "deepseek"}:
            raise ValueError("llm_provider must be 'openai' or 'deepseek'")

        service = ResearchRagService()
        answer = service.ask(
            question=str(payload["question"]),
            provider=llm_provider,
            model=payload.get("llm_model"),
            k=int(payload.get("k", 5)),
            use_llm=bool(payload.get("use_llm", True)),
        )
        return answer.model_dump(mode="json")


class GetTaskArtifactSkill(AgentSkill):
    name = "get_task_artifact"
    description = "Read a task artifact such as trace.json, results.json, or report.md."

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        artifact_name = str(payload["artifact_name"])
        if artifact_name not in {"trace.json", "results.json", "report.md"}:
            raise ValueError("Unknown artifact")

        run_dir = find_run_dir(str(payload["task_id"]))
        artifact_path = run_dir / artifact_name
        if not artifact_path.exists():
            raise FileNotFoundError("Artifact not found")
        return {
            "task_id": payload["task_id"],
            "artifact_name": artifact_name,
            "path": str(artifact_path),
            "text": artifact_path.read_text(encoding="utf-8"),
        }


def find_run_dir(task_id: str) -> Path:
    runs_dir = get_app_settings().runs_dir
    matches = sorted(runs_dir.glob(f"*-{task_id}"), reverse=True)
    if not matches:
        raise FileNotFoundError("Task run not found")
    return matches[0]


def register_builtin_skills(registry: SkillRegistry) -> None:
    registry.register(ListSupportedSitesSkill())
    registry.register(RunResearchTaskSkill())
    registry.register(IngestResearchResultsSkill())
    registry.register(TavilySearchSkill())
    registry.register(ExtractWebpageTextSkill())
    registry.register(WebResearchIngestSkill())
    registry.register(AskRagSkill())
    registry.register(GetTaskArtifactSkill())
