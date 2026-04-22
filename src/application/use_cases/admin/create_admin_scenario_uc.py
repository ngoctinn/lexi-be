from datetime import datetime, timezone
from typing import List, Optional
from application.repositories.scenario_repository import ScenarioRepository
from domain.entities.scenario import Scenario
from domain.value_objects.enums import ProficiencyLevel
from shared.result import Result
from shared.utils.ulid_util import new_ulid

_VALID_LEVELS = {level.value for level in ProficiencyLevel}


class CreateAdminScenarioUseCase:
    """Tạo scenario mới — dùng cho Admin."""

    def __init__(self, repo: ScenarioRepository):
        self._repo = repo

    def execute(
        self,
        scenario_title: str,
        context: str,
        roles: List[str],
        goals: List[str],
        difficulty_level: str = "",
        order: int = 0,
        notes: str = "",
        is_active: bool = True,
    ) -> Result:
        # Validation
        if not scenario_title or not scenario_title.strip():
            return Result.failure("scenario_title không được để trống")
        if len(scenario_title) > 100:
            return Result.failure("scenario_title không được vượt quá 100 ký tự")

        if not context or not context.strip():
            return Result.failure("context không được để trống")
        if len(context) > 100:
            return Result.failure("context không được vượt quá 100 ký tự")

        if not roles or len(roles) != 2:
            return Result.failure("roles phải có đúng 2 phần tử")

        if not goals or len(goals) < 1:
            return Result.failure("goals phải có ít nhất 1 phần tử")

        if difficulty_level and difficulty_level not in _VALID_LEVELS:
            return Result.failure(f"difficulty_level '{difficulty_level}' không hợp lệ. Chỉ chấp nhận: A1, A2, B1, B2, C1, C2")

        now = datetime.now(timezone.utc).isoformat()
        scenario = Scenario(
            scenario_id=new_ulid(),
            scenario_title=scenario_title.strip(),
            context=context.strip(),
            roles=[r.strip() for r in roles],
            goals=[g.strip() for g in goals],
            is_active=is_active,
            usage_count=0,
            difficulty_level=difficulty_level,
            order=order,
            notes=notes,
            created_at=now,
            updated_at=now,
        )

        self._repo.create(scenario)

        return Result.success({
            "scenario_id": scenario.scenario_id,
            "scenario_title": scenario.scenario_title,
            "context": scenario.context,
            "roles": scenario.roles,
            "goals": scenario.goals,
            "is_active": scenario.is_active,
            "usage_count": scenario.usage_count,
            "difficulty_level": scenario.difficulty_level,
            "order": scenario.order,
            "notes": scenario.notes,
            "created_at": scenario.created_at,
            "updated_at": scenario.updated_at,
        })
