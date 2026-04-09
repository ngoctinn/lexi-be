from infrastructure.persistence.dynamo_user_repo import DynamoDBUserRepo
from application.use_cases.profile.get_profile import GetProfileUseCase
from application.use_cases.profile.update_profile import UpdateProfileUseCase
from interfaces.controllers.profile_controller import ProfileController

# DI - Khởi tạo các lớp một lần
user_repo = DynamoDBUserRepo()
get_profile_uc = GetProfileUseCase(user_repo)
update_profile_uc = UpdateProfileUseCase(user_repo)
profile_controller = ProfileController(get_profile_uc, update_profile_uc)

def handler(event, context):
    """
    Handler mỏng (Thin Handler) đóng vai trò điều phối hạ tầng API Gateway.
    Toàn bộ logic map dữ liệu và điều phối Use Case thuộc về ProfileController.
    """
    method = event.get("httpMethod")
    
    # Lấy User ID từ Authorizer (đã được Cognito xác thực)
    try:
        user_id = event["requestContext"]["authorizer"]["claims"]["sub"]
    except KeyError:
        return {
            "statusCode": 401, 
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}, 
            "body": '{"error": "Unauthorized"}'
        }

    if method == "GET":
        return profile_controller.get_profile(user_id)

    if method in ["PUT", "POST"]:
        body_str = event.get("body")
        return profile_controller.update_profile(user_id, body_str)

    return {
        "statusCode": 405, 
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}, 
        "body": '{"error": "Method not allowed"}'
    }
