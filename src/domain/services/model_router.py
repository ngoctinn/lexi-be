"""
Model Router for Scenario B: Nova Micro Primary + Fallback Strategy

Routing matrix:
- A1-A2 → Micro (no fallback)
- B1 → Micro (5% fallback to Lite)
- B2 → Micro (10% fallback to Lite)
- C1 → Micro (30% fallback to Pro)
- C2 → Micro (40% fallback to Pro)

Model IDs:
- Micro: amazon.nova-micro-v1:0
- Lite: amazon.nova-lite-v1:0
- Pro: amazon.nova-pro-v1:0
"""

from dataclasses import dataclass
from typing import Optional
from domain.value_objects.enums import ProficiencyLevel


@dataclass
class ModelConfig:
    """Configuration for a model at a specific proficiency level."""
    primary_model: str
    fallback_model: Optional[str]
    fallback_rate: float  # 0.0-1.0, probability of using fallback
    max_tokens: int
    temperature: float


class ModelRouter:
    """Routes requests to appropriate model based on proficiency level."""

    # Model IDs
    MICRO = "amazon.nova-micro-v1:0"
    LITE = "amazon.nova-lite-v1:0"
    PRO = "amazon.nova-pro-v1:0"

    # Routing matrix: level → ModelConfig
    _ROUTING_MATRIX = {
        ProficiencyLevel.A1.value: ModelConfig(
            primary_model=MICRO,
            fallback_model=None,
            fallback_rate=0.0,
            max_tokens=40,
            temperature=0.6,
        ),
        ProficiencyLevel.A2.value: ModelConfig(
            primary_model=MICRO,
            fallback_model=None,
            fallback_rate=0.0,
            max_tokens=60,
            temperature=0.65,
        ),
        ProficiencyLevel.B1.value: ModelConfig(
            primary_model=MICRO,
            fallback_model=LITE,
            fallback_rate=0.05,
            max_tokens=100,
            temperature=0.7,
        ),
        ProficiencyLevel.B2.value: ModelConfig(
            primary_model=MICRO,
            fallback_model=LITE,
            fallback_rate=0.10,
            max_tokens=150,
            temperature=0.75,
        ),
        ProficiencyLevel.C1.value: ModelConfig(
            primary_model=MICRO,
            fallback_model=PRO,
            fallback_rate=0.30,
            max_tokens=200,
            temperature=0.80,
        ),
        ProficiencyLevel.C2.value: ModelConfig(
            primary_model=MICRO,
            fallback_model=PRO,
            fallback_rate=0.40,
            max_tokens=250,
            temperature=0.85,
        ),
    }

    @classmethod
    def get_config(cls, level: str) -> ModelConfig:
        """Get model configuration for a proficiency level."""
        config = cls._ROUTING_MATRIX.get(level)
        if not config:
            raise ValueError(f"Unknown proficiency level: {level}")
        return config

    @classmethod
    def get_primary_model(cls, level: str) -> str:
        """Get primary model ID for a proficiency level."""
        return cls.get_config(level).primary_model

    @classmethod
    def get_fallback_model(cls, level: str) -> Optional[str]:
        """Get fallback model ID for a proficiency level (None if no fallback)."""
        return cls.get_config(level).fallback_model

    @classmethod
    def get_fallback_rate(cls, level: str) -> float:
        """Get fallback rate (0.0-1.0) for a proficiency level."""
        return cls.get_config(level).fallback_rate

    @classmethod
    def get_max_tokens(cls, level: str) -> int:
        """Get max output tokens for a proficiency level."""
        return cls.get_config(level).max_tokens

    @classmethod
    def get_temperature(cls, level: str) -> float:
        """Get temperature for a proficiency level."""
        return cls.get_config(level).temperature

    @classmethod
    def should_use_fallback(cls, level: str, random_value: float) -> bool:
        """
        Determine if fallback should be used based on fallback rate.
        
        Args:
            level: Proficiency level
            random_value: Random value between 0.0 and 1.0
            
        Returns:
            True if fallback should be used, False otherwise
        """
        fallback_rate = cls.get_fallback_rate(level)
        return random_value < fallback_rate
