"""Unit tests for OffTopicDetector."""

import pytest
from domain.services.off_topic_detector import (
    OffTopicDetector,
    OffTopicSeverity,
    OffTopicDetectionResult,
    RedirectMessage,
)


class TestOffTopicDetector:
    """Test off-topic detection and redirect."""

    def test_detector_initialization(self):
        """Test OffTopicDetector initialization."""
        detector = OffTopicDetector(enable_detection=True)
        assert detector.enable_detection is True
        assert detector.off_topic_count == 0

    def test_detector_disabled(self):
        """Test OffTopicDetector with detection disabled."""
        detector = OffTopicDetector(enable_detection=False)
        assert detector.enable_detection is False

    def test_detect_empty_message(self):
        """Test detection with empty message."""
        detector = OffTopicDetector()
        result = detector.detect_off_topic("", "Restaurant", "A1")
        
        assert result.is_off_topic is False
        assert result.severity is None

    def test_detect_whitespace_only(self):
        """Test detection with whitespace only."""
        detector = OffTopicDetector()
        result = detector.detect_off_topic("   ", "Restaurant", "A1")
        
        assert result.is_off_topic is False

    def test_detect_on_topic_restaurant(self):
        """Test detection of on-topic restaurant message."""
        detector = OffTopicDetector()
        result = detector.detect_off_topic(
            "I like the restaurant. The food is good.",
            "Restaurant",
            "A1",
        )
        
        assert result.is_off_topic is False

    def test_detect_off_topic_restaurant(self):
        """Test detection of off-topic message for restaurant."""
        detector = OffTopicDetector()
        result = detector.detect_off_topic(
            "I like to play football.",
            "Restaurant",
            "A1",
        )
        
        assert result.is_off_topic is True
        assert result.severity is not None
        assert result.confidence > 0.0

    def test_detect_off_topic_hotel(self):
        """Test detection of off-topic message for hotel."""
        detector = OffTopicDetector()
        result = detector.detect_off_topic(
            "I like to swim.",
            "Hotel",
            "A1",
        )
        
        assert result.is_off_topic is True

    def test_detect_off_topic_airport(self):
        """Test detection of off-topic message for airport."""
        detector = OffTopicDetector()
        result = detector.detect_off_topic(
            "I like to cook.",
            "Airport",
            "B1",
        )
        
        assert result.is_off_topic is True

    def test_should_redirect_on_topic(self):
        """Test redirect decision for on-topic message."""
        detector = OffTopicDetector()
        should_redirect = detector.should_redirect(
            "I like the restaurant.",
            "Restaurant",
            "A1",
        )
        
        assert should_redirect is False

    def test_should_redirect_off_topic(self):
        """Test redirect decision for off-topic message."""
        detector = OffTopicDetector()
        should_redirect = detector.should_redirect(
            "I like to play football.",
            "Restaurant",
            "A1",
        )
        
        assert should_redirect is True

    def test_should_redirect_disabled(self):
        """Test redirect decision when detection disabled."""
        detector = OffTopicDetector(enable_detection=False)
        should_redirect = detector.should_redirect(
            "I like to play football.",
            "Restaurant",
            "A1",
        )
        
        assert should_redirect is False

    def test_generate_redirect_mild(self):
        """Test generating mild redirect."""
        detector = OffTopicDetector()
        redirect = detector.generate_redirect(
            "Restaurant",
            "A1",
            OffTopicSeverity.MILD,
        )
        
        assert redirect is not None
        assert redirect.severity == OffTopicSeverity.MILD
        assert "Restaurant" in redirect.vietnamese
        assert "Restaurant" in redirect.english

    def test_generate_redirect_moderate(self):
        """Test generating moderate redirect."""
        detector = OffTopicDetector()
        redirect = detector.generate_redirect(
            "Hotel",
            "B1",
            OffTopicSeverity.MODERATE,
        )
        
        assert redirect is not None
        assert redirect.severity == OffTopicSeverity.MODERATE
        assert "Hotel" in redirect.vietnamese

    def test_generate_redirect_severe(self):
        """Test generating severe redirect."""
        detector = OffTopicDetector()
        redirect = detector.generate_redirect(
            "Airport",
            "C1",
            OffTopicSeverity.SEVERE,
        )
        
        assert redirect is not None
        assert redirect.severity == OffTopicSeverity.SEVERE
        assert "Airport" in redirect.vietnamese

    def test_generate_redirect_auto_severity_a1(self):
        """Test auto-severity for A1 level."""
        detector = OffTopicDetector()
        redirect = detector.generate_redirect("Restaurant", "A1")
        
        assert redirect is not None
        assert redirect.severity == OffTopicSeverity.MILD

    def test_generate_redirect_auto_severity_b1(self):
        """Test auto-severity for B1 level."""
        detector = OffTopicDetector()
        redirect = detector.generate_redirect("Restaurant", "B1")
        
        assert redirect is not None
        assert redirect.severity == OffTopicSeverity.MODERATE

    def test_generate_redirect_auto_severity_c1(self):
        """Test auto-severity for C1 level."""
        detector = OffTopicDetector()
        redirect = detector.generate_redirect("Restaurant", "C1")
        
        assert redirect is not None
        assert redirect.severity == OffTopicSeverity.SEVERE

    def test_format_redirect_for_display(self):
        """Test formatting redirect for display."""
        detector = OffTopicDetector()
        redirect = detector.generate_redirect("Restaurant", "A1")
        
        formatted = detector.format_redirect_for_display(redirect)
        
        # Should have Vietnamese first, then English
        assert redirect.vietnamese in formatted
        assert redirect.english in formatted
        assert formatted.index(redirect.vietnamese) < formatted.index(redirect.english)

    def test_off_topic_count_increments(self):
        """Test off-topic count increments."""
        detector = OffTopicDetector()
        assert detector.get_off_topic_count() == 0
        
        detector.generate_redirect("Restaurant", "A1")
        assert detector.get_off_topic_count() == 1
        
        detector.generate_redirect("Hotel", "B1")
        assert detector.get_off_topic_count() == 2

    def test_reset_off_topic_count(self):
        """Test resetting off-topic count."""
        detector = OffTopicDetector()
        detector.generate_redirect("Restaurant", "A1")
        detector.generate_redirect("Hotel", "B1")
        assert detector.get_off_topic_count() == 2
        
        detector.reset_off_topic_count()
        assert detector.get_off_topic_count() == 0

    def test_is_detection_enabled(self):
        """Test checking if detection is enabled."""
        detector1 = OffTopicDetector(enable_detection=True)
        assert detector1.is_detection_enabled() is True
        
        detector2 = OffTopicDetector(enable_detection=False)
        assert detector2.is_detection_enabled() is False

    def test_get_off_topic_rate(self):
        """Test getting off-topic rate."""
        detector = OffTopicDetector()
        
        # No messages
        rate = detector.get_off_topic_rate(0)
        assert rate == 0.0
        
        # 2 off-topic out of 10 messages
        detector.off_topic_count = 2
        rate = detector.get_off_topic_rate(10)
        assert rate == 0.2

    def test_off_topic_detection_result_structure(self):
        """Test OffTopicDetectionResult structure."""
        result = OffTopicDetectionResult(
            is_off_topic=True,
            severity=OffTopicSeverity.MODERATE,
            confidence=0.8,
            reason="No keywords found",
        )
        
        assert result.is_off_topic is True
        assert result.severity == OffTopicSeverity.MODERATE
        assert result.confidence == 0.8
        assert result.reason == "No keywords found"

    def test_redirect_message_structure(self):
        """Test RedirectMessage structure."""
        redirect = RedirectMessage(
            vietnamese="Tiếng Việt",
            english="English",
            severity=OffTopicSeverity.MILD,
        )
        
        assert redirect.vietnamese == "Tiếng Việt"
        assert redirect.english == "English"
        assert redirect.severity == OffTopicSeverity.MILD

    def test_off_topic_severity_enum(self):
        """Test OffTopicSeverity enum values."""
        assert OffTopicSeverity.MILD.value == "mild"
        assert OffTopicSeverity.MODERATE.value == "moderate"
        assert OffTopicSeverity.SEVERE.value == "severe"

    def test_scenario_keywords_restaurant(self):
        """Test scenario keywords for restaurant."""
        detector = OffTopicDetector()
        keywords = detector._get_scenario_keywords("Restaurant")
        
        assert "restaurant" in keywords
        assert "food" in keywords
        assert "menu" in keywords
        assert "order" in keywords

    def test_scenario_keywords_hotel(self):
        """Test scenario keywords for hotel."""
        detector = OffTopicDetector()
        keywords = detector._get_scenario_keywords("Hotel")
        
        assert "hotel" in keywords
        assert "room" in keywords
        assert "reservation" in keywords

    def test_scenario_keywords_unknown(self):
        """Test scenario keywords for unknown scenario."""
        detector = OffTopicDetector()
        keywords = detector._get_scenario_keywords("Unknown")
        
        assert "unknown" in keywords

    def test_multiple_redirects_sequence(self):
        """Test generating multiple redirects in sequence."""
        detector = OffTopicDetector()
        
        # First redirect
        redirect1 = detector.generate_redirect("Restaurant", "A1")
        assert redirect1.severity == OffTopicSeverity.MILD
        
        # Second redirect
        redirect2 = detector.generate_redirect("Hotel", "B1")
        assert redirect2.severity == OffTopicSeverity.MODERATE
        
        # Third redirect
        redirect3 = detector.generate_redirect("Airport", "C1")
        assert redirect3.severity == OffTopicSeverity.SEVERE
        
        # Total redirects should be 3
        assert detector.get_off_topic_count() == 3

    def test_vietnamese_first_in_display(self):
        """Test Vietnamese appears first in display format."""
        detector = OffTopicDetector()
        redirect = detector.generate_redirect("Restaurant", "A1")
        formatted = detector.format_redirect_for_display(redirect)
        
        # Find positions
        viet_pos = formatted.find(redirect.vietnamese)
        eng_pos = formatted.find(redirect.english)
        
        # Vietnamese should come first
        assert viet_pos < eng_pos
        assert viet_pos == 0  # Should be at the beginning

    def test_off_topic_with_partial_keywords(self):
        """Test off-topic detection with partial keywords."""
        detector = OffTopicDetector()
        
        # Message with some scenario keywords
        result = detector.detect_off_topic(
            "I like restaurant and football.",
            "Restaurant",
            "A1",
        )
        
        # Should be on-topic because it has "restaurant"
        assert result.is_off_topic is False

    def test_off_topic_case_insensitive(self):
        """Test off-topic detection is case-insensitive."""
        detector = OffTopicDetector()
        
        # Uppercase scenario keyword
        result = detector.detect_off_topic(
            "I like the RESTAURANT.",
            "Restaurant",
            "A1",
        )
        
        assert result.is_off_topic is False

    def test_redirect_message_format(self):
        """Test redirect message format."""
        detector = OffTopicDetector()
        redirect = detector.generate_redirect("Restaurant", "A1")
        
        # Should have both Vietnamese and English
        assert isinstance(redirect.vietnamese, str)
        assert isinstance(redirect.english, str)
        assert len(redirect.vietnamese) > 0
        assert len(redirect.english) > 0

    def test_off_topic_rate_calculation(self):
        """Test off-topic rate calculation."""
        detector = OffTopicDetector()
        
        # 3 off-topic out of 10 messages
        detector.off_topic_count = 3
        rate = detector.get_off_topic_rate(10)
        
        assert rate == 0.3
        assert 0.0 <= rate <= 1.0

    def test_off_topic_rate_all_off_topic(self):
        """Test off-topic rate when all messages are off-topic."""
        detector = OffTopicDetector()
        
        detector.off_topic_count = 5
        rate = detector.get_off_topic_rate(5)
        
        assert rate == 1.0

    def test_off_topic_rate_none_off_topic(self):
        """Test off-topic rate when no messages are off-topic."""
        detector = OffTopicDetector()
        
        detector.off_topic_count = 0
        rate = detector.get_off_topic_rate(10)
        
        assert rate == 0.0
