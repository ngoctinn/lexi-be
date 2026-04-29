import logging

from infrastructure.persistence.dynamo_scenario_repo import DynamoScenarioRepository
from infrastructure.logging.config import configure_logging
from application.use_cases.scenario_use_cases import ListScenariosUseCase
from interfaces.controllers.scenario_controller import ScenarioController

# Configure logging
configure_logging("lambda")
logger = logging.getLogger(__name__)

# Initialize dependencies using dependency injection
scenario_repo = DynamoScenarioRepository()
list_scenarios_uc = ListScenariosUseCase(scenario_repo)
scenario_controller = ScenarioController(list_scenarios_uc)


def handler(event, context):
    """
    Handler mỏng (Thin Handler) - Chỉ đóng vai trò adapter hạ tầng.
    Logic Interface Adapter chuẩn nằm ở ScenarioController.
    """
    try:
        logger.info("Processing scenarios request")
        return scenario_controller.list_scenarios(event)
        
    except Exception as e:
        logger.exception("Error in scenarios_handler", extra={"context": {"error": str(e)}})
        # Fallback error response
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": '{"success": false, "message": "Internal server error"}'
        }
