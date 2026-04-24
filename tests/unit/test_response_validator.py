"""Unit tests for ResponseValidator."""

import pytest
from domain.services.response_validator import ResponseValidator, ValidationResult
from domain.value_objects.enums import ProficiencyLevel


class TestResponseValidator:
    """Test ResponseValidator validation logic."""

    def test_validate_empty_response(self):
        """Test empty response fails validation."""
        result = ResponseValidator.validate("", ProficiencyLevel.A1.value)
        assert result.is_valid is False
        assert "empty" in result.reason.lower()

    def test_validate_whitespace_only(self):
        """Test whitespace-only response fails validation."""
        result = ResponseValidator.validate("   ", ProficiencyLevel.A1.value)
        assert result.is_valid is False

    def test_validate_invalid_level(self):
        """Test invalid proficiency level raises error."""
        result = ResponseValidator.validate("Hello?", "INVALID")
        assert result.is_valid is False
        assert "Unknown proficiency level" in result.reason

    def test_validate_a1_valid(self):
        """Test valid A1 response."""
        response = "Good! Can you say more about this topic?"
        result = ResponseValidator.validate(response, ProficiencyLevel.A1.value)
        assert result.is_valid is True

    def test_validate_a1_too_many_sentences(self):
        """Test A1 response with too many sentences."""
        response = "Hello. How are you? I am fine. Thank you."
        result = ResponseValidator.validate(response, ProficiencyLevel.A1.value)
        assert result.is_valid is False
        assert "Too many sentences" in result.reason

    def test_validate_a1_missing_question(self):
        """Test A1 response without question."""
        response = "That is good."
        result = ResponseValidator.validate(response, ProficiencyLevel.A1.value)
        assert result.is_valid is False
        assert "must contain a question" in result.reason

    def test_validate_a1_low_vocabulary(self):
        """Test A1 response with low vocabulary diversity."""
        response = "Good good good good good?"
        result = ResponseValidator.validate(response, ProficiencyLevel.A1.value)
        assert result.is_valid is False
        assert "vocabulary diversity" in result.reason.lower()

    def test_validate_a2_valid(self):
        """Test valid A2 response."""
        response = "That sounds interesting. Can you tell me more about your experience and background?"
        result = ResponseValidator.validate(response, ProficiencyLevel.A2.value)
        assert result.is_valid is True

    def test_validate_b1_valid(self):
        """Test valid B1 response."""
        response = "That's a great point. Could you elaborate on how this connects to your daily life? I'd like to understand better."
        result = ResponseValidator.validate(response, ProficiencyLevel.B1.value)
        assert result.is_valid is True

    def test_validate_b1_too_few_sentences(self):
        """Test B1 response with too few sentences."""
        response = "That's good?"
        result = ResponseValidator.validate(response, ProficiencyLevel.B1.value)
        assert result.is_valid is False
        assert "Too few sentences" in result.reason

    def test_validate_b2_valid(self):
        """Test valid B2 response."""
        response = "Excellent observation. Your perspective demonstrates sophisticated thinking about this topic. How do you reconcile this with alternative viewpoints? What evidence supports your conclusion?"
        result = ResponseValidator.validate(response, ProficiencyLevel.B2.value)
        assert result.is_valid is True

    def test_validate_c1_valid(self):
        """Test valid C1 response."""
        response = "Your analysis demonstrates nuanced understanding of the subject matter. The interconnections you've identified are particularly insightful. Could you elaborate on the theoretical framework underlying your argument? What empirical evidence substantiates your position?"
        result = ResponseValidator.validate(response, ProficiencyLevel.C1.value)
        assert result.is_valid is True

    def test_validate_c2_valid(self):
        """Test valid C2 response."""
        response = "Your articulation of this complex phenomenon reveals sophisticated comprehension of the underlying mechanisms. The epistemological implications you've delineated warrant further examination. How do you reconcile the apparent contradictions between these theoretical frameworks? What methodological approaches would you employ to validate your hypothesis?"
        result = ResponseValidator.validate(response, ProficiencyLevel.C2.value)
        assert result.is_valid is True

    def test_validate_c2_too_few_sentences(self):
        """Test C2 response with too few sentences."""
        response = "Good point?"
        result = ResponseValidator.validate(response, ProficiencyLevel.C2.value)
        assert result.is_valid is False
        assert "Too few sentences" in result.reason

    def test_count_sentences(self):
        """Test sentence counting."""
        assert ResponseValidator._count_sentences("Hello. World.") == 2
        assert ResponseValidator._count_sentences("Hello! World?") == 2
        assert ResponseValidator._count_sentences("Hello") == 1
        assert ResponseValidator._count_sentences("Hello. World. How are you?") == 3
        assert ResponseValidator._count_sentences("") == 0

    def test_has_question(self):
        """Test question detection."""
        assert ResponseValidator._has_question("Hello?") is True
        assert ResponseValidator._has_question("Hello! How are you?") is True
        assert ResponseValidator._has_question("Hello.") is False
        assert ResponseValidator._has_question("Hello") is False

    def test_count_unique_words(self):
        """Test unique word counting (excluding stop words)."""
        # "good" and "answer" are meaningful
        assert ResponseValidator._count_unique_words("good answer") == 2
        # "hello", "world" are meaningful (how, are, you are stop words)
        assert ResponseValidator._count_unique_words("hello world how are you") == 2
        # Single word repeated
        assert ResponseValidator._count_unique_words("good good good") == 1
        # Empty
        assert ResponseValidator._count_unique_words("") == 0

    def test_validation_result_success(self):
        """Test ValidationResult for success."""
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        assert result.reason is None

    def test_validation_result_failure(self):
        """Test ValidationResult for failure."""
        result = ValidationResult(is_valid=False, reason="Test failure")
        assert result.is_valid is False
        assert result.reason == "Test failure"
