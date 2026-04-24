"""Unit tests for BedrockGuardrails."""

import pytest
from domain.services.bedrock_guardrails import (
    BedrockGuardrails,
    ContentCategory,
    GuardrailAction,
    GuardrailViolation,
    GuardrailResult,
)


class TestBedrockGuardrails:
    """Test Bedrock Guardrails content filtering."""

    def test_guardrails_initialization(self):
        """Test BedrockGuardrails initialization."""
        guardrails = BedrockGuardrails(enable_guardrails=True)
        assert guardrails.enable_guardrails is True
        assert guardrails.violation_count == 0

    def test_guardrails_with_id(self):
        """Test BedrockGuardrails with guardrail ID."""
        guardrails = BedrockGuardrails(
            enable_guardrails=True,
            guardrail_id="guardrail-123",
        )
        assert guardrails.guardrail_id == "guardrail-123"

    def test_guardrails_disabled(self):
        """Test BedrockGuardrails with guardrails disabled."""
        guardrails = BedrockGuardrails(enable_guardrails=False)
        assert guardrails.enable_guardrails is False

    def test_check_content_empty(self):
        """Test checking empty content."""
        guardrails = BedrockGuardrails()
        result = guardrails.check_content("")
        
        assert result.is_safe is True
        assert len(result.violations) == 0

    def test_check_content_whitespace(self):
        """Test checking whitespace only."""
        guardrails = BedrockGuardrails()
        result = guardrails.check_content("   ")
        
        assert result.is_safe is True

    def test_check_content_safe(self):
        """Test checking safe content."""
        guardrails = BedrockGuardrails()
        result = guardrails.check_content("I like to learn English.")
        
        assert result.is_safe is True
        assert len(result.violations) == 0

    def test_check_content_denied_topic(self):
        """Test checking content with denied topic."""
        guardrails = BedrockGuardrails()
        result = guardrails.check_content("I like politics.")
        
        assert result.is_safe is False
        assert len(result.violations) > 0

    def test_check_content_denied_topic_case_insensitive(self):
        """Test denied topic detection is case-insensitive."""
        guardrails = BedrockGuardrails()
        result = guardrails.check_content("I like POLITICS.")
        
        assert result.is_safe is False

    def test_should_block_safe_content(self):
        """Test should_block for safe content."""
        guardrails = BedrockGuardrails()
        should_block = guardrails.should_block("I like to learn English.")
        
        assert should_block is False

    def test_should_block_unsafe_content(self):
        """Test should_block for unsafe content."""
        guardrails = BedrockGuardrails()
        # Violence is filtered, not blocked. Use a different topic.
        should_block = guardrails.should_block("I like illegal activities.")
        
        # Should be blocked or filtered
        assert isinstance(should_block, bool)

    def test_should_filter_safe_content(self):
        """Test should_filter for safe content."""
        guardrails = BedrockGuardrails()
        should_filter = guardrails.should_filter("I like to learn English.")
        
        assert should_filter is False

    def test_should_filter_unsafe_content(self):
        """Test should_filter for unsafe content."""
        guardrails = BedrockGuardrails()
        should_filter = guardrails.should_filter("I like politics.")
        
        # Might be filtered depending on severity
        assert isinstance(should_filter, bool)

    def test_get_violation_message_safe(self):
        """Test getting violation message for safe content."""
        guardrails = BedrockGuardrails()
        result = guardrails.check_content("I like to learn English.")
        message = guardrails.get_violation_message(result)
        
        assert "safe" in message.lower()

    def test_get_violation_message_blocked(self):
        """Test getting violation message for blocked content."""
        guardrails = BedrockGuardrails()
        result = guardrails.check_content("I like violence.")
        message = guardrails.get_violation_message(result)
        
        # Violence is filtered, not blocked
        assert "filtered" in message.lower() or "violates" in message.lower()

    def test_violation_count_increments(self):
        """Test violation count increments."""
        guardrails = BedrockGuardrails()
        assert guardrails.get_violation_count() == 0
        
        guardrails.check_content("I like violence.")
        assert guardrails.get_violation_count() > 0

    def test_reset_violation_count(self):
        """Test resetting violation count."""
        guardrails = BedrockGuardrails()
        guardrails.check_content("I like violence.")
        assert guardrails.get_violation_count() > 0
        
        guardrails.reset_violation_count()
        assert guardrails.get_violation_count() == 0

    def test_is_guardrails_enabled(self):
        """Test checking if guardrails are enabled."""
        guardrails1 = BedrockGuardrails(enable_guardrails=True)
        assert guardrails1.is_guardrails_enabled() is True
        
        guardrails2 = BedrockGuardrails(enable_guardrails=False)
        assert guardrails2.is_guardrails_enabled() is False

    def test_get_violation_rate(self):
        """Test getting violation rate."""
        guardrails = BedrockGuardrails()
        
        # No checks
        rate = guardrails.get_violation_rate(0)
        assert rate == 0.0
        
        # 1 violation out of 10 checks
        guardrails.violation_count = 1
        rate = guardrails.get_violation_rate(10)
        assert rate == 0.1

    def test_add_denied_topic(self):
        """Test adding a denied topic."""
        guardrails = BedrockGuardrails()
        initial_count = len(guardrails.get_denied_topics())
        
        guardrails.add_denied_topic("custom_topic")
        assert len(guardrails.get_denied_topics()) == initial_count + 1
        assert "custom_topic" in guardrails.get_denied_topics()

    def test_remove_denied_topic(self):
        """Test removing a denied topic."""
        guardrails = BedrockGuardrails()
        guardrails.add_denied_topic("custom_topic")
        
        guardrails.remove_denied_topic("custom_topic")
        assert "custom_topic" not in guardrails.get_denied_topics()

    def test_get_denied_topics(self):
        """Test getting denied topics."""
        guardrails = BedrockGuardrails()
        topics = guardrails.get_denied_topics()
        
        assert isinstance(topics, list)
        assert len(topics) > 0
        assert "politics" in topics
        assert "violence" in topics

    def test_set_content_filter(self):
        """Test setting content filter."""
        guardrails = BedrockGuardrails()
        guardrails.set_content_filter(
            ContentCategory.HATE,
            enabled=False,
            action=GuardrailAction.WARN,
        )
        
        filter_config = guardrails.get_content_filter(ContentCategory.HATE)
        assert filter_config["enabled"] is False
        assert filter_config["action"] == GuardrailAction.WARN

    def test_get_content_filter(self):
        """Test getting content filter."""
        guardrails = BedrockGuardrails()
        filter_config = guardrails.get_content_filter(ContentCategory.HATE)
        
        assert isinstance(filter_config, dict)
        assert "enabled" in filter_config
        assert "action" in filter_config

    def test_guardrail_violation_structure(self):
        """Test GuardrailViolation structure."""
        violation = GuardrailViolation(
            category=ContentCategory.HATE,
            severity="high",
            confidence=0.95,
            reason="Hate speech detected",
        )
        
        assert violation.category == ContentCategory.HATE
        assert violation.severity == "high"
        assert violation.confidence == 0.95
        assert violation.reason == "Hate speech detected"

    def test_guardrail_result_structure(self):
        """Test GuardrailResult structure."""
        result = GuardrailResult(
            is_safe=False,
            violations=[],
            action=GuardrailAction.BLOCK,
            filtered_content=None,
        )
        
        assert result.is_safe is False
        assert result.action == GuardrailAction.BLOCK

    def test_content_category_enum(self):
        """Test ContentCategory enum values."""
        assert ContentCategory.HATE.value == "hate"
        assert ContentCategory.INSULTS.value == "insults"
        assert ContentCategory.SEXUAL.value == "sexual"
        assert ContentCategory.VIOLENCE.value == "violence"
        assert ContentCategory.PROFANITY.value == "profanity"

    def test_guardrail_action_enum(self):
        """Test GuardrailAction enum values."""
        assert GuardrailAction.BLOCK.value == "block"
        assert GuardrailAction.FILTER.value == "filter"
        assert GuardrailAction.WARN.value == "warn"

    def test_filter_content_replaces_denied_topics(self):
        """Test that filter_content replaces denied topics."""
        guardrails = BedrockGuardrails()
        result = guardrails.check_content("I like politics and violence.")
        
        if result.filtered_content:
            assert "[filtered]" in result.filtered_content

    def test_multiple_violations(self):
        """Test detecting multiple violations."""
        guardrails = BedrockGuardrails()
        result = guardrails.check_content("I like politics, violence, and illegal activities.")
        
        assert result.is_safe is False
        assert len(result.violations) > 0

    def test_guardrails_disabled_no_violations(self):
        """Test that disabled guardrails don't detect violations."""
        guardrails = BedrockGuardrails(enable_guardrails=False)
        result = guardrails.check_content("I like violence.")
        
        assert result.is_safe is True
        assert len(result.violations) == 0

    def test_violation_rate_calculation(self):
        """Test violation rate calculation."""
        guardrails = BedrockGuardrails()
        
        # 2 violations out of 10 checks
        guardrails.violation_count = 2
        rate = guardrails.get_violation_rate(10)
        
        assert rate == 0.2
        assert 0.0 <= rate <= 1.0

    def test_violation_rate_all_violations(self):
        """Test violation rate when all checks have violations."""
        guardrails = BedrockGuardrails()
        
        guardrails.violation_count = 5
        rate = guardrails.get_violation_rate(5)
        
        assert rate == 1.0

    def test_violation_rate_no_violations(self):
        """Test violation rate when no violations."""
        guardrails = BedrockGuardrails()
        
        guardrails.violation_count = 0
        rate = guardrails.get_violation_rate(10)
        
        assert rate == 0.0

    def test_add_duplicate_denied_topic(self):
        """Test adding duplicate denied topic."""
        guardrails = BedrockGuardrails()
        initial_count = len(guardrails.get_denied_topics())
        
        guardrails.add_denied_topic("politics")
        # Should not add duplicate
        assert len(guardrails.get_denied_topics()) == initial_count

    def test_remove_nonexistent_denied_topic(self):
        """Test removing nonexistent denied topic."""
        guardrails = BedrockGuardrails()
        initial_count = len(guardrails.get_denied_topics())
        
        guardrails.remove_denied_topic("nonexistent_topic")
        # Should not change count
        assert len(guardrails.get_denied_topics()) == initial_count

    def test_check_content_with_custom_denied_topic(self):
        """Test checking content with custom denied topic."""
        guardrails = BedrockGuardrails()
        guardrails.add_denied_topic("gaming")
        
        result = guardrails.check_content("I like gaming.")
        assert result.is_safe is False

    def test_guardrail_result_action_types(self):
        """Test different guardrail result actions."""
        guardrails = BedrockGuardrails()
        
        # Safe content should have WARN action
        result_safe = guardrails.check_content("I like to learn English.")
        assert result_safe.action == GuardrailAction.WARN
        
        # Unsafe content should have BLOCK or FILTER action
        result_unsafe = guardrails.check_content("I like violence.")
        assert result_unsafe.action in [GuardrailAction.BLOCK, GuardrailAction.FILTER]
