"""
Speaking session-related view models.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class SpeakingSessionViewModel:
    """Speaking session view model for API responses."""
    session_id: str
    user_id: str
    scenario_id: str
    status: str
    created_at: str
    turn_count: int = 0
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass(frozen=True)
class SpeakingTurnViewModel:
    """Speaking turn view model."""
    turn_index: int
    user_input: str
    ai_response: str
    created_at: str
    feedback: Optional[str] = None


@dataclass(frozen=True)
class SessionListViewModel:
    """Session list view model."""
    sessions: List[SpeakingSessionViewModel]
    total: int
