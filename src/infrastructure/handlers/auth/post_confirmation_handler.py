from infrastructure.persistence.dynamo_user_repo import DynamoDBUserRepo
from application.use_cases.auth.create_user_profile import CreateUserProfileUseCase
from interfaces.controllers.auth_controller import AuthController

# Khởi tạo DI ở ngoài handler
user_repo = DynamoDBUserRepo()
create_profile_use_case = CreateUserProfileUseCase(user_repo)
auth_controller = AuthController(create_profile_use_case)

def handler(event, context):
    """
    Handler mỏng (Thin Handler) - Chỉ đóng vai trò adapter hạ tầng.
    Logic Interface Adapter chuẩn nằm ở AuthController.
    """
    if event['triggerSource'] != "PostConfirmation_ConfirmSignUp":
        return event

    return auth_controller.handle_post_confirmation(event)
