from infrastructure.persistence.dynamo_user_repo import DynamoDBUserRepo
from infrastructure.persistence.dynamo_scenario_repo import DynamoScenarioRepository
from application.use_cases.admin.update_admin_scenario_uc import UpdateAdminScenarioUseCase
from infrastructure.handlers.admin._shared import check_admin, parse_body, _response

_user_repo = DynamoDBUserRepo()
_scenario_repo = DynamoScenarioRepository()
_update_scenario_uc = UpdateAdminScenarioUseCase(_scenario_repo)


def handler(event, context):
    """PATCH /admin/scenarios/{scenario_id}"""
    _, err = check_admin(event, _user_repo)
    if err:
        return err

    path_params = event.get("pathParameters") or {}
    scenario_id = path_params.get("scenario_id", "")
    if not scenario_id:
        return _response(400, {"error": "Thiếu scenario_id"})

    body = parse_body(event)
    result = _update_scenario_uc.execute(
        scenario_id=scenario_id,
        scenario_title=body.get("scenario_title"),
        context=body.get("context"),
        roles=body.get("roles"),
        goals=body.get("goals"),
        difficulty_level=body.get("difficulty_level"),
        order=body.get("order"),
        notes=body.get("notes"),
        is_active=body.get("is_active"),
    )

    if result.is_success:
        return _response(200, {"success": True, "scenario": result.value})

    if "không tồn tại" in result.error:
        return _response(404, {"error": result.error})
    return _response(400, {"error": result.error})
