from abc import ABC, abstractmethod
from src.domain.entities.user_profile import UserProfile


class IUserRepo(ABC):
    @abstractmethod
    def create(self, profile: UserProfile) -> None: ...
