from dataclasses import dataclass, field


@dataclass
class UserProfile:
    user_id: str           # Cognito sub (UUID)
    email: str
    display_name: str
    current_level: str     # A1, A2, B1, B2, C1, C2
    learning_goal: str = ""
    is_onboarded: bool = False
    role: str = "LEARNER"  # "LEARNER" | "ADMIN"
    is_active: bool = True
    current_streak: int = 0
    last_completed_at: str = ""
    total_words_learned: int = 0
