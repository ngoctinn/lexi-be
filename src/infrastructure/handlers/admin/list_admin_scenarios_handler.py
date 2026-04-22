from infrastructure.persistence.dynamo_user_repo import DynamoDBUserRepo
from infrastructure.persistence.dynamo_scenario_repo import DynamoScenarioRepository
from application.use_cases.admin.list_admin_scenarios_uc import ListAdminScenariosUseCase
from infrastructure.handlers.admin._shared import check_admin, _response

_user_repo = DynamoDBUserRepo()
_scenario_repo = DynamoScenarioRepository()
_list_scenarios_uc = ListAdminScenariosUseCase(_scenario_repo)


def handler(event, context):
    """GET /admin/scenarios"""
    _, err = check_admin(event, _user_repo)
    if err:
        return err

    result = _list_scenarios_uc.execute()

    if result.is_success:
        return _response(200, result.value)

    return _response(500, {"error": result.error})
