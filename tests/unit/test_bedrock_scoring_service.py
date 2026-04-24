"""Tests for SpeakingPerformanceScorer and BedrockScorerAdapter."""

import json
from unittest.mock import MagicMock, patch

import pytest

from domain.entities.turn import Turn
from domain.value_objects.enums import Speaker
from domain.services.speaking_performance_scorer import SpeakingPerformanceScorer
from infrastructure.services.bedrock_scorer_adapter import BedrockScorerAdapter


class TestBedrockScorerAdapter:
    """Test BedrockScorerAdapter."""

    def test_score_with_bedrock_success(self):
        """Test successful scoring with Bedrock."""
        # Mock Bedrock response
        mock_bedrock = MagicMock()
        mock_response = {
            "body": MagicMock(
                read=MagicMock(
                    return_value=json.dumps(
                        {
                            "content": [
                                {
                                    "text": json.dumps(
                                        {
                                            "fluency_score": 76,
                                            "pronunciation_score": 72,
                                            "grammar_score": 71,
                                            "vocabulary_score": 67,
                                            "overall_score": 72,
                                            "feedback": "Bạn làm tốt!",
                                        }
                                    )
                                }
                            ]
                        }
                    ).encode()
                )
            )
        }
        mock_bedrock.invoke_model.return_value = mock_response

        adapter = BedrockScorerAdapter(bedrock_client=mock_bedrock)

        # Create test turns
        user_turns = [
            Turn(
                session_id="test-session",
                turn_index=0,
                speaker=Speaker.USER,
                content="I like coffee",
            ),
            Turn(
                session_id="test-session",
                turn_index=2,
                speaker=Speaker.USER,
                content="It's very good",
            ),
        ]

        # Score
        result = adapter.score(user_turns, "B1", "Restaurant")

        # Verify result
        assert result["fluency_score"] == 76
        assert result["pronunciation_score"] == 72
        assert result["grammar_score"] == 71
        assert result["vocabulary_score"] == 67
        assert result["overall_score"] == 72
        assert result["feedback"] == "Bạn làm tốt!"

    def test_score_with_bedrock_failure(self):
        """Test Bedrock failure returns None."""
        # Mock Bedrock failure
        mock_bedrock = MagicMock()
        mock_bedrock.invoke_model.side_effect = Exception("Bedrock error")

        adapter = BedrockScorerAdapter(bedrock_client=mock_bedrock)

        # Create test turns
        user_turns = [
            Turn(
                session_id="test-session",
                turn_index=0,
                speaker=Speaker.USER,
                content="I like coffee",
            ),
        ]

        # Score (should return None on failure)
        result = adapter.score(user_turns, "B1", "Restaurant")
        assert result is None

    def test_score_with_empty_turns(self):
        """Test scoring with empty turns returns None."""
        adapter = BedrockScorerAdapter()
        result = adapter.score([], "B1", "Restaurant")
        assert result is None

    def test_score_validation_clamps_values(self):
        """Test that scores are clamped to 0-100."""
        # Mock Bedrock response with invalid scores
        mock_bedrock = MagicMock()
        mock_response = {
            "body": MagicMock(
                read=MagicMock(
                    return_value=json.dumps(
                        {
                            "content": [
                                {
                                    "text": json.dumps(
                                        {
                                            "fluency_score": 150,  # Invalid
                                            "pronunciation_score": -10,  # Invalid
                                            "grammar_score": 71,
                                            "vocabulary_score": 67,
                                            "overall_score": 200,  # Invalid
                                            "feedback": "Test",
                                        }
                                    )
                                }
                            ]
                        }
                    ).encode()
                )
            )
        }
        mock_bedrock.invoke_model.return_value = mock_response

        adapter = BedrockScorerAdapter(bedrock_client=mock_bedrock)

        # Create test turns
        user_turns = [
            Turn(
                session_id="test-session",
                turn_index=0,
                speaker=Speaker.USER,
                content="I like coffee",
            ),
        ]

        # Score
        result = adapter.score(user_turns, "B1", "Restaurant")

        # Verify scores are clamped
        assert result["fluency_score"] == 100  # Clamped from 150
        assert result["pronunciation_score"] == 0  # Clamped from -10
        assert result["grammar_score"] == 71
        assert result["vocabulary_score"] == 67
        assert result["overall_score"] == 100  # Clamped from 200


class TestSpeakingPerformanceScorer:
    """Test SpeakingPerformanceScorer."""

    def test_score_session_with_external_scorer(self):
        """Test scoring with external scorer."""
        # Mock external scorer
        mock_scorer = MagicMock()
        mock_scorer.score.return_value = {
            "fluency_score": 80,
            "pronunciation_score": 75,
            "grammar_score": 78,
            "vocabulary_score": 72,
            "overall_score": 76,
            "feedback": "Good job!",
        }

        scorer = SpeakingPerformanceScorer(external_scorer=mock_scorer)

        # Create test turns
        user_turns = [
            Turn(
                session_id="test-session",
                turn_index=0,
                speaker=Speaker.USER,
                content="I like coffee",
            ),
        ]

        # Score
        result = scorer.score_session(user_turns, "B1", "Restaurant")

        # Verify result
        assert result["overall_score"] == 76
        assert result["feedback"] == "Good job!"
        mock_scorer.score.assert_called_once()

    def test_score_session_requires_external_scorer(self):
        """Test that external scorer is required."""
        with pytest.raises(ValueError, match="external_scorer is required"):
            SpeakingPerformanceScorer(external_scorer=None)

    def test_score_session_with_empty_turns_raises(self):
        """Test that empty turns raises error."""
        mock_scorer = MagicMock()
        scorer = SpeakingPerformanceScorer(external_scorer=mock_scorer)

        with pytest.raises(ValueError, match="Cannot score session with no user turns"):
            scorer.score_session([], "B1", "Restaurant")

    def test_score_session_with_empty_result_raises(self):
        """Test that empty result from scorer raises error."""
        mock_scorer = MagicMock()
        mock_scorer.score.return_value = None

        scorer = SpeakingPerformanceScorer(external_scorer=mock_scorer)

        user_turns = [
            Turn(
                session_id="test-session",
                turn_index=0,
                speaker=Speaker.USER,
                content="I like coffee",
            ),
        ]

        with pytest.raises(Exception, match="LLM scoring returned empty result"):
            scorer.score_session(user_turns, "B1", "Restaurant")
