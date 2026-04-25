"""Greeting and first question generation for conversation sessions."""

import json
import logging
from dataclasses import dataclass
from typing import Optional

from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


@dataclass
class GreetingResult:
    """Result of greeting and first question generation."""
    greeting_text: str
    first_question: str
    combined_text: str


class GreetingGenerator:
    """Generates level-appropriate greetings and first questions for session start."""

    # Greeting templates per proficiency level (cached, no LLM call)
    _GREETING_TEMPLATES = {
        "A1": "Hi! How are you?",
        "A2": "Hello! How are you doing?",
        "B1": "Hi there! How's it going?",
        "B2": "Hello! How have you been?",
        "C1": "Hi! How are things with you?",
        "C2": "Greetings! How have you been lately?",
    }

    def __init__(self, bedrock_client):
        """Initialize GreetingGenerator with Bedrock client.
        
        Args:
            bedrock_client: boto3 Bedrock Runtime client
        """
        self._bedrock = bedrock_client

    def generate(
        self,
        level: str,
        scenario_title: str,
        learner_role: str,
        ai_role: str,
        selected_goals: list[str],
        ai_gender: str,
        session_id: Optional[str] = None,
    ) -> GreetingResult:
        """Generate greeting and first question for session start.
        
        Args:
            level: Proficiency level (A1-C2)
            scenario_title: Title of the scenario (e.g., "Restaurant")
            learner_role: Role of the learner in the scenario
            ai_role: Role of the AI in the scenario
            selected_goals: List of selected learning goals
            ai_gender: Gender of the AI (male/female)
            session_id: Optional session ID for logging
            
        Returns:
            GreetingResult with greeting_text, first_question, and combined_text
            
        Raises:
            ValueError: If level is invalid
            Exception: If Bedrock call fails
        """
        import time
        start_time = time.time()
        
        try:
            # Get greeting template (cached, no LLM call)
            greeting_text = self._get_greeting_template(level)
            
            # Generate first question using Bedrock
            first_question, input_tokens, output_tokens = self._generate_first_question(
                level=level,
                scenario_title=scenario_title,
                learner_role=learner_role,
                ai_role=ai_role,
                selected_goals=selected_goals,
            )
            
            # Combine greeting and first question
            combined_text = f"{greeting_text} {first_question}"
            
            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            
            # Estimate cost (Amazon Nova Micro pricing)
            # Input: $0.000035 per 1K tokens, Output: $0.00014 per 1K tokens
            cost_usd = (input_tokens / 1000 * 0.000035) + (output_tokens / 1000 * 0.00014)
            
            # Log performance metrics
            logger.info(
                "Greeting generated successfully",
                extra={
                    "session_id": session_id,
                    "level": level,
                    "scenario": scenario_title,
                    "latency_ms": round(latency_ms, 2),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_usd": round(cost_usd, 6),
                }
            )
            
            return GreetingResult(
                greeting_text=greeting_text,
                first_question=first_question,
                combined_text=combined_text,
            )
            
        except ValueError as e:
            # Log validation errors
            logger.error(
                "Invalid greeting generation parameters",
                extra={
                    "session_id": session_id,
                    "level": level,
                    "scenario": scenario_title,
                    "error": str(e),
                }
            )
            raise
            
        except Exception as e:
            # Log Bedrock API errors
            latency_ms = (time.time() - start_time) * 1000
            logger.error(
                "Greeting generation failed",
                extra={
                    "session_id": session_id,
                    "level": level,
                    "scenario": scenario_title,
                    "latency_ms": round(latency_ms, 2),
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )
            raise

    def _get_greeting_template(self, level: str) -> str:
        """Get greeting template for proficiency level.
        
        Args:
            level: Proficiency level (A1-C2)
            
        Returns:
            Greeting template string
            
        Raises:
            ValueError: If level is invalid
        """
        if level not in self._GREETING_TEMPLATES:
            raise ValueError(f"Invalid proficiency level: {level}")
        
        return self._GREETING_TEMPLATES[level]

    def _generate_first_question(
        self,
        level: str,
        scenario_title: str,
        learner_role: str,
        ai_role: str,
        selected_goals: list[str],
    ) -> tuple[str, int, int]:
        """Generate first question using Bedrock.
        
        Args:
            level: Proficiency level (A1-C2)
            scenario_title: Title of the scenario
            learner_role: Role of the learner
            ai_role: Role of the AI
            selected_goals: List of selected goals
            
        Returns:
            Tuple of (first_question, input_tokens, output_tokens)
            
        Raises:
            Exception: If Bedrock call fails
        """
        # Build prompt for Bedrock
        goals_text = ", ".join(selected_goals) if selected_goals else "general conversation"
        
        prompt = f"""You are an English conversation partner in a role-play scenario.

Scenario: {scenario_title}
Your role: {ai_role}
Learner's role: {learner_role}
Learning goals: {goals_text}
Proficiency level: {level}

Generate a natural first question to start the conversation. The question should:
1. Be appropriate for proficiency level {level}
2. Establish the conversation topic clearly
3. Reference the scenario context
4. Help the learner work toward the selected goals

Generate ONLY the question, no other text. Keep it to one sentence."""

        try:
            # Call Bedrock with Amazon Nova Micro
            response = self._bedrock.invoke_model(
                modelId="apac.amazon.nova-micro-v1:0",
                body=json.dumps({
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    "max_tokens": 100,
                    "temperature": 0.7,
                }),
            )
            
            # Parse response
            response_body = json.loads(response["body"].read())
            first_question = response_body["content"][0]["text"].strip()
            
            # Extract token usage from response (AWS Nova format)
            usage = response_body.get("usage", {})
            input_tokens = usage.get("inputTokens", 0)
            output_tokens = usage.get("outputTokens", 0)
            
            return first_question, input_tokens, output_tokens
            
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse Bedrock response JSON",
                extra={
                    "error": str(e),
                    "model_id": "apac.amazon.nova-micro-v1:0",
                }
            )
            raise
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            
            # Handle AWS Nova specific errors per AWS docs
            if error_code == "ValidationException":
                if "responsible AI" in error_message.lower() or "content policy" in error_message.lower():
                    logger.warning(
                        "Bedrock content blocked by Responsible AI policy",
                        extra={
                            "error_code": error_code,
                            "error_message": error_message,
                            "model_id": "apac.amazon.nova-micro-v1:0",
                        }
                    )
                else:
                    logger.error(
                        "Bedrock input validation error",
                        extra={
                            "error_code": error_code,
                            "error_message": error_message,
                            "model_id": "apac.amazon.nova-micro-v1:0",
                        }
                    )
            else:
                logger.error(
                    "Bedrock API call failed for first question generation",
                    extra={
                        "error_code": error_code,
                        "error_message": error_message,
                        "model_id": "apac.amazon.nova-micro-v1:0",
                    }
                )
            raise
