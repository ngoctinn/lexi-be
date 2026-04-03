from dataclasses import dataclass

@dataclass
class FlashCard:
    """
    Represents a FLASHCARD entity in DynamoDB.
    PK = USER#<user_id>  |  SK = FLASHCARD#<ulid>

    GSI1PK = USER#<user_id>#FLASHCARD
    GSI1SK = <created_at ISO8601>
    GSI2PK = USER#<user_id>
    GSI2SK = <next_review_at ISO8601>  ← used by SRS review queue
    """
    user_id: str           # Cognito sub
    word: str
    review_count: int = 0
    interval_days: int = 1
    difficulty: int = 0    # 0–5
    last_reviewed_at: str = ""
    next_review_at: str = ""   
