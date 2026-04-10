from application.dtos.base_dto import BaseDTO

class UpdateProfileResponse(BaseDTO):
    """DTO đầu ra cho UpdateProfileUseCase."""
    is_success: bool
    message: str
