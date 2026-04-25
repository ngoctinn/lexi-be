"""Unit tests for GreetingGenerator service."""

from pathlib import Path
import sys
import json
from unittest.mock import Mock, MagicMock
import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from domain.services.greeting_generator import GreetingGenerator, GreetingResult


class TestGreetingGenerator:
    """Tests for GreetingGenerator."""

    def test_get_greeting_template_all_levels(self):
        """Test greeting template selection for each level (A1-C2)."""
        mock_bedrock = Mock()
        generator = GreetingGenerator(mock_bedrock)
        
        expected_templates = {
            "A1": "Hi! How are you?",
            "A2": "Hello! How are you doing?",
            "B1": "Hi there! How's it going?",
            "B2": "Hello! How have you been?",
            "C1": "Hi! How are things with you?",
            "C2": "Greetings! How have you been lately?",
        }
        
        for level, expected_greeting in expected_templates.items():
            greeting = generator._get_greeting_template(level)
            assert greeting == expected_greeting

    def test_get_greeting_template_invalid_level(self):
        """Test that invalid level raises ValueError."""
        mock_bedrock = Mock()
        generator = GreetingGenerator(mock_bedrock)
        
        with pytest.raises(ValueError, match="Invalid proficiency level"):
            generator._get_greeting_template("Z1")

    def test_generate_first_question_success(self):
        """Test first question generation with mocked Bedrock response."""
        mock_bedrock = Mock()
        mock_response = {
            "body": MagicMock(read=lambda: json.dumps({
                "content": [{"text": "What brings you to the restaurant today?"}]
            }).encode())
        }
        mock_bedrock.invoke_model.return_value = mock_response
        
        generator = GreetingGenerator(mock_bedrock)
        first_question = generator._generate_first_question(
            level="A1",
            scenario_title="Restaurant",
            learner_role="Customer",
            ai_role="Waiter",
            selected_goals=["ordering food"],
        )
        
        assert first_question == "What brings you to the restaurant today?"
        mock_bedrock.invoke_model.assert_called_once()
        
        # Verify Bedrock was called with correct model
        call_args = mock_bedrock.invoke_model.call_args
        assert call_args[1]["modelId"] == "apac.amazon.nova-micro-v1:0"

    def test_generate_first_question_bedrock_error(self):
        """Test error handling when Bedrock call fails."""
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.side_effect = Exception("Bedrock API error")
        
        generator = GreetingGenerator(mock_bedrock)
        
        with pytest.raises(Exception, match="Bedrock API error"):
            generator._generate_first_question(
                level="A1",
                scenario_title="Restaurant",
                learner_role="Customer",
                ai_role="Waiter",
                selected_goals=["ordering food"],
            )

    def test_generate_combined_greeting_and_question(self):
        """Test combined text format (greeting + first question)."""
        mock_bedrock = Mock()
        mock_response = {
            "body": MagicMock(read=lambda: json.dumps({
                "content": [{"text": "What would you like to order?"}]
            }).encode())
        }
        mock_bedrock.invoke_model.return_value = mock_response
        
        generator = GreetingGenerator(mock_bedrock)
        result = generator.generate(
            level="A1",
            scenario_title="Restaurant",
            learner_role="Customer",
            ai_role="Waiter",
            selected_goals=["ordering food"],
            ai_gender="male",
        )
        
        assert isinstance(result, GreetingResult)
        assert result.greeting_text == "Hi! How are you?"
        assert result.first_question == "What would you like to order?"
        assert result.combined_text == "Hi! How are you? What would you like to order?"

    def test_generate_with_multiple_goals(self):
        """Test first question generation with multiple goals."""
        mock_bedrock = Mock()
        mock_response = {
            "body": MagicMock(read=lambda: json.dumps({
                "content": [{"text": "What would you like to order?"}]
            }).encode())
        }
        mock_bedrock.invoke_model.return_value = mock_response
        
        generator = GreetingGenerator(mock_bedrock)
        result = generator.generate(
            level="B1",
            scenario_title="Restaurant",
            learner_role="Customer",
            ai_role="Waiter",
            selected_goals=["ordering food", "asking for recommendations"],
            ai_gender="female",
        )
        
        assert result.greeting_text == "Hi there! How's it going?"
        assert result.first_question == "What would you like to order?"

    def test_generate_with_empty_goals(self):
        """Test first question generation with empty goals list."""
        mock_bedrock = Mock()
        mock_response = {
            "body": MagicMock(read=lambda: json.dumps({
                "content": [{"text": "How can I help you?"}]
            }).encode())
        }
        mock_bedrock.invoke_model.return_value = mock_response
        
        generator = GreetingGenerator(mock_bedrock)
        result = generator.generate(
            level="A2",
            scenario_title="Hotel",
            learner_role="Guest",
            ai_role="Receptionist",
            selected_goals=[],
            ai_gender="female",
        )
        
        assert result.greeting_text == "Hello! How are you doing?"
        assert result.first_question == "How can I help you?"

    def test_generate_different_levels(self):
        """Test greeting generation for different proficiency levels."""
        mock_bedrock = Mock()
        mock_response = {
            "body": MagicMock(read=lambda: json.dumps({
                "content": [{"text": "Test question"}]
            }).encode())
        }
        mock_bedrock.invoke_model.return_value = mock_response
        
        generator = GreetingGenerator(mock_bedrock)
        
        levels_and_greetings = [
            ("A1", "Hi! How are you?"),
            ("B2", "Hello! How have you been?"),
            ("C2", "Greetings! How have you been lately?"),
        ]
        
        for level, expected_greeting in levels_and_greetings:
            result = generator.generate(
                level=level,
                scenario_title="Test",
                learner_role="Role1",
                ai_role="Role2",
                selected_goals=["goal1"],
                ai_gender="male",
            )
            assert result.greeting_text == expected_greeting

    def test_bedrock_request_format(self):
        """Test that Bedrock is called with correct request format."""
        mock_bedrock = Mock()
        mock_response = {
            "body": MagicMock(read=lambda: json.dumps({
                "content": [{"text": "Test question"}]
            }).encode())
        }
        mock_bedrock.invoke_model.return_value = mock_response
        
        generator = GreetingGenerator(mock_bedrock)
        generator._generate_first_question(
            level="A1",
            scenario_title="Restaurant",
            learner_role="Customer",
            ai_role="Waiter",
            selected_goals=["ordering"],
        )
        
        # Verify Bedrock call
        call_args = mock_bedrock.invoke_model.call_args
        assert call_args[1]["modelId"] == "apac.amazon.nova-micro-v1:0"
        
        # Verify request body
        body = json.loads(call_args[1]["body"])
        assert "messages" in body
        assert body["max_tokens"] == 100
        assert body["temperature"] == 0.7
        assert body["messages"][0]["role"] == "user"
        assert "Restaurant" in body["messages"][0]["content"]
        assert "Customer" in body["messages"][0]["content"]
        assert "Waiter" in body["messages"][0]["content"]
