import json

from application.dtos.onboarding.complete_onboarding_command import CompleteOnboardingCommand
from application.use_cases.onboarding.complete_onboarding_uc import CompleteOnboardingUseCase
from infrastructure.persistence.dynamo_user_repo import DynamoDBUserRepo
from shared.http_utils import dumps

# DI - khởi tạo một lần khi Lambda cold start
_user_repo = DynamoDBUserRepo()
_complete_onboarding_uc = CompleteOnboardingUseCase(_user_repo)


def _response(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": dumps(body),
    }


def handler(event, context):
    """Handler cho POST /onboarding/complete."""
    # 1. Lấy user_id từ JWT claims
    try:
        user_id = event["requestContext"]["authorizer"]["claims"]["sub"]
    except KeyError:
        return _response(401, {"error": "Unauthorized"})

    # 2. Parse body
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response(400, {"error": "JSON không hợp lệ"})

    # 3. Build command
    command = CompleteOnboardingCommand(
        user_id=user_id,
        display_name=body.get("display_name", ""),
        current_level=body.get("current_level", ""),
        target_level=body.get("target_level", ""),
        avatar_url=body.get("avatar_url", ""),
    )

    # 4. Execute use case
    result = _complete_onboarding_uc.execute(command)

    # 5. Format response
    if result.is_success:
        return _response(200, {
            "success": True,
            "message": result.value.message,
            "profile": result.value.profile,
        })

    error = result.error
    if "không tồn tại" in error:
        return _response(404, {"error": error})
    return _response(400, {"error": error})
