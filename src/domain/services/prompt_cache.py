"""
Prompt Cache Manager for Bedrock

Handles:
- Cache key generation
- Cache control configuration
- Cache metrics tracking
- TTL management

Note: Amazon Nova models support automatic prompt caching for all text prompts.
This class manages cache configuration and metrics.
"""

import hashlib
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Cache configuration for a prompt."""
    enabled: bool = True
    ttl_seconds: int = 300  # 5 minutes default
    cache_key: Optional[str] = None


@dataclass
class CacheMetrics:
    """Metrics for cache performance."""
    cache_hits: int = 0
    cache_misses: int = 0
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0
    latency_reduction_percent: float = 0.0


class PromptCache:
    """Manages prompt caching for Bedrock Nova models."""

    # Cache TTL options (in seconds)
    TTL_5_MINUTES = 300
    TTL_1_HOUR = 3600

    # Minimum tokens for cache checkpoint (Nova requirement)
    MIN_CACHE_TOKENS = 1024

    def __init__(self, enable_caching: bool = True, ttl_seconds: int = TTL_5_MINUTES):
        """
        Initialize prompt cache manager.
        
        Args:
            enable_caching: Whether to enable prompt caching
            ttl_seconds: Cache TTL in seconds (300 or 3600)
        """
        self.enable_caching = enable_caching
        self.ttl_seconds = ttl_seconds
        self.metrics = CacheMetrics()

    def generate_cache_key(
        self,
        scenario_title: str,
        level: str,
        selected_goals: list,
    ) -> str:
        """
        Generate cache key for a prompt.
        
        Cache key is based on:
        - Scenario title (static)
        - Proficiency level (static)
        - Selected goals (static)
        
        Args:
            scenario_title: Scenario title
            level: Proficiency level (A1-C2)
            selected_goals: List of selected goals
            
        Returns:
            Cache key (SHA256 hash)
        """
        # Create cache key from static components
        cache_input = f"{scenario_title}:{level}:{','.join(sorted(selected_goals))}"
        cache_key = hashlib.sha256(cache_input.encode()).hexdigest()[:16]
        return cache_key

    def get_cache_config(self) -> CacheConfig:
        """
        Get cache configuration.
        
        Returns:
            CacheConfig with enabled flag, TTL, and cache key
        """
        return CacheConfig(
            enabled=self.enable_caching,
            ttl_seconds=self.ttl_seconds,
        )

    def add_cache_control_to_prompt(self, system_prompt: str) -> str:
        """
        Add cache control to system prompt.
        
        For Nova models, caching is automatic. This method adds metadata
        that can be used for cache tracking.
        
        Args:
            system_prompt: Original system prompt
            
        Returns:
            System prompt with cache control metadata
        """
        if not self.enable_caching:
            return system_prompt

        # For Nova models, caching is automatic for all text prompts
        # We add a marker comment for tracking purposes
        cache_marker = f"\n<!-- Cache TTL: {self.ttl_seconds}s -->"
        return system_prompt + cache_marker

    def record_cache_hit(self, latency_ms: float, baseline_latency_ms: float):
        """
        Record a cache hit and calculate latency reduction.
        
        Args:
            latency_ms: Actual latency with cache hit
            baseline_latency_ms: Baseline latency without cache
        """
        self.metrics.cache_hits += 1
        
        if baseline_latency_ms > 0:
            reduction = ((baseline_latency_ms - latency_ms) / baseline_latency_ms) * 100
            self.metrics.latency_reduction_percent = max(0, reduction)
            logger.debug(
                f"Cache hit: {latency_ms:.2f}ms vs {baseline_latency_ms:.2f}ms "
                f"({reduction:.1f}% reduction)"
            )

    def record_cache_miss(self):
        """Record a cache miss."""
        self.metrics.cache_misses += 1
        logger.debug("Cache miss")

    def record_cache_tokens(self, write_tokens: int = 0, read_tokens: int = 0):
        """
        Record cache token usage.
        
        Args:
            write_tokens: Tokens written to cache
            read_tokens: Tokens read from cache
        """
        self.metrics.cache_write_tokens += write_tokens
        self.metrics.cache_read_tokens += read_tokens

    def get_cache_hit_rate(self) -> float:
        """
        Get cache hit rate as percentage.
        
        Returns:
            Cache hit rate (0-100)
        """
        total = self.metrics.cache_hits + self.metrics.cache_misses
        if total == 0:
            return 0.0
        return (self.metrics.cache_hits / total) * 100

    def get_metrics(self) -> CacheMetrics:
        """Get current cache metrics."""
        return self.metrics

    def reset_metrics(self):
        """Reset cache metrics."""
        self.metrics = CacheMetrics()

    @staticmethod
    def is_cache_supported(model_id: str) -> bool:
        """
        Check if model supports prompt caching.
        
        Args:
            model_id: Bedrock model ID
            
        Returns:
            True if model supports caching
        """
        # Nova models support automatic prompt caching
        if "nova" in model_id.lower():
            return True
        
        # Claude models support prompt caching
        if "claude" in model_id.lower():
            return True
        
        return False

    @staticmethod
    def get_ttl_for_model(model_id: str) -> int:
        """
        Get recommended TTL for a model.
        
        Args:
            model_id: Bedrock model ID
            
        Returns:
            TTL in seconds (300 or 3600)
        """
        # Most models support 5-minute TTL
        # Claude Opus/Haiku/Sonnet 4.5 support 1-hour TTL
        if any(x in model_id.lower() for x in ["opus", "haiku", "sonnet"]):
            return PromptCache.TTL_1_HOUR
        
        return PromptCache.TTL_5_MINUTES
