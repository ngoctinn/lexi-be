"""Tests for A/B testing framework."""

import pytest
from src.domain.services.ab_testing import (
    ABTestingManager,
    ExperimentAnalyzer,
    ExperimentAssignment,
    ExperimentConfig,
    ExperimentMetrics,
    ExperimentVariant,
)


class TestExperimentConfig:
    """Test experiment configuration."""
    
    def test_valid_experiment_config(self):
        """Test creating valid experiment config."""
        config = ExperimentConfig(
            experiment_id="test",
            name="Test Experiment",
            description="Test description",
            treatment_percentage=50,
            control_percentage=50,
        )
        
        assert config.experiment_id == "test"
        assert config.treatment_percentage == 50
        assert config.control_percentage == 50
        assert config.enabled is True
    
    def test_invalid_percentages(self):
        """Test that invalid percentages raise error."""
        with pytest.raises(ValueError):
            ExperimentConfig(
                experiment_id="test",
                name="Test",
                description="Test",
                treatment_percentage=60,
                control_percentage=50,  # Total = 110
            )
    
    def test_zero_treatment_percentage(self):
        """Test experiment with 0% treatment."""
        config = ExperimentConfig(
            experiment_id="test",
            name="Test",
            description="Test",
            treatment_percentage=0,
            control_percentage=100,
        )
        
        assert config.treatment_percentage == 0
        assert config.control_percentage == 100


class TestABTestingManager:
    """Test A/B testing manager."""
    
    def test_manager_initialization(self):
        """Test manager initialization."""
        manager = ABTestingManager()
        
        assert manager.active_experiment is not None
        assert manager.active_experiment.enabled is True
    
    def test_assign_variant_treatment(self):
        """Test assigning variant to treatment."""
        manager = ABTestingManager()
        
        # Use a session ID that hashes to < 10 (treatment percentage)
        assignment = manager.assign_variant("session_treatment_001")
        
        assert assignment.experiment_id == manager.active_experiment.experiment_id
        assert assignment.session_id == "session_treatment_001"
        assert assignment.variant in [ExperimentVariant.CONTROL, ExperimentVariant.TREATMENT]
    
    def test_assign_variant_deterministic(self):
        """Test that variant assignment is deterministic."""
        manager = ABTestingManager()
        
        session_id = "test_session_123"
        assignment1 = manager.assign_variant(session_id)
        assignment2 = manager.assign_variant(session_id)
        
        assert assignment1.variant == assignment2.variant
    
    def test_assign_variant_no_active_experiment(self):
        """Test variant assignment with no active experiment."""
        manager = ABTestingManager()
        manager.active_experiment = None
        
        assignment = manager.assign_variant("session_001")
        
        assert assignment.variant == ExperimentVariant.CONTROL
        assert assignment.experiment_id == "none"
    
    def test_enable_experiment(self):
        """Test enabling an experiment."""
        manager = ABTestingManager()
        
        # Disable current experiment
        manager.disable_experiment(manager.active_experiment.experiment_id)
        assert manager.active_experiment is None
        
        # Enable phase2
        success = manager.enable_experiment("phase2_50_percent")
        
        assert success is True
        assert manager.active_experiment is not None
        assert manager.active_experiment.experiment_id == "phase2_50_percent"
        assert manager.active_experiment.treatment_percentage == 50
    
    def test_enable_nonexistent_experiment(self):
        """Test enabling nonexistent experiment."""
        manager = ABTestingManager()
        
        success = manager.enable_experiment("nonexistent")
        
        assert success is False
    
    def test_disable_experiment(self):
        """Test disabling an experiment."""
        manager = ABTestingManager()
        
        exp_id = manager.active_experiment.experiment_id
        success = manager.disable_experiment(exp_id)
        
        assert success is True
        assert manager.active_experiment is None
    
    def test_disable_nonexistent_experiment(self):
        """Test disabling nonexistent experiment."""
        manager = ABTestingManager()
        
        success = manager.disable_experiment("nonexistent")
        
        assert success is False
    
    def test_get_active_experiment(self):
        """Test getting active experiment."""
        manager = ABTestingManager()
        
        exp = manager.get_active_experiment()
        
        assert exp is not None
        assert exp.enabled is True
    
    def test_get_experiment_stats(self):
        """Test getting experiment statistics."""
        manager = ABTestingManager()
        
        stats = manager.get_experiment_stats()
        
        assert "active_experiment" in stats
        assert "experiments" in stats
        assert stats["active_experiment"] is not None
        assert len(stats["experiments"]) == 3
    
    def test_phase1_10_percent(self):
        """Test phase 1 experiment (10% treatment)."""
        manager = ABTestingManager()
        manager.enable_experiment("phase1_10_percent")
        
        exp = manager.get_active_experiment()
        
        assert exp.treatment_percentage == 10
        assert exp.control_percentage == 90
    
    def test_phase2_50_percent(self):
        """Test phase 2 experiment (50% treatment)."""
        manager = ABTestingManager()
        manager.enable_experiment("phase2_50_percent")
        
        exp = manager.get_active_experiment()
        
        assert exp.treatment_percentage == 50
        assert exp.control_percentage == 50
    
    def test_phase3_100_percent(self):
        """Test phase 3 experiment (100% treatment)."""
        manager = ABTestingManager()
        manager.enable_experiment("phase3_100_percent")
        
        exp = manager.get_active_experiment()
        
        assert exp.treatment_percentage == 100
        assert exp.control_percentage == 0


