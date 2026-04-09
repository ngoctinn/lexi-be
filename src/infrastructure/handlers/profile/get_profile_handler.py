import json
import os
import dataclasses
from infrastructure.persistence.dynamo_user_repo import DynamoDBUserRepo
from application.use_cases.profile.get_profile import GetProfileUseCase
from application.use_cases.profile.update_profile import UpdateProfileUseCase
from application.dtos.profile.update.update_profile_command import UpdateProfileCommand

# DI - Khởi tạo các lớp một lần
user_repo = DynamoDBUserRepo()
get_profile_uc = GetProfileUseCase(user_repo)
update_profile_uc = UpdateProfileUseCase(user_repo)

def _response(status, body):
    return {
        "statusCode": status, 
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*" # Chuẩn bị cho tích hợp Frontend
        }, 
        "body": json.dumps(body)
    }

def handler(event, context):
    method = event["httpMethod"]
    # Lấy User ID từ Authorizer (đã được Cognito xác thực)
    try:
        user_id = event["requestContext"]["authorizer"]["claims"]["sub"]
    except KeyError:
        return _response(401, {"error": "Unauthorized"})

    # --- XỬ LÝ GET (LẤY PROFILE) ---
    if method == "GET":
        result = get_profile_uc.execute(user_id)
        if not result.is_success:
            return _response(404, {"error": result.error})
        
        # Result value là GetProfileResponse DTO
        response_dto = result.value
        return _response(200, dataclasses.asdict(response_dto))

    # --- XỬ LÝ PUT/POST (CẬP NHẬT PROFILE / ONBOARDING) ---
    if method in ["PUT", "POST"]:
        try:
            body = json.loads(event.get("body") or "{}")
        except json.JSONDecodeError:
            return _response(400, {"error": "Invalid JSON body"})

        request = UpdateProfileCommand(
            user_id=user_id,
            display_name=body.get("display_name"),
            current_level=body.get("current_level"),
            learning_goal=body.get("learning_goal")
        )

        result = update_profile_uc.execute(request)
        if not result.is_success:
            return _response(400, {"error": result.error})

        response_dto = result.value
        return _response(200, dataclasses.asdict(response_dto))

    return _response(405, {"error": "Method not allowed"})
