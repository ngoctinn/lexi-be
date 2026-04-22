from infrastructure.persistence.dynamo_user_repo import DynamoDBUserRepo
from infrastructure.persistence.dynamo_scenario_repo import DynamoScenarioRepository
from application.use_cases.admin.create_admin_scenario_uc import CreateAdminScenarioUseCase
from infrastructure.handlers.admin._shared import check_admin, parse_body, _response

_user_repo = DynamoDBUserRepo()
_scenario_repo = DynamoScenarioRepository()
_create_scenario_uc = CreateAdminScenarioUseCase(_scenario_repo)


def handler(event, context):
    """POST /admin/scenarios"""
    _, err = check_admin(event, _user_repo)
    if err:
        return err

    body = parse_body(event)
    result = _create_scenario_uc.execute(
        scenario_title=body.get("scenario_title", ""),
        context=body.get("context", ""),
        roles=body.get("roles", []),
        goals=body.get("goals", []),
        difficulty_level=body.get("difficulty_level", ""),
        order=body.get("order", 0),
        notes=body.get("notes", ""),
        is_active=body.get("is_active", True),
    )

    if result.is_success:
        return _response(201, {"success": True, "scenario": result.value})

    return _response(400, {"error": result.error})