class TestExperimentMetrics:
    """Test experiment metrics."""
    
    def test_create_metrics(self):
        """Test creating experiment metrics."""
        metrics = ExperimentMetrics(
            variant=ExperimentVariant.TREATMENT,
            sample_size=1000,
            avg_ttft_ms=350.0,
            avg_latency_ms=1800.0,
            avg_cost_usd=0.008,
            avg_quality_score=85.0,
            fallback_rate_percent=12.0,
            user_satisfaction=4.2,
        )
        
        assert metrics.variant == ExperimentVariant.TREATMENT
        assert metrics.sample_size == 1000
        assert metrics.avg_ttft_ms == 350.0
    
    def test_metrics_string_representation(self):
        """Test metrics string representation."""
        metrics = ExperimentMetrics(
            variant=ExperimentVariant.CONTROL,
            sample_size=500,
            avg_ttft_ms=400.0,
            avg_latency_ms=2000.0,
            avg_cost_usd=0.032,
            avg_quality_score=80.0,
            fallback_rate_percent=0.0,
            user_satisfaction=4.0,
        )
        
        str_repr = str(metrics)
        
        assert "control" in str_repr
        assert "500" in str_repr
        assert "400" in str_repr


class TestExperimentAnalyzer:
    """Test experiment analyzer."""
    
    def test_compare_variants_treatment_better(self):
        """Test comparing variants where treatment is better."""
        control = ExperimentMetrics(
            variant=ExperimentVariant.CONTROL,
            sample_size=1000,
            avg_ttft_ms=400.0,
            avg_latency_ms=2000.0,
            avg_cost_usd=0.032,
            avg_quality_score=80.0,
            fallback_rate_percent=0.0,
            user_satisfaction=4.0,
        )
        
        treatment = ExperimentMetrics(
            variant=ExperimentVariant.TREATMENT,
            sample_size=1000,
            avg_ttft_ms=350.0,
            avg_latency_ms=1800.0,
            avg_cost_usd=0.008,
            avg_quality_score=85.0,
            fallback_rate_percent=12.0,
            user_satisfaction=4.2,
        )
        
        comparison = ExperimentAnalyzer.compare_variants(control, treatment)
        
        assert "control" in comparison
        assert "treatment" in comparison
        assert "improvements" in comparison
        
        # Check improvements
        improvements = comparison["improvements"]
        assert improvements["cost_percent"] > 0  # Cost improved
        assert improvements["quality_percent"] > 0  # Quality improved
    
    def test_calculate_improvement_lower_is_better(self):
        """Test improvement calculation for lower-is-better metrics."""
        improvement = ExperimentAnalyzer._calculate_improvement(
            control_value=400.0,
            treatment_value=350.0,
            lower_is_better=True,
        )
        
        # (400 - 350) / 400 * 100 = 12.5%
        assert improvement == pytest.approx(12.5)
    
    def test_calculate_improvement_higher_is_better(self):
        """Test improvement calculation for higher-is-better metrics."""
        improvement = ExperimentAnalyzer._calculate_improvement(
            control_value=80.0,
            treatment_value=85.0,
            lower_is_better=False,
        )
        
        # (85 - 80) / 80 * 100 = 6.25%
        assert improvement == pytest.approx(6.25)
    
    def test_calculate_improvement_zero_control(self):
        """Test improvement calculation with zero control value."""
        improvement = ExperimentAnalyzer._calculate_improvement(
            control_value=0.0,
            treatment_value=100.0,
            lower_is_better=False,
        )
        
        assert improvement == 0.0
    
    def test_should_rollout_positive(self):
        """Test rollout decision with positive results."""
        control = ExperimentMetrics(
            variant=ExperimentVariant.CONTROL,
            sample_size=1000,
            avg_ttft_ms=400.0,
            avg_latency_ms=2000.0,
            avg_cost_usd=0.032,
            avg_quality_score=80.0,
            fallback_rate_percent=0.0,
            user_satisfaction=4.0,
        )
        
        treatment = ExperimentMetrics(
            variant=ExperimentVariant.TREATMENT,
            sample_size=1000,
            avg_ttft_ms=350.0,
            avg_latency_ms=1800.0,
            avg_cost_usd=0.008,
            avg_quality_score=85.0,
            fallback_rate_percent=12.0,
            user_satisfaction=4.2,
        )
        
        comparison = ExperimentAnalyzer.compare_variants(control, treatment)
        should_rollout = ExperimentAnalyzer.should_rollout(comparison)
        
        assert should_rollout is True
    
    def test_should_rollout_negative_cost(self):
        """Test rollout decision with negative cost results."""
        control = ExperimentMetrics(
            variant=ExperimentVariant.CONTROL,
            sample_size=1000,
            avg_ttft_ms=400.0,
            avg_latency_ms=2000.0,
            avg_cost_usd=0.008,
            avg_quality_score=80.0,
            fallback_rate_percent=0.0,
            user_satisfaction=4.0,
        )
        
        treatment = ExperimentMetrics(
            variant=ExperimentVariant.TREATMENT,
            sample_size=1000,
            avg_ttft_ms=350.0,
            avg_latency_ms=1800.0,
            avg_cost_usd=0.032,  # Worse cost
            avg_quality_score=85.0,
            fallback_rate_percent=12.0,
            user_satisfaction=4.2,
        )
        
        comparison = ExperimentAnalyzer.compare_variants(control, treatment)
        should_rollout = ExperimentAnalyzer.should_rollout(comparison)
        
        assert should_rollout is False
    
    def test_should_rollout_quality_degradation(self):
        """Test rollout decision with quality degradation."""
        control = ExperimentMetrics(
            variant=ExperimentVariant.CONTROL,
            sample_size=1000,
            avg_ttft_ms=400.0,
            avg_latency_ms=2000.0,
            avg_cost_usd=0.032,
            avg_quality_score=85.0,
            fallback_rate_percent=0.0,
            user_satisfaction=4.0,
        )
        
        treatment = ExperimentMetrics(
            variant=ExperimentVariant.TREATMENT,
            sample_size=1000,
            avg_ttft_ms=350.0,
            avg_latency_ms=1800.0,
            avg_cost_usd=0.008,
            avg_quality_score=80.0,  # Worse quality
            fallback_rate_percent=12.0,
            user_satisfaction=4.2,
        )
        
        comparison = ExperimentAnalyzer.compare_variants(control, treatment)
        should_rollout = ExperimentAnalyzer.should_rollout(comparison)
        
        assert should_rollout is False
    
    def test_should_rollout_satisfaction_degradation(self):
        """Test rollout decision with satisfaction degradation."""
        control = ExperimentMetrics(
            variant=ExperimentVariant.CONTROL,
            sample_size=1000,
            avg_ttft_ms=400.0,
            avg_latency_ms=2000.0,
            avg_cost_usd=0.032,
            avg_quality_score=80.0,
            fallback_rate_percent=0.0,
            user_satisfaction=4.5,
        )
        
        treatment = ExperimentMetrics(
            variant=ExperimentVariant.TREATMENT,
            sample_size=1000,
            avg_ttft_ms=350.0,
            avg_latency_ms=1800.0,
            avg_cost_usd=0.008,
            avg_quality_score=85.0,
            fallback_rate_percent=12.0,
            user_satisfaction=4.0,  # Worse satisfaction (> 5% degradation)
        )
        
        comparison = ExperimentAnalyzer.compare_variants(control, treatment)
        should_rollout = ExperimentAnalyzer.should_rollout(comparison)
        
        assert should_rollout is False
