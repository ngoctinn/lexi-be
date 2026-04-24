"""Unit tests for VietnameseDetector."""

import pytest
from domain.services.vietnamese_detector import (
    VietnameseDetector,
    LanguageDetectionResult,
)


class TestVietnameseDetector:
    """Test Vietnamese language detection."""

    def test_detector_initialization(self):
        """Test VietnameseDetector initialization."""
        detector = VietnameseDetector()
        assert detector.comprehend_client is None

    def test_detector_with_client(self):
        """Test VietnameseDetector with Comprehend client."""
        mock_client = object()
        detector = VietnameseDetector(comprehend_client=mock_client)
        assert detector.comprehend_client is mock_client

    def test_detect_empty_text(self):
        """Test detection with empty text."""
        detector = VietnameseDetector()
        result = detector.detect_language("")
        
        assert result.language_code == "unknown"
        assert result.is_vietnamese is False
        assert result.confidence == 0.0

    def test_detect_whitespace_only(self):
        """Test detection with whitespace only."""
        detector = VietnameseDetector()
        result = detector.detect_language("   ")
        
        assert result.language_code == "unknown"
        assert result.is_vietnamese is False

    def test_detect_english_text(self):
        """Test detection of English text."""
        detector = VietnameseDetector()
        result = detector.detect_language("Hello, how are you?")
        
        assert result.is_vietnamese is False
        assert result.language_code == "en"
        assert result.language_name == "English"

    def test_detect_vietnamese_text(self):
        """Test detection of Vietnamese text."""
        detector = VietnameseDetector()
        result = detector.detect_language("Xin chào, bạn khỏe không?")
        
        assert result.is_vietnamese is True
        assert result.language_code == "vi"
        assert result.language_name == "Vietnamese"
        assert result.confidence > 0.1

    def test_detect_vietnamese_with_diacritics(self):
        """Test detection of Vietnamese with diacritics."""
        detector = VietnameseDetector()
        result = detector.detect_language("Tôi yêu tiếng Anh")
        
        assert result.is_vietnamese is True
        assert result.language_code == "vi"

    def test_detect_mixed_vietnamese_english(self):
        """Test detection of mixed Vietnamese and English."""
        detector = VietnameseDetector()
        result = detector.detect_language("Hello, tôi là Việt Nam")
        
        # Should detect as Vietnamese due to Vietnamese characters
        assert result.is_vietnamese is True

    def test_should_redirect_to_english_vietnamese(self):
        """Test redirect decision for Vietnamese text."""
        detector = VietnameseDetector()
        # Use text with more Vietnamese characters and lower threshold
        should_redirect = detector.should_redirect_to_english(
            "Xin chào, tôi là Việt Nam",
            confidence_threshold=0.2,
        )
        
        assert should_redirect is True

    def test_should_redirect_to_english_english(self):
        """Test redirect decision for English text."""
        detector = VietnameseDetector()
        should_redirect = detector.should_redirect_to_english("Hello")
        
        assert should_redirect is False

    def test_should_redirect_with_threshold(self):
        """Test redirect decision with custom threshold."""
        detector = VietnameseDetector()
        
        # High threshold - less likely to redirect
        should_redirect = detector.should_redirect_to_english(
            "Hello world",
            confidence_threshold=0.9,
        )
        assert should_redirect is False

    def test_get_redirect_message(self):
        """Test getting redirect message."""
        detector = VietnameseDetector()
        message = detector.get_redirect_message()
        
        assert "vietnamese" in message
        assert "english" in message
        assert "tiếng Anh" in message["vietnamese"]
        assert "English" in message["english"]

    def test_get_follow_up_prompt_a1(self):
        """Test getting follow-up prompt for A1."""
        detector = VietnameseDetector()
        prompt = detector.get_follow_up_prompt("A1")
        
        assert "vietnamese" in prompt
        assert "english" in prompt
        assert len(prompt["vietnamese"]) > 0
        assert len(prompt["english"]) > 0

    def test_get_follow_up_prompt_a2(self):
        """Test getting follow-up prompt for A2."""
        detector = VietnameseDetector()
        prompt = detector.get_follow_up_prompt("A2")
        
        assert "vietnamese" in prompt
        assert "english" in prompt

    def test_get_follow_up_prompt_b1(self):
        """Test getting follow-up prompt for B1."""
        detector = VietnameseDetector()
        prompt = detector.get_follow_up_prompt("B1")
        
        assert "vietnamese" in prompt
        assert "english" in prompt

    def test_get_follow_up_prompt_c1(self):
        """Test getting follow-up prompt for C1."""
        detector = VietnameseDetector()
        prompt = detector.get_follow_up_prompt("C1")
        
        assert "vietnamese" in prompt
        assert "english" in prompt

    def test_get_follow_up_prompt_invalid_level(self):
        """Test getting follow-up prompt for invalid level."""
        detector = VietnameseDetector()
        prompt = detector.get_follow_up_prompt("INVALID")
        
        # Should return A1 as default
        assert "vietnamese" in prompt
        assert "english" in prompt

    def test_get_detection_confidence_vietnamese(self):
        """Test getting detection confidence for Vietnamese."""
        detector = VietnameseDetector()
        confidence = detector.get_detection_confidence("Xin chào")
        
        assert confidence > 0.1
        assert confidence <= 1.0

    def test_get_detection_confidence_english(self):
        """Test getting detection confidence for English."""
        detector = VietnameseDetector()
        confidence = detector.get_detection_confidence("Hello")
        
        assert confidence == 0.0

    def test_language_detection_result_structure(self):
        """Test LanguageDetectionResult structure."""
        result = LanguageDetectionResult(
            language_code="vi",
            language_name="Vietnamese",
            confidence=0.95,
            is_vietnamese=True,
        )
        
        assert result.language_code == "vi"
        assert result.language_name == "Vietnamese"
        assert result.confidence == 0.95
        assert result.is_vietnamese is True

    def test_vietnamese_codes(self):
        """Test Vietnamese language codes."""
        detector = VietnameseDetector()
        assert "vi" in detector.VIETNAMESE_CODES
        assert "vie" in detector.VIETNAMESE_CODES

    def test_english_codes(self):
        """Test English language codes."""
        detector = VietnameseDetector()
        assert "en" in detector.ENGLISH_CODES
        assert "eng" in detector.ENGLISH_CODES

    def test_get_language_name_vietnamese(self):
        """Test getting language name for Vietnamese."""
        detector = VietnameseDetector()
        name = detector._get_language_name("vi")
        assert name == "Vietnamese"

    def test_get_language_name_english(self):
        """Test getting language name for English."""
        detector = VietnameseDetector()
        name = detector._get_language_name("en")
        assert name == "English"

    def test_get_language_name_unknown(self):
        """Test getting language name for unknown code."""
        detector = VietnameseDetector()
        name = detector._get_language_name("unknown")
        assert name == "Unknown"

    def test_vietnamese_character_detection(self):
        """Test Vietnamese character detection."""
        detector = VietnameseDetector()
        
        # Text with Vietnamese diacritics
        result = detector.detect_language("Tiếng Việt")
        assert result.is_vietnamese is True

    def test_vietnamese_character_detection_lowercase(self):
        """Test Vietnamese character detection with lowercase."""
        detector = VietnameseDetector()
        
        result = detector.detect_language("TIẾNG VIỆT")
        assert result.is_vietnamese is True

    def test_confidence_calculation(self):
        """Test confidence calculation."""
        detector = VietnameseDetector()
        
        # Pure Vietnamese with many diacritics
        result1 = detector.detect_language("Tiếng Việt là ngôn ngữ của tôi")
        assert result1.confidence > 0.1
        
        # Pure English
        result2 = detector.detect_language("Hello")
        assert result2.confidence < 0.2

    def test_mixed_text_detection(self):
        """Test detection of mixed Vietnamese and English."""
        detector = VietnameseDetector()
        
        # More Vietnamese than English
        result = detector.detect_language("Tôi là Việt Nam, I am Vietnamese")
        assert result.is_vietnamese is True

    def test_numbers_and_punctuation(self):
        """Test detection with numbers and punctuation."""
        detector = VietnameseDetector()
        
        result = detector.detect_language("123 !@# Xin chào")
        assert result.is_vietnamese is True

    def test_single_vietnamese_word(self):
        """Test detection with single Vietnamese word."""
        detector = VietnameseDetector()
        
        result = detector.detect_language("Xin")
        # Single word might not have enough Vietnamese characters
        # but should still be detected if it has Vietnamese diacritics
        assert result.language_code in ["vi", "en"]

    def test_redirect_message_format(self):
        """Test redirect message format."""
        detector = VietnameseDetector()
        message = detector.get_redirect_message()
        
        # Should have both Vietnamese and English
        assert isinstance(message, dict)
        assert len(message) == 2
        assert all(isinstance(v, str) for v in message.values())

    def test_follow_up_prompt_format(self):
        """Test follow-up prompt format."""
        detector = VietnameseDetector()
        prompt = detector.get_follow_up_prompt("A1")
        
        # Should have both Vietnamese and English
        assert isinstance(prompt, dict)
        assert len(prompt) == 2
        assert all(isinstance(v, str) for v in prompt.values())
