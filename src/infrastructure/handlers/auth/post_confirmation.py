import logging
from src.infrastructure.handlers.auth._di import build_post_confirmation_use_case
from src.application.dtos.auth_dto import CreateUserProfileDTO

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_use_case = build_post_confirmation_use_case()


def handler(event, context):
    attrs = event["request"]["userAttributes"]
    dto = CreateUserProfileDTO(
        user_id=attrs["sub"],
        email=attrs["email"],
    )
    try:
        _use_case.execute(dto)
    except Exception as e:
        logger.error("Failed to create user profile: %s", e)
        raise
    return event
