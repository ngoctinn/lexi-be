"""Infrastructure adapter for Bedrock-based scoring.

This adapter wraps the Bedrock API and implements the external scorer interface.
It's responsible for calling Bedrock (Amazon Nova Lite) and parsing responses.
"""

import json
import logging
from typing import List, Optional

import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

from domain.entities.turn import Turn

logger = logging.getLogger(__name__)


class BedrockScorerAdapter:
    """
    Adapter for Bedrock Nova Lite scoring service.
    
    Error Handling:
    - 429 ThrottlingException: Handled by boto3 exponential backoff
    - 503 ServiceUnavailableException: Handled by boto3 exponential backoff
    - Other errors: Logged and None returned (graceful degradation)
    """

    # Use Nova Lite for scoring (same as conversation)
    MODEL_ID = "apac.amazon.nova-lite-v1:0"

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
        Call Bedrock Nova Lite to score learner's performance using Converse API.

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
                "user_turns_preview": [turn.content[:50] for turn in user_turns[:3]] if user_turns else [],
                "model_id": self.MODEL_ID,
            }
        )
        
        if not user_turns:
            logger.error(
                "score() called with empty user_turns - THIS SHOULD NOT HAPPEN",
                extra={
                    "level": level,
                    "scenario_title": scenario_title,
                }
            )
            return None

        turn_texts = [turn.content for turn in user_turns]
        turns_str = "\n".join([f"- {text}" for text in turn_texts])

        system_prompt = f"""Analyze this English learner's speaking performance.

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

        user_message = "Please score the above performance."

        try:
            logger.info(
                "Calling Bedrock Converse API for scoring",
                extra={
                    "level": level,
                    "scenario": scenario_title,
                    "turn_count": len(user_turns),
                    "system_prompt_length": len(system_prompt),
                    "model_id": self.MODEL_ID,
                }
            )
            
            # Use Converse API (AWS best practice, same as conversation_orchestrator)
            # Reference: https://docs.aws.amazon.com/nova/latest/userguide/using-converse-api.html
            response = self.bedrock_client.converse(
                modelId=self.MODEL_ID,
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": user_message}]
                    }
                ],
                system=[{"text": system_prompt}],
                inferenceConfig={
                    "maxTokens": 500,
                    "temperature": 0.7
                }
            )

            # Converse API: standardized response format
            logger.info(
                "Bedrock Converse API response received",
                extra={
                    "response_keys": list(response.keys()),
                    "has_output": "output" in response,
                    "stop_reason": response.get("stopReason", "N/A"),
                    "usage": response.get("usage", {}),
                }
            )
            
            # Extract text from Converse API response
            content = response["output"]["message"]["content"][0]["text"]
            
            logger.info(
                "Extracted content from Bedrock response",
                extra={
                    "content_length": len(content),
                    "content_preview": content[:300] if content else "EMPTY",
                    "has_json_markers": "{" in content and "}" in content,
                }
            )
            
            if not content.strip():
                logger.error(
                    "CRITICAL: Bedrock response has no text content",
                    extra={
                        "response_keys": list(response.keys()),
                        "level": level,
                        "scenario": scenario_title,
                        "turn_count": len(user_turns),
                        "stop_reason": response.get("stopReason", "N/A"),
                    }
                )
                return None
            
            # Try to parse JSON
            try:
                # Clean up content - remove markdown code blocks if present
                content_clean = content.strip()
                if content_clean.startswith("```json"):
                    content_clean = content_clean[7:]
                if content_clean.startswith("```"):
                    content_clean = content_clean[3:]
                if content_clean.endswith("```"):
                    content_clean = content_clean[:-3]
                content_clean = content_clean.strip()
                
                logger.info(
                    "Attempting to parse JSON",
                    extra={
                        "original_length": len(content),
                        "cleaned_length": len(content_clean),
                        "cleaned_preview": content_clean[:200],
                    }
                )
                
                scoring_data = json.loads(content_clean)
                
                logger.info(
                    "Successfully parsed scoring JSON",
                    extra={
                        "scoring_keys": list(scoring_data.keys()),
                        "has_all_scores": all(
                            key in scoring_data
                            for key in [
                                "fluency_score",
                                "pronunciation_score",
                                "grammar_score",
                                "vocabulary_score",
                                "overall_score",
                            ]
                        ),
                    }
                )
            except json.JSONDecodeError as parse_error:
                logger.error(
                    "CRITICAL: Failed to parse scoring JSON from Bedrock",
                    extra={
                        "level": level,
                        "scenario": scenario_title,
                        "content_length": len(content),
                        "content_full": content,
                        "parse_error": str(parse_error),
                        "parse_error_line": parse_error.lineno if hasattr(parse_error, 'lineno') else "N/A",
                        "parse_error_col": parse_error.colno if hasattr(parse_error, 'colno') else "N/A",
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
