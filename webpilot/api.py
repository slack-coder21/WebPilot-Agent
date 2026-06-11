import json
from asyncio import sleep

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from webpilot.models import AsyncTaskCreated, AsyncTaskState, TaskTraceEvent, WorkflowResult
from webpilot.rag import RagAnswer
from webpilot.sites import SUPPORTED_SITES
from webpilot.skills import get_skill_registry
from webpilot.skills.builtins import find_run_dir
from webpilot.task_runtime import task_runtime


class TaskCreateRequest(BaseModel):
    task: str = Field(min_length=3)
    site: str = "arxiv"
    limit: int = Field(default=5, ge=1, le=10)
    planner: str = "rule"
    llm_provider: str = "openai"
    llm_model: str | None = None
    headless: bool = True


class IngestResponse(BaseModel):
    documents: int
    vector_store: str = "chroma"


class TavilySearchRequest(BaseModel):
    query: str = Field(min_length=3)
    max_results: int = Field(default=5, ge=1, le=10)
    search_depth: str = "basic"


class ExtractWebpageRequest(BaseModel):
    url: str = Field(min_length=8)
    use_tavily_extract: bool = True


class WebIngestRequest(BaseModel):
    query: str = Field(min_length=3)
    max_results: int = Field(default=5, ge=1, le=10)
    search_depth: str = "basic"
    use_tavily_extract: bool = True


class RagQuestionRequest(BaseModel):
    question: str = Field(min_length=3)
    llm_provider: str = "openai"
    llm_model: str | None = None
    k: int = Field(default=5, ge=1, le=10)
    use_llm: bool = True


app = FastAPI(
    title="WebPilot Agent API",
    version="0.2.0",
    description="REST API for browser research agents, LangChain RAG, and vector search.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "backend": "fastapi",
        "rag": "langchain",
        "vector_store": "chroma",
        "skills": "enabled",
        "mcp": "available",
    }


@app.get("/api/sites")
def sites() -> dict[str, list[str]]:
    return get_skill_registry().run("list_supported_sites")


@app.get("/api/skills")
def skills() -> dict[str, list[dict[str, str]]]:
    return {"skills": get_skill_registry().list()}


@app.post("/api/tasks", response_model=WorkflowResult)
def create_task(request: TaskCreateRequest) -> WorkflowResult:
    try:
        payload = get_skill_registry().run(
            "run_research_task",
            request.model_dump(),
        )
        return WorkflowResult.model_validate(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Task execution failed: {exc}") from exc


@app.post("/api/tasks/async", response_model=AsyncTaskCreated)
def create_async_task(request: TaskCreateRequest) -> AsyncTaskCreated:
    _validate_task_request(request)
    state = task_runtime.create(request.model_dump())
    return AsyncTaskCreated(
        run_id=state.run_id,
        status=state.status,
        events_url=f"/api/tasks/{state.run_id}/events",
        status_url=f"/api/tasks/{state.run_id}/status",
    )


@app.get("/api/tasks/{run_id}/status", response_model=AsyncTaskState)
def get_async_task_status(run_id: str) -> AsyncTaskState:
    try:
        return task_runtime.get(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Task run not found") from exc


@app.get("/api/tasks/{run_id}/events")
async def stream_async_task_events(run_id: str) -> StreamingResponse:
    try:
        task_runtime.get(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Task run not found") from exc

    async def event_stream():
        last_index = 0
        last_status = None
        while True:
            try:
                state = task_runtime.get(run_id)
            except KeyError:
                yield _sse("error", json.dumps({"error": "Task run not found"}))
                break

            if state.status != last_status:
                yield _sse("status", state.model_dump_json())
                last_status = state.status

            for event in state.trace[last_index:]:
                yield _sse("trace", event.model_dump_json())
            last_index = len(state.trace)

            if state.status in {"completed", "failed"}:
                yield _sse(state.status, state.model_dump_json())
                break

            await sleep(0.5)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/tasks/{task_id}/artifacts/{artifact_name}")
def get_task_artifact(task_id: str, artifact_name: str):
    if artifact_name not in {"trace.json", "results.json", "report.md"}:
        raise HTTPException(status_code=404, detail="Unknown artifact")

    try:
        run_dir = find_run_dir(task_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    artifact_path = run_dir / artifact_name
    if not artifact_path.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")
    return FileResponse(artifact_path)


@app.get("/api/tasks/{task_id}/trace", response_model=list[TaskTraceEvent])
def get_task_trace(task_id: str) -> list[TaskTraceEvent]:
    try:
        run_dir = find_run_dir(task_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    trace_path = run_dir / "trace.json"
    if not trace_path.exists():
        raise HTTPException(status_code=404, detail="Trace artifact not found")

    try:
        payload = json.loads(trace_path.read_text(encoding="utf-8"))
        return [TaskTraceEvent.model_validate(event) for event in payload]
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Trace artifact is not valid JSON") from exc


@app.post("/api/rag/ingestions", response_model=IngestResponse)
def ingest_research_results() -> IngestResponse:
    try:
        payload = get_skill_registry().run("ingest_research_results")
        return IngestResponse.model_validate(payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/search/tavily")
def search_tavily(request: TavilySearchRequest) -> dict:
    try:
        return get_skill_registry().run("tavily_search", request.model_dump())
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Tavily search failed: {exc}") from exc


@app.post("/api/web/extract")
def extract_webpage(request: ExtractWebpageRequest) -> dict:
    try:
        return get_skill_registry().run("extract_webpage_text", request.model_dump())
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Webpage extraction failed: {exc}") from exc


@app.post("/api/rag/web-ingestions")
def ingest_web_research(request: WebIngestRequest) -> dict:
    try:
        return get_skill_registry().run("web_research_ingest", request.model_dump())
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Web research ingestion failed: {exc}") from exc


@app.post("/api/rag/questions", response_model=RagAnswer)
def ask_rag(request: RagQuestionRequest) -> RagAnswer:
    try:
        payload = get_skill_registry().run("ask_rag", request.model_dump())
        return RagAnswer.model_validate(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"RAG query failed: {exc}") from exc


def _validate_task_request(request: TaskCreateRequest) -> None:
    if request.site not in SUPPORTED_SITES:
        raise HTTPException(status_code=400, detail=f"Unsupported site: {request.site}")
    if request.planner not in {"rule", "llm"}:
        raise HTTPException(status_code=400, detail="planner must be 'rule' or 'llm'")
    if request.llm_provider not in {"openai", "deepseek"}:
        raise HTTPException(status_code=400, detail="llm_provider must be 'openai' or 'deepseek'")


def _sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"
