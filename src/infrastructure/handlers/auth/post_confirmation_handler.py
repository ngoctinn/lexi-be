from infrastructure.persistence.dynamo_user_repo import DynamoDBUserRepo
from application.use_cases.auth.create_user_profile import CreateUserProfileUseCase
from application.dtos.auth.create_profile.create_profile_command import CreateUserProfileCommand


# Khởi tạo DI ở ngoài handler
user_repo = DynamoDBUserRepo()
create_profile_use_case = CreateUserProfileUseCase(user_repo)

def handler(event, context):
    """
    Handler mỏng (Thin Handler) - Chỉ đóng vai trò điều phối.
    Chuẩn Chương 12: Framework Integration.
    """
    if event['triggerSource'] != "PostConfirmation_ConfirmSignUp":
        return event

    user_attrs = event['request']['userAttributes']
    
    # 1. Chuyển đổi dữ liệu từ Framework (Cognito) sang RequestDTO
    request = CreateUserProfileCommand(
        user_id=event['userName'],
        email=user_attrs.get('email', ''),
        current_level=user_attrs.get('custom:current_level', 'A1'),
        learning_goal=user_attrs.get('custom:learning_goal', 'B2')
    )

    
    # 2. Thực thi Use Case và nhận Result
    result = create_profile_use_case.execute(request)
    
    # 3. Xử lý kết quả trả về
    if result.is_success:
        print(f"BÁO CÁO: {result.value.message} - User: {result.value.user_id}")
    else:
        # Nếu thất bại, ta log lỗi nhưng vẫn trả về event để Cognito không chặn user đăng nhập
        print(f"CẢNH BÁO: {result.error}")
        
    return event
