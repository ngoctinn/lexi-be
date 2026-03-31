from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class ChatSession:
    session_id: str
    user_id: str
    topic_id: str
    status: str #ACTIVE, COMPLETE
    messages: List[Dict] = field(default_factory=list)
    feedback_summary: List[Dict] = field(default_factory=list)
    start: str
