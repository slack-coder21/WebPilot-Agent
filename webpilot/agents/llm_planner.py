import json

from pydantic import ValidationError

from webpilot.llm import build_chat_model
from webpilot.models import BrowserAction, PageObservation


class LLMPlanner:
    """Optional LLM planner with the same constrained action interface.

    Install the optional dependencies with `pip install -e ".[agent]"` and set
    `OPENAI_API_KEY` before using `--planner llm`.
    """

    def __init__(self, provider: str | None = None, model: str | None = None) -> None:
        self.model = build_chat_model(provider=provider, model=model)

    def next_action(self, task: str, site: str, observation: PageObservation | None) -> BrowserAction:
        obs = observation.model_dump() if observation else None
        prompt = (
            "You are a browser automation planner for technical research tasks.\n"
            "Return exactly one JSON object matching this schema:\n"
            '{"action":"goto|click|type|select|scroll|wait|extract|finish",'
            '"target_id":null,"value":null,"url":null}\n'
            "Use only element_id values from observation.interactive_elements.\n"
            "Prefer extract when the current search result page likely contains useful results.\n\n"
            f"Task: {task}\nSite: {site}\nObservation JSON: {json.dumps(obs, ensure_ascii=False)}"
        )
        response = self.model.invoke(prompt)
        content = response.content if isinstance(response.content, str) else str(response.content)
        try:
            payload = json.loads(_strip_code_fence(content))
            return BrowserAction.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise RuntimeError(f"Invalid LLM action: {content}") from exc


def _strip_code_fence(content: str) -> str:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    return text.strip()
