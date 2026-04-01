from dataclasses import dataclass


@dataclass
class Turn:
    """
    Represents a TURN entity in DynamoDB.
    PK = SESSION#<ulid>  |  SK = TURN#<index zero-padded 5 digits>

    Each Turn is a separate DynamoDB item — NOT stored as a list inside Session.
    """
    session_id: str        # ULID of parent session
    turn_index: int        # 1, 2, 3, ...
    speaker: str           # AI | USER
    content: str           # English text
    audio_s3_key: str = ""
    translated_content: str = ""  # Vietnamese translation (lazy — populated on demand)
    stt_confidence: float = 0.0   # 0.0–1.0, only for USER turns
    is_hint_used: bool = False
    is_skipped: bool = False
    timestamp: str = ""    # ISO8601
    ttl: int = 0           # Unix timestamp for auto-expiry
