"""
Scenario-related view models.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class ScenarioViewModel:
    """Scenario view model for API responses."""
    scenario_id: str
    scenario_title: str
    context: str
    roles: List[str]
    goals: List[str]
    is_active: bool
    usage_count: int
    difficulty_level: Optional[str] = None
    order: int = 0


@dataclass(frozen=True)
class ScenarioListViewModel:
    """Scenario list view model."""
    scenarios: List[dict]
    total: int
