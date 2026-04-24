import json
import logging
from typing import Optional
from pydantic import ValidationError

from application.use_cases.admin_scenario_use_cases import CreateAdminScenarioUseCase
from application.use_cases.admin_scenario_use_cases import ListAdminScenariosUseCase
from application.use_cases.admin_scenario_use_cases import UpdateAdminScenarioUseCase
from application.use_cases.admin_user_use_cases import ListAdminUsersUseCase
from application.use_cases.admin_user_use_cases import UpdateAdminUserUseCase
from interfaces.presenters.http_presenter import HttpPresenter
from interfaces.view_models.base import OperationResult
from interfaces.view_models.admin_vm import AdminScenarioViewModel, AdminScenarioListViewModel, AdminUserViewModel, AdminUserListViewModel

logger = logging.getLogger(__name__)


class AdminController:
    """
    Điều phối logic cho các yêu cầu quản trị (Admin).
    
    Trách nhiệm:
    - Tiếp nhận yêu cầu từ Lambda Handler.
    - Gọi Use Case tương ứng.
    - Chuyển đổi Response DTO sang View Model.
    - Trả về OperationResult[ViewModel].
    """
    def __init__(
        self,
        create_scenario_uc: CreateAdminScenarioUseCase,
        list_scenarios_uc: ListAdminScenariosUseCase,
        update_scenario_uc: UpdateAdminScenarioUseCase,
        list_users_uc: ListAdminUsersUseCase,
        update_user_uc: UpdateAdminUserUseCase,
        presenter: HttpPresenter | None = None,
    ):
        self._create_scenario_uc = create_scenario_uc
        self._list_scenarios_uc = list_scenarios_uc
        self._update_scenario_uc = update_scenario_uc
        self._list_users_uc = list_users_uc
        self._update_user_uc = update_user_uc
        self._presenter = presenter or HttpPresenter()

    def create_scenario(self, body_str: str | None) -> OperationResult[AdminScenarioViewModel]:
        """Create a new scenario."""
        try:
            body = json.loads(body_str or "{}")
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in create_scenario request")
            return OperationResult.fail("Invalid JSON format", "BAD_REQUEST")

        try:
            logger.info("Creating scenario")
            result = self._create_scenario_uc.execute(
                scenario_title=body.get("scenario_title", ""),
                context=body.get("context", ""),
                roles=body.get("roles", []),
                goals=body.get("goals", []),
                difficulty_level=body.get("difficulty_level", ""),
                order=body.get("order", 0),
                notes=body.get("notes", ""),
                is_active=body.get("is_active", True),
            )
            
            if not result.is_success:
                logger.warning("Scenario creation failed", extra={"context": {"error": result.error}})
                return OperationResult.fail(result.error, "CREATION_FAILED")
            
            scenario = result.value
            view_model = AdminScenarioViewModel(
                scenario_id=str(scenario.scenario_id),
                scenario_title=scenario.scenario_title,
                context=scenario.context,
                roles=list(scenario.roles),
                goals=list(scenario.goals),
                is_active=scenario.is_active,
                usage_count=scenario.usage_count,
                difficulty_level=scenario.difficulty_level,
                order=scenario.order,
            )
            logger.info("Scenario created successfully", extra={"context": {"scenario_id": scenario.scenario_id}})
            return OperationResult.succeed(view_model)
        except ValidationError as exc:
            logger.warning("Validation error in create_scenario", extra={"context": {"errors": str(exc)}})
            return OperationResult.fail(f"Invalid request data: {str(exc)}", "VALIDATION_ERROR")
        except Exception as exc:
            logger.exception("Error creating scenario", extra={"context": {"error": str(exc)}})
            raise

    def list_scenarios(self) -> OperationResult[AdminScenarioListViewModel]:
        """List all scenarios."""
        try:
            logger.info("Listing scenarios")
            result = self._list_scenarios_uc.execute()
            
            if not result.is_success:
                logger.warning("Failed to list scenarios", extra={"context": {"error": result.error}})
                return OperationResult.fail(result.error, "LIST_FAILED")
            
            scenarios = [
                AdminScenarioViewModel(
                    scenario_id=str(s.scenario_id),
                    scenario_title=s.scenario_title,
                    context=s.context,
                    roles=list(s.roles),
                    goals=list(s.goals),
                    is_active=s.is_active,
                    usage_count=s.usage_count,
                    difficulty_level=s.difficulty_level,
                    order=s.order,
                )
                for s in result.value
            ]
            view_model = AdminScenarioListViewModel(scenarios=scenarios, total=len(scenarios))
            return OperationResult.succeed(view_model)
        except Exception as exc:
            logger.exception("Error listing scenarios", extra={"context": {"error": str(exc)}})
            raise

    def update_scenario(self, scenario_id: str, body_str: str | None) -> OperationResult[AdminScenarioViewModel]:
        """Update a scenario."""
        try:
            body = json.loads(body_str or "{}")
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in update_scenario request")
            return OperationResult.fail("Invalid JSON format", "BAD_REQUEST")

        try:
            logger.info("Updating scenario", extra={"context": {"scenario_id": scenario_id}})
            result = self._update_scenario_uc.execute(
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
            
            if not result.is_success:
                logger.warning("Scenario update failed", extra={"context": {"scenario_id": scenario_id, "error": result.error}})
                return OperationResult.fail(result.error, "UPDATE_FAILED")
            
            scenario = result.value
            view_model = AdminScenarioViewModel(
                scenario_id=str(scenario.scenario_id),
                scenario_title=scenario.scenario_title,
                context=scenario.context,
                roles=list(scenario.roles),
                goals=list(scenario.goals),
                is_active=scenario.is_active,
                usage_count=scenario.usage_count,
                difficulty_level=scenario.difficulty_level,
                order=scenario.order,
                notes=scenario.notes if hasattr(scenario, 'notes') else "",
                created_at=scenario.created_at if hasattr(scenario, 'created_at') else "",
                updated_at=scenario.updated_at if hasattr(scenario, 'updated_at') else "",
            )
            logger.info("Scenario updated successfully", extra={"context": {"scenario_id": scenario_id}})
            return OperationResult.succeed(view_model)
        except ValidationError as exc:
            logger.warning("Validation error in update_scenario", extra={"context": {"scenario_id": scenario_id, "errors": str(exc)}})
            return OperationResult.fail(f"Invalid request data: {str(exc)}", "VALIDATION_ERROR")
        except Exception as exc:
            logger.exception("Error updating scenario", extra={"context": {"scenario_id": scenario_id, "error": str(exc)}})
            raise

    def list_users(self) -> OperationResult[AdminUserListViewModel]:
        """List all users."""
        try:
            logger.info("Listing users")
            result = self._list_users_uc.execute()
            
            if not result.is_success:
                logger.warning("Failed to list users", extra={"context": {"error": result.error}})
                return OperationResult.fail(result.error, "LIST_FAILED")
            
            users = [
                AdminUserViewModel(
                    user_id=u.user_id,
                    email=u.email,
                    display_name=u.display_name,
                    role=u.role,
                    is_active=u.is_active,
                    created_at=u.created_at,
                )
                for u in result.value
            ]
            view_model = AdminUserListViewModel(users=users, total=len(users))
            return OperationResult.succeed(view_model)
        except Exception as exc:
            logger.exception("Error listing users", extra={"context": {"error": str(exc)}})
            raise

    def update_user(self, user_id: str, body_str: str | None) -> OperationResult[AdminUserViewModel]:
        """Update a user."""
        try:
            body = json.loads(body_str or "{}")
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in update_user request")
            return OperationResult.fail("Invalid JSON format", "BAD_REQUEST")

        try:
            logger.info("Updating user", extra={"context": {"user_id": user_id}})
            result = self._update_user_uc.execute(
                user_id=user_id,
                role=body.get("role"),
                is_active=body.get("is_active"),
            )
            
            if not result.is_success:
                logger.warning("User update failed", extra={"context": {"user_id": user_id, "error": result.error}})
                return OperationResult.fail(result.error, "UPDATE_FAILED")
            
            user = result.value
            view_model = AdminUserViewModel(
                user_id=user.user_id,
                email=user.email,
                display_name=user.display_name,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
            )
            logger.info("User updated successfully", extra={"context": {"user_id": user_id}})
            return OperationResult.succeed(view_model)
        except ValidationError as exc:
            logger.warning("Validation error in update_user", extra={"context": {"user_id": user_id, "errors": str(exc)}})
            return OperationResult.fail(f"Invalid request data: {str(exc)}", "VALIDATION_ERROR")
        except Exception as exc:
            logger.exception("Error updating user", extra={"context": {"user_id": user_id, "error": str(exc)}})
            raise
