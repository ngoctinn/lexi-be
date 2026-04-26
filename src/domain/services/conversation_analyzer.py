"""
Conversation Analyzer - Analyzes learner turns for formative assessment.

Provides turn-by-turn feedback with:
- Mistakes (⚠️): Grammar, vocabulary, or usage errors with formatting
- Improvements (💡): Suggestions for better expression
"""

import json
import logging
import time
from dataclasses import dataclass
from botocore.exceptions import ClientError
from domain.services.prompt_validator import validate_conversation_analyzer_response, log_validation_errors

logger = logging.getLogger(__name__)


@dataclass
class TurnAnalysis:
    """Analysis result for a single turn."""

    markdown_vi: str  # Vietnamese markdown
    markdown_en: str  # English markdown
    strengths: list[str]
    mistakes: list[str]
    improvements: list[str]
    overall_assessment: str


class ConversationAnalyzer:
    """Analyzes learner conversation turns using LLM."""

    def __init__(self, bedrock_client=None):
        self.bedrock_client = bedrock_client
        self._model_id = "apac.amazon.nova-lite-v1:0"

    def analyze_turn(
        self,
        learner_message: str,
        ai_response: str,
        level: str,
        scenario_context: str,
    ) -> TurnAnalysis:
        if not self.bedrock_client:
            raise ValueError("bedrock_client is required")

        system_prompt = self._build_system_prompt(level, scenario_context)
        user_prompt = self._build_user_prompt(learner_message, ai_response, level)

        # Define JSON schema for structured output (Nova best practice)
        tool_config = {
            "tools": [
                {
                    "toolSpec": {
                        "name": "TurnAnalysis",
                        "description": "Analyze learner's English turn with bilingual feedback",
                        "inputSchema": {
                            "json": {
                                "type": "object",
                                "properties": {
                                    "mistakes_vi": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Mistakes in Vietnamese (explanation) with English examples"
                                    },
                                    "mistakes_en": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Mistakes in English (explanation) with English examples"
                                    },
                                    "improvements_vi": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Improvements in Vietnamese (explanation) with English examples"
                                    },
                                    "improvements_en": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Improvements in English (explanation) with English examples"
                                    }
                                },
                                "required": []  # All fields optional (no mistakes = empty arrays)
                            }
                        }
                    }
                }
            ],
            "toolChoice": {
                "tool": {
                    "name": "TurnAnalysis"
                }
            }
        }

        # Retry logic for transient Bedrock errors
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                # Use Converse API with structured output (Nova best practice)
                # Reference: https://docs.aws.amazon.com/bedrock/latest/userguide/structured-output.html
                # AWS best practices:
                # - temperature=0 for structured output (greedy decoding)
                # - performanceConfig.latency="optimized" for 20-30% latency reduction
                response = self.bedrock_client.converse_stream(
                    modelId=self._model_id,
                    system=[{"text": system_prompt}],
                    messages=[{"role": "user", "content": [{"text": user_prompt}]}],
                    toolConfig=tool_config,
                    inferenceConfig={
                        "maxTokens": 500,
                        "temperature": 0,
                    },
                    performanceConfig={
                        "latency": "optimized"  # AWS best practice: 20-30% latency reduction
                    },
                )

                # Collect streamed response
                input_tokens = 0
                output_tokens = 0
                tool_use_data = None
                
                for event in response["stream"]:
                    # Handle tool use (structured output)
                    if "contentBlockStart" in event:
                        start = event["contentBlockStart"]
                        if "toolUse" in start.get("start", {}):
                            tool_use_data = start["start"]["toolUse"]
                    
                    if "contentBlockDelta" in event:
                        delta = event["contentBlockDelta"].get("delta", {})
                        if "toolUse" in delta:
                            # Accumulate tool input
                            if tool_use_data is None:
                                tool_use_data = {}
                            if "input" not in tool_use_data:
                                tool_use_data["input"] = ""
                            tool_use_data["input"] += delta["toolUse"].get("input", "")
                    
                    # Extract token usage from metadata
                    if "metadata" in event:
                        usage = event["metadata"].get("usage", {})
                        input_tokens = usage.get("inputTokens", input_tokens)
                        output_tokens = usage.get("outputTokens", output_tokens)

                # Parse tool use input as JSON
                if tool_use_data and "input" in tool_use_data:
                    data = json.loads(tool_use_data["input"])
                else:
                    raise ValueError("No tool use data received from Bedrock")

                # Validate response structure and content
                is_valid, validation_errors = validate_conversation_analyzer_response(data)
                if not is_valid:
                    log_validation_errors(validation_errors, "conversation_analyzer response")
                    logger.warning(
                        "Response validation failed but continuing with response",
                        extra={
                            "error_count": len(validation_errors),
                            "learner_message": learner_message[:100],
                        }
                    )

                # Extract bilingual content from LLM
                mistakes_vi = data.get("mistakes_vi", [])
                mistakes_en = data.get("mistakes_en", [])
                improvements_vi = data.get("improvements_vi", [])
                improvements_en = data.get("improvements_en", [])

                # Format markdown with proper styling
                markdown_vi = self._format_markdown_vi(mistakes_vi, improvements_vi)
                markdown_en = self._format_markdown_en(mistakes_en, improvements_en)

                return TurnAnalysis(
                    markdown_vi=markdown_vi,
                    markdown_en=markdown_en,
                    strengths=[],
                    mistakes=mistakes_vi,
                    improvements=improvements_vi,
                    overall_assessment="",
                )

            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to parse analysis JSON (attempt {attempt + 1}/{max_retries + 1}): {e}",
                    extra={
                        "attempt": attempt + 1,
                        "max_retries": max_retries + 1,
                        "error_type": "json_decode_error",
                    }
                )
                # JSON errors are permanent, don't retry
                return self._fallback_analysis()

            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                error_message = e.response.get("Error", {}).get("Message", str(e))

                # Retry on transient errors
                if error_code in ["ThrottlingException", "ServiceUnavailableException", "InternalServerException"]:
                    if attempt < max_retries:
                        backoff = 2 ** attempt  # Exponential backoff: 1s, 2s
                        logger.warning(
                            f"Bedrock transient error (attempt {attempt + 1}/{max_retries + 1}), retrying in {backoff}s",
                            extra={
                                "error_code": error_code,
                                "error_message": error_message,
                                "attempt": attempt + 1,
                                "max_retries": max_retries + 1,
                                "backoff_seconds": backoff,
                            }
                        )
                        time.sleep(backoff)
                        continue

                # Permanent errors or max retries exhausted
                logger.error(
                    f"Bedrock API error (attempt {attempt + 1}/{max_retries + 1}): {error_code}",
                    extra={
                        "error_code": error_code,
                        "error_message": error_message,
                        "attempt": attempt + 1,
                        "max_retries": max_retries + 1,
                    }
                )
                return self._fallback_analysis()

            except Exception as e:
                logger.exception(
                    f"Unexpected error during analysis (attempt {attempt + 1}/{max_retries + 1}): {e}",
                    extra={
                        "attempt": attempt + 1,
                        "max_retries": max_retries + 1,
                        "error_type": type(e).__name__,
                    }
                )
                return self._fallback_analysis()

    def _build_system_prompt(self, level: str, scenario_context: str) -> str:
        level_guidance = {
            "A1": "Focus on basic errors: vocabulary, verb tense, simple sentence structure.",
            "A2": "Focus on common errors: tense, prepositions, sentence structure.",
            "B1": "Focus on errors affecting clarity: tense, prepositions, connectors.",
            "B2": "Focus on fluency errors: precise vocabulary, complex structures.",
            "C1": "Focus on subtle errors: style, nuance, expression.",
            "C2": "Focus on mastery errors: nuance, register, idiom.",
        }

        return f"""You are an English teacher analyzing errors from Vietnamese learners.

Context: {scenario_context}
Level: {level}
Guidance: {level_guidance.get(level, level_guidance["B1"])}

TASK: Analyze errors and suggest improvements
- EXPLAIN in Vietnamese (so learner understands)
- EXAMPLES/CORRECTIONS ALWAYS in English (so learner learns correctly)
- NEVER translate English sentences to Vietnamese

GOLDEN RULES:
- Each mistake: show wrong phrase (English), explain why (Vietnamese)
- Each improvement: show better way (English), explain why better (Vietnamese)
- Maximum 2-3 mistakes, 2-3 improvements
- Return ONLY valid JSON, no markdown wrapper"""

    def _build_user_prompt(self, learner_message: str, ai_response: str, level: str) -> str:
        """Build user prompt with few-shot examples.
        
        AWS best practice: Few-shot prompting improves accuracy and consistency.
        Reference: https://docs.aws.amazon.com/nova/latest/userguide/prompting-examples.html
        """
        # Few-shot examples (diverse: basic, intermediate, advanced)
        examples = [
            {
                "input": 'Learner: "I go to school yesterday" | Level: A1',
                "output": """{
  "mistakes_vi": ["Bạn nhầm lẫn ở ~~go~~ (hiện tại), nên sửa thành **went** (quá khứ)\\n\\nVì khi có 'yesterday' thì động từ phải ở dạng quá khứ. Dùng **past simple** cho sự kiện đã xảy ra."],
  "mistakes_en": ["You mixed up ~~go~~ (present), should be **went** (past)\\n\\nBecause when you have 'yesterday', the verb needs past tense. Use **past simple** for completed actions."],
  "improvements_vi": [],
  "improvements_en": []
}"""
            },
            {
                "input": 'Learner: "I like drink coffee" | Level: A2',
                "output": """{
  "mistakes_vi": ["Bạn nhầm lẫn ở ~~drink~~, nên sửa thành **drinking**\\n\\nVì sau 'like' cần dùng gerund (V-ing): **like + V-ing**. Ví dụ: like drinking, like playing."],
  "mistakes_en": ["You mixed up ~~drink~~, should be **drinking**\\n\\nBecause after 'like' you need gerund (V-ing): **like + V-ing**. Examples: like drinking, like playing."],
  "improvements_vi": [],
  "improvements_en": []
}"""
            }
        ]

        prompt = f"""Learner message: "{learner_message}"
AI response: "{ai_response}"
Level: {level}

EXAMPLES (few-shot):
Example 1: {examples[0]['input']}
Output: {examples[0]['output']}

Example 2: {examples[1]['input']}
Output: {examples[1]['output']}

NOW, analyze this learner message:
Learner: "{learner_message}" | Level: {level}

Return ONLY the JSON object (no preamble, no markdown wrapper)."""

        return prompt

    def _format_markdown_vi(self, mistakes: list[str], improvements: list[str]) -> str:
        sections = []

        if mistakes:
            for mistake in mistakes:
                sections.append(f"⚠️ {mistake}\n")
        
        if improvements:
            for improvement in improvements:
                sections.append(f"💡 {improvement}\n")

        return "".join(sections) if sections else "Không có phân tích nào."

    def _format_markdown_en(self, mistakes: list[str], improvements: list[str]) -> str:
        sections = []

        if mistakes:
            for mistake in mistakes:
                sections.append(f"⚠️ {mistake}\n")
        
        if improvements:
            for improvement in improvements:
                sections.append(f"💡 {improvement}\n")

        return "".join(sections) if sections else "No analysis available."

    def _fallback_analysis(self) -> TurnAnalysis:
        fallback_vi = "💡 Hệ thống phân tích đang gặp sự cố tạm thời. Vui lòng thử lại sau vài giây."
        fallback_en = "💡 Analysis system is temporarily unavailable. Please try again in a few seconds."

        return TurnAnalysis(
            markdown_vi=fallback_vi,
            markdown_en=fallback_en,
            strengths=[],
            mistakes=[],
            improvements=[],
            overall_assessment="",
        )
