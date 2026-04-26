"""Unit tests for PromptCache."""

import pytest
from domain.services.prompt_cache import PromptCache, CacheConfig, CacheMetrics


class TestPromptCache:
    """Test PromptCache caching logic."""

    def test_cache_initialization(self):
        """Test PromptCache initialization."""
        cache = PromptCache(enable_caching=True, ttl_seconds=300)
        assert cache.enable_caching is True
        assert cache.ttl_seconds == 300
        assert cache.metrics.cache_hits == 0
        assert cache.metrics.cache_misses == 0

    def test_cache_disabled(self):
        """Test PromptCache with caching disabled."""
        cache = PromptCache(enable_caching=False)
        assert cache.enable_caching is False

    def test_generate_cache_key(self):
        """Test cache key generation."""
        cache = PromptCache()
        
        key1 = cache.generate_cache_key(
            scenario_title="Restaurant",
            level="A1",
            selected_goal="ordering",
        )
        
        # Same inputs should generate same key
        key2 = cache.generate_cache_key(
            scenario_title="Restaurant",
            level="A1",
            selected_goal="ordering",
        )
        
        assert key1 == key2
        assert len(key1) == 16  # SHA256 truncated to 16 chars

    def test_generate_cache_key_different_inputs(self):
        """Test cache key generation with different inputs."""
        cache = PromptCache()
        
        key1 = cache.generate_cache_key(
            scenario_title="Restaurant",
            level="A1",
            selected_goals=["ordering"],
        )
        
        key2 = cache.generate_cache_key(
            scenario_title="Restaurant",
            level="B1",
            selected_goals=["ordering"],
        )
        
        # Different level should generate different key
        assert key1 != key2

    def test_generate_cache_key_order_independent(self):
        """Test cache key generation is order-independent for goals."""
        cache = PromptCache()
        
        key1 = cache.generate_cache_key(
            scenario_title="Restaurant",
            level="A1",
            selected_goal="ordering",
        )
        
        key2 = cache.generate_cache_key(
            scenario_title="Restaurant",
            level="A1",
            selected_goal="greeting",
        )
        
        # Order shouldn't matter (goals are sorted)
        assert key1 == key2

    def test_get_cache_config(self):
        """Test getting cache configuration."""
        cache = PromptCache(enable_caching=True, ttl_seconds=600)
        config = cache.get_cache_config()
        
        assert isinstance(config, CacheConfig)
        assert config.enabled is True
        assert config.ttl_seconds == 600

    def test_add_cache_control_to_prompt_enabled(self):
        """Test adding cache control to prompt when enabled."""
        cache = PromptCache(enable_caching=True)
        prompt = "You are a helpful assistant."
        
        result = cache.add_cache_control_to_prompt(prompt)
        
        assert prompt in result
        assert "Cache TTL" in result

    def test_add_cache_control_to_prompt_disabled(self):
        """Test adding cache control to prompt when disabled."""
        cache = PromptCache(enable_caching=False)
        prompt = "You are a helpful assistant."
        
        result = cache.add_cache_control_to_prompt(prompt)
        
        # Should return original prompt unchanged
        assert result == prompt

    def test_record_cache_hit(self):
        """Test recording cache hit."""
        cache = PromptCache()
        
        cache.record_cache_hit(latency_ms=100, baseline_latency_ms=200)
        
        assert cache.metrics.cache_hits == 1
        assert cache.metrics.latency_reduction_percent == 50.0

    def test_record_cache_hit_zero_baseline(self):
        """Test recording cache hit with zero baseline."""
        cache = PromptCache()
        
        cache.record_cache_hit(latency_ms=100, baseline_latency_ms=0)
        
        assert cache.metrics.cache_hits == 1
        assert cache.metrics.latency_reduction_percent == 0.0

    def test_record_cache_miss(self):
        """Test recording cache miss."""
        cache = PromptCache()
        
        cache.record_cache_miss()
        
        assert cache.metrics.cache_misses == 1

    def test_record_cache_tokens(self):
        """Test recording cache token usage."""
        cache = PromptCache()
        
        cache.record_cache_tokens(write_tokens=100, read_tokens=50)
        
        assert cache.metrics.cache_write_tokens == 100
        assert cache.metrics.cache_read_tokens == 50

    def test_get_cache_hit_rate_no_requests(self):
        """Test cache hit rate with no requests."""
        cache = PromptCache()
        
        hit_rate = cache.get_cache_hit_rate()
        
        assert hit_rate == 0.0

    def test_get_cache_hit_rate_all_hits(self):
        """Test cache hit rate with all hits."""
        cache = PromptCache()
        
        cache.record_cache_hit(100, 200)
        cache.record_cache_hit(100, 200)
        cache.record_cache_hit(100, 200)
        
        hit_rate = cache.get_cache_hit_rate()
        
        assert hit_rate == 100.0

    def test_get_cache_hit_rate_mixed(self):
        """Test cache hit rate with mixed hits and misses."""
        cache = PromptCache()
        
        cache.record_cache_hit(100, 200)
        cache.record_cache_hit(100, 200)
        cache.record_cache_miss()
        
        hit_rate = cache.get_cache_hit_rate()
        
        assert hit_rate == pytest.approx(66.67, rel=0.01)

    def test_get_metrics(self):
        """Test getting cache metrics."""
        cache = PromptCache()
        
        cache.record_cache_hit(100, 200)
        cache.record_cache_tokens(write_tokens=100, read_tokens=50)
        
        metrics = cache.get_metrics()
        
        assert metrics.cache_hits == 1
        assert metrics.cache_write_tokens == 100
        assert metrics.cache_read_tokens == 50

    def test_reset_metrics(self):
        """Test resetting cache metrics."""
        cache = PromptCache()
        
        cache.record_cache_hit(100, 200)
        cache.record_cache_tokens(write_tokens=100, read_tokens=50)
        
        cache.reset_metrics()
        
        assert cache.metrics.cache_hits == 0
        assert cache.metrics.cache_misses == 0
        assert cache.metrics.cache_write_tokens == 0
        assert cache.metrics.cache_read_tokens == 0

    def test_is_cache_supported_nova(self):
        """Test cache support for Nova models."""
        assert PromptCache.is_cache_supported("amazon.nova-micro-v1:0") is True
        assert PromptCache.is_cache_supported("amazon.nova-lite-v1:0") is True
        assert PromptCache.is_cache_supported("amazon.nova-pro-v1:0") is True

    def test_is_cache_supported_claude(self):
        """Test cache support for Claude models."""
        assert PromptCache.is_cache_supported("anthropic.claude-3-haiku-20240307-v1:0") is True
        assert PromptCache.is_cache_supported("anthropic.claude-3-sonnet-20240229-v1:0") is True

    def test_is_cache_supported_unsupported(self):
        """Test cache support for unsupported models."""
        assert PromptCache.is_cache_supported("amazon.titan-text-express-v1") is False

    def test_get_ttl_for_model_nova(self):
        """Test TTL for Nova models."""
        ttl = PromptCache.get_ttl_for_model("amazon.nova-micro-v1:0")
        assert ttl == PromptCache.TTL_5_MINUTES

    def test_get_ttl_for_model_claude_opus(self):
        """Test TTL for Claude Opus (supports 1-hour TTL)."""
        ttl = PromptCache.get_ttl_for_model("anthropic.claude-opus-v1")
        assert ttl == PromptCache.TTL_1_HOUR

    def test_get_ttl_for_model_claude_haiku(self):
        """Test TTL for Claude Haiku (supports 1-hour TTL)."""
        ttl = PromptCache.get_ttl_for_model("anthropic.claude-haiku-v1")
        assert ttl == PromptCache.TTL_1_HOUR

    def test_get_ttl_for_model_claude_sonnet(self):
        """Test TTL for Claude Sonnet (supports 1-hour TTL)."""
        ttl = PromptCache.get_ttl_for_model("anthropic.claude-sonnet-v1")
        assert ttl == PromptCache.TTL_1_HOUR

    def test_cache_metrics_initialization(self):
        """Test CacheMetrics initialization."""
        metrics = CacheMetrics()
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0
        assert metrics.cache_write_tokens == 0
        assert metrics.cache_read_tokens == 0
        assert metrics.latency_reduction_percent == 0.0

    def test_cache_config_initialization(self):
        """Test CacheConfig initialization."""
        config = CacheConfig(enabled=True, ttl_seconds=300)
        assert config.enabled is True
        assert config.ttl_seconds == 300
        assert config.cache_key is None
