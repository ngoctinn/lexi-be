from functools import lru_cache

from infrastructure.persistence.dynamo_user_repo import DynamoDBUserRepo
from application.use_cases.profile.get_profile import GetProfileUseCase
from application.use_cases.profile.update_profile import UpdateProfileUseCase
from interfaces.controllers.profile_controller import ProfileController


def build_profile_controller() -> ProfileController:
    """Build profile controller with dependencies."""
    user_repo = DynamoDBUserRepo()
    get_profile_uc = GetProfileUseCase(user_repo)
    update_profile_uc = UpdateProfileUseCase(user_repo)
    return ProfileController(get_profile_uc, update_profile_uc)


@lru_cache(maxsize=1)
def get_profile_controller() -> ProfileController:
    """Get cached profile controller (reuse across invocations)."""
    return build_profile_controller()


def _unauthorized_response():
    return {
        "statusCode": 401,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": '{"error": "Unauthorized"}',
    }


def handler(event, context):
    """Lambda handler for PATCH /profile."""
    try:
        user_id = event["requestContext"]["authorizer"]["claims"]["sub"]
    except KeyError:
        return _unauthorized_response()

    controller = get_profile_controller()
    body_str = event.get("body")
    return controller.update_profile(user_id, body_str)
