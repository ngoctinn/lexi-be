from abc import ABC, abstractmethod
from src.domain.entities.user import UserProfile


class IUserRepo(ABC):
    @abstractmethod
    def create(self, profile: UserProfile) -> None: ...
