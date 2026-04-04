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
    scenario_id: int          
    ai_gender: str         # "male" | "female" (for TTS)
    level: str             # A1, A2, B1, B2, C1, C2
    connection_id: str = ""       # WebSocket connectionId
    total_turns: int = 0
    user_turns: int = 0
    hint_used_count: int = 0
