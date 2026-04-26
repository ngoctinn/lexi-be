"""Orchestrates conversation generation with model routing and quality validation."""

import logging
import json
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

# Reuse boto3 client for Lambda warm start
_bedrock_client = None


def _get_bedrock_client():
    global _bedrock_client
    if _bedrock_client is None:
        region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
        retry_config = Config(
            retries={"max_attempts": 2, "mode": "adaptive"},
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


class ConversationOrchestrator:
    """Orchestrates conversation generation with model routing and quality validation."""
    
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
            scenario_title=session.scenario_id,
            learner_role=session.learner_role_id,
            ai_role=session.ai_role_id,
            level=session.level,
            selected_goal=session.selected_goal,
            ai_character=session.ai_character,
        )
        
        system_prompt = base_prompt
        
        # Step 3: Generate response with non-streaming API
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
            # Fallback to fallback model
            try:
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
        
        # Step 5: Extract delivery cue from response
        delivery_cue = self._extract_delivery_cue(ai_text)
        
        # Step 6: Calculate cost
        cost_usd = self.metrics_logger._calculate_cost(
            model_id=routing.primary_model if model_source == "primary" else routing.fallback_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        
        # Step 7: Log metrics
        metrics = self.metrics_logger.create_metrics(
            total_latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model_used=routing.primary_model if model_source == "primary" else routing.fallback_model,
            model_source=model_source,
            fallback_reason=fallback_reason,
            proficiency_level=session.level,
            scenario_title=session.scenario_id,
            session_id=session.session_id,
            turn_index=user_turn.turn_index,
            response_length=len(ai_text),
            validation_passed=validation_passed,
            user_utterance_length=len(user_turn.content),
            turn_count=len(request.turn_history),
            selected_goal=session.selected_goal,
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
        Invoke Bedrock model with non-streaming API.
        
        Args:
            model_id: Bedrock model ID
            system_prompt: System prompt
            user_message: User message
            max_tokens: Maximum tokens to generate
            temperature: Temperature for sampling
            
        Returns:
            Dict with keys: text, latency_ms, input_tokens, output_tokens
        """
        import time
        
        start_time = time.time()
        
        # Detect model family and build appropriate request format
        if "nova" in model_id.lower():
            # Amazon Nova format
            native_request = {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": user_message}],
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": max_tokens,
                    "temperature": temperature,
                }
            }
            
            # Add system prompt
            if system_prompt:
                if isinstance(system_prompt, str):
                    native_request["system"] = [{"text": system_prompt}]
                elif isinstance(system_prompt, list):
                    native_request["system"] = [
                        {"text": block["text"]} for block in system_prompt if "text" in block
                    ]
        else:
            # Anthropic Claude format (fallback)
            native_request = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": user_message}],
                    }
                ],
            }
            
            # Add system prompt
            if system_prompt:
                native_request["system"] = system_prompt
        
        # Convert to JSON
        request_body = json.dumps(native_request)
        
        try:
            # Invoke model (non-streaming)
            # AWS best practice: Add performanceConfig for latency optimization
            response = self.bedrock_client.invoke_model(
                modelId=model_id,
                body=request_body,
                performanceConfig={
                    "latency": "optimized"  # AWS best practice: 20-30% latency reduction
                },
            )
            
            # Parse response
            response_body = json.loads(response["body"].read())
            
            # Extract text based on model format
            response_text = ""
            input_tokens = 0
            output_tokens = 0
            
            if "nova" in model_id.lower():
                # Nova format
                if "content" in response_body:
                    for block in response_body["content"]:
                        if "text" in block:
                            response_text += block["text"]
                
                # Extract token counts
                if "usage" in response_body:
                    input_tokens = response_body["usage"].get("inputTokens", 0)
                    output_tokens = response_body["usage"].get("outputTokens", 0)
            else:
                # Claude format
                if "content" in response_body:
                    for block in response_body["content"]:
                        if "text" in block:
                            response_text += block["text"]
                
                # Extract token counts
                if "usage" in response_body:
                    input_tokens = response_body["usage"].get("input_tokens", 0)
                    output_tokens = response_body["usage"].get("output_tokens", 0)
            
            latency_ms = (time.time() - start_time) * 1000
            
            return {
                "text": response_text,
                "latency_ms": latency_ms,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Bedrock API error: {e}")
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
