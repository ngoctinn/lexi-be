"""Infrastructure adapter for Bedrock-based scoring.

This adapter wraps the Bedrock API and implements the external scorer interface.
It's responsible for calling Bedrock (Amazon Nova Micro) and parsing responses.
"""

import json
import logging
from typing import List, Optional

from shared.http_utils import dumps

import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

from domain.entities.turn import Turn

logger = logging.getLogger(__name__)


class BedrockScorerAdapter:
    """
    Adapter for Bedrock Nova Micro scoring service.
    
    Error Handling:
    - 429 ThrottlingException: Handled by boto3 exponential backoff
    - 503 ServiceUnavailableException: Handled by boto3 exponential backoff
    - Other errors: Logged and None returned (graceful degradation)
    """

    def __init__(self, bedrock_client=None, region: str = "ap-southeast-1"):
        """
        Initialize with retry configuration per AWS best practices.
        
        Args:
            bedrock_client: Optional boto3 Bedrock client. If not provided, creates one
                          with exponential backoff retry configuration.
            region: AWS region for Bedrock
        """
        if bedrock_client:
            self.bedrock_client = bedrock_client
        else:
            # Configure retry with exponential backoff + jitter (AWS recommended)
            retry_config = Config(
                retries={
                    "max_attempts": 3,  # Total attempts (1 initial + 2 retries)
                    "mode": "adaptive",  # Exponential backoff with jitter
                }
            )
            self.bedrock_client = boto3.client(
                "bedrock-runtime", region_name=region, config=retry_config
            )

    def score(self, user_turns: List[Turn], level: str, scenario_title: str) -> Optional[dict]:
        """
        Call Bedrock Nova Micro to score learner's performance.

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

        # Amazon Nova format (per AWS docs: https://docs.aws.amazon.com/nova/latest/userguide/complete-request-schema.html)
        # Note: Nova Micro does not support prompt caching (Anthropic-specific feature)
        system_content = [{"text": prompt}]

        try:
            response = self.bedrock_client.invoke_model(
                modelId="apac.amazon.nova-micro-v1:0",  # Use inference profile for APAC regions
                body=dumps(
                    {
                        "system": system_content,
                        "messages": [
                            {
                                "role": "user",
                                "content": [{"text": "Please score the above performance."}]
                            }
                        ],
                        "inferenceConfig": {
                            "maxTokens": 500,
                            "temperature": 0.7
                        }
                    }
                ),
            )

            response_body = json.loads(response["body"].read())
            # Nova response format: {"output": {"message": {"content": [{"text": "..."}]}}}
            content = response_body["output"]["message"]["content"][0]["text"]
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

            logger.info(f"Bedrock scoring successful: level={level}, scenario={scenario_title}")
            return scoring_data

        except ClientError as e:
            # AWS API error - distinguish between error types
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            
            if error_code == "ThrottlingException":
                # 429: Quota exceeded - boto3 already retried
                logger.warning(
                    f"Bedrock scoring throttled (429): level={level}, scenario={scenario_title}"
                )
            elif error_code == "ServiceUnavailableException":
                # 503: Service temporarily unavailable - boto3 already retried
                logger.warning(
                    f"Bedrock scoring unavailable (503): level={level}, scenario={scenario_title}"
                )
            else:
                # Other AWS errors
                logger.error(
                    f"Bedrock scoring API error ({error_code}): level={level}, "
                    f"scenario={scenario_title}, message={str(e)}"
                )
            
            return None

        except Exception as e:
            # Non-AWS errors (JSON parsing, network, etc.)
            error_type = type(e).__name__
            logger.error(
                f"Bedrock scoring error ({error_type}): level={level}, "
                f"scenario={scenario_title}, message={str(e)}",
                exc_info=True
            )
            
            return None
