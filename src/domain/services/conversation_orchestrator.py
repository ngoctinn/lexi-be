"""Orchestrates conversation generation with model routing and quality validation."""

import logging
import os
from dataclasses import dataclass
from typing import Optional
import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from domain.entities.session import Session
from domain.entities.turn import Turn
from domain.services.model_router import ModelRouter
from domain.services.prompt_builder import OptimizedPromptBuilder
from domain.services.response_validator import ResponseValidator
from domain.services.metrics_logger import MetricsLogger, QualityMetrics

logger = logging.getLogger(__name__)

# AWS Best Practice: Reuse boto3 client for Lambda warm start
# Retry strategy: Exponential backoff with jitter (AWS SDK adaptive mode)
# Reference: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_limit_retries.html
_bedrock_client = None


def _get_bedrock_client():
    """
    Get or create Bedrock client with standardized retry configuration.
    
    Retry Strategy (AWS SDK Adaptive Mode):
    - max_attempts=3: 1 initial + 2 retries
    - mode=adaptive: Exponential backoff with jitter (AWS SDK built-in)
    - Jitter: Randomizes retry intervals to prevent retry storms
    - Backoff: Progressively longer intervals (e.g., 1s, 2s, 4s)
    
    Timeouts:
    - connect_timeout=5s: Max time to establish connection
    - read_timeout=30s: Max time to read response (covers LLM generation time)
    
    Reference: https://docs.aws.amazon.com/sdkref/latest/guide/feature-retry-behavior.html
    """
    global _bedrock_client
    if _bedrock_client is None:
        region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
        retry_config = Config(
            retries={
                "max_attempts": 3,  # Standardized: 1 initial + 2 retries (matches websocket_handler)
                "mode": "adaptive",  # AWS SDK adaptive mode: exponential backoff + jitter
            },
            connect_timeout=5,
            read_timeout=30,
        )
        _bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=region if region else None,
            config=retry_config
        )
    return _bedrock_client


@dataclass
class ConversationGenerationRequest:
    """Request for conversation generation."""
    
    session: Session
    user_turn: Turn
    turn_history: list[Turn]
    analysis: Optional[object] = None  # SpeakingAnalysis


@dataclass
class ConversationGenerationResponse:
    """Response from conversation generation."""
    
    ai_text: str
    delivery_cue: str
    latency_ms: Optional[float]
    input_tokens: int
    output_tokens: int
    cost_usd: float
    model_used: str
    model_source: str  # "primary" or "fallback"
    fallback_reason: Optional[str]
    validation_passed: bool
    ttft_ms: Optional[float] = None  # Time to first token (same as latency_ms for non-streaming)


