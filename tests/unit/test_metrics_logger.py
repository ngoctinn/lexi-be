"""Unit tests for MetricsLogger."""

import pytest
from domain.services.metrics_logger import MetricsLogger, ConversationMetrics


class TestMetricsLogger:
    """Test MetricsLogger metrics collection."""

    def test_metrics_initialization(self):
        """Test ConversationMetrics initialization."""
        metrics = ConversationMetrics()
        assert metrics.ttft_ms is None
        assert metrics.total_latency_ms is None
        assert metrics.input_tokens == 0
        assert metrics.output_tokens == 0
        assert metrics.model_source == "primary"
        assert metrics.validation_passed is True

    def test_logger_initialization(self):
        """Test MetricsLogger initialization."""
        logger = MetricsLogger(enable_logging=True)
        assert logger.enable_logging is True
        assert logger.cloudwatch_client is None

    def test_logger_disabled(self):
        """Test MetricsLogger with logging disabled."""
        logger = MetricsLogger(enable_logging=False)
        assert logger.enable_logging is False

    def test_create_metrics_basic(self):
        """Test creating basic metrics."""
        logger = MetricsLogger()
        
        metrics = logger.create_metrics(
            ttft_ms=100.0,
            total_latency_ms=500.0,
            input_tokens=50,
            output_tokens=100,
            model_used="amazon.nova-micro-v1:0",
            proficiency_level="A1",
        )
        
        assert metrics.ttft_ms == 100.0
        assert metrics.total_latency_ms == 500.0
        assert metrics.input_tokens == 50
        assert metrics.output_tokens == 100
        assert metrics.model_used == "amazon.nova-micro-v1:0"
        assert metrics.proficiency_level == "A1"

    def test_create_metrics_with_fallback(self):
        """Test creating metrics with fallback."""
        logger = MetricsLogger()
        
        metrics = logger.create_metrics(
            ttft_ms=150.0,
            total_latency_ms=600.0,
            input_tokens=50,
            output_tokens=100,
            model_used="amazon.nova-lite-v1:0",
            model_source="fallback",
            fallback_reason="validation_failed",
            proficiency_level="B1",
        )
        
        assert metrics.model_source == "fallback"
        assert metrics.fallback_reason == "validation_failed"

    def test_create_metrics_with_cache(self):
        """Test creating metrics with cache tokens."""
        logger = MetricsLogger()
        
        metrics = logger.create_metrics(
            ttft_ms=80.0,
            total_latency_ms=400.0,
            input_tokens=50,
            output_tokens=100,
            cache_read_tokens=30,
            cache_write_tokens=20,
            model_used="amazon.nova-micro-v1:0",
            proficiency_level="A2",
        )
        
        assert metrics.cache_read_tokens == 30
        assert metrics.cache_write_tokens == 20

    def test_calculate_cost_micro(self):
        """Test cost calculation for Micro model."""
        logger = MetricsLogger()
        
        cost = logger._calculate_cost(
            model_id="amazon.nova-micro-v1:0",
            input_tokens=1000,
            output_tokens=100,
        )
        
        # Micro: input $0.03/1M, output $0.06/1M
        # Expected: (1000 * 0.03 + 100 * 0.06) / 1_000_000 = 0.000036
        assert cost > 0
        assert cost < 0.0001

    def test_calculate_cost_lite(self):
        """Test cost calculation for Lite model."""
        logger = MetricsLogger()
        
        cost = logger._calculate_cost(
            model_id="amazon.nova-lite-v1:0",
            input_tokens=1000,
            output_tokens=100,
        )
        
        # Lite: input $0.06/1M, output $0.24/1M
        # Expected: (1000 * 0.06 + 100 * 0.24) / 1_000_000 = 0.000084
        assert cost > 0
        assert cost < 0.0001

    def test_calculate_cost_pro(self):
        """Test cost calculation for Pro model."""
        logger = MetricsLogger()
        
        cost = logger._calculate_cost(
            model_id="amazon.nova-pro-v1:0",
            input_tokens=1000,
            output_tokens=100,
        )
        
        # Pro: input $0.80/1M, output $2.40/1M
        # Expected: (1000 * 0.80 + 100 * 2.40) / 1_000_000 = 0.00104
        assert cost > 0
        assert cost < 0.002

    def test_calculate_cost_with_cache(self):
        """Test cost calculation with cache tokens."""
        logger = MetricsLogger()
        
        # Without cache
        cost_no_cache = logger._calculate_cost(
            model_id="amazon.nova-micro-v1:0",
            input_tokens=1000,
            output_tokens=100,
        )
        
        # With cache read (cache read is cheaper than regular input)
        cost_with_cache_read = logger._calculate_cost(
            model_id="amazon.nova-micro-v1:0",
            input_tokens=500,  # Reduced input tokens
            output_tokens=100,
            cache_read_tokens=500,  # 500 tokens from cache
        )
        
        # Cache read should reduce cost (cache_read is cheaper than input)
        assert cost_with_cache_read < cost_no_cache

    def test_calculate_cost_unknown_model(self):
        """Test cost calculation for unknown model."""
        logger = MetricsLogger()
        
        cost = logger._calculate_cost(
            model_id="unknown-model",
            input_tokens=1000,
            output_tokens=100,
        )
        
        assert cost == 0.0

    def test_log_metrics_disabled(self):
        """Test logging metrics when disabled."""
        logger = MetricsLogger(enable_logging=False)
        
        metrics = logger.create_metrics(
            ttft_ms=100.0,
            total_latency_ms=500.0,
            model_used="amazon.nova-micro-v1:0",
            proficiency_level="A1",
        )
        
        # Should not raise error
        logger.log_metrics(metrics)

    def test_log_metrics_enabled(self):
        """Test logging metrics when enabled."""
        logger = MetricsLogger(enable_logging=True)
        
        metrics = logger.create_metrics(
            ttft_ms=100.0,
            total_latency_ms=500.0,
            model_used="amazon.nova-micro-v1:0",
            proficiency_level="A1",
        )
        
        # Should not raise error
        logger.log_metrics(metrics)

    def test_get_metrics_dict(self):
        """Test converting metrics to dictionary."""
        logger = MetricsLogger()
        
        metrics = logger.create_metrics(
            ttft_ms=100.0,
            total_latency_ms=500.0,
            input_tokens=50,
            output_tokens=100,
            model_used="amazon.nova-micro-v1:0",
            proficiency_level="A1",
        )
        
        metrics_dict = logger.get_metrics_dict(metrics)
        
        assert isinstance(metrics_dict, dict)
        assert metrics_dict["ttft_ms"] == 100.0
        assert metrics_dict["total_latency_ms"] == 500.0
        assert metrics_dict["input_tokens"] == 50
        assert metrics_dict["output_tokens"] == 100

    def test_metrics_with_validation_failure(self):
        """Test metrics with validation failure."""
        logger = MetricsLogger()
        
        metrics = logger.create_metrics(
            ttft_ms=100.0,
            total_latency_ms=500.0,
            model_used="amazon.nova-micro-v1:0",
            proficiency_level="B1",
            validation_passed=False,
            validation_reason="Too few sentences",
        )
        
        assert metrics.validation_passed is False
        assert metrics.validation_reason == "Too few sentences"

    def test_metrics_timestamp(self):
        """Test metrics timestamp is set."""
        logger = MetricsLogger()
        
        metrics = logger.create_metrics(
            ttft_ms=100.0,
            total_latency_ms=500.0,
            model_used="amazon.nova-micro-v1:0",
            proficiency_level="A1",
        )
        
        assert metrics.timestamp is not None
        assert len(metrics.timestamp) > 0
        assert "T" in metrics.timestamp  # ISO format

    def test_metrics_cost_calculation(self):
        """Test cost is calculated in metrics."""
        logger = MetricsLogger()
        
        metrics = logger.create_metrics(
            ttft_ms=100.0,
            total_latency_ms=500.0,
            input_tokens=1000,
            output_tokens=100,
            model_used="amazon.nova-micro-v1:0",
            proficiency_level="A1",
        )
        
        assert metrics.cost_usd is not None
        assert metrics.cost_usd > 0

    def test_metrics_all_fields(self):
        """Test metrics with all fields populated."""
        logger = MetricsLogger()
        
        metrics = logger.create_metrics(
            ttft_ms=100.0,
            total_latency_ms=500.0,
            input_tokens=50,
            output_tokens=100,
            cache_read_tokens=20,
            cache_write_tokens=30,
            model_used="amazon.nova-micro-v1:0",
            model_source="primary",
            fallback_reason=None,
            proficiency_level="A1",
            scenario_title="Restaurant",
            session_id="session-123",
            turn_index=1,
            response_length=150,
            validation_passed=True,
            validation_reason=None,
        )
        
        assert metrics.ttft_ms == 100.0
        assert metrics.total_latency_ms == 500.0
        assert metrics.input_tokens == 50
        assert metrics.output_tokens == 100
        assert metrics.cache_read_tokens == 20
        assert metrics.cache_write_tokens == 30
        assert metrics.model_used == "amazon.nova-micro-v1:0"
        assert metrics.model_source == "primary"
        assert metrics.proficiency_level == "A1"
        assert metrics.scenario_title == "Restaurant"
        assert metrics.session_id == "session-123"
        assert metrics.turn_index == 1
        assert metrics.response_length == 150
        assert metrics.validation_passed is True
