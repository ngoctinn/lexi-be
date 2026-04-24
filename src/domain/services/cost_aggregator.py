"""Cost aggregation and analysis for conversation metrics."""

import logging
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum

from domain.services.metrics_logger import ConversationMetrics

logger = logging.getLogger(__name__)


class CostAlertLevel(Enum):
    """Alert levels for cost thresholds."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class CostAlert:
    """Alert for cost threshold violation."""
    
    alert_level: CostAlertLevel
    message: str
    threshold_usd: float
    actual_cost_usd: float
    proficiency_level: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class CostComparison:
    """Cost comparison with baseline (Claude Haiku)."""
    
    nova_cost_usd: float
    haiku_cost_usd: float
    savings_usd: float
    savings_percent: float
    
    def __post_init__(self):
        """Calculate savings."""
        if self.haiku_cost_usd > 0:
            self.savings_percent = (self.savings_usd / self.haiku_cost_usd) * 100


class CostAggregator:
    """Aggregates and analyzes costs."""
    
    # Claude Haiku pricing (USD per 1M tokens)
    HAIKU_PRICING = {
        "input": 0.80,
        "output": 4.00,
    }
    
    # Cost thresholds
    COST_THRESHOLDS = {
        "per_turn_warning": 0.01,  # $0.01 per turn
        "per_turn_critical": 0.02,  # $0.02 per turn
        "per_session_warning": 0.10,  # $0.10 per session
        "per_session_critical": 0.20,  # $0.20 per session
    }

    @staticmethod
    def calculate_haiku_cost(
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """
        Calculate cost for Claude Haiku baseline.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Cost in USD
        """
        input_cost = input_tokens * CostAggregator.HAIKU_PRICING["input"] / 1_000_000
        output_cost = output_tokens * CostAggregator.HAIKU_PRICING["output"] / 1_000_000
        return input_cost + output_cost

    @staticmethod
    def aggregate_session_cost(
        metrics_list: List[ConversationMetrics],
    ) -> Optional[dict]:
        """
        Aggregate cost for a session.
        
        Args:
            metrics_list: List of ConversationMetrics for a session
            
        Returns:
            Dictionary with cost aggregates or None if empty
        """
        if not metrics_list:
            return None
        
        total_nova_cost = 0.0
        total_haiku_cost = 0.0
        total_input_tokens = 0
        total_output_tokens = 0
        turn_count = 0
        
        for metric in metrics_list:
            # Nova cost
            if metric.cost_usd:
                total_nova_cost += metric.cost_usd
            
            # Haiku cost (for comparison)
            haiku_cost = CostAggregator.calculate_haiku_cost(
                metric.input_tokens,
                metric.output_tokens,
            )
            total_haiku_cost += haiku_cost
            
            # Tokens
            total_input_tokens += metric.input_tokens
            total_output_tokens += metric.output_tokens
            turn_count += 1
        
        # Calculate aggregates
        avg_nova_cost = total_nova_cost / turn_count if turn_count > 0 else 0.0
        avg_haiku_cost = total_haiku_cost / turn_count if turn_count > 0 else 0.0
        
        savings = total_haiku_cost - total_nova_cost
        savings_percent = (savings / total_haiku_cost * 100) if total_haiku_cost > 0 else 0.0
        
        return {
            "session_id": metrics_list[0].session_id,
            "proficiency_level": metrics_list[0].proficiency_level,
            "total_turns": turn_count,
            "total_nova_cost_usd": total_nova_cost,
            "total_haiku_cost_usd": total_haiku_cost,
            "avg_nova_cost_per_turn_usd": avg_nova_cost,
            "avg_haiku_cost_per_turn_usd": avg_haiku_cost,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "savings_usd": savings,
            "savings_percent": savings_percent,
        }

    @staticmethod
    def aggregate_level_cost(
        metrics_list: List[ConversationMetrics],
    ) -> Optional[dict]:
        """
        Aggregate cost for a proficiency level.
        
        Args:
            metrics_list: List of ConversationMetrics for a level
            
        Returns:
            Dictionary with cost aggregates or None if empty
        """
        if not metrics_list:
            return None
        
        total_nova_cost = 0.0
        total_haiku_cost = 0.0
        total_turns = 0
        
        for metric in metrics_list:
            # Nova cost
            if metric.cost_usd:
                total_nova_cost += metric.cost_usd
            
            # Haiku cost
            haiku_cost = CostAggregator.calculate_haiku_cost(
                metric.input_tokens,
                metric.output_tokens,
            )
            total_haiku_cost += haiku_cost
            total_turns += 1
        
        # Calculate aggregates
        avg_nova_cost = total_nova_cost / total_turns if total_turns > 0 else 0.0
        avg_haiku_cost = total_haiku_cost / total_turns if total_turns > 0 else 0.0
        
        savings = total_haiku_cost - total_nova_cost
        savings_percent = (savings / total_haiku_cost * 100) if total_haiku_cost > 0 else 0.0
        
        return {
            "proficiency_level": metrics_list[0].proficiency_level,
            "total_turns": total_turns,
            "avg_nova_cost_per_turn_usd": avg_nova_cost,
            "avg_haiku_cost_per_turn_usd": avg_haiku_cost,
            "blended_cost_per_turn_usd": avg_nova_cost,
            "savings_usd": savings,
            "savings_percent": savings_percent,
        }

    @staticmethod
    def check_cost_alerts(
        metrics: ConversationMetrics,
        session_cost: Optional[float] = None,
    ) -> List[CostAlert]:
        """
        Check if cost exceeds thresholds and generate alerts.
        
        Args:
            metrics: ConversationMetrics for a turn
            session_cost: Optional session-level cost (for session alerts)
            
        Returns:
            List of CostAlert objects
        """
        alerts = []
        
        # Per-turn alerts
        if metrics.cost_usd:
            if metrics.cost_usd > CostAggregator.COST_THRESHOLDS["per_turn_critical"]:
                alerts.append(CostAlert(
                    alert_level=CostAlertLevel.CRITICAL,
                    message=f"Turn cost ${metrics.cost_usd:.4f} exceeds critical threshold "
                            f"${CostAggregator.COST_THRESHOLDS['per_turn_critical']:.4f}",
                    threshold_usd=CostAggregator.COST_THRESHOLDS["per_turn_critical"],
                    actual_cost_usd=metrics.cost_usd,
                    proficiency_level=metrics.proficiency_level,
                    session_id=metrics.session_id,
                ))
            elif metrics.cost_usd > CostAggregator.COST_THRESHOLDS["per_turn_warning"]:
                alerts.append(CostAlert(
                    alert_level=CostAlertLevel.WARNING,
                    message=f"Turn cost ${metrics.cost_usd:.4f} exceeds warning threshold "
                            f"${CostAggregator.COST_THRESHOLDS['per_turn_warning']:.4f}",
                    threshold_usd=CostAggregator.COST_THRESHOLDS["per_turn_warning"],
                    actual_cost_usd=metrics.cost_usd,
                    proficiency_level=metrics.proficiency_level,
                    session_id=metrics.session_id,
                ))
        
        # Session-level alerts
        if session_cost:
            if session_cost > CostAggregator.COST_THRESHOLDS["per_session_critical"]:
                alerts.append(CostAlert(
                    alert_level=CostAlertLevel.CRITICAL,
                    message=f"Session cost ${session_cost:.4f} exceeds critical threshold "
                            f"${CostAggregator.COST_THRESHOLDS['per_session_critical']:.4f}",
                    threshold_usd=CostAggregator.COST_THRESHOLDS["per_session_critical"],
                    actual_cost_usd=session_cost,
                    proficiency_level=metrics.proficiency_level,
                    session_id=metrics.session_id,
                ))
            elif session_cost > CostAggregator.COST_THRESHOLDS["per_session_warning"]:
                alerts.append(CostAlert(
                    alert_level=CostAlertLevel.WARNING,
                    message=f"Session cost ${session_cost:.4f} exceeds warning threshold "
                            f"${CostAggregator.COST_THRESHOLDS['per_session_warning']:.4f}",
                    threshold_usd=CostAggregator.COST_THRESHOLDS["per_session_warning"],
                    actual_cost_usd=session_cost,
                    proficiency_level=metrics.proficiency_level,
                    session_id=metrics.session_id,
                ))
        
        return alerts

    @staticmethod
    def calculate_blended_cost(
        level_costs: dict,
    ) -> float:
        """
        Calculate blended cost across all proficiency levels.
        
        Args:
            level_costs: Dictionary mapping level -> avg_cost_per_turn
            
        Returns:
            Blended cost per turn (weighted average)
        """
        if not level_costs:
            return 0.0
        
        total_cost = sum(level_costs.values())
        avg_cost = total_cost / len(level_costs)
        return avg_cost

    @staticmethod
    def get_cost_savings_target(
        current_cost: float,
        target_savings_percent: float = 50,
    ) -> float:
        """
        Calculate target cost to achieve savings goal.
        
        Args:
            current_cost: Current cost (e.g., Claude Haiku)
            target_savings_percent: Target savings percentage (default 50%)
            
        Returns:
            Target cost to achieve savings goal
        """
        return current_cost * (1 - target_savings_percent / 100)
