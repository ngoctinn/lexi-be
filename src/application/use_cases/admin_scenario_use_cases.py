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


class ListAdminScenariosUseCase:
    """Liệt kê tất cả scenario kể cả inactive — dùng cho Admin."""

    def __init__(self, repo: ScenarioRepository):
        self._repo = repo

    def execute(self) -> Result:
        scenarios = self._repo.list_all()
        scenarios.sort(key=lambda s: s.order)

        return Result.success({
            "scenarios": [_scenario_to_dict(s) for s in scenarios]
        })


class UpdateAdminScenarioUseCase:
    """Cập nhật scenario đã tồn tại — dùng cho Admin."""

    def __init__(self, repo: ScenarioRepository):
        self._repo = repo

    def execute(
        self,
        scenario_id: str,
        scenario_title: Optional[str] = None,
        context: Optional[str] = None,
        roles: Optional[List[str]] = None,
        goals: Optional[List[str]] = None,
        difficulty_level: Optional[str] = None,
        order: Optional[int] = None,
        notes: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Result:
        scenario = self._repo.get_by_id(scenario_id)
        if not scenario:
            return Result.failure("Kịch bản không tồn tại.")

        # Validate nếu có
        if scenario_title is not None and len(scenario_title.strip()) == 0:
            return Result.failure("scenario_title không được để trống")
        if scenario_title is not None and len(scenario_title) > 100:
            return Result.failure("scenario_title không được vượt quá 100 ký tự")

        if roles is not None and len(roles) != 2:
            return Result.failure("roles phải có đúng 2 phần tử")

        if goals is not None and len(goals) < 1:
            return Result.failure("goals phải có ít nhất 1 phần tử")

        if difficulty_level is not None and difficulty_level not in _VALID_LEVELS:
            return Result.failure(f"difficulty_level '{difficulty_level}' không hợp lệ. Chỉ chấp nhận: A1, A2, B1, B2, C1, C2")

        scenario.update_info(
            scenario_title=scenario_title,
            context=context,
            roles=roles,
            goals=goals,
            difficulty_level=difficulty_level,
            order=order,
            notes=notes,
            is_active=is_active,
        )

        self._repo.update(scenario)

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


def _scenario_to_dict(s) -> dict:
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
