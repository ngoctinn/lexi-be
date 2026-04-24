"""Integration tests for MetricsRepository with DynamoDB."""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

from domain.services.metrics_logger import (
    MetricsLogger,
    QualityMetrics,
    HintMetrics,
)
from infrastructure.persistence.dynamo_metrics_repo import MetricsRepository


class TestMetricsRepository:
    """Integration tests for MetricsRepository."""

    @pytest.fixture
    def mock_table(self):
        """Create mock DynamoDB table."""
        return MagicMock()

    @pytest.fixture
    def repo(self, mock_table):
        """Create MetricsRepository with mock table."""
        return MetricsRepository(table=mock_table)

    def test_save_metrics_basic(self, repo, mock_table):
        """Test saving basic metrics."""
        logger = MetricsLogger()
        
        metrics = logger.create_metrics(
            ttft_ms=100.0,
            total_latency_ms=500.0,
            input_tokens=50,
            output_tokens=100,
            model_used="amazon.nova-micro-v1:0",
            proficiency_level="A1",
            session_id="session-123",
            turn_index=0,
        )
        
        repo.save_metrics(metrics)
        
        # Verify put_item was called
        mock_table.put_item.assert_called_once()
        call_args = mock_table.put_item.call_args
        item = call_args[1]["Item"]
        
        # Verify item structure
        assert item["PK"] == "METRICS#session-123#0"
        assert item["SK"].startswith("TURN#")
        assert item["GSI1PK"] == "SESSION#session-123"
        assert item["GSI2PK"] == "LEVEL#A1"
        assert item["EntityType"] == "METRICS"
        assert item["ttft_ms"] == Decimal("100.0")
        assert item["total_latency_ms"] == Decimal("500.0")
        assert item["model_used"] == "amazon.nova-micro-v1:0"

    def test_save_metrics_with_quality(self, repo, mock_table):
        """Test saving metrics with quality metrics."""
        logger = MetricsLogger()
        
        quality = QualityMetrics(
            has_markdown=False,
            delivery_cues_count=2,
            question_count=1,
            quality_score=85.0,
            format_compliant=True,
            length_compliant=True,
            has_question=True,
        )
        
        metrics = logger.create_metrics(
            ttft_ms=100.0,
            total_latency_ms=500.0,
            model_used="amazon.nova-micro-v1:0",
            proficiency_level="A1",
            session_id="session-quality",
            turn_index=0,
            quality_metrics=quality,
        )
        
        repo.save_metrics(metrics)
        
        call_args = mock_table.put_item.call_args
        item = call_args[1]["Item"]
        
        # Verify quality metrics in item
        assert item["quality_has_markdown"] is False
        assert item["quality_delivery_cues_count"] == 2
        assert item["quality_question_count"] == 1
        assert item["quality_score"] == Decimal("85.0")
        assert item["quality_format_compliant"] is True

    def test_save_metrics_with_hints(self, repo, mock_table):
        """Test saving metrics with hint metrics."""
        logger = MetricsLogger()
        
        hints = HintMetrics(
            hint_level="gentle_prompt",
            hint_provided=True,
            hint_accepted=True,
            scaffolding_effectiveness=0.8,
            hint_count_in_session=1,
            vietnamese_detected=False,
            off_topic_detected=False,
        )
        
        metrics = logger.create_metrics(
            ttft_ms=100.0,
            total_latency_ms=500.0,
            model_used="amazon.nova-micro-v1:0",
            proficiency_level="A1",
            session_id="session-hints",
            turn_index=0,
            hint_metrics=hints,
        )
        
        repo.save_metrics(metrics)
        
        call_args = mock_table.put_item.call_args
        item = call_args[1]["Item"]
        
        # Verify hint metrics in item
        assert item["hint_level"] == "gentle_prompt"
        assert item["hint_provided"] is True
        assert item["hint_accepted"] is True
        assert item["hint_scaffolding_effectiveness"] == Decimal("0.8")
        assert item["hint_count_in_session"] == 1

    def test_get_metrics_by_session(self, repo, mock_table):
        """Test retrieving metrics by session."""
        logger = MetricsLogger()
        
        # Create mock response
        metrics1 = logger.create_metrics(
            ttft_ms=100.0,
            total_latency_ms=500.0,
            model_used="amazon.nova-micro-v1:0",
            proficiency_level="A1",
            session_id="session-456",
            turn_index=0,
        )
        
        item1 = repo._metrics_to_item(metrics1)
        
        mock_table.query.return_value = {"Items": [item1]}
        
        # Query metrics
        result = repo.get_metrics_by_session("session-456")
        
        # Verify query was called correctly
        mock_table.query.assert_called_once()
        call_args = mock_table.query.call_args
        assert call_args[1]["IndexName"] == "GSI1-SessionMetrics"
        # Just verify the query was called with correct index
        assert "KeyConditionExpression" in call_args[1]
        
        # Verify result
        assert len(result) == 1
        assert result[0].session_id == "session-456"
        assert result[0].proficiency_level == "A1"

    def test_get_metrics_by_level(self, repo, mock_table):
        """Test retrieving metrics by proficiency level."""
        logger = MetricsLogger()
        
        # Create mock response
        metrics1 = logger.create_metrics(
            ttft_ms=100.0,
            total_latency_ms=500.0,
            model_used="amazon.nova-micro-v1:0",
            proficiency_level="B1",
            session_id="session-b1-1",
            turn_index=0,
        )
        
        item1 = repo._metrics_to_item(metrics1)
        
        mock_table.query.return_value = {"Items": [item1]}
        
        # Query metrics
        result = repo.get_metrics_by_level("B1")
        
        # Verify query was called correctly
        mock_table.query.assert_called_once()
        call_args = mock_table.query.call_args
        assert call_args[1]["IndexName"] == "GSI2-LevelMetrics"
        
        # Verify result
        assert len(result) == 1
        assert result[0].proficiency_level == "B1"

    def test_metrics_to_item_and_back(self, repo):
        """Test round-trip conversion: metrics -> item -> metrics."""
        logger = MetricsLogger()
        
        quality = QualityMetrics(
            quality_score=90.0,
            format_compliant=True,
            has_question=True,
        )
        
        hints = HintMetrics(
            hint_level="vocabulary_hint",
            hint_provided=True,
            scaffolding_effectiveness=0.75,
        )
        
        original_metrics = logger.create_metrics(
            ttft_ms=120.0,
            total_latency_ms=550.0,
            input_tokens=60,
            output_tokens=110,
            model_used="amazon.nova-lite-v1:0",
            model_source="fallback",
            fallback_reason="validation_failed",
            proficiency_level="B1",
            scenario_title="Restaurant",
            session_id="session-roundtrip",
            turn_index=2,
            response_length=200,
            validation_passed=False,
            validation_reason="Too few sentences",
            quality_metrics=quality,
            hint_metrics=hints,
        )
        
        # Convert to item and back
        item = repo._metrics_to_item(original_metrics)
        restored_metrics = repo._item_to_metrics(item)
        
        # Verify key fields match
        assert restored_metrics.ttft_ms == original_metrics.ttft_ms
        assert restored_metrics.total_latency_ms == original_metrics.total_latency_ms
        assert restored_metrics.input_tokens == original_metrics.input_tokens
        assert restored_metrics.output_tokens == original_metrics.output_tokens
        assert restored_metrics.model_used == original_metrics.model_used
        assert restored_metrics.model_source == original_metrics.model_source
        assert restored_metrics.fallback_reason == original_metrics.fallback_reason
        assert restored_metrics.proficiency_level == original_metrics.proficiency_level
        assert restored_metrics.session_id == original_metrics.session_id
        assert restored_metrics.turn_index == original_metrics.turn_index
        
        # Verify quality metrics
        assert restored_metrics.quality_metrics.quality_score == quality.quality_score
        assert restored_metrics.quality_metrics.format_compliant == quality.format_compliant
        
        # Verify hint metrics
        assert restored_metrics.hint_metrics.hint_level == hints.hint_level
        assert restored_metrics.hint_metrics.scaffolding_effectiveness == hints.scaffolding_effectiveness

    def test_get_metrics_empty_result(self, repo, mock_table):
        """Test retrieving metrics with empty result."""
        mock_table.query.return_value = {"Items": []}
        
        result = repo.get_metrics_by_session("nonexistent-session")
        
        assert result == []

    def test_get_metrics_malformed_item(self, repo, mock_table):
        """Test retrieving metrics with malformed item - should still parse with defaults."""
        # Create a malformed item (missing most fields)
        malformed_item = {
            "PK": "METRICS#session#0",
            # Missing most fields - will use defaults
        }
        
        mock_table.query.return_value = {"Items": [malformed_item]}
        
        # Should not raise, just parse with defaults
        result = repo.get_metrics_by_session("session")
        
        # Result should have 1 item (with default values)
        assert len(result) == 1
        # Verify defaults are used
        assert result[0].input_tokens == 0
        assert result[0].output_tokens == 0
        assert result[0].model_source == "primary"

    def test_save_metrics_with_none_values(self, repo, mock_table):
        """Test saving metrics with None values."""
        logger = MetricsLogger()
        
        metrics = logger.create_metrics(
            ttft_ms=None,
            total_latency_ms=None,
            model_used="amazon.nova-micro-v1:0",
            proficiency_level="A1",
            session_id="session-none",
            turn_index=0,
        )
        
        repo.save_metrics(metrics)
        
        call_args = mock_table.put_item.call_args
        item = call_args[1]["Item"]
        
        # Verify None values are handled
        assert item["ttft_ms"] is None
        assert item["total_latency_ms"] is None

    def test_metrics_cost_preserved(self, repo):
        """Test that cost is preserved in round-trip."""
        logger = MetricsLogger()
        
        metrics = logger.create_metrics(
            ttft_ms=100.0,
            total_latency_ms=500.0,
            input_tokens=1000,
            output_tokens=100,
            model_used="amazon.nova-micro-v1:0",
            proficiency_level="A1",
            session_id="session-cost",
            turn_index=0,
        )
        
        original_cost = metrics.cost_usd
        
        # Round-trip
        item = repo._metrics_to_item(metrics)
        restored_metrics = repo._item_to_metrics(item)
        
        # Verify cost is preserved
        assert restored_metrics.cost_usd == original_cost