class ConversationOrchestrator:
    """
    Orchestrates conversation generation with model routing and quality validation.
    
    Architecture:
    - Model Routing: Routes to appropriate model based on proficiency level (A1-C2)
    - Retry Strategy: AWS SDK adaptive mode (exponential backoff + jitter, max 3 attempts)
    - Fallback Logic: Primary → Fallback (if configured) → Default response
    - Quality Validation: Validates response against level-specific rules
    - Metrics Logging: Tracks latency, tokens, cost, fallback rate
    
    Resilience Patterns:
    1. Exponential Backoff: AWS SDK automatically retries with increasing intervals
    2. Jitter: Randomizes retry intervals to prevent retry storms
    3. Fallback Model: C1-C2 levels have Pro fallback (A1-B2 use default response)
    4. Default Response: Graceful degradation when all models fail
    
    AWS Best Practices:
    - Reuse Bedrock client across Lambda invocations (warm start optimization)
    - Use inference profiles for cross-region support (apac.amazon.nova-*)
    - Limit max retries to prevent metastable failures
    - Log errors with context for debugging
    
    References:
    - Retry Best Practices: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_limit_retries.html
    - AWS SDK Retry Behavior: https://docs.aws.amazon.com/sdkref/latest/guide/feature-retry-behavior.html
    """
    
    def __init__(
        self,
        model_router: ModelRouter,
        response_validator: ResponseValidator,
        metrics_logger: MetricsLogger,
        bedrock_client=None,
    ):
        """
        Initialize conversation orchestrator.
        
        Args:
            model_router: Routes to appropriate model based on level
            response_validator: Validates response quality
            metrics_logger: Logs metrics
            bedrock_client: AWS Bedrock client (optional, uses default if not provided)
        """
        self.model_router = model_router
        self.response_validator = response_validator
        self.metrics_logger = metrics_logger
        self.bedrock_client = bedrock_client or _get_bedrock_client()
    
    def generate_response(
        self,
        request: ConversationGenerationRequest,
    ) -> ConversationGenerationResponse:
        """
        Generate AI response with model routing and validation.
        
        Args:
            request: ConversationGenerationRequest
            
        Returns:
            ConversationGenerationResponse with metrics
        """
        import time
        
        session = request.session
        user_turn = request.user_turn
        start_time = time.time()
        
        # Step 1: Route to appropriate model
        level_str = session.level.value if hasattr(session.level, "value") else str(session.level)
        routing = self.model_router.get_config(level_str)
        
        # Step 2: Build optimized prompt
        base_prompt = OptimizedPromptBuilder.build(
            scenario_title=session.scenario_title,
            learner_role=session.learner_role_id,
            ai_role=session.ai_role_id,
            level=session.level,
            selected_goal=session.selected_goal,
            ai_character=session.ai_character,
        )
        
        system_prompt = base_prompt
        
        # Step 3: Generate response with non-streaming API
        # Fallback Strategy:
        # 1. Try primary model (with AWS SDK auto-retry: exponential backoff + jitter)
        # 2. If primary fails after retries → try fallback model (if configured)
        # 3. If fallback also fails → use default response
        # Note: A1-B2 levels have no fallback model (fallback_model=None)
        try:
            response_data = self._invoke_model(
                model_id=routing.primary_model,
                system_prompt=system_prompt,
                user_message=user_turn.content,
                max_tokens=routing.max_tokens,
                temperature=routing.temperature,
            )
            
            ai_text = response_data.get("text", "")
            latency_ms = response_data.get("latency_ms")
            input_tokens = response_data.get("input_tokens", 0)
            output_tokens = response_data.get("output_tokens", 0)
            model_source = "primary"
            fallback_reason = None
            
        except Exception as e:
            logger.error(f"Primary model failed: {e}")
            
            # Check if fallback model is available
            if routing.fallback_model is None:
                logger.warning(f"No fallback model configured for level {level_str}, using default response")
                # Use default response
                ai_text = "Thanks. Could you say a bit more about that?"
                latency_ms = (time.time() - start_time) * 1000
                input_tokens = 0
                output_tokens = 0
                model_source = "fallback"
                fallback_reason = f"Primary model failed: {str(e)}, no fallback configured"
            else:
                # Fallback to fallback model
                try:
                    logger.info(f"Attempting fallback model: {routing.fallback_model}")
                    response_data = self._invoke_model(
                        model_id=routing.fallback_model,
                        system_prompt=system_prompt,
                        user_message=user_turn.content,
                        max_tokens=routing.max_tokens,
                        temperature=routing.temperature,
                    )
                    
                    ai_text = response_data.get("text", "")
                    latency_ms = response_data.get("latency_ms")
                    input_tokens = response_data.get("input_tokens", 0)
                    output_tokens = response_data.get("output_tokens", 0)
                    model_source = "fallback"
                    fallback_reason = str(e)
                    
                except Exception as fallback_error:
                    logger.error(f"Fallback model also failed: {fallback_error}")
                    # Use default response
                    ai_text = "Thanks. Could you say a bit more about that?"
                    latency_ms = (time.time() - start_time) * 1000
                    input_tokens = 0
                    output_tokens = 0
                    model_source = "fallback"
                    fallback_reason = str(fallback_error)
        
        # Step 4: Validate response quality
        level_str = session.level.value if hasattr(session.level, "value") else str(session.level)
        validation_result = self.response_validator.validate(
            response=ai_text,
            level=level_str,
        )
        validation_passed = validation_result.is_valid
        validation_reason = validation_result.reason if not validation_result.is_valid else None
        
        # Step 5: Extract delivery cue from response
        delivery_cue = self._extract_delivery_cue(ai_text)
        
        # Step 6: Calculate cost
        cost_usd = self.metrics_logger._calculate_cost(
            model_id=routing.primary_model if model_source == "primary" else routing.fallback_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        
        # Step 7: Log metrics
        # Convert level to string for JSON serialization
        level_str_for_metrics = session.level.value if hasattr(session.level, "value") else str(session.level)
        
        metrics = self.metrics_logger.create_metrics(
            total_latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model_used=routing.primary_model if model_source == "primary" else routing.fallback_model,
            model_source=model_source,
            fallback_reason=fallback_reason,
            proficiency_level=level_str_for_metrics,
            scenario_title=session.scenario_title,
            session_id=session.session_id,
            turn_index=user_turn.turn_index,
            response_length=len(ai_text),
            validation_passed=validation_passed,
            validation_reason=validation_reason,
            user_utterance_length=len(user_turn.content),
            turn_count=len(request.turn_history),
            selected_goals=[session.selected_goal] if session.selected_goal else [],
        )
        
        self.metrics_logger.log_metrics(metrics)
        
        return ConversationGenerationResponse(
            ai_text=ai_text,
            delivery_cue=delivery_cue,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            model_used=routing.primary_model if model_source == "primary" else routing.fallback_model,
            model_source=model_source,
            fallback_reason=fallback_reason,
            validation_passed=validation_passed,
            ttft_ms=latency_ms,  # For non-streaming, TTFT = total latency
        )
    
    def _invoke_model(
        self,
        model_id: str,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> dict:
        """
        Invoke Bedrock model using the Converse API (AWS best practice).

        The Converse API provides a unified interface across all models with a
        standardized response format - no manual JSON parsing needed.

        Reference: https://docs.aws.amazon.com/nova/latest/userguide/using-converse-api.html
        """
        import time

        start_time = time.time()

        messages = [{"role": "user", "content": [{"text": user_message}]}]
        system = [{"text": system_prompt}] if system_prompt else []

        try:
            response = self.bedrock_client.converse(
                modelId=model_id,
                messages=messages,
                system=system,
                inferenceConfig={
                    "maxTokens": max_tokens,
                    "temperature": temperature,
                },
            )

            # Converse API: standardized response format for all models
            # Reference: https://docs.aws.amazon.com/nova/latest/userguide/using-converse-api.html
            response_text = response["output"]["message"]["content"][0]["text"]
            usage = response.get("usage", {})
            input_tokens = usage.get("inputTokens", 0)
            output_tokens = usage.get("outputTokens", 0)
            latency_ms = (time.time() - start_time) * 1000

            return {
                "text": response_text,
                "latency_ms": latency_ms,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }

        except (ClientError, BotoCoreError) as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown") if hasattr(e, "response") else "Unknown"
            logger.error(
                f"Bedrock Converse API error after retries: {error_code}",
                extra={
                    "model_id": model_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
            )
            raise
    
    def _extract_delivery_cue(self, response: str) -> str:
        """
        Extract delivery cue from START of response only.
        
        Args:
            response: Response text with potential delivery cue
            
        Returns:
            Delivery cue (e.g., "[warmly]") or empty string
        """
        import re
        # Only match at start of string
        match = re.match(r"^\[([a-zA-Z\s]+)\]", response.strip())
        if match:
            return f"[{match.group(1)}]"
        return ""
    
    def _clean_text_for_tts(self, text: str) -> str:
        """
        Remove delivery cues from text for TTS synthesis.
        
        Args:
            text: Text with potential delivery cues
            
        Returns:
            Clean text without delivery cues
        """
        import re
        # Remove delivery cues like [warmly], [thoughtfully], etc.
        cleaned = re.sub(r"\[([a-zA-Z\s]+)\]\s*", "", text)
        return cleaned.strip()
