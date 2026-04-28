"""
Lambda handler for POST /admin/scenarios (create scenario).
"""
import logging
from typing import Any

from application.use_cases.admin_scenario_use_cases import (
    CreateAdminScenarioUseCase,
    ListAdminScenariosUseCase,
    UpdateAdminScenarioUseCase,
)
from application.use_cases.admin_user_use_cases import (
    ListAdminUsersUseCase,
    UpdateAdminUserUseCase,
)
from infrastructure.persistence.dynamo_user_repo import DynamoDBUserRepo
from infrastructure.persistence.dynamo_scenario_repo import DynamoScenarioRepository
from infrastructure.logging.config import configure_logging
from infrastructure.handlers.admin_base_handler import AdminBaseHandler
from interfaces.controllers.admin_controller import AdminController

# Configure logging
configure_logging("lambda")
logger = logging.getLogger(__name__)


class CreateAdminScenarioHandler(AdminBaseHandler[AdminController]):
    """Handler for creating admin scenario."""

    def build_dependencies(self) -> AdminController:
        """Build admin controller with dependencies."""
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

    def handle(self, user_id: str, event: dict, context: Any) -> dict:
        """Handle scenario creation."""
        controller = self.get_dependencies()
        result = controller.create_scenario(event.get("body"))
        
        if result.is_success:
            return self.presenter.present_created(result.value)
        else:
            return self.presenter._format_response(400, {
                "error": result.error
            })


# Module-level handler instance (singleton)
_handler = CreateAdminScenarioHandler()


def handler(event, context):
    """Lambda handler entry point."""
    return _handler(event, context)
