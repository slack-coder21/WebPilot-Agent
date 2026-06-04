from functools import lru_cache
from typing import Any

from webpilot.skills.base import AgentSkill


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, AgentSkill] = {}

    def register(self, skill: AgentSkill) -> None:
        if skill.name in self._skills:
            raise ValueError(f"Skill already registered: {skill.name}")
        self._skills[skill.name] = skill

    def get(self, name: str) -> AgentSkill:
        try:
            return self._skills[name]
        except KeyError as exc:
            raise ValueError(f"Unknown skill: {name}") from exc

    def list(self) -> list[dict[str, str]]:
        return [
            {"name": skill.name, "description": skill.description}
            for skill in sorted(self._skills.values(), key=lambda item: item.name)
        ]

    def run(self, name: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.get(name).run(payload or {})


@lru_cache
def get_skill_registry() -> SkillRegistry:
    from webpilot.skills.builtins import register_builtin_skills

    registry = SkillRegistry()
    register_builtin_skills(registry)
    return registry
