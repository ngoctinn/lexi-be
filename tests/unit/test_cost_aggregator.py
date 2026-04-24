"""Unit tests for CostAggregator."""

import pytest
from domain.services.metrics_logger import MetricsLogger
from domain.services.cost_aggregator import (
    CostAggregator,
    CostAlert,
    CostAlertLevel,
)


class TestCostAggregator:
    """Test CostAggregator functionality."""

    def test_calculate_haiku_cost(self):
        """Test Haiku cost calculation."""
        # 1000 input tokens + 100 output tokens
        cost = CostAggregator.calculate_haiku_cost(1000, 100)
        
        # Expected: (1000 * 0.80 + 100 * 4.00) / 1_000_000 = 0.0012
        assert cost > 0
        assert cost < 0.002

    def test_calculate_haiku_cost_zero(self):
        """Test Haiku cost with zero tokens."""
        cost = CostAggregator.calculate_haiku_cost(0, 0)
        assert cost == 0.0

    def test_aggregate_session_cost_empty(self):
        """Test aggregating empty session."""
        result = CostAggregator.aggregate_session_cost([])
        assert result is None

    def test_aggregate_session_cost_single_turn(self):
        """Test aggregating single turn cost."""
        logger = MetricsLogger()
        
        metrics = logger.create_metrics(
            ttft_ms=100.0,
            total_latency_ms=500.0,
            input_tokens=1000,
            output_tokens=100,
            model_used="amazon.nova-micro-v1:0",
            proficiency_level="A1",
            session_id="session-123",
            turn_index=0,
        )
        
        result = CostAggregator.aggregate_session_cost([metrics])
        
        assert result is not None
        assert result["session_id"] == "session-123"
        assert result["proficiency_level"] == "A1"
        assert result["total_turns"] == 1
        assert result["total_nova_cost_usd"] > 0
        assert result["total_haiku_cost_usd"] > 0
        assert result["savings_usd"] > 0  # Nova should be cheaper
        assert result["savings_percent"] > 0

    def test_aggregate_session_cost_multiple_turns(self):
        """Test aggregating multiple turns."""
        logger = MetricsLogger()
        
        metrics_list = []
        for i in range(3):
            metrics = logger.create_metrics(
                ttft_ms=100.0,
                total_latency_ms=500.0,
                input_tokens=1000,
                output_tokens=100,
                model_used="amazon.nova-micro-v1:0",
                proficiency_level="B1",
                session_id="session-456",
                turn_index=i,
            )
            metrics_list.append(metrics)
        
        result = CostAggregator.aggregate_session_cost(metrics_list)
        
        assert result is not None
        assert result["total_turns"] == 3
        assert result["total_nova_cost_usd"] > 0
        assert result["avg_nova_cost_per_turn_usd"] > 0
        # Average should be close to single turn cost
        assert result["avg_nova_cost_per_turn_usd"] == result["total_nova_cost_usd"] / 3

    def test_aggregate_session_cost_savings_calculation(self):
        """Test savings calculation."""
        logger = MetricsLogger()
        
        metrics = logger.create_metrics(
            ttft_ms=100.0,
            total_latency_ms=500.0,
            input_tokens=1000,
            output_tokens=100,
            model_used="amazon.nova-micro-v1:0",
            proficiency_level="A1",
            session_id="session-savings",
            turn_index=0,
        )
        
        result = CostAggregator.aggregate_session_cost([metrics])
        
        # Verify savings calculation
        expected_savings = result["total_haiku_cost_usd"] - result["total_nova_cost_usd"]
        assert result["savings_usd"] == expected_savings
        
        # Verify savings percent
        expected_percent = (expected_savings / result["total_haiku_cost_usd"]) * 100
        assert abs(result["savings_percent"] - expected_percent) < 0.01

    def test_aggregate_level_cost_empty(self):
        """Test aggregating empty level."""
        result = CostAggregator.aggregate_level_cost([])
        assert result is None

    def test_aggregate_level_cost_multiple_sessions(self):
        """Test aggregating cost for multiple sessions."""
        logger = MetricsLogger()
        
        metrics_list = []
        for session_id in ["session-c1-1", "session-c1-2"]:
            for i in range(2):
                metrics = logger.create_metrics(
                    ttft_ms=100.0,
                    total_latency_ms=500.0,
                    input_tokens=1000,
                    output_tokens=100,
                    model_used="amazon.nova-pro-v1:0",
                    proficiency_level="C1",
                    session_id=session_id,
                    turn_index=i,
                )
                metrics_list.append(metrics)
        
        result = CostAggregator.aggregate_level_cost(metrics_list)
        
        assert result is not None
        assert result["proficiency_level"] == "C1"
        assert result["total_turns"] == 4
        assert result["avg_nova_cost_per_turn_usd"] > 0
        assert result["savings_percent"] > 0

    def test_check_cost_alerts_no_alerts(self):
        """Test cost check with no alerts."""
        logger = MetricsLogger()
        
        metrics = logger.create_metrics(
            ttft_ms=100.0,
            total_latency_ms=500.0,
            input_tokens=100,  # Low tokens
            output_tokens=10,
            model_used="amazon.nova-micro-v1:0",
            proficiency_level="A1",
            session_id="session-low-cost",
            turn_index=0,
        )
        
        alerts = CostAggregator.check_cost_alerts(metrics)
        
        assert len(alerts) == 0

    def test_check_cost_alerts_warning(self):
        """Test cost check with warning alert."""
        logger = MetricsLogger()
        
        # Create metrics with high cost (but not critical)
        metrics = logger.create_metrics(
            ttft_ms=100.0,
            total_latency_ms=500.0,
            input_tokens=50000,  # High tokens
            output_tokens=5000,
            model_used="amazon.nova-pro-v1:0",  # Expensive model
            proficiency_level="C1",
            session_id="session-high-cost",
            turn_index=0,
        )
        
        alerts = CostAggregator.check_cost_alerts(metrics)
        
        # Should have at least one alert
        assert len(alerts) > 0
        # Check alert level (could be warning or critical)
        assert any(alert.alert_level in [CostAlertLevel.WARNING, CostAlertLevel.CRITICAL] for alert in alerts)

    def test_check_cost_alerts_critical(self):
        """Test cost check with critical alert."""
        logger = MetricsLogger()
        
        # Create metrics with very high cost
        metrics = logger.create_metrics(
            ttft_ms=100.0,
            total_latency_ms=500.0,
            input_tokens=500000,  # Very high tokens
            output_tokens=50000,
            model_used="amazon.nova-pro-v1:0",  # Expensive model
            proficiency_level="C2",
            session_id="session-critical-cost",
            turn_index=0,
        )
        
        alerts = CostAggregator.check_cost_alerts(metrics)
        
        # Should have critical alert
        assert len(alerts) > 0
        assert any(alert.alert_level == CostAlertLevel.CRITICAL for alert in alerts)

    def test_check_cost_alerts_session_level(self):
        """Test cost check with session-level cost."""
        logger = MetricsLogger()
        
        metrics = logger.create_metrics(
            ttft_ms=100.0,
            total_latency_ms=500.0,
            input_tokens=1000,
            output_tokens=100,
            model_used="amazon.nova-micro-v1:0",
            proficiency_level="A1",
            session_id="session-alert",
            turn_index=0,
        )
        
        # High session cost
        session_cost = 0.25
        
        alerts = CostAggregator.check_cost_alerts(metrics, session_cost=session_cost)
        
        # Should have session-level alert
        assert len(alerts) > 0
        assert any(alert.actual_cost_usd == session_cost for alert in alerts)

    def test_calculate_blended_cost(self):
        """Test blended cost calculation."""
        level_costs = {
            "A1": 0.005,
            "A2": 0.006,
            "B1": 0.008,
            "B2": 0.010,
            "C1": 0.015,
            "C2": 0.020,
        }
        
        blended = CostAggregator.calculate_blended_cost(level_costs)
        
        # Should be average of all costs
        expected = sum(level_costs.values()) / len(level_costs)
        assert blended == expected

    def test_calculate_blended_cost_empty(self):
        """Test blended cost with empty dict."""
        blended = CostAggregator.calculate_blended_cost({})
        assert blended == 0.0

    def test_get_cost_savings_target(self):
        """Test cost savings target calculation."""
        current_cost = 0.032  # Claude Haiku baseline
        target_savings = 50  # 50% savings
        
        target = CostAggregator.get_cost_savings_target(current_cost, target_savings)
        
        # Should be 50% of current cost
        assert target == 0.016

    def test_get_cost_savings_target_custom_percent(self):
        """Test cost savings target with custom percentage."""
        current_cost = 0.100
        target_savings = 60  # 60% savings
        
        target = CostAggregator.get_cost_savings_target(current_cost, target_savings)
        
        # Should be 40% of current cost (100% - 60%)
        assert abs(target - 0.040) < 0.0001

    def test_cost_alert_structure(self):
        """Test CostAlert dataclass."""
        alert = CostAlert(
            alert_level=CostAlertLevel.WARNING,
            message="Cost exceeded",
            threshold_usd=0.01,
            actual_cost_usd=0.015,
            proficiency_level="A1",
            session_id="session-123",
        )
        
        assert alert.alert_level == CostAlertLevel.WARNING
        assert alert.message == "Cost exceeded"
        assert alert.threshold_usd == 0.01
        assert alert.actual_cost_usd == 0.015

    def test_aggregate_session_cost_with_different_models(self):
        """Test aggregating cost with different models."""
        logger = MetricsLogger()
        
        metrics_list = [
            logger.create_metrics(
                ttft_ms=100.0,
                total_latency_ms=500.0,
                input_tokens=1000,
                output_tokens=100,
                model_used="amazon.nova-micro-v1:0",
                proficiency_level="A1",
                session_id="session-mixed",
                turn_index=0,
            ),
            logger.create_metrics(
                ttft_ms=150.0,
                total_latency_ms=600.0,
                input_tokens=1000,
                output_tokens=100,
                model_used="amazon.nova-lite-v1:0",
                proficiency_level="A1",
                session_id="session-mixed",
                turn_index=1,
            ),
        ]
        
        result = CostAggregator.aggregate_session_cost(metrics_list)
        
        assert result is not None
        assert result["total_turns"] == 2
        # Lite is more expensive than Micro, so total cost should reflect that
        assert result["total_nova_cost_usd"] > 0

    def test_haiku_pricing_constants(self):
        """Test Haiku pricing constants."""
        assert CostAggregator.HAIKU_PRICING["input"] == 0.80
        assert CostAggregator.HAIKU_PRICING["output"] == 4.00

    def test_cost_thresholds_constants(self):
        """Test cost threshold constants."""
        assert CostAggregator.COST_THRESHOLDS["per_turn_warning"] == 0.01
        assert CostAggregator.COST_THRESHOLDS["per_turn_critical"] == 0.02
        assert CostAggregator.COST_THRESHOLDS["per_session_warning"] == 0.10
        assert CostAggregator.COST_THRESHOLDS["per_session_critical"] == 0.20
