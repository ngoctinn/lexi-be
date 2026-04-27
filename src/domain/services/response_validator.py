"""
Response Validator - lightweight quality gate for AI conversation responses.

Philosophy: Validate only what matters for UX. Don't over-constrain the model.
A short, natural response with no question is still valid — the model may be
acknowledging before asking. Reject only truly broken responses (empty, too long).
"""

import re
from dataclasses import dataclass
from typing import Optional
from domain.value_objects.enums import ProficiencyLevel


@dataclass
class ValidationResult:
    is_valid: bool
    reason: Optional[str] = None


class ResponseValidator:
    """
    Lightweight validator — only rejects clearly broken responses.

    Rules (intentionally permissive):
    - Empty response → reject
    - Extremely long response (> hard cap) → reject
    - Otherwise → accept

    Rationale: The model is prompted to be natural and short. Over-constraining
    with sentence counts and vocabulary diversity causes false rejections and
    forces fallback to generic responses, which is worse UX.
    """

    # Hard token cap per level (generous — model is already prompted to be short)
    _MAX_CHARS = {
        ProficiencyLevel.A1.value: 300,
        ProficiencyLevel.A2.value: 400,
        ProficiencyLevel.B1.value: 600,
        ProficiencyLevel.B2.value: 800,
        ProficiencyLevel.C1.value: 1000,
        ProficiencyLevel.C2.value: 1200,
    }

    @classmethod
    def validate(cls, response: str, level: str) -> ValidationResult:
        """
        Validate AI response. Only rejects empty or excessively long responses.

        Args:
            response: AI response text
            level: Proficiency level string (A1-C2)

        Returns:
            ValidationResult
        """
        if not response or not response.strip():
            return ValidationResult(is_valid=False, reason="Response is empty")

        # Strip delivery cues like [warmly] before length check
        clean = re.sub(r"^\[[a-zA-Z\s]+\]\s*", "", response.strip())

        if not clean:
            return ValidationResult(is_valid=False, reason="Response is empty after stripping cues")

        max_chars = cls._MAX_CHARS.get(level, 800)
        if len(clean) > max_chars:
            return ValidationResult(
                is_valid=False,
                reason=f"Response too long: {len(clean)} chars (max {max_chars})",
            )

        return ValidationResult(is_valid=True)
