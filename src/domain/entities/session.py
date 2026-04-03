from dataclasses import dataclass, field


@dataclass
class Session:
    """
    Represents the SESSION entity in DynamoDB.
    PK = SESSION#<ulid>  |  SK = METADATA

    GSI1PK = USER#<user_id>#SESSION
    GSI1SK = <created_at ISO8601>
    """
    session_id: str        # ULID
    user_id: str           # Cognito sub
    scenario: str          # E.g., "Ordering food in a restaurant"
    my_character: str      # E.g., "A hungry customer"
    ai_character: str      # E.g., "A polite waiter"
    ai_gender: str         # "male" | "female" (for TTS)
    level: str             # A1, A2, B1, B2, C1, C2
    status: str            # ACTIVE | COMPLETED
    connection_id: str = ""       # WebSocket connectionId
    hint_history: dict = field(default_factory=dict) # Map of Turn Index to Hint Content
    total_turns: int = 0
    user_turns: int = 0
    hint_used_count: int = 0
    new_words_count: int = 0
    overall_score: int = 0
    last_active_at: str = ""      # ISO8601
