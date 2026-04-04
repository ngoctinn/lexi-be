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
    grammar_score: int = 0       # 0–100
    vocabulary_score: int = 0    # 0–100
    overall_score: int = 0       # Average of the four
    feedback_fluency: str = ""
