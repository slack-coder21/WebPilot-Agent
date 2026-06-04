from functools import lru_cache
from os import getenv
from pathlib import Path

from pydantic import BaseModel

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional during partial installs
    load_dotenv = None

if load_dotenv:
    load_dotenv()


class LLMSettings(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4.1-mini"
    api_key: str | None = None
    base_url: str | None = None
    temperature: float = 0


class WebSearchSettings(BaseModel):
    tavily_api_key: str | None = None


class AppSettings(BaseModel):
    runs_dir: Path = Path("runs")
    vector_dir: Path = Path("vector_store")
    default_embedding_provider: str = "hash"
    embedding_model: str = "text-embedding-3-small"


@lru_cache
def get_app_settings() -> AppSettings:
    return AppSettings(
        runs_dir=Path(getenv("WEBPILOT_RUNS_DIR", "runs")),
        vector_dir=Path(getenv("WEBPILOT_VECTOR_DIR", "vector_store")),
        default_embedding_provider=getenv("WEBPILOT_EMBEDDINGS_PROVIDER", "hash"),
        embedding_model=getenv("WEBPILOT_EMBEDDING_MODEL", "text-embedding-3-small"),
    )


def get_llm_settings(provider: str | None = None, model: str | None = None) -> LLMSettings:
    selected_provider = (provider or getenv("WEBPILOT_LLM_PROVIDER", "openai")).lower()
    if selected_provider == "deepseek":
        return LLMSettings(
            provider="deepseek",
            model=model or getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            api_key=getenv("DEEPSEEK_API_KEY"),
            base_url=getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        )

    return LLMSettings(
        provider="openai",
        model=model or getenv("OPENAI_MODEL", getenv("WEBPILOT_MODEL", "gpt-4.1-mini")),
        api_key=getenv("OPENAI_API_KEY"),
        base_url=getenv("OPENAI_BASE_URL"),
    )


def get_web_search_settings() -> WebSearchSettings:
    return WebSearchSettings(tavily_api_key=getenv("TAVILY_API_KEY"))
