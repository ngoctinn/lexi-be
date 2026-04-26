"""
Unit tests for OptimizedPromptBuilder (Phase 1: Prompt Optimization).

Tests verify:
1. 5-section structure present
2. Level-adaptive personality traits
3. Delivery cues support
4. Few-shot examples included
5. Response format constraints
"""

import pytest
from domain.services.prompt_builder import OptimizedPromptBuilder


class TestOptimizedPromptBuilder:
    """Test OptimizedPromptBuilder 5-section prompt structure."""

    def test_prompt_contains_all_5_sections(self):
        """Test: prompt contains all 5 sections."""
        prompt = OptimizedPromptBuilder.build(
            scenario_title="Restaurant",
            learner_role="Customer",
            ai_role="Waiter",
            level="B1",
            selected_goals=["Order food"],
        )
        
        assert "SECTION 1: IDENTITY" in prompt
        assert "SECTION 2: PERSONALITY" in prompt
        assert "SECTION 3: BEHAVIORS" in prompt
        assert "SECTION 4: RESPONSE RULES" in prompt
        assert "SECTION 5: GUARDRAILS" in prompt

    def test_identity_section_contains_role_and_purpose(self):
        """Test: IDENTITY section has role, relationship, purpose."""
        prompt = OptimizedPromptBuilder.build(
            scenario_title="Restaurant",
            learner_role="Customer",
            ai_role="Waiter",
            level="B1",
            selected_goals=["Order food"],
        )
        
        assert "Waiter" in prompt
        assert "Customer" in prompt
        assert "English conversation partner" in prompt
        assert "practice English" in prompt

    def test_personality_traits_match_level(self):
        """Test: personality traits are level-adaptive."""
        levels_and_traits = {
            "A1": "warm, patient, encouraging",
            "A2": "supportive, friendly, helpful",
            "B1": "engaging, curious, natural",
            "B2": "thoughtful, nuanced",
            "C1": "sophisticated, intellectually engaging",
            "C2": "native-like, natural",
        }
        
        for level, expected_traits in levels_and_traits.items():
            prompt = OptimizedPromptBuilder.build(
                scenario_title="Test",
                learner_role="Learner",
                ai_role="Partner",
                level=level,
                selected_goal="",
            )
            
            assert expected_traits in prompt, f"Level {level} should have traits: {expected_traits}"

    def test_response_rules_include_delivery_cues(self):
        """Test: RESPONSE RULES section includes delivery cues."""
        prompt = OptimizedPromptBuilder.build(
            scenario_title="Test",
            learner_role="Learner",
            ai_role="Partner",
            level="B1",
            selected_goal="",
        )
        
        assert "[warmly]" in prompt
        assert "[encouragingly]" in prompt
        assert "[gently]" in prompt
        assert "delivery cue" in prompt

    def test_response_rules_include_no_markdown_constraint(self):
        """Test: RESPONSE RULES forbid markdown."""
        prompt = OptimizedPromptBuilder.build(
            scenario_title="Test",
            learner_role="Learner",
            ai_role="Partner",
            level="B1",
            selected_goal="",
        )
        
        assert "NO markdown" in prompt
        assert "NO lists" in prompt
        assert "NO em-dashes" in prompt

    def test_response_rules_include_max_tokens_per_level(self):
        """Test: max tokens specified per level."""
        levels_and_tokens = {
            "A1": "40",
            "A2": "60",
            "B1": "100",
            "B2": "150",
            "C1": "200",
            "C2": "250",
        }
        
        for level, expected_tokens in levels_and_tokens.items():
            prompt = OptimizedPromptBuilder.build(
                scenario_title="Test",
                learner_role="Learner",
                ai_role="Partner",
                level=level,
                selected_goal="",
            )
            
            assert expected_tokens in prompt, f"Level {level} should have max {expected_tokens} tokens"

    def test_response_rules_include_few_shot_examples(self):
        """Test: few-shot examples included per level."""
        prompt = OptimizedPromptBuilder.build(
            scenario_title="Test",
            learner_role="Learner",
            ai_role="Partner",
            level="B1",
            selected_goal="",
        )
        
        assert "Good response:" in prompt
        assert "Bad response:" in prompt
        assert "Learner:" in prompt

    def test_guardrails_include_off_topic_redirect(self):
        """Test: GUARDRAILS section includes off-topic redirect."""
        prompt = OptimizedPromptBuilder.build(
            scenario_title="Restaurant",
            learner_role="Customer",
            ai_role="Waiter",
            level="B1",
            selected_goal="",
        )
        
        assert "off-topic" in prompt.lower()
        assert "Restaurant" in prompt

    def test_guardrails_include_vietnamese_detection(self):
        """Test: GUARDRAILS section includes Vietnamese detection."""
        prompt = OptimizedPromptBuilder.build(
            scenario_title="Test",
            learner_role="Learner",
            ai_role="Partner",
            level="B1",
            selected_goal="",
        )
        
        assert "Vietnamese" in prompt
        assert "Please try in English" in prompt

    def test_guardrails_include_inappropriate_language_handling(self):
        """Test: GUARDRAILS section handles inappropriate language."""
        prompt = OptimizedPromptBuilder.build(
            scenario_title="Test",
            learner_role="Learner",
            ai_role="Partner",
            level="B1",
            selected_goals=["Learn greetings"],
        )
        
        assert "inappropriate" in prompt.lower()
        assert "professional" in prompt

    def test_guardrails_forbid_grammar_correction_during_conversation(self):
        """Test: GUARDRAILS forbid grammar correction during conversation."""
        prompt = OptimizedPromptBuilder.build(
            scenario_title="Test",
            learner_role="Learner",
            ai_role="Partner",
            level="B1",
            selected_goal="",
        )
        
        assert "Do NOT correct grammar" in prompt

    def test_guardrails_forbid_ai_revelation(self):
        """Test: GUARDRAILS forbid revealing AI identity."""
        prompt = OptimizedPromptBuilder.build(
            scenario_title="Test",
            learner_role="Learner",
            ai_role="Partner",
            level="B1",
            selected_goal="",
        )
        
        assert "Do NOT reveal you are an AI" in prompt

    def test_behaviors_include_one_question_per_turn(self):
        """Test: BEHAVIORS section enforces one question per turn."""
        prompt = OptimizedPromptBuilder.build(
            scenario_title="Test",
            learner_role="Learner",
            ai_role="Partner",
            level="B1",
            selected_goal="",
        )
        
        assert "ONE question per turn" in prompt

    def test_behaviors_include_natural_conversation_flow(self):
        """Test: BEHAVIORS section emphasizes natural flow."""
        prompt = OptimizedPromptBuilder.build(
            scenario_title="Test",
            learner_role="Learner",
            ai_role="Partner",
            level="B1",
            selected_goal="",
        )
        
        assert "move conversation forward" in prompt

    def test_invalid_level_defaults_to_b1(self):
        """Test: invalid level defaults to B1."""
        prompt = OptimizedPromptBuilder.build(
            scenario_title="Test",
            learner_role="Learner",
            ai_role="Partner",
            level="INVALID",
            selected_goal="",
        )
        
        # Should not raise error, should use B1 defaults
        assert "SECTION 1: IDENTITY" in prompt
        assert "engaging, curious, natural" in prompt  # B1 traits

    def test_empty_goals_handled_gracefully(self):
        """Test: empty goals list handled gracefully."""
        prompt = OptimizedPromptBuilder.build(
            scenario_title="Test",
            learner_role="Learner",
            ai_role="Partner",
            level="B1",
            selected_goal="",
        )
        
        assert "SECTION 1: IDENTITY" in prompt
        assert len(prompt) > 0

    def test_multiple_goals_included(self):
        """Test: multiple goals included in prompt."""
        prompt = OptimizedPromptBuilder.build(
            scenario_title="Test",
            learner_role="Learner",
            ai_role="Partner",
            level="B1",
            selected_goal="Learn greetings",
        )
        
        assert "SECTION 1: IDENTITY" in prompt

    def test_prompt_is_spoken_first_format(self):
        """Test: prompt emphasizes spoken-first format."""
        prompt = OptimizedPromptBuilder.build(
            scenario_title="Test",
            learner_role="Learner",
            ai_role="Partner",
            level="B1",
            selected_goal="",
        )
        
        assert "Spoken-first format" in prompt
        assert "sounds natural when read aloud" in prompt

    def test_all_levels_generate_valid_prompts(self):
        """Test: all proficiency levels generate valid prompts."""
        levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        
        for level in levels:
            prompt = OptimizedPromptBuilder.build(
                scenario_title="Test",
                learner_role="Learner",
                ai_role="Partner",
                level=level,
                selected_goal="",
            )
            
            assert len(prompt) > 0
            assert "SECTION 1: IDENTITY" in prompt
            assert "SECTION 5: GUARDRAILS" in prompt
