"""Unit tests for MetricsAggregator."""

import pytest
from domain.services.metrics_logger import (
    MetricsLogger,
    ConversationMetrics,
    QualityMetrics,
    HintMetrics,
)
from domain.services.metrics_aggregator import (
    MetricsAggregator,
    SessionMetricsAggregate,
    LevelMetricsAggregate,
)


class TestMetricsAggregator:
    """Test MetricsAggregator functionality."""

    def test_aggregate_session_metrics_empty(self):
        """Test aggregating empty metrics list."""
        result = MetricsAggregator.aggregate_session_metrics([])
        assert result is None

    def test_aggregate_session_metrics_single_turn(self):
        """Test aggregating single turn metrics."""
        logger = MetricsLogger()
        
        metrics = logger.create_metrics(
            ttft_ms=100.0,
            total_latency_ms=500.0,
            input_tokens=50,
            output_tokens=100,
            model_used="amazon.nova-micro-v1:0",
            model_source="primary",
            proficiency_level="A1",
            session_id="session-123",
            turn_index=0,
        )
        
        aggregate = MetricsAggregator.aggregate_session_metrics([metrics])
        
        assert aggregate is not None
        assert aggregate.session_id == "session-123"
        assert aggregate.proficiency_level == "A1"
        assert aggregate.total_turns == 1
        assert aggregate.avg_ttft_ms == 100.0
        assert aggregate.avg_total_latency_ms == 500.0
        assert aggregate.total_output_tokens == 100
        assert aggregate.primary_model_count == 1
        assert aggregate.fallback_model_count == 0

    def test_aggregate_session_metrics_multiple_turns(self):
        """Test aggregating multiple turns."""
        logger = MetricsLogger()
        
        metrics_list = []
        for i in range(3):
            metrics = logger.create_metrics(
                ttft_ms=100.0 + (i * 10),
                total_latency_ms=500.0 + (i * 50),
                input_tokens=50,
                output_tokens=100,
                model_used="amazon.nova-micro-v1:0",
                model_source="primary",
                proficiency_level="A1",
                session_id="session-123",
                turn_index=i,
            )
            metrics_list.append(metrics)
        
        aggregate = MetricsAggregator.aggregate_session_metrics(metrics_list)
        
        assert aggregate is not None
        assert aggregate.total_turns == 3
        assert aggregate.total_output_tokens == 300
        assert aggregate.avg_ttft_ms == 110.0  # (100 + 110 + 120) / 3
        assert aggregate.avg_total_latency_ms == 550.0  # (500 + 550 + 600) / 3

    def test_aggregate_session_metrics_with_fallback(self):
        """Test aggregating metrics with fallback."""
        logger = MetricsLogger()
        
        metrics_list = [
            logger.create_metrics(
                ttft_ms=100.0,
                total_latency_ms=500.0,
                model_used="amazon.nova-micro-v1:0",
                model_source="primary",
                proficiency_level="B1",
                session_id="session-456",
                turn_index=0,
            ),
            logger.create_metrics(
                ttft_ms=150.0,
                total_latency_ms=600.0,
                model_used="amazon.nova-lite-v1:0",
                model_source="fallback",
                fallback_reason="validation_failed",
                proficiency_level="B1",
                session_id="session-456",
                turn_index=1,
            ),
        ]
        
        aggregate = MetricsAggregator.aggregate_session_metrics(metrics_list)
        
        assert aggregate is not None
        assert aggregate.primary_model_count == 1
        assert aggregate.fallback_model_count == 1
        assert aggregate.fallback_rate == 0.5

    def test_aggregate_session_metrics_with_quality(self):
        """Test aggregating metrics with quality scores."""
        logger = MetricsLogger()
        
        quality1 = QualityMetrics(
            quality_score=85.0,
            format_compliant=True,
            length_compliant=True,
            has_question=True,
        )
        
        quality2 = QualityMetrics(
            quality_score=75.0,
            format_compliant=True,
            length_compliant=False,
            has_question=True,
        )
        
        metrics_list = [
            logger.create_metrics(
                ttft_ms=100.0,
                total_latency_ms=500.0,
                model_used="amazon.nova-micro-v1:0",
                proficiency_level="A1",
                session_id="session-789",
                turn_index=0,
                quality_metrics=quality1,
            ),
            logger.create_metrics(
                ttft_ms=110.0,
                total_latency_ms=510.0,
                model_used="amazon.nova-micro-v1:0",
                proficiency_level="A1",
                session_id="session-789",
                turn_index=1,
                quality_metrics=quality2,
            ),
        ]
        
        aggregate = MetricsAggregator.aggregate_session_metrics(metrics_list)
        
        assert aggregate is not None
        assert aggregate.avg_quality_score == 80.0  # (85 + 75) / 2
        assert aggregate.format_compliant_rate == 1.0  # 2/2
        assert aggregate.length_compliant_rate == 0.5  # 1/2
        assert aggregate.has_question_rate == 1.0  # 2/2

    def test_aggregate_session_metrics_with_hints(self):
        """Test aggregating metrics with hint usage."""
        logger = MetricsLogger()
        
        hint1 = HintMetrics(
            hint_provided=True,
            hint_accepted=True,
            scaffolding_effectiveness=0.8,
        )
        
        hint2 = HintMetrics(
            hint_provided=True,
            hint_accepted=False,
            scaffolding_effectiveness=0.3,
        )
        
        metrics_list = [
            logger.create_metrics(
                ttft_ms=100.0,
                total_latency_ms=500.0,
                model_used="amazon.nova-micro-v1:0",
                proficiency_level="A1",
                session_id="session-hint",
                turn_index=0,
                hint_metrics=hint1,
            ),
            logger.create_metrics(
                ttft_ms=110.0,
                total_latency_ms=510.0,
                model_used="amazon.nova-micro-v1:0",
                proficiency_level="A1",
                session_id="session-hint",
                turn_index=1,
                hint_metrics=hint2,
            ),
        ]
        
        aggregate = MetricsAggregator.aggregate_session_metrics(metrics_list)
        
        assert aggregate is not None
        assert aggregate.hint_provided_count == 2
        assert aggregate.hint_accepted_count == 1
        assert aggregate.hint_acceptance_rate == 0.5  # 1/2

    def test_aggregate_session_metrics_cost(self):
        """Test aggregating cost metrics."""
        logger = MetricsLogger()
        
        metrics_list = [
            logger.create_metrics(
                ttft_ms=100.0,
                total_latency_ms=500.0,
                input_tokens=1000,
                output_tokens=100,
                model_used="amazon.nova-micro-v1:0",
                proficiency_level="A1",
                session_id="session-cost",
                turn_index=0,
            ),
            logger.create_metrics(
                ttft_ms=110.0,
                total_latency_ms=510.0,
                input_tokens=1000,
                output_tokens=100,
                model_used="amazon.nova-micro-v1:0",
                proficiency_level="A1",
                session_id="session-cost",
                turn_index=1,
            ),
        ]
        
        aggregate = MetricsAggregator.aggregate_session_metrics(metrics_list)
        
        assert aggregate is not None
        assert aggregate.total_cost_usd > 0
        assert aggregate.avg_cost_per_turn_usd > 0
        assert aggregate.avg_cost_per_turn_usd == aggregate.total_cost_usd / 2

    def test_aggregate_level_metrics_empty(self):
        """Test aggregating empty level metrics."""
        result = MetricsAggregator.aggregate_level_metrics([])
        assert result is None

    def test_aggregate_level_metrics_single_session(self):
        """Test aggregating level metrics for single session."""
        logger = MetricsLogger()
        
        metrics_list = []
        for i in range(3):
            metrics = logger.create_metrics(
                ttft_ms=100.0,
                total_latency_ms=500.0,
                input_tokens=50,
                output_tokens=100,
                model_used="amazon.nova-micro-v1:0",
                proficiency_level="B1",
                session_id="session-b1-1",
                turn_index=i,
            )
            metrics_list.append(metrics)
        
        aggregate = MetricsAggregator.aggregate_level_metrics(metrics_list)
        
        assert aggregate is not None
        assert aggregate.proficiency_level == "B1"
        assert aggregate.total_turns == 3
        assert aggregate.total_sessions == 1

    def test_aggregate_level_metrics_multiple_sessions(self):
        """Test aggregating level metrics for multiple sessions."""
        logger = MetricsLogger()
        
        metrics_list = []
        for session_id in ["session-c1-1", "session-c1-2"]:
            for i in range(2):
                metrics = logger.create_metrics(
                    ttft_ms=100.0,
                    total_latency_ms=500.0,
                    input_tokens=50,
                    output_tokens=100,
                    model_used="amazon.nova-pro-v1:0",
                    proficiency_level="C1",
                    session_id=session_id,
                    turn_index=i,
                )
                metrics_list.append(metrics)
        
        aggregate = MetricsAggregator.aggregate_level_metrics(metrics_list)
        
        assert aggregate is not None
        assert aggregate.proficiency_level == "C1"
        assert aggregate.total_turns == 4
        assert aggregate.total_sessions == 2

    def test_percentile_calculation(self):
        """Test percentile calculation."""
        values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        
        p50 = MetricsAggregator._percentile(values, 50)
        p95 = MetricsAggregator._percentile(values, 95)
        
        assert p50 >= 40 and p50 <= 60
        assert p95 >= 85 and p95 <= 100

    def test_percentile_single_value(self):
        """Test percentile with single value."""
        values = [42.0]
        
        p95 = MetricsAggregator._percentile(values, 95)
        assert p95 == 42.0

    def test_percentile_empty(self):
        """Test percentile with empty list."""
        values = []
        
        p95 = MetricsAggregator._percentile(values, 95)
        assert p95 == 0.0

    def test_aggregate_session_validation_rate(self):
        """Test validation rate calculation."""
        logger = MetricsLogger()
        
        metrics_list = [
            logger.create_metrics(
                ttft_ms=100.0,
                total_latency_ms=500.0,
                model_used="amazon.nova-micro-v1:0",
                proficiency_level="A2",
                session_id="session-val",
                turn_index=0,
                validation_passed=True,
            ),
            logger.create_metrics(
                ttft_ms=110.0,
                total_latency_ms=510.0,
                model_used="amazon.nova-micro-v1:0",
                proficiency_level="A2",
                session_id="session-val",
                turn_index=1,
                validation_passed=False,
                validation_reason="Too few sentences",
            ),
        ]
        
        aggregate = MetricsAggregator.aggregate_session_metrics(metrics_list)
        
        assert aggregate is not None
        assert aggregate.validation_passed_rate == 0.5  # 1/2

    def test_aggregate_session_max_ttft(self):
        """Test max TTFT calculation."""
        logger = MetricsLogger()
        
        metrics_list = [
            logger.create_metrics(
                ttft_ms=100.0,
                total_latency_ms=500.0,
                model_used="amazon.nova-micro-v1:0",
                proficiency_level="A1",
                session_id="session-max",
                turn_index=0,
            ),
            logger.create_metrics(
                ttft_ms=250.0,
                total_latency_ms=600.0,
                model_used="amazon.nova-micro-v1:0",
                proficiency_level="A1",
                session_id="session-max",
                turn_index=1,
            ),
            logger.create_metrics(
                ttft_ms=150.0,
                total_latency_ms=550.0,
                model_used="amazon.nova-micro-v1:0",
                proficiency_level="A1",
                session_id="session-max",
                turn_index=2,
            ),
        ]
        
        aggregate = MetricsAggregator.aggregate_session_metrics(metrics_list)
        
        assert aggregate is not None
        assert aggregate.max_ttft_ms == 250.0
