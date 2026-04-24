import logging

from infrastructure.persistence.dynamo_scenario_repo import DynamoScenarioRepository
from infrastructure.logging.config import configure_logging
from interfaces.presenters.http_presenter import HttpPresenter
from interfaces.view_models.scenario_vm import ScenarioListViewModel

# Configure logging
configure_logging("lambda")
logger = logging.getLogger(__name__)


def handler(event, context):
    """GET /scenarios - List all active scenarios"""
    try:
        logger.info("Listing scenarios")
        repository = DynamoScenarioRepository()
        scenarios = sorted(
            repository.list_active(),
            key=lambda item: item.order,
        )
        
        presenter = HttpPresenter()
        scenario_list = ScenarioListViewModel(
            scenarios=[
                {
                    "scenario_id": str(s.scenario_id),
                    "scenario_title": s.scenario_title,
                    "context": s.context,
                    "roles": list(s.roles),
                    "goals": list(s.goals),
                    "is_active": s.is_active,
                    "usage_count": s.usage_count,
                    "difficulty_level": s.difficulty_level,
                    "order": s.order,
                }
                for s in scenarios
            ],
            total=len(scenarios),
        )
        
        return presenter.present_success(scenario_list)
    except Exception as e:
        logger.exception("Error listing scenarios", extra={"context": {"error": str(e)}})
        presenter = HttpPresenter()
        return presenter._format_response(500, {"success": False, "message": "Internal server error", "error": str(e)})
