from abc import ABC, abstractmethod
from domain.entities.user_profile import UserProfile


class IUserRepo(ABC):
    @abstractmethod
    def create(self, profile: UserProfile) -> None: ...
