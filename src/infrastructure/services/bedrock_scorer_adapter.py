"""Infrastructure adapter for Bedrock-based scoring.

This adapter wraps the Bedrock API and implements the external scorer interface.
It's responsible for calling Bedrock and parsing responses.
"""

import json
import logging
from typing import List, Optional

from shared.http_utils import dumps

import boto3

from domain.entities.turn import Turn

logger = logging.getLogger(__name__)


class BedrockScorerAdapter:
    """Adapter for Bedrock Claude scoring service."""

    def __init__(self, bedrock_client=None, region: str = "ap-southeast-1"):
        """
        Args:
            bedrock_client: Optional boto3 Bedrock client. If not provided, creates one.
            region: AWS region for Bedrock
        """
        self.bedrock_client = bedrock_client or boto3.client(
            "bedrock-runtime", region_name=region
        )

    def score(self, user_turns: List[Turn], level: str, scenario_title: str) -> Optional[dict]:
        """
        Call Bedrock to score learner's performance.

        Args:
            user_turns: List of user Turn entities
            level: Proficiency level (A1-C2)
            scenario_title: Scenario name

        Returns:
            Scoring dict or None if failed
        """
        if not user_turns:
            return None

        turn_texts = [turn.content for turn in user_turns]
        turns_str = "\n".join([f"- {text}" for text in turn_texts])

        prompt = f"""Analyze this English learner's speaking performance.

Level: {level}
Scenario: {scenario_title}
Number of turns: {len(user_turns)}

Turns spoken:
{turns_str}

Score the learner (0-100) on:
1. Fluency: Smoothness, natural pacing, minimal hesitation
2. Pronunciation: Clear articulation, correct stress/intonation
3. Grammar: Correct sentence structure, verb tenses, agreement
4. Vocabulary: Word choice, variety, appropriateness for level

Respond in JSON format only:
{{
  "fluency_score": <0-100>,
  "pronunciation_score": <0-100>,
  "grammar_score": <0-100>,
  "vocabulary_score": <0-100>,
  "overall_score": <0-100>,
  "feedback": "<personalized feedback in Vietnamese>"
}}"""

        try:
            response = self.bedrock_client.invoke_model(
                modelId="anthropic.claude-3-5-sonnet-20241022",
                body=dumps(
                    {
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 500,
                        "messages": [{"role": "user", "content": prompt}],
                    }
                ),
            )

            response_body = json.loads(response["body"].read())
            content = response_body["content"][0]["text"]
            scoring_data = json.loads(content)

            # Validate and clamp scores
            for key in [
                "fluency_score",
                "pronunciation_score",
                "grammar_score",
                "vocabulary_score",
                "overall_score",
            ]:
                score = scoring_data.get(key, 0)
                scoring_data[key] = max(0, min(100, int(score)))

            logger.info(f"Bedrock scoring successful: {scoring_data}")
            return scoring_data

        except Exception as e:
            logger.error(f"Bedrock scoring failed: {e}")
            return None
