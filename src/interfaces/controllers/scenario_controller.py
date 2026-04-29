import logging
from typing import Dict, Any

from application.use_cases.scenario_use_cases import ListScenariosUseCase
from interfaces.presenters.http_presenter import HttpPresenter
from interfaces.view_models.scenario_vm import ScenarioListViewModel
from shared.result import Result

logger = logging.getLogger(__name__)


class ScenarioController:
    """
    Controller điều phối các thao tác với Scenario cho public endpoints.
    
    Trách nhiệm:
    - Tiếp nhận HTTP requests từ Lambda handlers
    - Phối hợp với Use Cases để thực thi business logic
    - Chuyển đổi kết quả sang View Models
    - Trả về HTTP responses thông qua Presenter
    """
    
    def __init__(self, list_scenarios_uc: ListScenariosUseCase, presenter: HttpPresenter = None):
        self._list_scenarios_uc = list_scenarios_uc
        self._presenter = presenter or HttpPresenter()

    def list_scenarios(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Xử lý request GET /scenarios - Liệt kê các scenario active.
        """
        try:
            logger.info("Processing list scenarios request")
            
            # Execute business logic
            result = self._list_scenarios_uc.execute()
            
            if not result.is_success:
                logger.error("Failed to list scenarios", extra={"context": {"error": result.error}})
                return self._presenter.present_error(result.error, status_code=500)
            
            # Convert to view model
            data = result.value
            scenario_list = ScenarioListViewModel(
                scenarios=data["scenarios"],
                total=data["total"]
            )
            
            logger.info("Successfully listed scenarios", extra={"context": {"total": data["total"]}})
            return self._presenter.present_success(scenario_list)
            
        except Exception as e:
            logger.exception("System error in ScenarioController", extra={"context": {"error": str(e)}})
            return self._presenter.present_error("Internal server error", status_code=500)