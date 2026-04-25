"""
Onboarding Mapper - converts HTTP body to Command DTOs
"""
from typing import Dict, Any
from application.dtos.onboarding_dtos import CompleteOnboardingCommand


class OnboardingMapper:
    """Maps HTTP request data to onboarding command DTOs."""
    
    @staticmethod
    def to_complete_command(user_id: str, body: Dict[str, Any]) -> CompleteOnboardingCommand:
        """
        Map HTTP body to CompleteOnboardingCommand.
        
        Args:
            user_id: User ID from JWT
            body: HTTP request body
            
        Returns:
            CompleteOnboardingCommand
        """
        return CompleteOnboardingCommand(
            user_id=user_id,
            display_name=body.get("display_name", ""),
            current_level=body.get("current_level", ""),
            target_level=body.get("target_level", ""),
            avatar_url=body.get("avatar_url", ""),
        )
