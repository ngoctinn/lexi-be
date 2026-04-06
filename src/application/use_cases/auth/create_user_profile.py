from src.application.repositories.user_profile_repository import UserProfileRepository
from src.application.dtos.auth_dto import CreateUserProfileDTO
from src.domain.entities.user_profile import UserProfile


class CreateUserProfileUseCase:
    def __init__(self, repo: UserProfileRepository):
        self._repo = repo

    def execute(self, dto: CreateUserProfileDTO) -> None:
        profile = UserProfile(
            user_id=dto.user_id,
            email=dto.email,
            display_name=dto.email.split("@")[0],
            current_level="A1",
        )
        self._repo.create(profile)
