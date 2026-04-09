import os
from infrastructure.persistence.dynamo_user_repo import DynamoDBUserRepo
from application.use_cases.auth.create_user_profile import CreateUserProfileUseCase
from application.dtos.auth_dto import CreateUserProfileDTO

# Khởi tạo Repository và Use Case ở ngoài handler để tối ưu hiệu năng (Lambda warm start)
# Why: Giảm latency cho các yêu cầu xác thực người dùng.
user_repo = DynamoDBUserRepo()
create_profile_use_case = CreateUserProfileUseCase(user_repo)

def handler(event, context):
    """
    Handler xử lý sự kiện PostConfirmation từ Amazon Cognito.
    
    Logic:
    Sau khi người dùng xác nhận email thành công, Cognito sẽ kích hoạt hàm này.
    Hàm này có nhiệm vụ đồng bộ thông tin user từ Cognito sang DynamoDB.
    """
    
    # Lấy thông tin từ event của Cognito
    # triggerSource có thể là: PostConfirmation_ConfirmSignUp or PostConfirmation_ConfirmForgotPassword
    if event['triggerSource'] != "PostConfirmation_ConfirmSignUp":
        return event

    user_attrs = event['request']['userAttributes']
    user_id = event['userName'] # Đây là Sub (UUID) của user trong Cognito
    email = user_attrs.get('email')
    
    # Đọc các thuộc tính tùy chỉnh từ Cognito (có tiền tố custom:)
    current_level = user_attrs.get('custom:current_level', 'A1')
    learning_goal = user_attrs.get('custom:learning_goal', 'B2')
    
    # Tạo DTO và thực thi Use Case theo Clean Architecture
    dto = CreateUserProfileDTO(
        user_id=user_id,
        email=email,
        current_level=current_level,
        learning_goal=learning_goal
    )
    
    try:
        create_profile_use_case.execute(dto)
        print(f"Successfully created profile for user: {user_id}")
    except Exception as e:
        # Business rule: Nếu lỗi tạo profile, ta log lại để xử lý sau (Dead Letter Queue)
        # nhưng vẫn trả về event để không làm gián đoạn luồng login của user.
        print(f"Error creating user profile: {str(e)}")
        
    return event
