"""Aggregates metrics at session and level levels."""

import logging
from typing import List, Optional
from dataclasses import dataclass

from domain.services.metrics_logger import ConversationMetrics

logger = logging.getLogger(__name__)


@dataclass
class SessionMetricsAggregate:
    """Aggregated metrics for a session."""
    
    session_id: str
    proficiency_level: str
    
    # Timing aggregates
    avg_ttft_ms: float = 0.0
    p95_ttft_ms: float = 0.0
    max_ttft_ms: float = 0.0
    
    avg_total_latency_ms: float = 0.0
    p95_total_latency_ms: float = 0.0
    max_total_latency_ms: float = 0.0
    
    # Token aggregates
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    avg_output_tokens: float = 0.0
    
    # Cost aggregates
    total_cost_usd: float = 0.0
    avg_cost_per_turn_usd: float = 0.0
    
    # Model usage
    primary_model_count: int = 0
    fallback_model_count: int = 0
    fallback_rate: float = 0.0
    
    # Quality aggregates
    avg_quality_score: float = 0.0
    format_compliant_rate: float = 0.0
    length_compliant_rate: float = 0.0
    has_question_rate: float = 0.0
    
    # Hint aggregates
    hint_provided_count: int = 0
    hint_accepted_count: int = 0
    hint_acceptance_rate: float = 0.0
    
    # Validation
    validation_passed_rate: float = 0.0
    
    # Turn count
    total_turns: int = 0


@dataclass
class LevelMetricsAggregate:
    """Aggregated metrics for a proficiency level."""
    
    proficiency_level: str
    
    # Timing aggregates
    avg_ttft_ms: float = 0.0
    p95_ttft_ms: float = 0.0
    
    avg_total_latency_ms: float = 0.0
    p95_total_latency_ms: float = 0.0
    
    # Cost aggregates
    avg_cost_per_turn_usd: float = 0.0
    blended_cost_per_turn_usd: float = 0.0
    
    # Model usage
    fallback_rate: float = 0.0
    
    # Quality aggregates
    avg_quality_score: float = 0.0
    format_compliant_rate: float = 0.0
    
    # Hint aggregates
    hint_acceptance_rate: float = 0.0
    
    # Sample size
    total_turns: int = 0
    total_sessions: int = 0


