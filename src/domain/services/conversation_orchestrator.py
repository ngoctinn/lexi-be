"""Orchestrates conversation generation with model routing, streaming, and quality validation."""

from dataclasses import dataclass
from typing import Optional
from domain.entities.session import Session
from domain.entities.turn import Turn
from domain.services.model_router import ModelRouter
from domain.services.prompt_builder import OptimizedPromptBuilder
from domain.services.streaming_response import StreamingResponse
from domain.services.response_validator import ResponseValidator
from domain.services.metrics_logger import MetricsLogger, QualityMetrics
from domain.services.scaffolding_system import ScaffoldingSystem


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
    ttft_ms: Optional[float]
    latency_ms: Optional[float]
    input_tokens: int
    output_tokens: int
    cost_usd: float
    model_used: str
    model_source: str  # "primary" or "fallback"
    fallback_reason: Optional[str]
    validation_passed: bool


class ConversationOrchestrator:
    """Orchestrates conversation generation with all new features."""
    
    def __init__(
        self,
        model_router: ModelRouter,
        prompt_builder: OptimizedPromptBuilder,
        streaming_response: StreamingResponse,
        response_validator: ResponseValidator,
        metrics_logger: MetricsLogger,
        scaffolding_system: ScaffoldingSystem,
        bedrock_client=None,
    ):
        """
        Initialize conversation orchestrator.
        
        Args:
            model_router: Routes to appropriate model based on level
            prompt_builder: Builds optimized prompts (OptimizedPromptBuilder)
            streaming_response: Handles streaming responses
            response_validator: Validates response quality
            metrics_logger: Logs metrics
            scaffolding_system: Provides hints and scaffolding
            bedrock_client: AWS Bedrock client
        """
        self.model_router = model_router
        self.prompt_builder = prompt_builder
        self.streaming_response = streaming_response
        self.response_validator = response_validator
        self.metrics_logger = metrics_logger
        self.scaffolding_system = scaffolding_system
        self.bedrock_client = bedrock_client
    
    def generate_response(
        self,
        request: ConversationGenerationRequest,
    ) -> ConversationGenerationResponse:
        """
        Generate AI response with all optimizations.
        
        Args:
            request: ConversationGenerationRequest
            
        Returns:
            ConversationGenerationResponse with metrics
        """
        session = request.session
        user_turn = request.user_turn
        
        # Step 1: Route to appropriate model
        level_str = session.level.value if hasattr(session.level, "value") else str(session.level)
        routing = self.model_router.get_config(level_str)
        
        # Step 2: Build optimized prompt
        prompt = self.prompt_builder.build(
            scenario_title=session.scenario_id,
            learner_role=session.learner_role_id,
            ai_role=session.ai_role_id,
            level=session.level,
            selected_goals=session.selected_goals,
            ai_gender=session.ai_gender,
        )
        
        # Step 3: Generate response with streaming
        try:
            response_data = self.streaming_response.invoke_with_streaming(
                model_id=routing.primary_model,
                system_prompt=prompt,
                user_message=user_turn.content,
                max_tokens=routing.max_tokens,
                temperature=routing.temperature,
            )
            
            ai_text = response_data.get("text", "")
            ttft_ms = response_data.get("ttft_ms")
            latency_ms = response_data.get("latency_ms")
            input_tokens = response_data.get("input_tokens", 0)
            output_tokens = response_data.get("output_tokens", 0)
            model_source = "primary"
            fallback_reason = None
            
        except Exception as e:
            # Fallback to sync mode or fallback model
            ai_text = "Thanks. Could you say a bit more about that?"
            ttft_ms = None
            latency_ms = None
            input_tokens = 0
            output_tokens = 0
            model_source = "fallback"
            fallback_reason = str(e)
        
        # Step 4: Validate response quality
        level_str = session.level.value if hasattr(session.level, "value") else str(session.level)
        validation_result = self.response_validator.validate(
            response=ai_text,
            level=level_str,
        )
        validation_passed = validation_result.is_valid
        
        # If validation fails, use fallback model
        if not validation_passed and model_source == "primary":
            try:
                response_data = self.streaming_response.invoke_with_streaming(
                    model_id=routing.fallback_model,
                    system_prompt=prompt,
                    user_message=user_turn.content,
                    max_tokens=routing.max_tokens,
                    temperature=routing.temperature,
                )
                
                ai_text = response_data.get("text", "")
                output_tokens = response_data.get("output_tokens", 0)
                model_source = "fallback"
                fallback_reason = "validation_failed"
                validation_passed = True
                
            except Exception:
                pass  # Keep original response
        
        # Step 5: Extract delivery cue from response
        delivery_cue = self._extract_delivery_cue(ai_text)
        
        # Step 6: Calculate cost
        cost_usd = self.metrics_logger._calculate_cost(
            model_id=routing.primary_model if model_source == "primary" else routing.fallback_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        
        # Step 7: Log metrics (without per-turn quality scoring)
        metrics = self.metrics_logger.create_metrics(
            ttft_ms=ttft_ms,
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
        )
        
        self.metrics_logger.log_metrics(metrics)
        
        return ConversationGenerationResponse(
            ai_text=ai_text,
            delivery_cue=delivery_cue,
            ttft_ms=ttft_ms,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            model_used=routing.primary_model if model_source == "primary" else routing.fallback_model,
            model_source=model_source,
            fallback_reason=fallback_reason,
            validation_passed=validation_passed,
        )
    
    def _extract_delivery_cue(self, response: str) -> str:
        """
        Extract delivery cue from response and return clean text.
        
        Args:
            response: Response text with potential delivery cue
            
        Returns:
            Delivery cue (e.g., "[warmly]") or empty string
        """
        import re
        match = re.search(r"\[([a-zA-Z\s]+)\]", response)
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
    
    def get_hint(
        self,
        session: Session,
        scenario: "Scenario",
        turn_history: list[Turn],
        silence_duration_seconds: int,
    ) -> Optional[str]:
        """
        Get hint for learner based on silence duration with context.
        
        Args:
            session: Current session
            scenario: Current scenario
            turn_history: List of turns in session
            silence_duration_seconds: Duration of silence (10, 20, or 30)
            
        Returns:
            Hint text or None
        """
        # Only provide hints for A1-A2 levels
        level_str = session.level.value if hasattr(session.level, "value") else str(session.level)
        if level_str not in ["A1", "A2"]:
            return None
        
        # Extract context for scaffolding
        from application.use_cases.speaking_session_use_cases import _extract_scaffolding_context
        context = _extract_scaffolding_context(session, scenario, turn_history)
        
        # Generate hint with context
        hint = self.scaffolding_system.generate_hint(
            proficiency_level=level_str,
            silence_duration_seconds=silence_duration_seconds,
            context=context,
        )
        
        if hint:
            return self.scaffolding_system.format_hint_for_display(hint)
        
        return None
