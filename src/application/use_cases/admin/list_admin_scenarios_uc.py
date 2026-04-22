from application.repositories.scenario_repository import ScenarioRepository
from shared.result import Result


class ListAdminScenariosUseCase:
    """Liệt kê tất cả scenario kể cả inactive — dùng cho Admin."""

    def __init__(self, repo: ScenarioRepository):
        self._repo = repo

    def execute(self) -> Result:
        scenarios = self._repo.list_all()
        scenarios.sort(key=lambda s: s.order)

        return Result.success({
            "scenarios": [_to_dict(s) for s in scenarios]
        })


def _to_dict(s) -> dict:
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
        "notes": s.notes,
        "created_at": s.created_at,
        "updated_at": s.updated_at,
    }
