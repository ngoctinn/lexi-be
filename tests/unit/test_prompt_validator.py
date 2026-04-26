"""Unit tests for prompt validator."""

import pytest
from domain.services.prompt_validator import (
    has_vietnamese_text,
    validate_example_language,
    validate_conversation_analyzer_response,
    validate_structured_hint_response,
)


class TestVietnameseDetection:
    """Test Vietnamese text detection."""

    def test_detect_vietnamese_text(self):
        """Test detection of Vietnamese text."""
        assert has_vietnamese_text("Xin chào") is True
        assert has_vietnamese_text("Tôi là học viên") is True
        assert has_vietnamese_text("Đây là tiếng Việt") is True

    def test_no_vietnamese_text(self):
        """Test English text is not detected as Vietnamese."""
        assert has_vietnamese_text("Hello world") is False
        assert has_vietnamese_text("I am a student") is False
        assert has_vietnamese_text("This is English") is False

    def test_mixed_text(self):
        """Test mixed English and Vietnamese."""
        assert has_vietnamese_text("Hello xin chào") is True
        assert has_vietnamese_text("I am tôi") is True


class TestExampleLanguageValidation:
    """Test example language validation."""

    def test_valid_english_example(self):
        """Test valid English examples."""
        is_valid, error = validate_example_language("I went to school")
        assert is_valid is True
        assert error == ""

    def test_valid_english_with_punctuation(self):
        """Test English with punctuation."""
        is_valid, error = validate_example_language("I went to school yesterday.")
        assert is_valid is True

    def test_invalid_vietnamese_example(self):
        """Test Vietnamese example is rejected."""
        is_valid, error = validate_example_language("Tôi đi học")
        assert is_valid is False
        assert "Vietnamese" in error

    def test_empty_example(self):
        """Test empty example is valid."""
        is_valid, error = validate_example_language("")
        assert is_valid is True


class TestConversationAnalyzerValidation:
    """Test conversation analyzer response validation."""

    def test_valid_response(self):
        """Test valid response structure."""
        response = {
            "mistakes_vi": ["Bạn nhầm lẫn ở ~~go~~ nên sửa thành **went**\n\nVì..."],
            "mistakes_en": ["You mixed up ~~go~~ should be **went**\n\nBecause..."],
            "improvements_vi": ["Bạn có thể nói **I went to school**\n\nĐể..."],
            "improvements_en": ["You could say **I went to school**\n\nTo..."],
        }
        is_valid, errors = validate_conversation_analyzer_response(response)
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_field(self):
        """Test missing required field."""
        response = {
            "mistakes_vi": [],
            "mistakes_en": [],
            "improvements_vi": [],
        }
        is_valid, errors = validate_conversation_analyzer_response(response)
        assert is_valid is False
        assert any("improvements_en" in error for error in errors)

    def test_vietnamese_in_english_example(self):
        """Test Vietnamese text in English example field."""
        response = {
            "mistakes_vi": ["Bạn nhầm lẫn ở ~~đi~~ nên sửa thành **đã đi**\n\nVì..."],
            "mistakes_en": ["You mixed up ~~go~~ should be **went**\n\nBecause..."],
            "improvements_vi": [],
            "improvements_en": [],
        }
        is_valid, errors = validate_conversation_analyzer_response(response)
        # Should detect Vietnamese in the example
        assert is_valid is False or len(errors) > 0


class TestStructuredHintValidation:
    """Test structured hint response validation."""

    def test_valid_hint_response(self):
        """Test valid hint response."""
        response = {
            "level": "A1",
            "type": "hint",
            "markdown_vi": "Sarah đang hỏi...\n- **I wake up at 6 AM**\n\n💡 Dùng **simple present tense**",
            "markdown_en": "Sarah is asking...\n- **I wake up at 6 AM**\n\n💡 Use **simple present tense**",
        }
        is_valid, errors = validate_structured_hint_response(response)
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_field(self):
        """Test missing required field."""
        response = {
            "level": "A1",
            "type": "hint",
            "markdown_vi": "...",
        }
        is_valid, errors = validate_structured_hint_response(response)
        assert is_valid is False
        assert any("markdown_en" in error for error in errors)

    def test_vietnamese_in_example(self):
        """Test Vietnamese text in example."""
        response = {
            "level": "A1",
            "type": "hint",
            "markdown_vi": "Sarah đang hỏi...\n- **Tôi thức dậy lúc 6 giờ sáng**\n\n💡 Dùng **simple present tense**",
            "markdown_en": "Sarah is asking...\n- **I wake up at 6 AM**\n\n💡 Use **simple present tense**",
        }
        is_valid, errors = validate_structured_hint_response(response)
        # Should detect Vietnamese in the example
        assert is_valid is False or len(errors) > 0
