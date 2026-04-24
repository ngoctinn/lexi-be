from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CompleteOnboardingCommand:
    """Command DTO cho CompleteOnboardingUseCase."""
    user_id: str
    display_name: str
    current_level: str
    target_level: str
    avatar_url: str = ""


@dataclass
class CompleteOnboardingResponse:
    """Response DTO cho CompleteOnboardingUseCase."""
    is_success: bool
    message: str
    profile: Optional[dict] = field(default=None)
