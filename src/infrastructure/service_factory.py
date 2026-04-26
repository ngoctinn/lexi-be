"""
Service factory for creating and configuring service implementations.
Centralizes service instantiation and dependency injection.
"""

import os
import logging

from application.service_ports.translation_service import TranslationService
from application.service_ports.dictionary_service import DictionaryService
from infrastructure.services.aws_translate_service import AwsTranslateService
from infrastructure.services.cache_service import CacheService
from infrastructure.services.retry_service import RetryService
from infrastructure.adapters.dictionary_service_adapter import DictionaryServiceAdapter

logger = logging.getLogger(__name__)


class ServiceFactory:
    """Factory for creating service instances."""

    _translation_service: TranslationService | None = None
    _dictionary_service: DictionaryService | None = None
    _cache_service: CacheService | None = None
    _retry_service: RetryService | None = None

    @classmethod
    def create_translation_service(cls) -> TranslationService:
        """Create and cache translation service."""
        if cls._translation_service is None:
            logger.info("Creating AWS Translate service")
            cls._translation_service = AwsTranslateService()
        return cls._translation_service

    @classmethod
    def create_cache_service(cls) -> CacheService:
        """Create and cache cache service."""
        if cls._cache_service is None:
            logger.info("Creating Cache service")
            # Use single table design with LexiApp table
            table_name = os.environ.get("LEXI_TABLE_NAME", "LexiApp")
            cls._cache_service = CacheService(table_name=table_name)
        return cls._cache_service

    @classmethod
    def create_retry_service(cls) -> RetryService:
        """Create and cache retry service."""
        if cls._retry_service is None:
            logger.info("Creating Retry service")
            cls._retry_service = RetryService()
        return cls._retry_service

    @classmethod
    def create_dictionary_service(cls) -> DictionaryService:
        """Create and cache dictionary service."""
        if cls._dictionary_service is None:
            logger.info("Creating Dictionary service adapter")
            cache_service = cls.create_cache_service()
            retry_service = cls.create_retry_service()
            cls._dictionary_service = DictionaryServiceAdapter(
                cache_service=cache_service,
                retry_service=retry_service
            )
        return cls._dictionary_service

    @classmethod
    def reset(cls) -> None:
        """Reset cached services (for testing)."""
        cls._translation_service = None
        cls._dictionary_service = None
        cls._cache_service = None
        cls._retry_service = None
