"""Unit tests for ModelRouter."""

import pytest
from domain.services.model_router import ModelRouter, ModelConfig
from domain.value_objects.enums import ProficiencyLevel


class TestModelRouter:
    """Test ModelRouter routing logic."""

    def test_get_config_a1(self):
        """Test A1 configuration."""
        config = ModelRouter.get_config(ProficiencyLevel.A1.value)
        assert config.primary_model == ModelRouter.MICRO
        assert config.fallback_model is None
        assert config.fallback_rate == 0.0
        assert config.max_tokens == 40
        assert config.temperature == 0.6

    def test_get_config_a2(self):
        """Test A2 configuration."""
        config = ModelRouter.get_config(ProficiencyLevel.A2.value)
        assert config.primary_model == ModelRouter.MICRO
        assert config.fallback_model is None
        assert config.fallback_rate == 0.0
        assert config.max_tokens == 60
        assert config.temperature == 0.65

    def test_get_config_b1(self):
        """Test B1 configuration (with fallback)."""
        config = ModelRouter.get_config(ProficiencyLevel.B1.value)
        assert config.primary_model == ModelRouter.MICRO
        assert config.fallback_model == ModelRouter.LITE
        assert config.fallback_rate == 0.05
        assert config.max_tokens == 100
        assert config.temperature == 0.7

    def test_get_config_b2(self):
        """Test B2 configuration (with fallback)."""
        config = ModelRouter.get_config(ProficiencyLevel.B2.value)
        assert config.primary_model == ModelRouter.MICRO
        assert config.fallback_model == ModelRouter.LITE
        assert config.fallback_rate == 0.10
        assert config.max_tokens == 150
        assert config.temperature == 0.75

    def test_get_config_c1(self):
        """Test C1 configuration (with Pro fallback)."""
        config = ModelRouter.get_config(ProficiencyLevel.C1.value)
        assert config.primary_model == ModelRouter.MICRO
        assert config.fallback_model == ModelRouter.PRO
        assert config.fallback_rate == 0.30
        assert config.max_tokens == 200
        assert config.temperature == 0.80

    def test_get_config_c2(self):
        """Test C2 configuration (with Pro fallback)."""
        config = ModelRouter.get_config(ProficiencyLevel.C2.value)
        assert config.primary_model == ModelRouter.MICRO
        assert config.fallback_model == ModelRouter.PRO
        assert config.fallback_rate == 0.40
        assert config.max_tokens == 250
        assert config.temperature == 0.85

    def test_get_config_invalid_level(self):
        """Test invalid proficiency level raises error."""
        with pytest.raises(ValueError, match="Unknown proficiency level"):
            ModelRouter.get_config("INVALID")

    def test_get_primary_model(self):
        """Test get_primary_model returns correct model."""
        assert ModelRouter.get_primary_model(ProficiencyLevel.A1.value) == ModelRouter.MICRO
        assert ModelRouter.get_primary_model(ProficiencyLevel.B1.value) == ModelRouter.MICRO
        assert ModelRouter.get_primary_model(ProficiencyLevel.C1.value) == ModelRouter.MICRO

    def test_get_fallback_model(self):
        """Test get_fallback_model returns correct model or None."""
        assert ModelRouter.get_fallback_model(ProficiencyLevel.A1.value) is None
        assert ModelRouter.get_fallback_model(ProficiencyLevel.B1.value) == ModelRouter.LITE
        assert ModelRouter.get_fallback_model(ProficiencyLevel.C1.value) == ModelRouter.PRO

    def test_get_fallback_rate(self):
        """Test get_fallback_rate returns correct rate."""
        assert ModelRouter.get_fallback_rate(ProficiencyLevel.A1.value) == 0.0
        assert ModelRouter.get_fallback_rate(ProficiencyLevel.B1.value) == 0.05
        assert ModelRouter.get_fallback_rate(ProficiencyLevel.B2.value) == 0.10
        assert ModelRouter.get_fallback_rate(ProficiencyLevel.C1.value) == 0.30
        assert ModelRouter.get_fallback_rate(ProficiencyLevel.C2.value) == 0.40

    def test_get_max_tokens(self):
        """Test get_max_tokens returns correct value."""
        assert ModelRouter.get_max_tokens(ProficiencyLevel.A1.value) == 40
        assert ModelRouter.get_max_tokens(ProficiencyLevel.A2.value) == 60
        assert ModelRouter.get_max_tokens(ProficiencyLevel.B1.value) == 100
        assert ModelRouter.get_max_tokens(ProficiencyLevel.B2.value) == 150
        assert ModelRouter.get_max_tokens(ProficiencyLevel.C1.value) == 200
        assert ModelRouter.get_max_tokens(ProficiencyLevel.C2.value) == 250

    def test_get_temperature(self):
        """Test get_temperature returns correct value."""
        assert ModelRouter.get_temperature(ProficiencyLevel.A1.value) == 0.6
        assert ModelRouter.get_temperature(ProficiencyLevel.A2.value) == 0.65
        assert ModelRouter.get_temperature(ProficiencyLevel.B1.value) == 0.7
        assert ModelRouter.get_temperature(ProficiencyLevel.B2.value) == 0.75
        assert ModelRouter.get_temperature(ProficiencyLevel.C1.value) == 0.80
        assert ModelRouter.get_temperature(ProficiencyLevel.C2.value) == 0.85

    def test_should_use_fallback_no_fallback_level(self):
        """Test should_use_fallback returns False for A1-A2 (no fallback)."""
        assert ModelRouter.should_use_fallback(ProficiencyLevel.A1.value, 0.0) is False
        assert ModelRouter.should_use_fallback(ProficiencyLevel.A1.value, 0.5) is False
        assert ModelRouter.should_use_fallback(ProficiencyLevel.A1.value, 1.0) is False

    def test_should_use_fallback_b1(self):
        """Test should_use_fallback for B1 (5% fallback rate)."""
        # Below threshold → use fallback
        assert ModelRouter.should_use_fallback(ProficiencyLevel.B1.value, 0.04) is True
        # At threshold → don't use fallback
        assert ModelRouter.should_use_fallback(ProficiencyLevel.B1.value, 0.05) is False
        # Above threshold → don't use fallback
        assert ModelRouter.should_use_fallback(ProficiencyLevel.B1.value, 0.06) is False

    def test_should_use_fallback_c1(self):
        """Test should_use_fallback for C1 (30% fallback rate)."""
        # Below threshold → use fallback
        assert ModelRouter.should_use_fallback(ProficiencyLevel.C1.value, 0.29) is True
        # At threshold → don't use fallback
        assert ModelRouter.should_use_fallback(ProficiencyLevel.C1.value, 0.30) is False
        # Above threshold → don't use fallback
        assert ModelRouter.should_use_fallback(ProficiencyLevel.C1.value, 0.31) is False

    def test_model_ids_are_correct(self):
        """Test model IDs match AWS documentation."""
        assert ModelRouter.MICRO == "amazon.nova-micro-v1:0"
        assert ModelRouter.LITE == "amazon.nova-lite-v1:0"
        assert ModelRouter.PRO == "amazon.nova-pro-v1:0"
