from dataclasses import dataclass, field


@dataclass
class UserProfile:
    """
    Represents the USER_PROFILE entity in DynamoDB.
    PK = USER#<user_id>  |  SK = PROFILE
    """
    user_id: str           # Cognito sub (UUID)
    email: str
    display_name: str
    current_level: str     # A1, A2, B1, B2, C1, C2
    role: str = "LEARNER"  # "LEARNER" | "ADMIN"
    is_active: bool = True # Admin can block/disable users
    current_streak: int = 0
    last_completed_at: str = ""   # ISO8601, dùng để tính streak
    total_sessions: int = 0
    total_words_learned: int = 0
    created_at: str = ""
    updated_at: str = ""
