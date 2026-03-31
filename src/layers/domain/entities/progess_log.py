from dataclasses import dataclass, field

@dataclass
class ProgessLog:
    log_id: str
    user_id: str
    updated_at: str
    score: int