"""
Admin-related view models.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class AdminUserViewModel:
    """Admin user view model for API responses."""
    user_id: str
    email: str
    display_name: str
    role: str
    is_active: bool
    joined_at: str
    total_words_learned: int


@dataclass(frozen=True)
class AdminUserListViewModel:
    """Admin user list view model."""
    users: List[dict]
    total_count: int
    next_key: Optional[dict] = None


@dataclass(frozen=True)
class AdminScenarioViewModel:
    """Admin scenario view model for API responses."""
    scenario_id: str
    scenario_title: str
    context: str
    roles: List[str]
    goals: List[str]
    is_active: bool
    usage_count: int
    created_at: str
    updated_at: str
    difficulty_level: Optional[str] = None
    order: Optional[int] = None
    notes: str = ""


@dataclass(frozen=True)
class AdminScenarioListViewModel:
    """Admin scenario list view model."""
    scenarios: List[dict]
    total_count: int
    next_key: Optional[dict] = None
