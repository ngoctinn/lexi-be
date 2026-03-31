from dataclasses import dataclass, field

@dataclass
class User:
    user_id: str
    target_level: str
    current_level: str
    totalXP: int = 0
    role: str #STUDENT, ADMIN
    is_active: bool
