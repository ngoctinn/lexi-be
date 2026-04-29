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
        logger.info(
            "BedrockScorerAdapter.score() called",
            extra={
                "level": level,
                "scenario_title": scenario_title,
                "user_turns_count": len(user_turns) if user_turns else 0,
            }
        )
        
        if not user_turns:
            logger.warning("score() called with empty user_turns")
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
            request_body = {
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
            
            logger.info(
                "Calling Bedrock for scoring",
                extra={
                    "level": level,
                    "scenario": scenario_title,
                    "turn_count": len(user_turns),
                    "prompt_length": len(prompt),
                    "request_body_keys": list(request_body.keys()),
                }
            )
            
            # Use non-streaming API (simpler and more reliable)
            response = self.bedrock_client.invoke_model(
                modelId="apac.amazon.nova-micro-v1:0",
                body=dumps(request_body),
            )

            # Parse response
            response_body = json.loads(response["body"].read())
            
            logger.info(
                "Bedrock response received",
                extra={
                    "response_keys": list(response_body.keys()),
                    "has_content": "content" in response_body,
                    "content_blocks": len(response_body.get("content", [])) if "content" in response_body else 0,
                    "full_response_body": response_body,  # Log full response to debug
                }
            )
            
            # Extract text from Nova format
            content = ""
            if "content" in response_body:
                for block in response_body["content"]:
                    if "text" in block:
                        content += block["text"]
            
            if not content.strip():
                logger.error(
                    "Bedrock response has no text content",
                    extra={
                        "response_body": response_body,
                        "level": level,
                        "scenario": scenario_title,
                        "turn_count": len(user_turns),
                    }
                )
                return None
            
            logger.info(
                "Extracted content from Bedrock",
                extra={
                    "content_length": len(content),
                    "content_preview": content[:200],
                }
            )
            
            # Try to parse JSON
            try:
                scoring_data = json.loads(content.strip())
            except json.JSONDecodeError as parse_error:
                logger.error(
                    "Failed to parse scoring JSON from Bedrock",
                    extra={
                        "level": level,
                        "scenario": scenario_title,
                        "content": content,
                        "parse_error": str(parse_error),
                    }
                )
                return None

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

            logger.info(
                "Bedrock scoring successful",
                extra={
                    "level": level,
                    "scenario": scenario_title,
                    "overall_score": scoring_data.get("overall_score"),
                }
            )
            return scoring_data

        except ClientError as e:
            # AWS API error - distinguish between error types
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            
            if error_code == "ThrottlingException":
                # 429: Quota exceeded - boto3 already retried
                logger.warning(
                    "Bedrock scoring throttled (429)",
                    extra={
                        "level": level,
                        "scenario": scenario_title,
                        "error_message": error_message,
                    }
                )
            elif error_code == "ServiceUnavailableException":
                # 503: Service temporarily unavailable - boto3 already retried
                logger.warning(
                    "Bedrock scoring unavailable (503)",
                    extra={
                        "level": level,
                        "scenario": scenario_title,
                        "error_message": error_message,
                    }
                )
            else:
                # Other AWS errors
                logger.error(
                    "Bedrock scoring API error",
                    extra={
                        "error_code": error_code,
                        "level": level,
                        "scenario": scenario_title,
                        "error_message": error_message,
                    }
                )
            
            return None

        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse Bedrock JSON response",
                extra={
                    "level": level,
                    "scenario": scenario_title,
                    "error": str(e),
                    "content_preview": content[:200] if 'content' in locals() else "N/A",
                }
            )
            return None

        except Exception as e:
            # Non-AWS errors (network, etc.)
            error_type = type(e).__name__
            logger.error(
                "Bedrock scoring error",
                extra={
                    "error_type": error_type,
                    "level": level,
                    "scenario": scenario_title,
                    "error": str(e),
                },
                exc_info=True
            )
            
            return None
