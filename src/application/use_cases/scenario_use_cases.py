from typing import List
from application.repositories.scenario_repository import ScenarioRepository
from domain.entities.scenario import Scenario
from shared.result import Result


class ListScenariosUseCase:
    """Liệt kê các scenario active — dùng cho Learner (public endpoint)."""

    def __init__(self, repo: ScenarioRepository):
        self._repo = repo

    def execute(self) -> Result:
        scenarios = self._repo.list_active()
        scenarios.sort(key=lambda s: s.order)

        return Result.success({
            "scenarios": [_scenario_to_dict(s) for s in scenarios],
            "total": len(scenarios)
        })


def _scenario_to_dict(s: Scenario) -> dict:
    """Convert scenario entity to dict for API response."""
    return {
        "scenario_id": s.scenario_id,
        "scenario_title": s.scenario_title,
        "context": s.context,
        "roles": s.roles,
        "goals": s.goals,
        "is_active": s.is_active,
        "usage_count": s.usage_count,
        "difficulty_level": s.difficulty_level,
        "order": s.order,
    }