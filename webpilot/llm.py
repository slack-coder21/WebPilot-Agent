from webpilot.settings import LLMSettings, get_llm_settings


def build_chat_model(provider: str | None = None, model: str | None = None):
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        raise RuntimeError('LLM support requires: pip install -e ".[agent]"') from exc

    settings: LLMSettings = get_llm_settings(provider=provider, model=model)
    if not settings.api_key:
        env_name = "DEEPSEEK_API_KEY" if settings.provider == "deepseek" else "OPENAI_API_KEY"
        raise RuntimeError(f"{settings.provider} planner requires {env_name}")

    kwargs = {
        "model": settings.model,
        "api_key": settings.api_key,
        "temperature": settings.temperature,
    }
    if settings.base_url:
        kwargs["base_url"] = settings.base_url

    return ChatOpenAI(**kwargs)
