from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CompleteOnboardingResponse:
    """Response DTO cho CompleteOnboardingUseCase."""
    is_success: bool
    message: str
    profile: Optional[dict] = field(default=None)
