from dataclasses import dataclass


@dataclass
class Scoring:
    """
    Represents the SCORING entity in DynamoDB.
    PK = SESSION#<ulid>  |  SK = SCORING

    Populated asynchronously by fn_scoring_worker via SQS FIFO.
    user_id is included here so the scoring worker can update
    USER_PROFILE stats without an extra GetItem on SESSION#METADATA.
    """
    session_id: str        # ULID of parent session
    user_id: str           # Cognito sub — avoids extra GetItem in scoring worker
    fluency_score: int = 0       # 0–100
    pronunciation_score: int = 0 # 0–100
    grammar_score: int = 0       # 0–100
    vocabulary_score: int = 0    # 0–100
    overall_score: int = 0       # Average of the four
    feedback_general: str = ""
    feedback_fluency: str = ""
    feedback_grammar: str = ""
    scored_at: str = ""    # ISO8601
