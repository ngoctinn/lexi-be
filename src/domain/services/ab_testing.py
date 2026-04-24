"""A/B testing framework for gradual rollout."""

import random
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ExperimentVariant(str, Enum):
    """Experiment variants."""
    CONTROL = "control"  # Old system (Claude Haiku)
    TREATMENT = "treatment"  # New system (Nova Micro + Lite + Pro)


@dataclass
class ExperimentConfig:
    """Configuration for an A/B test experiment."""
    
    experiment_id: str
    name: str
    description: str
    treatment_percentage: int  # 0-100
    control_percentage: int  # 0-100
    enabled: bool = True
    
    def __post_init__(self):
        """Validate percentages."""
        if self.treatment_percentage + self.control_percentage != 100:
            raise ValueError(
                f"Treatment ({self.treatment_percentage}%) + Control ({self.control_percentage}%) "
                f"must equal 100%"
            )


@dataclass
class ExperimentAssignment:
    """Assignment of a user/session to an experiment variant."""
    
    experiment_id: str
    session_id: str
    variant: ExperimentVariant
    percentage: int  # Percentage assigned to this variant


class ABTestingManager:
    """Manages A/B testing experiments."""
    
    def __init__(self):
        """Initialize A/B testing manager."""
        # Create instance-level experiments to avoid test interference
        self.experiments = {
            "phase1_10_percent": ExperimentConfig(
                experiment_id="phase1_10_percent",
                name="Phase 1: 10% Treatment",
                description="Route 10% of A1-A2 traffic to new system",
                treatment_percentage=10,
                control_percentage=90,
                enabled=True,
            ),
            "phase2_50_percent": ExperimentConfig(
                experiment_id="phase2_50_percent",
                name="Phase 2: 50% Treatment",
                description="Route 50% of traffic to new system",
                treatment_percentage=50,
                control_percentage=50,
                enabled=False,  # Disabled until Phase 2
            ),
            "phase3_100_percent": ExperimentConfig(
                experiment_id="phase3_100_percent",
                name="Phase 3: 100% Treatment",
                description="Route 100% of traffic to new system",
                treatment_percentage=100,
                control_percentage=0,
                enabled=False,  # Disabled until Phase 3
            ),
        }
        self.active_experiment: Optional[ExperimentConfig] = None
        self._set_active_experiment()
    
    def _set_active_experiment(self):
        """Set the active experiment based on enabled status."""
        for exp_id, exp_config in self.experiments.items():
            if exp_config.enabled:
                self.active_experiment = exp_config
                return
        self.active_experiment = None
    
    def assign_variant(
        self,
        session_id: str,
        proficiency_level: str = "A1",
    ) -> ExperimentAssignment:
        """
        Assign a session to a variant based on active experiment.
        
        Args:
            session_id: Session ID
            proficiency_level: Learner proficiency level
            
        Returns:
            ExperimentAssignment with variant and percentage
        """
        if not self.active_experiment or not self.active_experiment.enabled:
            # No active experiment, default to control
            return ExperimentAssignment(
                experiment_id="none",
                session_id=session_id,
                variant=ExperimentVariant.CONTROL,
                percentage=100,
            )
        
        # Use session_id hash for deterministic assignment
        hash_value = hash(session_id) % 100
        
        # Assign based on treatment percentage
        if hash_value < self.active_experiment.treatment_percentage:
            variant = ExperimentVariant.TREATMENT
            percentage = self.active_experiment.treatment_percentage
        else:
            variant = ExperimentVariant.CONTROL
            percentage = self.active_experiment.control_percentage
        
        return ExperimentAssignment(
            experiment_id=self.active_experiment.experiment_id,
            session_id=session_id,
            variant=variant,
            percentage=percentage,
        )
    
    def get_active_experiment(self) -> Optional[ExperimentConfig]:
        """
        Get the active experiment.
        
        Returns:
            Active ExperimentConfig or None
        """
        return self.active_experiment
    
    def enable_experiment(self, experiment_id: str) -> bool:
        """
        Enable an experiment and disable others.
        
        Args:
            experiment_id: Experiment ID to enable
            
        Returns:
            True if successful, False if experiment not found
        """
        if experiment_id not in self.experiments:
            return False
        
        # Disable all experiments
        for exp_config in self.experiments.values():
            exp_config.enabled = False
        
        # Enable the specified experiment
        self.experiments[experiment_id].enabled = True
        self._set_active_experiment()
        
        return True
    
    def disable_experiment(self, experiment_id: str) -> bool:
        """
        Disable an experiment.
        
        Args:
            experiment_id: Experiment ID to disable
            
        Returns:
            True if successful, False if experiment not found
        """
        if experiment_id not in self.experiments:
            return False
        
        self.experiments[experiment_id].enabled = False
        self._set_active_experiment()
        
        return True
    
    def get_experiment_stats(self) -> dict:
        """
        Get statistics about all experiments.
        
        Returns:
            Dictionary with experiment stats
        """
        stats = {
            "active_experiment": None,
            "experiments": {},
        }
        
        if self.active_experiment:
            stats["active_experiment"] = {
                "id": self.active_experiment.experiment_id,
                "name": self.active_experiment.name,
                "treatment_percentage": self.active_experiment.treatment_percentage,
                "control_percentage": self.active_experiment.control_percentage,
            }
        
        for exp_id, exp_config in self.experiments.items():
            stats["experiments"][exp_id] = {
                "name": exp_config.name,
                "description": exp_config.description,
                "enabled": exp_config.enabled,
                "treatment_percentage": exp_config.treatment_percentage,
                "control_percentage": exp_config.control_percentage,
            }
        
        return stats


