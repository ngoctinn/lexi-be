import logging

from infrastructure.persistence.dynamo_user_repo import DynamoDBUserRepo
from application.use_cases.user_profile_use_cases import GetProfileUseCase, UpdateProfileUseCase
from interfaces.controllers.profile_controller import ProfileController
from interfaces.presenters.http_presenter import HttpPresenter
from infrastructure.logging.config import configure_logging

logger = logging.getLogger(__name__)
configure_logging("lambda")

# Module-level singleton (AWS best practice)
# Initialized once per Lambda container, reused across invocations
_profile_controller = None


def build_profile_controller() -> ProfileController:
    """Build profile controller with dependencies."""
    user_repo = DynamoDBUserRepo()
    get_profile_uc = GetProfileUseCase(user_repo)
    update_profile_uc = UpdateProfileUseCase(user_repo)
    return ProfileController(get_profile_uc, update_profile_uc)


def _get_or_build_profile_controller() -> ProfileController:
    """
    Lazy initialization of profile controller (singleton pattern).
    
    AWS best practice: Initialize SDK clients and dependencies outside handler
    to take advantage of execution environment reuse.
    
    Returns:
        ProfileController: Reusable controller instance
    """
    global _profile_controller
    if _profile_controller is None:
        logger.info("Building profile controller (first invocation in this container)")
        _profile_controller = build_profile_controller()
    return _profile_controller


def _unauthorized_response():
    return {
        "statusCode": 401,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": '{"error": "Unauthorized"}',
    }


def handler(event, context):
    """Lambda handler for PATCH /profile."""
    presenter = HttpPresenter()
    
    try:
        user_id = event["requestContext"]["authorizer"]["claims"]["sub"]
        logger.info("Update profile handler invoked", extra={"context": {"user_id": user_id}})
    except KeyError:
        logger.warning("Unauthorized access attempt")
        return _unauthorized_response()

    try:
        controller = _get_or_build_profile_controller()
        body_str = event.get("body")
        result = controller.update_profile(user_id, body_str)
        
        if result.is_success:
            return presenter.present_success(result.value)
        else:
            return presenter.present_bad_request(result.error)
    except Exception as exc:
        logger.exception("Error updating profile", extra={"context": {"user_id": user_id, "error": str(exc)}})
        return presenter._format_response(500, {"success": False, "message": "Internal server error", "error": str(exc)})
