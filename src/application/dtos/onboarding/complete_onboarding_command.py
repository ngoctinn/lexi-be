from dataclasses import dataclass


@dataclass
class CompleteOnboardingCommand:
    """Command DTO cho CompleteOnboardingUseCase."""
    user_id: str
    display_name: str
    current_level: str
    target_level: str
    avatar_url: str = ""
