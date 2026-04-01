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
    card_id: str           # ULID
    user_id: str           # Cognito sub
    word: str
    word_type: str         # adjective, noun, verb, adverb, ...
    definition_vi: str     # Vietnamese definition
    phonetic: str          # IPA e.g. /ˈskeɪləbl/
    audio_s3_key: str      # Copied from WordCache — independent of cache TTL
    example_sentence: str
    source_session_id: str # ULID of the session where word was encountered
    # SRS fields (SM-2 algorithm)
    review_count: int = 0
    easiness_factor: float = 2.5
    interval_days: int = 1
    difficulty: int = 0    # 0–5
    last_reviewed_at: str = ""
    next_review_at: str = ""   # ISO8601 — written to GSI2SK
    created_at: str = ""
    updated_at: str = ""
