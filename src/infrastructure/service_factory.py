"""
Service factory for creating and configuring service implementations.
Centralizes service instantiation and dependency injection.
"""

import logging

from application.service_ports.translation_service import TranslationService
from infrastructure.services.aws_translate_service import AwsTranslateService

logger = logging.getLogger(__name__)


class ServiceFactory:
    """Factory for creating service instances."""

    _translation_service: TranslationService | None = None

    @classmethod
    def create_translation_service(cls) -> TranslationService:
        """Create and cache translation service."""
        if cls._translation_service is None:
            logger.info("Creating AWS Translate service")
            cls._translation_service = AwsTranslateService()
        return cls._translation_service

    @classmethod
    def reset(cls) -> None:
        """Reset cached services (for testing)."""
        cls._translation_service = None
