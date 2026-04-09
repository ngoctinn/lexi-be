from dataclasses import dataclass

@dataclass
class CreateUserProfileDTO:
    """
    DTO dùng để truyền dữ liệu tạo profile người dùng từ Cognito sang Database.
    """
    user_id: str
    email: str
    current_level: str = "A1"
    learning_goal: str = "B2"
