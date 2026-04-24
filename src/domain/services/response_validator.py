"""
Response Validator for Scenario B: Quality validation for Micro model responses

Validation rules per level:
- A1-A2: Simple responses (1-2 sentences, has question)
- B1-B2: Moderate responses (2-4 sentences, has question, vocabulary diversity)
- C1-C2: Complex responses (3-5 sentences, has question, vocabulary diversity)
"""

import re
from dataclasses import dataclass
from typing import Optional
from domain.value_objects.enums import ProficiencyLevel


@dataclass
class ValidationResult:
    """Result of response validation."""
    is_valid: bool
    reason: Optional[str] = None  # Reason for failure if not valid


class ResponseValidator:
    """Validates AI responses for quality based on proficiency level."""

    # Validation rules per level
    _VALIDATION_RULES = {
        ProficiencyLevel.A1.value: {
            "min_sentences": 1,
            "max_sentences": 2,
            "require_question": True,
            "min_unique_words": 5,
        },
        ProficiencyLevel.A2.value: {
            "min_sentences": 1,
            "max_sentences": 3,
            "require_question": True,
            "min_unique_words": 8,
        },
        ProficiencyLevel.B1.value: {
            "min_sentences": 2,
            "max_sentences": 4,
            "require_question": True,
            "min_unique_words": 12,
        },
        ProficiencyLevel.B2.value: {
            "min_sentences": 2,
            "max_sentences": 5,
            "require_question": True,
            "min_unique_words": 15,
        },
        ProficiencyLevel.C1.value: {
            "min_sentences": 3,
            "max_sentences": 6,
            "require_question": True,
            "min_unique_words": 20,
        },
        ProficiencyLevel.C2.value: {
            "min_sentences": 3,
            "max_sentences": 7,
            "require_question": True,
            "min_unique_words": 25,
        },
    }

    @classmethod
    def validate(cls, response: str, level: str) -> ValidationResult:
        """
        Validate response against rules for a proficiency level.
        
        Args:
            response: AI response text
            level: Proficiency level
            
        Returns:
            ValidationResult with is_valid and reason
        """
        if not response or not response.strip():
            return ValidationResult(is_valid=False, reason="Response is empty")

        rules = cls._VALIDATION_RULES.get(level)
        if not rules:
            return ValidationResult(is_valid=False, reason=f"Unknown proficiency level: {level}")

        # Check sentence count
        sentences = cls._count_sentences(response)
        if sentences < rules["min_sentences"]:
            return ValidationResult(
                is_valid=False,
                reason=f"Too few sentences: {sentences} (min: {rules['min_sentences']})",
            )
        if sentences > rules["max_sentences"]:
            return ValidationResult(
                is_valid=False,
                reason=f"Too many sentences: {sentences} (max: {rules['max_sentences']})",
            )

        # Check for question
        if rules["require_question"] and not cls._has_question(response):
            return ValidationResult(
                is_valid=False,
                reason="Response must contain a question",
            )

        # Check vocabulary diversity
        unique_words = cls._count_unique_words(response)
        if unique_words < rules["min_unique_words"]:
            return ValidationResult(
                is_valid=False,
                reason=f"Low vocabulary diversity: {unique_words} unique words (min: {rules['min_unique_words']})",
            )

        return ValidationResult(is_valid=True)

    @classmethod
    def _count_sentences(cls, text: str) -> int:
        """Count sentences in text (split by . ! ?)."""
        sentences = re.split(r"[.!?]+", text.strip())
        # Filter out empty strings
        sentences = [s.strip() for s in sentences if s.strip()]
        return len(sentences)

    @classmethod
    def _has_question(cls, text: str) -> bool:
        """Check if text contains a question (ends with ?)."""
        return "?" in text

    @classmethod
    def _count_unique_words(cls, text: str) -> int:
        """Count unique words in text (case-insensitive, excluding common words)."""
        # Extract words (alphanumeric + apostrophe)
        words = re.findall(r"\b[a-z']+\b", text.lower())
        
        # Common English words to exclude (stop words)
        stop_words = {
            "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
            "has", "he", "in", "is", "it", "of", "on", "or", "that", "the",
            "to", "was", "will", "with", "you", "i", "me", "my", "we", "us",
            "this", "these", "those", "what", "which", "who", "when",
            "where", "why", "how", "can", "could", "would", "should", "do",
            "does", "did", "have", "had", "having", "been", "being", "am",
        }
        
        # Filter out stop words and count unique (include words of any length)
        meaningful_words = {w for w in words if w not in stop_words}
        return len(meaningful_words)
