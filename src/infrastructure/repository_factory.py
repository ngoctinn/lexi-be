"""
Repository factory for creating and configuring repository implementations.
Centralizes repository instantiation and dependency injection.
"""

import logging
from typing import Tuple

from application.repositories.flash_card_repository import FlashCardRepository
from application.repositories.scenario_repository import ScenarioRepository
from application.repositories.user_profile_repository import UserProfileRepository
from infrastructure.configuration.config import Config
from infrastructure.persistence.dynamo_flashcard_repo import DynamoFlashCardRepository
from infrastructure.persistence.dynamo_scenario_repo import DynamoScenarioRepository
from infrastructure.persistence.dynamo_user_repo import DynamoDBUserRepo
from infrastructure.persistence.static_scenario_repo import StaticScenarioRepository

logger = logging.getLogger(__name__)


class RepositoryFactory:
    """Factory for creating repository instances."""

    _user_repo: UserProfileRepository | None = None
    _scenario_repo: ScenarioRepository | None = None
    _flashcard_repo: FlashCardRepository | None = None

    @classmethod
    def create_user_repository(cls) -> UserProfileRepository:
        """Create and cache user profile repository."""
        if cls._user_repo is None:
            logger.info("Creating DynamoDB user repository")
            cls._user_repo = DynamoDBUserRepo()
        return cls._user_repo

    @classmethod
    def create_scenario_repository(cls) -> ScenarioRepository:
        """Create and cache scenario repository."""
        if cls._scenario_repo is None:
            logger.info("Creating scenario repository")
            # Use static scenarios for now, can switch to DynamoDB
            cls._scenario_repo = StaticScenarioRepository()
        return cls._scenario_repo

    @classmethod
    def create_flashcard_repository(cls) -> FlashCardRepository:
        """Create and cache flashcard repository."""
        if cls._flashcard_repo is None:
            logger.info("Creating DynamoDB flashcard repository")
            cls._flashcard_repo = DynamoFlashCardRepository()
        return cls._flashcard_repo

    @classmethod
    def create_all_repositories(
        cls,
    ) -> Tuple[UserProfileRepository, ScenarioRepository, FlashCardRepository]:
        """Create all repositories at once."""
        return (
            cls.create_user_repository(),
            cls.create_scenario_repository(),
            cls.create_flashcard_repository(),
        )

    @classmethod
    def reset(cls) -> None:
        """Reset cached repositories (for testing)."""
        cls._user_repo = None
        cls._scenario_repo = None
        cls._flashcard_repo = None
