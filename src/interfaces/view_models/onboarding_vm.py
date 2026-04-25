"""
Onboarding View Models
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class OnboardingCompletionViewModel:
    """View model for onboarding completion response."""
    
    is_success: bool
    message: str
    profile: Optional[Dict[str, Any]] = None