@dataclass
class ExperimentMetrics:
    """Metrics for comparing experiment variants."""
    
    variant: ExperimentVariant
    sample_size: int
    avg_ttft_ms: float
    avg_latency_ms: float
    avg_cost_usd: float
    avg_quality_score: float
    fallback_rate_percent: float
    user_satisfaction: float  # 1-5 scale
    
    def __str__(self) -> str:
        """String representation."""
        return (
            f"{self.variant.value}: "
            f"n={self.sample_size}, "
            f"ttft={self.avg_ttft_ms:.0f}ms, "
            f"latency={self.avg_latency_ms:.0f}ms, "
            f"cost=${self.avg_cost_usd:.4f}, "
            f"quality={self.avg_quality_score:.1f}, "
            f"fallback={self.fallback_rate_percent:.1f}%, "
            f"satisfaction={self.user_satisfaction:.1f}/5.0"
        )


class ExperimentAnalyzer:
    """Analyzes experiment results."""
    
    @staticmethod
    def compare_variants(
        control_metrics: ExperimentMetrics,
        treatment_metrics: ExperimentMetrics,
    ) -> dict:
        """
        Compare control and treatment variants.
        
        Args:
            control_metrics: Metrics for control variant
            treatment_metrics: Metrics for treatment variant
            
        Returns:
            Dictionary with comparison results
        """
        return {
            "control": {
                "ttft_ms": control_metrics.avg_ttft_ms,
                "latency_ms": control_metrics.avg_latency_ms,
                "cost_usd": control_metrics.avg_cost_usd,
                "quality_score": control_metrics.avg_quality_score,
                "fallback_rate": control_metrics.fallback_rate_percent,
                "satisfaction": control_metrics.user_satisfaction,
            },
            "treatment": {
                "ttft_ms": treatment_metrics.avg_ttft_ms,
                "latency_ms": treatment_metrics.avg_latency_ms,
                "cost_usd": treatment_metrics.avg_cost_usd,
                "quality_score": treatment_metrics.avg_quality_score,
                "fallback_rate": treatment_metrics.fallback_rate_percent,
                "satisfaction": treatment_metrics.user_satisfaction,
            },
            "improvements": {
                "ttft_percent": ExperimentAnalyzer._calculate_improvement(
                    control_metrics.avg_ttft_ms,
                    treatment_metrics.avg_ttft_ms,
                    lower_is_better=True,
                ),
                "latency_percent": ExperimentAnalyzer._calculate_improvement(
                    control_metrics.avg_latency_ms,
                    treatment_metrics.avg_latency_ms,
                    lower_is_better=True,
                ),
                "cost_percent": ExperimentAnalyzer._calculate_improvement(
                    control_metrics.avg_cost_usd,
                    treatment_metrics.avg_cost_usd,
                    lower_is_better=True,
                ),
                "quality_percent": ExperimentAnalyzer._calculate_improvement(
                    control_metrics.avg_quality_score,
                    treatment_metrics.avg_quality_score,
                    lower_is_better=False,
                ),
                "fallback_percent": ExperimentAnalyzer._calculate_improvement(
                    control_metrics.fallback_rate_percent,
                    treatment_metrics.fallback_rate_percent,
                    lower_is_better=True,
                ),
                "satisfaction_percent": ExperimentAnalyzer._calculate_improvement(
                    control_metrics.user_satisfaction,
                    treatment_metrics.user_satisfaction,
                    lower_is_better=False,
                ),
            },
        }
    
    @staticmethod
    def _calculate_improvement(
        control_value: float,
        treatment_value: float,
        lower_is_better: bool = True,
    ) -> float:
        """
        Calculate percentage improvement.
        
        Args:
            control_value: Control variant value
            treatment_value: Treatment variant value
            lower_is_better: Whether lower values are better
            
        Returns:
            Percentage improvement (positive = better)
        """
        if control_value == 0:
            return 0.0
        
        if lower_is_better:
            # For metrics where lower is better (latency, cost)
            improvement = (control_value - treatment_value) / control_value * 100
        else:
            # For metrics where higher is better (quality, satisfaction)
            improvement = (treatment_value - control_value) / control_value * 100
        
        return improvement
    
    @staticmethod
    def should_rollout(
        comparison: dict,
        min_improvement_percent: float = 5.0,
    ) -> bool:
        """
        Determine if treatment should be rolled out.
        
        Args:
            comparison: Comparison results from compare_variants
            min_improvement_percent: Minimum improvement threshold
            
        Returns:
            True if treatment should be rolled out
        """
        improvements = comparison["improvements"]
        
        # Check if treatment is better on key metrics
        # Cost improvement is most important
        if improvements["cost_percent"] < min_improvement_percent:
            return False
        
        # Quality should not degrade
        if improvements["quality_percent"] < 0:
            return False
        
        # Satisfaction should not degrade significantly
        if improvements["satisfaction_percent"] < -5:
            return False
        
        return True
