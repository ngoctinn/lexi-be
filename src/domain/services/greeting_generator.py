"""Greeting and first question generation for conversation sessions."""

import json
import logging
import time
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
    """Generates level-appropriate greetings and first questions for session start using LLM."""

    # Fallback greetings per proficiency level (if LLM fails)
    _FALLBACK_GREETINGS = {
        "A1": "Hi! I'm {character}. Nice to meet you!",
        "A2": "Hello! I'm {character}. How are you?",
        "B1": "Hi there! I'm {character}. How's it going?",
        "B2": "Hello! I'm {character}. How have you been?",
        "C1": "Hi! I'm {character}. How are things with you?",
        "C2": "Greetings! I'm {character}. How have you been lately?",
    }
    
    # Fallback first questions per proficiency level (if LLM fails)
    _FALLBACK_FIRST_QUESTIONS = {
        "A1": "What do you like?",
        "A2": "What do you want to do?",
        "B1": "What brings you here today?",
        "B2": "What would you like to discuss?",
        "C1": "What's on your mind today?",
        "C2": "What would you like to explore?",
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
        selected_goal: str,
        ai_character: str,
        session_id: Optional[str] = None,
    ) -> GreetingResult:
        """Generate full greeting using LLM (character introduces themselves + first question).
        
        Args:
            level: Proficiency level (A1-C2)
            scenario_title: Title of the scenario (e.g., "Restaurant")
            learner_role: Role of the learner in the scenario
            ai_role: Role of the AI in the scenario
            selected_goal: Selected learning goal
            ai_character: Character name (Sarah, Marco, Emma, James)
            session_id: Optional session ID for logging
            
        Returns:
            GreetingResult with greeting_text, first_question, and combined_text
            
        Raises:
            ValueError: If level is invalid
            Exception: If Bedrock call fails
        """
        start_time = time.time()
        
        try:
            # Generate full greeting using LLM
            greeting_text, first_question, input_tokens, output_tokens = self._generate_full_greeting(
                level=level,
                scenario_title=scenario_title,
                learner_role=learner_role,
                ai_role=ai_role,
                selected_goal=selected_goal,
                ai_character=ai_character,
            )
            
            # Combine greeting and first question
            combined_text = f"{greeting_text} {first_question}"
            
            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            
            # Estimate cost (Amazon Nova Lite pricing)
            cost_usd = (input_tokens / 1000 * 0.00006) + (output_tokens / 1000 * 0.00024)
            
            # Log performance metrics
            logger.info(
                "Greeting generated successfully",
                extra={
                    "session_id": session_id,
                    "level": level,
                    "scenario": scenario_title,
                    "character": ai_character,
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
                    "character": ai_character,
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
                    "character": ai_character,
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
        valid_levels = {"A1", "A2", "B1", "B2", "C1", "C2"}
        if level not in valid_levels:
            raise ValueError(f"Invalid proficiency level: {level}")
        
        return self._FALLBACK_GREETINGS.get(level, "Hi! I'm {character}.")

    def _generate_first_question(
        self,
        level: str,
        scenario_title: str,
        learner_role: str,
        ai_role: str,
        selected_goal: str,
    ) -> tuple[str, int, int]:
        """Generate first question using Bedrock with fallback.
        
        Args:
            level: Proficiency level (A1-C2)
            scenario_title: Title of the scenario
            learner_role: Role of the learner
            ai_role: Role of the AI
            selected_goal: Selected learning goal
            
        Returns:
            Tuple of (first_question, input_tokens, output_tokens)
        """
        goal_text = selected_goal if selected_goal else "general conversation"
        
        prompt = f"""You are an English conversation partner in a role-play scenario.

Scenario: {scenario_title}
Your role: {ai_role}
Learner's role: {learner_role}
Learning goal: {goal_text}
Proficiency level: {level}

Generate a natural first question to start the conversation. The question should:
1. Be appropriate for proficiency level {level}
2. Establish the conversation topic clearly
3. Reference the scenario context
4. Help the learner work toward the selected goal

Generate ONLY the question, no other text. Keep it to one sentence."""

        try:
            # Call Bedrock with converse API (non-streaming)
            response = self._bedrock.converse(
                modelId="apac.amazon.nova-lite-v1:0",
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={
                    "maxTokens": 100,
                    "temperature": 0.7,
                },
            )
            
            # Extract response
            first_question = ""
            for content_block in response.get("output", {}).get("message", {}).get("content", []):
                if "text" in content_block:
                    first_question += content_block["text"]
            
            # Extract token usage
            input_tokens = response.get("usage", {}).get("inputTokens", 0)
            output_tokens = response.get("usage", {}).get("outputTokens", 0)
            
            return first_question.strip(), input_tokens, output_tokens
            
        except Exception as e:
            # Use fallback first question
            logger.warning(
                "First question generation failed, using fallback",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "level": level,
                    "scenario": scenario_title,
                }
            )
            fallback = self._FALLBACK_FIRST_QUESTIONS.get(level, "What would you like to talk about?")
            return fallback, 0, 0

    def _generate_full_greeting(
        self,
        level: str,
        scenario_title: str,
        learner_role: str,
        ai_role: str,
        selected_goal: str,
        ai_character: str,
    ) -> tuple[str, str, int, int]:
        """Generate full greeting using LLM (character introduces + first question).
        
        Args:
            level: Proficiency level (A1-C2)
            scenario_title: Title of the scenario
            learner_role: Role of the learner
            ai_role: Role of the AI
            selected_goal: Selected learning goal
            ai_character: Character name (Sarah, Marco, Emma, James)
            
        Returns:
            Tuple of (greeting_text, first_question, input_tokens, output_tokens)
        """
        goal_text = selected_goal if selected_goal else "general conversation"
        
        system_prompt = f"""You are an English conversation partner in a role-play scenario.

Scenario: {scenario_title}
Your character name: {ai_character}
Your role: {ai_role}
Learner's role: {learner_role}
Learning goal: {goal_text}
Proficiency level: {level}

Generate a natural greeting where you introduce yourself and ask the first question.

Requirements:
- Be appropriate for proficiency level {level}
- Keep it SHORT and NATURAL
- Establish the scenario context clearly
- Help the learner work toward the goal

Output format (2 lines only):
[GREETING]: <greeting with character introduction>
[QUESTION]: <first question>"""

        user_prompt = "Generate the greeting and first question now."

        try:
            # Call Bedrock with Amazon Nova Lite using converse (non-streaming)
            response = self._bedrock.converse(
                modelId="apac.amazon.nova-lite-v1:0",
                system=[{"text": system_prompt}],
                messages=[{"role": "user", "content": [{"text": user_prompt}]}],
                inferenceConfig={
                    "maxTokens": 150,
                    "temperature": 0.7,
                },
            )
            
            # Extract response
            full_response = ""
            for content_block in response.get("output", {}).get("message", {}).get("content", []):
                if "text" in content_block:
                    full_response += content_block["text"]
            
            # Extract token usage
            input_tokens = response.get("usage", {}).get("inputTokens", 0)
            output_tokens = response.get("usage", {}).get("outputTokens", 0)
            
            # Parse response
            greeting_text = ""
            first_question = ""
            
            for line in full_response.split("\n"):
                line = line.strip()
                if line.startswith("[GREETING]:"):
                    greeting_text = line.replace("[GREETING]:", "").strip()
                elif line.startswith("[QUESTION]:"):
                    first_question = line.replace("[QUESTION]:", "").strip()
            
            # Fallback if parsing fails
            if not greeting_text or not first_question:
                logger.warning(
                    "Failed to parse LLM greeting response, using fallback",
                    extra={
                        "level": level,
                        "scenario": scenario_title,
                        "character": ai_character,
                        "response": full_response[:200],
                    }
                )
                greeting_text = self._FALLBACK_GREETINGS.get(level, "Hi! I'm {character}.").format(character=ai_character)
                first_question = self._FALLBACK_FIRST_QUESTIONS.get(level, "What would you like to talk about?")
            
            return greeting_text, first_question, input_tokens, output_tokens
            
        except (json.JSONDecodeError, ClientError, Exception) as e:
            # Use fallback greeting
            logger.warning(
                "Full greeting generation failed, using fallback",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "level": level,
                    "scenario": scenario_title,
                    "character": ai_character,
                }
            )
            greeting_text = self._FALLBACK_GREETINGS.get(level, "Hi! I'm {character}.").format(character=ai_character)
            first_question = self._FALLBACK_FIRST_QUESTIONS.get(level, "What would you like to talk about?")
            return greeting_text, first_question, 0, 0
