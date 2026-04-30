import logging

from infrastructure.persistence.dynamo_user_repo import DynamoDBUserRepo
from infrastructure.logging.config import configure_logging
from infrastructure.handlers.admin._shared import check_admin
from interfaces.controllers.admin_controller import AdminController
from interfaces.presenters.http_presenter import HttpPresenter

# Configure logging
configure_logging("lambda")
logger = logging.getLogger(__name__)

# Module-level singleton (AWS best practice)
# Initialized once per Lambda container, reused across invocations
_admin_controller = None


def build_admin_controller() -> AdminController:
    """Build admin controller with dependencies."""
    from application.use_cases.admin_scenario_use_cases import CreateAdminScenarioUseCase
    from application.use_cases.admin_scenario_use_cases import ListAdminScenariosUseCase
    from application.use_cases.admin_scenario_use_cases import UpdateAdminScenarioUseCase
    from application.use_cases.admin_user_use_cases import ListAdminUsersUseCase
    from application.use_cases.admin_user_use_cases import UpdateAdminUserUseCase
    from infrastructure.persistence.dynamo_scenario_repo import DynamoScenarioRepository
    
    user_repo = DynamoDBUserRepo()
    scenario_repo = DynamoScenarioRepository()
    
    create_scenario_uc = CreateAdminScenarioUseCase(scenario_repo)
    list_scenarios_uc = ListAdminScenariosUseCase(scenario_repo)
    update_scenario_uc = UpdateAdminScenarioUseCase(scenario_repo)
    list_users_uc = ListAdminUsersUseCase(user_repo)
    update_user_uc = UpdateAdminUserUseCase(user_repo)
    
    return AdminController(
        create_scenario_uc=create_scenario_uc,
        list_scenarios_uc=list_scenarios_uc,
        update_scenario_uc=update_scenario_uc,
        list_users_uc=list_users_uc,
        update_user_uc=update_user_uc,
    )


def _get_or_build_admin_controller() -> AdminController:
    """
    Lazy initialization of admin controller (singleton pattern).
    
    AWS best practice: Initialize SDK clients and dependencies outside handler
    to take advantage of execution environment reuse.
    
    Returns:
        AdminController: Reusable controller instance
    """
    global _admin_controller
    if _admin_controller is None:
        logger.info("Building admin controller (first invocation in this container)")
        _admin_controller = build_admin_controller()
    return _admin_controller


def _unauthorized_response():
    return {
        "statusCode": 401,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": '{"error": "Unauthorized"}',
    }


def handler(event, context):
    """GET /admin/users
    
    Authentication is handled by API Gateway Cognito Authorizer.
    Authorization (admin role check) is performed in this handler.
    """
    try:
        # Use cognito:username to match PostConfirmation trigger's event['userName']
        # For federated users (Google), this will be "Google_xxx" format
        user_id = event["requestContext"]["authorizer"]["claims"]["cognito:username"]
        logger.info("List users handler invoked", extra={"context": {"user_id": user_id}})
    except KeyError:
        logger.error("Missing Cognito claims - check API Gateway authorizer configuration")
        return _unauthorized_response()

    # Check admin role
    user_repo = DynamoDBUserRepo()
    _, err = check_admin(event, user_repo)
    if err:
        logger.warning("Admin check failed", extra={"context": {"user_id": user_id}})
        return err

    controller = _get_or_build_admin_controller()
    presenter = HttpPresenter()
    
    result = controller.list_users()
    if result.is_success:
        return presenter.present_success(result.value)
    else:
        return presenter._format_response(500, {"error": result.error})
