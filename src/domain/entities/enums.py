from enum import Enum

class ProficiencyLevel(Enum):
    """Trình độ ngoại ngữ theo khung tham chiếu CEFR."""
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"

class Gender(Enum):
    """Giới tính cho việc chọn giọng đọc AI."""
    MALE = "MALE"
    FEMALE = "FEMALE"

class Speaker(Enum):
    """Vai trò của người nói trong lượt hội thoại."""
    AI = "AI"
    USER = "USER"

class Role(Enum):
    """Phân quyền người dùng trong hệ thống."""
    LEARNER = "LEARNER"
    ADMIN = "ADMIN"
