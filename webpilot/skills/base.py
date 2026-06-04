from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class SkillResult(BaseModel):
    ok: bool = True
    data: dict[str, Any] = {}


class AgentSkill(ABC):
    name: str
    description: str

    @abstractmethod
    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Run this skill with a JSON-serializable payload."""