class MetricsAggregator:
    """Aggregates metrics at session and level levels."""

    @staticmethod
    def aggregate_session_metrics(
        metrics_list: List[ConversationMetrics],
    ) -> Optional[SessionMetricsAggregate]:
        """
        Aggregate metrics for a session.
        
        Args:
            metrics_list: List of ConversationMetrics for a session
            
        Returns:
            SessionMetricsAggregate or None if empty
        """
        if not metrics_list:
            return None
        
        # Get session info from first metric
        first_metric = metrics_list[0]
        aggregate = SessionMetricsAggregate(
            session_id=first_metric.session_id,
            proficiency_level=first_metric.proficiency_level,
        )
        
        # Collect timing metrics
        ttft_values = []
        latency_values = []
        quality_scores = []
        
        for metric in metrics_list:
            # Timing
            if metric.ttft_ms is not None:
                ttft_values.append(metric.ttft_ms)
            if metric.total_latency_ms is not None:
                latency_values.append(metric.total_latency_ms)
            
            # Tokens
            aggregate.total_input_tokens += metric.input_tokens
            aggregate.total_output_tokens += metric.output_tokens
            
            # Cost
            if metric.cost_usd:
                aggregate.total_cost_usd += metric.cost_usd
            
            # Model usage
            if metric.model_source == "primary":
                aggregate.primary_model_count += 1
            else:
                aggregate.fallback_model_count += 1
            
            # Quality
            if metric.quality_metrics:
                qm = metric.quality_metrics
                quality_scores.append(qm.quality_score)
                if qm.format_compliant:
                    aggregate.format_compliant_rate += 1
                if qm.length_compliant:
                    aggregate.length_compliant_rate += 1
                if qm.has_question:
                    aggregate.has_question_rate += 1
            
            # Hints
            if metric.hint_metrics:
                hm = metric.hint_metrics
                if hm.hint_provided:
                    aggregate.hint_provided_count += 1
                if hm.hint_accepted:
                    aggregate.hint_accepted_count += 1
            
            # Validation
            if metric.validation_passed:
                aggregate.validation_passed_rate += 1
        
        # Calculate aggregates
        turn_count = len(metrics_list)
        aggregate.total_turns = turn_count
        
        # Timing aggregates
        if ttft_values:
            aggregate.avg_ttft_ms = sum(ttft_values) / len(ttft_values)
            aggregate.p95_ttft_ms = MetricsAggregator._percentile(ttft_values, 95)
            aggregate.max_ttft_ms = max(ttft_values)
        
        if latency_values:
            aggregate.avg_total_latency_ms = sum(latency_values) / len(latency_values)
            aggregate.p95_total_latency_ms = MetricsAggregator._percentile(latency_values, 95)
            aggregate.max_total_latency_ms = max(latency_values)
        
        # Token aggregates
        if turn_count > 0:
            aggregate.avg_output_tokens = aggregate.total_output_tokens / turn_count
        
        # Cost aggregates
        if turn_count > 0:
            aggregate.avg_cost_per_turn_usd = aggregate.total_cost_usd / turn_count
        
        # Model usage rates
        if turn_count > 0:
            aggregate.fallback_rate = aggregate.fallback_model_count / turn_count
        
        # Quality rates
        if turn_count > 0:
            aggregate.format_compliant_rate = aggregate.format_compliant_rate / turn_count
            aggregate.length_compliant_rate = aggregate.length_compliant_rate / turn_count
            aggregate.has_question_rate = aggregate.has_question_rate / turn_count
            aggregate.validation_passed_rate = aggregate.validation_passed_rate / turn_count
        
        # Hint rates
        if aggregate.hint_provided_count > 0:
            aggregate.hint_acceptance_rate = (
                aggregate.hint_accepted_count / aggregate.hint_provided_count
            )
        
        # Quality score average
        if quality_scores:
            aggregate.avg_quality_score = sum(quality_scores) / len(quality_scores)
        
        return aggregate

    @staticmethod
    def aggregate_level_metrics(
        metrics_list: List[ConversationMetrics],
    ) -> Optional[LevelMetricsAggregate]:
        """
        Aggregate metrics for a proficiency level.
        
        Args:
            metrics_list: List of ConversationMetrics for a level
            
        Returns:
            LevelMetricsAggregate or None if empty
        """
        if not metrics_list:
            return None
        
        # Get level from first metric
        first_metric = metrics_list[0]
        aggregate = LevelMetricsAggregate(
            proficiency_level=first_metric.proficiency_level,
        )
        
        # Collect metrics
        ttft_values = []
        latency_values = []
        cost_values = []
        quality_scores = []
        
        sessions_seen = set()
        
        for metric in metrics_list:
            # Timing
            if metric.ttft_ms is not None:
                ttft_values.append(metric.ttft_ms)
            if metric.total_latency_ms is not None:
                latency_values.append(metric.total_latency_ms)
            
            # Cost
            if metric.cost_usd:
                cost_values.append(metric.cost_usd)
            
            # Model usage
            if metric.model_source == "fallback":
                aggregate.fallback_rate += 1
            
            # Quality
            if metric.quality_metrics:
                qm = metric.quality_metrics
                quality_scores.append(qm.quality_score)
                if qm.format_compliant:
                    aggregate.format_compliant_rate += 1
            
            # Hints
            if metric.hint_metrics and metric.hint_metrics.hint_accepted:
                aggregate.hint_acceptance_rate += 1
            
            # Track unique sessions
            sessions_seen.add(metric.session_id)
            
            aggregate.total_turns += 1
        
        # Calculate aggregates
        if ttft_values:
            aggregate.avg_ttft_ms = sum(ttft_values) / len(ttft_values)
            aggregate.p95_ttft_ms = MetricsAggregator._percentile(ttft_values, 95)
        
        if latency_values:
            aggregate.avg_total_latency_ms = sum(latency_values) / len(latency_values)
            aggregate.p95_total_latency_ms = MetricsAggregator._percentile(latency_values, 95)
        
        if cost_values:
            aggregate.avg_cost_per_turn_usd = sum(cost_values) / len(cost_values)
            aggregate.blended_cost_per_turn_usd = sum(cost_values) / len(cost_values)
        
        if aggregate.total_turns > 0:
            aggregate.fallback_rate = aggregate.fallback_rate / aggregate.total_turns
            aggregate.format_compliant_rate = aggregate.format_compliant_rate / aggregate.total_turns
            aggregate.hint_acceptance_rate = aggregate.hint_acceptance_rate / aggregate.total_turns
        
        if quality_scores:
            aggregate.avg_quality_score = sum(quality_scores) / len(quality_scores)
        
        aggregate.total_sessions = len(sessions_seen)
        
        return aggregate

    @staticmethod
    def _percentile(values: List[float], percentile: int) -> float:
        """
        Calculate percentile of a list of values.
        
        Args:
            values: List of numeric values
            percentile: Percentile to calculate (0-100)
            
        Returns:
            Percentile value
        """
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        index = min(index, len(sorted_values) - 1)
        
        return sorted_values[index]
