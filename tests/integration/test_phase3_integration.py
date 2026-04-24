"""Integration tests for Phase 3: Scaffolding & Guardrails."""

import pytest
from domain.services.scaffolding_system import ScaffoldingSystem, HintLevel
from domain.services.vietnamese_detector import VietnameseDetector
from domain.services.off_topic_detector import OffTopicDetector, OffTopicSeverity
from domain.services.bedrock_guardrails import BedrockGuardrails, GuardrailAction
from domain.services.metrics_logger import MetricsLogger


class TestPhase3Integration:
    """Integration tests for Phase 3 components."""

    def test_scaffolding_with_vietnamese_detection_a1(self):
        """Test scaffolding + Vietnamese detection for A1 learner."""
        scaffolding = ScaffoldingSystem()
        vietnamese_detector = VietnameseDetector()
        
        # A1 learner writes in Vietnamese
        message = "Xin chào, tôi là Việt Nam"
        
        # Detect Vietnamese
        detection_result = vietnamese_detector.detect_language(message)
        assert detection_result.is_vietnamese is True
        
        # Generate redirect
        redirect = vietnamese_detector.get_redirect_message()
        assert "tiếng Anh" in redirect["vietnamese"]
        
        # After redirect, provide hint
        hint = scaffolding.generate_hint("A1", 10)
        assert hint is not None
        assert hint.hint_level == HintLevel.GENTLE_PROMPT

    def test_scaffolding_with_vietnamese_detection_a2(self):
        """Test scaffolding + Vietnamese detection for A2 learner."""
        scaffolding = ScaffoldingSystem()
        vietnamese_detector = VietnameseDetector()
        
        # A2 learner writes in English (on-topic)
        message = "I like the restaurant"
        
        # Detect language
        detection_result = vietnamese_detector.detect_language(message)
        assert detection_result.is_vietnamese is False
        
        # No redirect needed, provide hint at 20s
        hint = scaffolding.generate_hint("A2", 20)
        assert hint is not None
        assert hint.hint_level == HintLevel.VOCABULARY_HINT

    def test_off_topic_with_guardrails_restaurant(self):
        """Test off-topic detection + guardrails for restaurant scenario."""
        off_topic_detector = OffTopicDetector()
        guardrails = BedrockGuardrails()
        
        # Learner writes off-topic message
        message = "I like to play football"
        
        # Detect off-topic
        should_redirect = off_topic_detector.should_redirect(
            message,
            "Restaurant",
            "B1",
        )
        assert should_redirect is True
        
        # Generate redirect
        redirect = off_topic_detector.generate_redirect("Restaurant", "B1")
        assert redirect is not None
        assert "Restaurant" in redirect.english
        
        # Check guardrails (should be safe)
        guardrail_result = guardrails.check_content(message)
        assert guardrail_result.is_safe is True

    def test_off_topic_with_guardrails_blocked_content(self):
        """Test off-topic detection + guardrails for blocked content."""
        off_topic_detector = OffTopicDetector()
        guardrails = BedrockGuardrails()
        
        # Learner writes inappropriate content
        message = "I like violence and illegal activities"
        
        # Check guardrails (should be blocked)
        guardrail_result = guardrails.check_content(message)
        assert guardrail_result.is_safe is False
        assert guardrail_result.action in [GuardrailAction.BLOCK, GuardrailAction.FILTER]

    def test_end_to_end_a1_learner_flow(self):
        """Test end-to-end flow for A1 learner."""
        scaffolding = ScaffoldingSystem()
        vietnamese_detector = VietnameseDetector()
        off_topic_detector = OffTopicDetector()
        guardrails = BedrockGuardrails()
        metrics_logger = MetricsLogger()
        
        # Scenario: A1 learner in restaurant scenario
        level = "A1"
        scenario = "Restaurant"
        
        # Turn 1: Learner writes in Vietnamese
        message1 = "Xin chào"
        
        # Check language
        lang_result = vietnamese_detector.detect_language(message1)
        if lang_result.is_vietnamese:
            # Redirect to English
            redirect = vietnamese_detector.get_redirect_message()
            assert "tiếng Anh" in redirect["vietnamese"]
        
        # Turn 2: Learner writes in English (on-topic)
        message2 = "I like the restaurant"
        
        # Check off-topic
        is_off_topic = off_topic_detector.should_redirect(message2, scenario, level)
        assert is_off_topic is False
        
        # Check guardrails
        guardrail_result = guardrails.check_content(message2)
        assert guardrail_result.is_safe is True
        
        # Provide hint at 10s
        hint = scaffolding.generate_hint(level, 10)
        assert hint is not None
        
        # Log metrics
        metrics = metrics_logger.create_metrics(
            ttft_ms=100.0,
            total_latency_ms=500.0,
            input_tokens=50,
            output_tokens=100,
            model_used="amazon.nova-micro-v1:0",
            proficiency_level=level,
        )
        assert metrics.proficiency_level == level

    def test_end_to_end_b1_learner_flow(self):
        """Test end-to-end flow for B1 learner."""
        scaffolding = ScaffoldingSystem()
        vietnamese_detector = VietnameseDetector()
        off_topic_detector = OffTopicDetector()
        guardrails = BedrockGuardrails()
        
        # Scenario: B1 learner in hotel scenario
        level = "B1"
        scenario = "Hotel"
        
        # Turn 1: Learner writes off-topic
        message1 = "I like to play video games"
        
        # Check off-topic
        is_off_topic = off_topic_detector.should_redirect(message1, scenario, level)
        assert is_off_topic is True
        
        # Generate redirect (should be moderate for B1)
        redirect = off_topic_detector.generate_redirect(scenario, level)
        assert redirect.severity == OffTopicSeverity.MODERATE
        
        # Turn 2: Learner writes on-topic
        message2 = "I want to check in to the hotel"
        
        # Check language
        lang_result = vietnamese_detector.detect_language(message2)
        assert lang_result.is_vietnamese is False
        
        # Check off-topic
        is_off_topic = off_topic_detector.should_redirect(message2, scenario, level)
        assert is_off_topic is False
        
        # Check guardrails
        guardrail_result = guardrails.check_content(message2)
        assert guardrail_result.is_safe is True
        
        # B1 should not receive hints (only A1-A2)
        hint = scaffolding.generate_hint(level, 10)
        assert hint is None

    def test_end_to_end_c1_learner_flow(self):
        """Test end-to-end flow for C1 learner."""
        off_topic_detector = OffTopicDetector()
        guardrails = BedrockGuardrails()
        
        # Scenario: C1 learner in airport scenario
        level = "C1"
        scenario = "Airport"
        
        # Turn 1: Learner writes on-topic
        message1 = "I need to check my flight status"
        
        # Check off-topic
        is_off_topic = off_topic_detector.should_redirect(message1, scenario, level)
        assert is_off_topic is False
        
        # Check guardrails
        guardrail_result = guardrails.check_content(message1)
        assert guardrail_result.is_safe is True
        
        # Turn 2: Learner writes inappropriate content
        message2 = "I like violence"
        
        # Check guardrails (should be blocked)
        guardrail_result = guardrails.check_content(message2)
        assert guardrail_result.is_safe is False

    def test_scaffolding_hint_sequence(self):
        """Test scaffolding hint sequence (10s, 20s, 30s)."""
        scaffolding = ScaffoldingSystem()
        
        # First hint at 10s
        hint1 = scaffolding.generate_hint("A1", 10)
        assert hint1.hint_level == HintLevel.GENTLE_PROMPT
        assert scaffolding.get_hint_count() == 1
        
        # Second hint at 20s
        hint2 = scaffolding.generate_hint("A1", 20)
        assert hint2.hint_level == HintLevel.VOCABULARY_HINT
        assert scaffolding.get_hint_count() == 2
        
        # Third hint at 30s
        hint3 = scaffolding.generate_hint("A1", 30)
        assert hint3.hint_level == HintLevel.SENTENCE_STARTER
        assert scaffolding.get_hint_count() == 3

    def test_vietnamese_detection_with_guardrails(self):
        """Test Vietnamese detection + guardrails interaction."""
        vietnamese_detector = VietnameseDetector()
        guardrails = BedrockGuardrails()
        
        # Vietnamese message with inappropriate content (English keywords for detection)
        message = "Tôi thích violence"  # Mix Vietnamese + English keyword
        
        # Detect Vietnamese
        lang_result = vietnamese_detector.detect_language(message)
        assert lang_result.is_vietnamese is True
        
        # Check guardrails (should detect violation due to "violence" keyword)
        guardrail_result = guardrails.check_content(message)
        assert guardrail_result.is_safe is False

    def test_off_topic_severity_per_level(self):
        """Test off-topic severity varies by proficiency level."""
        off_topic_detector = OffTopicDetector()
        
        # A1: mild redirect
        redirect_a1 = off_topic_detector.generate_redirect("Restaurant", "A1")
        assert redirect_a1.severity == OffTopicSeverity.MILD
        
        # B1: moderate redirect
        redirect_b1 = off_topic_detector.generate_redirect("Restaurant", "B1")
        assert redirect_b1.severity == OffTopicSeverity.MODERATE
        
        # C1: severe redirect
        redirect_c1 = off_topic_detector.generate_redirect("Restaurant", "C1")
        assert redirect_c1.severity == OffTopicSeverity.SEVERE

    def test_metrics_collection_from_all_components(self):
        """Test metrics collection from all Phase 3 components."""
        scaffolding = ScaffoldingSystem()
        vietnamese_detector = VietnameseDetector()
        off_topic_detector = OffTopicDetector()
        guardrails = BedrockGuardrails()
        metrics_logger = MetricsLogger()
        
        # Simulate conversation
        scaffolding.generate_hint("A1", 10)
        vietnamese_detector.detect_language("Hello")
        off_topic_detector.should_redirect("I like restaurant", "Restaurant", "A1")
        guardrails.check_content("I like to learn")
        
        # Collect metrics
        metrics = metrics_logger.create_metrics(
            ttft_ms=120.0,
            total_latency_ms=600.0,
            input_tokens=60,
            output_tokens=120,
            model_used="amazon.nova-micro-v1:0",
            proficiency_level="A1",
        )
        
        # Verify metrics
        assert metrics.ttft_ms == 120.0
        assert metrics.total_latency_ms == 600.0
        assert metrics.input_tokens == 60
        assert metrics.output_tokens == 120
        
        # Verify component states
        assert scaffolding.get_hint_count() == 1
        assert off_topic_detector.get_off_topic_count() == 0
        assert guardrails.get_violation_count() == 0

    def test_multiple_turns_conversation(self):
        """Test multiple turns in a conversation."""
        scaffolding = ScaffoldingSystem()
        off_topic_detector = OffTopicDetector()
        guardrails = BedrockGuardrails()
        
        # Turn 1: On-topic
        msg1 = "I like the restaurant"
        assert off_topic_detector.should_redirect(msg1, "Restaurant", "A1") is False
        assert guardrails.check_content(msg1).is_safe is True
        
        # Turn 2: Off-topic
        msg2 = "I like to play football"
        assert off_topic_detector.should_redirect(msg2, "Restaurant", "A1") is True
        # Generate redirect to increment count
        redirect = off_topic_detector.generate_redirect("Restaurant", "A1")
        assert redirect is not None
        assert guardrails.check_content(msg2).is_safe is True
        
        # Turn 3: On-topic again
        msg3 = "The food is delicious"
        assert off_topic_detector.should_redirect(msg3, "Restaurant", "A1") is False
        assert guardrails.check_content(msg3).is_safe is True
        
        # Verify off-topic count (incremented when generate_redirect was called)
        assert off_topic_detector.get_off_topic_count() == 1

    def test_guardrails_with_custom_denied_topic(self):
        """Test guardrails with custom denied topic."""
        guardrails = BedrockGuardrails()
        
        # Add custom denied topic
        guardrails.add_denied_topic("gaming")
        
        # Check content with custom topic
        result = guardrails.check_content("I like gaming")
        assert result.is_safe is False
        
        # Remove custom topic
        guardrails.remove_denied_topic("gaming")
        
        # Check content again (should be safe now)
        result = guardrails.check_content("I like gaming")
        assert result.is_safe is True
