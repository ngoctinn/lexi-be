from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class Topic:
    topic_id: str
    title: str
    description: str
    system_instruction: str
    is_active: bool
    created_at: str
