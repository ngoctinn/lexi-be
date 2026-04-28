"""
Onboarding Controller - handles onboarding completion
"""
import json
import logging
from pydantic import ValidationError

from application.use_cases.onboarding_use_cases import CompleteOnboardingUseCase
from interfaces.mapper.onboarding_mapper import OnboardingMapper
from shared.result import Result
from interfaces.view_models.onboarding_vm import OnboardingCompletionViewModel

logger = logging.getLogger(__name__)


class OnboardingController:
    """
    Controller for onboarding operations.
    
    Responsibilities:
    - Receive requests from Lambda Handler
    - Convert raw data to DTOs via Mapper
    - Call corresponding Use Case
    - Convert Response DTO to View Model
    - Return Result[ViewModel, str]
    """

    def __init__(self, complete_onboarding_uc: CompleteOnboardingUseCase):
        self._complete_onboarding_uc = complete_onboarding_uc

    def complete(self, user_id: str, body_str: str | None) -> Result[OnboardingCompletionViewModel, str]:
        """
        Handle onboarding completion request.
        
        Args:
            user_id: User ID from JWT
            body_str: JSON body with onboarding data
            
        Returns:
            Result with OnboardingCompletionViewModel
        """
        try:
            body = json.loads(body_str or "{}")
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in complete onboarding request")
            return Result.failure("Invalid JSON format")
        
        try:
            logger.info("Completing onboarding", extra={"context": {"user_id": user_id}})
            
            # 1. Map raw data to Command DTO
            command = OnboardingMapper.to_complete_command(user_id, body)
            
            # 2. Execute business logic
            result = self._complete_onboarding_uc.execute(command)
            
            if not result.is_success:
                logger.warning("Onboarding completion failed", extra={"context": {"user_id": user_id, "error": result.error}})
                return Result.failure(result.error)
            
            # 3. Convert Response DTO to View Model
            response = result.value
            view_model = OnboardingCompletionViewModel(
                is_success=response.is_success,
                message=response.message,
                profile=response.profile,
            )
            
            logger.info("Onboarding completed successfully", extra={"context": {"user_id": user_id}})
            return Result.success(view_model)
            
        except ValidationError as exc:
            logger.warning("Validation error in complete onboarding", extra={"context": {"user_id": user_id, "errors": str(exc)}})
            return Result.failure(f"Invalid request data: {str(exc)}")
        except Exception as e:
            logger.exception("Error in onboarding completion", extra={"context": {"user_id": user_id, "error": str(e)}})
            raise
