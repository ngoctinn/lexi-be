from dataclasses import dataclass

@dataclass
class FlashCard:
    user_id: str           # Cognito sub
    word: str
    review_count: int = 0
    interval_days: int = 1
    difficulty: int = 0    # 0–5
    last_reviewed_at: str = ""
    next_review_at: str = ""   
