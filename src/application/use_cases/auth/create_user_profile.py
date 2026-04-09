from application.repositories.user_profile_repository import UserProfileRepository
from application.dtos.auth_dto import CreateUserProfileDTO
from domain.entities.user_profile import UserProfile
from domain.value_objects.enums import ProficiencyLevel


class CreateUserProfileUseCase:
    def __init__(self, repo: UserProfileRepository):
        self._repo = repo

    def execute(self, dto: CreateUserProfileDTO) -> None:
        # Chuyển đổi từ string sang Enum (với dự phòng lỗi)
        try:
            current_level = ProficiencyLevel(dto.current_level)
        except ValueError:
            current_level = ProficiencyLevel.A1

        try:
            learning_goal = ProficiencyLevel(dto.learning_goal)
        except ValueError:
            learning_goal = ProficiencyLevel.B2

        profile = UserProfile(
            user_id=dto.user_id,
            email=dto.email,
            display_name=dto.email.split("@")[0],
            current_level=current_level,
            learning_goal=learning_goal
        )
        self._repo.create(profile)
