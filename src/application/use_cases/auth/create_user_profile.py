from datetime import datetime, timezone
from src.application.repositories.user_repo import IUserRepo
from src.application.dtos.auth_dto import CreateUserProfileDTO
from src.domain.entities.user_profile import UserProfile


class CreateUserProfileUseCase:
    def __init__(self, repo: IUserRepo):
        self._repo = repo

    def execute(self, dto: CreateUserProfileDTO) -> None:
        now = datetime.now(timezone.utc).isoformat()
        profile = UserProfile(
            user_id=dto.user_id,
            email=dto.email,
            display_name=dto.email.split("@")[0],
            current_level="A1",
            is_onboarded=False,
            created_at=now,
            updated_at=now,
        )
        self._repo.create(profile)
