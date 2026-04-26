"""
Metrics Logger for Bedrock Conversation Quality

Handles:
- Metrics collection (TTFT, latency, tokens, model_source, fallback_reason)
- Quality metrics (markdown, delivery_cues, question_count)
- Hint metrics (hint_level, hint_count, scaffolding_effectiveness)
- CloudWatch integration
- Metrics aggregation
- Cost calculation
"""

import logging
from dataclasses import dataclass, asdict, field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class HintLevel(Enum):
    """Hint levels for scaffolding."""
    GENTLE_PROMPT = "gentle_prompt"
    VOCABULARY_HINT = "vocabulary_hint"
    SENTENCE_STARTER = "sentence_starter"


@dataclass
class QualityMetrics:
    """Quality metrics for a response."""
    
    # Format compliance
    has_markdown: bool = False  # Should be False (no markdown)
    delivery_cues_count: int = 0  # Count of delivery cues like [warmly]
    question_count: int = 0  # Number of questions in response
    
    # Response characteristics
    sentence_count: int = 0
    word_count: int = 0
    
    # Quality score (0-100)
    quality_score: float = 0.0
    
    # Compliance flags
    format_compliant: bool = True  # No markdown
    length_compliant: bool = True  # Within token limits
    has_question: bool = False  # Should have at least 1 question


@dataclass
class HintMetrics:
    """Hint usage metrics."""
    
    hint_level: Optional[str] = None  # gentle_prompt, vocabulary_hint, sentence_starter
    hint_provided: bool = False
    hint_accepted: bool = False  # Did learner use the hint?
    
    # Scaffolding effectiveness
    scaffolding_effectiveness: float = 0.0  # 0-1 scale
    hint_count_in_session: int = 0
    
    # Vietnamese detection
    vietnamese_detected: bool = False
    vietnamese_redirect_provided: bool = False
    
    # Off-topic detection
    off_topic_detected: bool = False
    off_topic_redirect_provided: bool = False


@dataclass
class ConversationMetrics:
    """Metrics for a single conversation turn."""
    
    # Timing metrics (milliseconds)
    ttft_ms: Optional[float] = None  # Time to first token
    total_latency_ms: Optional[float] = None  # Total latency
    
    # Token metrics
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    
    # Model metrics
    model_used: str = ""  # Primary model ID
    model_source: str = "primary"  # "primary" or "fallback"
    fallback_reason: Optional[str] = None  # Why fallback was used
    
    # Context metrics
    proficiency_level: str = ""  # A1-C2
    scenario_title: str = ""
    session_id: str = ""
    turn_index: int = 0
    
    # Cost metrics
    cost_usd: Optional[float] = None
    
    # Quality metrics
    response_length: int = 0  # Character count
    validation_passed: bool = True
    validation_reason: Optional[str] = None
    
    # Quality & Hint metrics (NEW)
    quality_metrics: Optional[QualityMetrics] = field(default_factory=QualityMetrics)
    hint_metrics: Optional[HintMetrics] = field(default_factory=HintMetrics)
    
    # Timestamp
    timestamp: str = ""


class MetricsLogger:
    """Logs metrics for conversation quality monitoring."""

    # Model pricing (USD per 1M tokens)
    PRICING = {
        "apac.amazon.nova-lite-v1:0": {
            "input": 0.06,
            "output": 0.24,
            "cache_read": 0.03,
            "cache_write": 0.24,
        },
        "apac.amazon.nova-pro-v1:0": {
            "input": 0.80,
            "output": 2.40,
            "cache_read": 0.40,
            "cache_write": 2.40,
        },
        # Legacy model IDs (for backward compatibility)
        "amazon.nova-lite-v1:0": {
            "input": 0.06,
            "output": 0.24,
            "cache_read": 0.03,
            "cache_write": 0.24,
        },
        "amazon.nova-pro-v1:0": {
            "input": 0.80,
            "output": 2.40,
            "cache_read": 0.40,
            "cache_write": 2.40,
        },
    }

    def __init__(self, enable_logging: bool = True, cloudwatch_client=None):
        """
        Initialize metrics logger.
        
        Args:
            enable_logging: Whether to enable metrics logging
            cloudwatch_client: Optional CloudWatch client for sending metrics
        """
        self.enable_logging = enable_logging
        self.cloudwatch_client = cloudwatch_client
        self.namespace = "Lexi/ConversationQuality"

    def create_metrics(
        self,
        ttft_ms: Optional[float] = None,
        total_latency_ms: Optional[float] = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        model_used: str = "",
        model_source: str = "primary",
        fallback_reason: Optional[str] = None,
        proficiency_level: str = "",
        scenario_title: str = "",
        session_id: str = "",
        turn_index: int = 0,
        response_length: int = 0,
        validation_passed: bool = True,
        validation_reason: Optional[str] = None,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
        quality_metrics: Optional[QualityMetrics] = None,
        hint_metrics: Optional[HintMetrics] = None,
        # Enhanced context (Fix #7)
        user_utterance_length: int = 0,
        turn_count: int = 0,
        selected_goals: Optional[list[str]] = None,
    ) -> ConversationMetrics:
        """
        Create metrics object for a conversation turn.
        
        Args:
            ttft_ms: Time to first token in milliseconds
            total_latency_ms: Total latency in milliseconds
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model_used: Model ID used
            model_source: "primary" or "fallback"
            fallback_reason: Reason for fallback (if any)
            proficiency_level: Learner proficiency level (A1-C2)
            scenario_title: Scenario title
            session_id: Session ID
            turn_index: Turn index in session
            response_length: Response length in characters
            validation_passed: Whether response passed validation
            validation_reason: Reason for validation failure (if any)
            cache_read_tokens: Tokens read from cache
            cache_write_tokens: Tokens written to cache
            quality_metrics: QualityMetrics object (optional)
            hint_metrics: HintMetrics object (optional)
            user_utterance_length: Length of user utterance (Fix #7)
            turn_count: Total turn count in session (Fix #7)
            selected_goals: Selected learning goals (Fix #7)
            
        Returns:
            ConversationMetrics object
        """
        # Calculate cost
        cost = self._calculate_cost(
            model_used,
            input_tokens,
            output_tokens,
            cache_read_tokens,
            cache_write_tokens,
        )
        
        metrics = ConversationMetrics(
            ttft_ms=ttft_ms,
            total_latency_ms=total_latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens,
            model_used=model_used,
            model_source=model_source,
            fallback_reason=fallback_reason,
            proficiency_level=proficiency_level,
            scenario_title=scenario_title,
            session_id=session_id,
            turn_index=turn_index,
            cost_usd=cost,
            response_length=response_length,
            validation_passed=validation_passed,
            validation_reason=validation_reason,
            quality_metrics=quality_metrics or QualityMetrics(),
            hint_metrics=hint_metrics or HintMetrics(),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        return metrics

    def log_metrics(self, metrics: ConversationMetrics):
        """
        Log metrics to CloudWatch and local logger.
        
        Args:
            metrics: ConversationMetrics object to log
        """
        if not self.enable_logging:
            return
        
        # Log to local logger
        logger.info(
            f"Conversation metrics: "
            f"level={metrics.proficiency_level} "
            f"model={metrics.model_used} "
            f"source={metrics.model_source} "
            f"ttft={metrics.ttft_ms:.0f}ms "
            f"latency={metrics.total_latency_ms:.0f}ms "
            f"tokens={metrics.output_tokens} "
            f"cost=${metrics.cost_usd:.4f}"
        )
        
        # Log fallback reason if applicable
        if metrics.model_source == "fallback" and metrics.fallback_reason:
            logger.warning(
                f"Fallback triggered: {metrics.fallback_reason} "
                f"(level={metrics.proficiency_level})"
            )
        
        # Log validation failure if applicable
        if not metrics.validation_passed and metrics.validation_reason:
            logger.warning(
                f"Validation failed: {metrics.validation_reason} "
                f"(level={metrics.proficiency_level})"
            )
        
        # Send to CloudWatch using EMF (Phase 6)
        # EMF is printed to stdout, CloudWatch extracts metrics asynchronously
        # Docs: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html
        self.log_metrics_emf(metrics)
        
        # Legacy CloudWatch API (optional, can be removed if EMF is sufficient)
        if self.cloudwatch_client:
            self._send_to_cloudwatch(metrics)

    def _calculate_cost(
        self,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
    ) -> float:
        """
        Calculate cost for a model invocation.
        
        Args:
            model_id: Model ID
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cache_read_tokens: Tokens read from cache
            cache_write_tokens: Tokens written to cache
            
        Returns:
            Cost in USD
        """
        pricing = self.PRICING.get(model_id)
        if not pricing:
            logger.warning(f"Unknown model for pricing: {model_id}")
            return 0.0
        
        # Calculate cost
        # Input tokens: regular input + cache write (cache write is charged at input rate)
        input_cost = input_tokens * pricing["input"] / 1_000_000
        
        # Output tokens
        output_cost = output_tokens * pricing["output"] / 1_000_000
        
        # Cache read tokens (cheaper than regular input)
        cache_read_cost = cache_read_tokens * pricing["cache_read"] / 1_000_000
        
        # Note: cache_write_tokens are already included in input_tokens
        # so we don't double-count them
        
        total_cost = input_cost + output_cost + cache_read_cost
        return total_cost

    def _send_to_cloudwatch(self, metrics: ConversationMetrics):
        """
        Send metrics to CloudWatch.
        
        Args:
            metrics: ConversationMetrics object
        """
        try:
            # Prepare metric data
            metric_data = []
            
            # TTFT metric
            if metrics.ttft_ms is not None:
                metric_data.append({
                    "MetricName": "TTFT",
                    "Value": metrics.ttft_ms,
                    "Unit": "Milliseconds",
                    "Dimensions": [
                        {"Name": "Level", "Value": metrics.proficiency_level},
                        {"Name": "ModelSource", "Value": metrics.model_source},
                    ],
                })
            
            # Total latency metric
            if metrics.total_latency_ms is not None:
                metric_data.append({
                    "MetricName": "TotalLatency",
                    "Value": metrics.total_latency_ms,
                    "Unit": "Milliseconds",
                    "Dimensions": [
                        {"Name": "Level", "Value": metrics.proficiency_level},
                        {"Name": "ModelSource", "Value": metrics.model_source},
                    ],
                })
            
            # Output tokens metric
            metric_data.append({
                "MetricName": "OutputTokens",
                "Value": metrics.output_tokens,
                "Unit": "Count",
                "Dimensions": [
                    {"Name": "Level", "Value": metrics.proficiency_level},
                    {"Name": "Model", "Value": metrics.model_used},
                ],
            })
            
            # Cost metric
            if metrics.cost_usd is not None:
                metric_data.append({
                    "MetricName": "CostPerTurn",
                    "Value": metrics.cost_usd,
                    "Unit": "None",
                    "Dimensions": [
                        {"Name": "Level", "Value": metrics.proficiency_level},
                        {"Name": "Model", "Value": metrics.model_used},
                    ],
                })
            
            # Fallback metric
            if metrics.model_source == "fallback":
                metric_data.append({
                    "MetricName": "FallbackCount",
                    "Value": 1,
                    "Unit": "Count",
                    "Dimensions": [
                        {"Name": "Level", "Value": metrics.proficiency_level},
                        {"Name": "Reason", "Value": metrics.fallback_reason or "unknown"},
                    ],
                })
            
            # Send to CloudWatch
            if metric_data:
                self.cloudwatch_client.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=metric_data,
                )
                logger.debug(f"Sent {len(metric_data)} metrics to CloudWatch")
        
        except Exception as e:
            logger.exception(f"Failed to send metrics to CloudWatch: {e}")

    def log_metrics_emf(self, metrics: ConversationMetrics):
        """
        Log metrics using EMF (Embedded Metric Format) to CloudWatch.
        
        EMF is printed to stdout as JSON. CloudWatch Logs automatically extracts
        metrics asynchronously without API calls.
        
        Docs: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html
        
        Args:
            metrics: ConversationMetrics object to log
        """
        import json
        import sys
        from datetime import datetime, timezone
        
        # Convert timestamp to milliseconds since epoch
        try:
            dt = datetime.fromisoformat(metrics.timestamp.replace('Z', '+00:00'))
            timestamp_ms = int(dt.timestamp() * 1000)
        except Exception:
            timestamp_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        
        # Build EMF JSON structure
        emf_log = {
            "_aws": {
                "Timestamp": timestamp_ms,
                "CloudWatchMetrics": [
                    {
                        "Namespace": self.namespace,
                        "Dimensions": [
                            ["Level", "ModelSource"],
                            ["Level", "Model"],
                        ],
                        "Metrics": []
                    }
                ]
            },
            # Dimensions (must be on root node)
            "Level": metrics.proficiency_level,
            "ModelSource": metrics.model_source,
            "Model": metrics.model_used,
            "SessionId": metrics.session_id,
            "TurnIndex": metrics.turn_index,
            "ScenarioTitle": metrics.scenario_title,
        }
        
        # Add metrics to MetricDefinition array
        metric_definitions = emf_log["_aws"]["CloudWatchMetrics"][0]["Metrics"]
        
        # TTFT metric
        if metrics.ttft_ms is not None:
            metric_definitions.append({
                "Name": "TTFT",
                "Unit": "Milliseconds",
                "StorageResolution": 60
            })
            emf_log["TTFT"] = float(metrics.ttft_ms)
        
        # Total latency metric
        if metrics.total_latency_ms is not None:
            metric_definitions.append({
                "Name": "TotalLatency",
                "Unit": "Milliseconds",
                "StorageResolution": 60
            })
            emf_log["TotalLatency"] = float(metrics.total_latency_ms)
        
        # Output tokens metric
        metric_definitions.append({
            "Name": "OutputTokens",
            "Unit": "Count",
            "StorageResolution": 60
        })
        emf_log["OutputTokens"] = metrics.output_tokens
        
        # Input tokens metric
        metric_definitions.append({
            "Name": "InputTokens",
            "Unit": "Count",
            "StorageResolution": 60
        })
        emf_log["InputTokens"] = metrics.input_tokens
        
        # Cache read tokens metric
        if metrics.cache_read_tokens > 0:
            metric_definitions.append({
                "Name": "CacheReadTokens",
                "Unit": "Count",
                "StorageResolution": 60
            })
            emf_log["CacheReadTokens"] = metrics.cache_read_tokens
        
        # Cost metric
        if metrics.cost_usd is not None:
            metric_definitions.append({
                "Name": "CostPerTurn",
                "Unit": "None",
                "StorageResolution": 60
            })
            emf_log["CostPerTurn"] = float(metrics.cost_usd)
        
        # Fallback count metric
        if metrics.model_source == "fallback":
            metric_definitions.append({
                "Name": "FallbackCount",
                "Unit": "Count",
                "StorageResolution": 60
            })
            emf_log["FallbackCount"] = 1
            emf_log["FallbackReason"] = metrics.fallback_reason or "unknown"
        
        # Validation failure metric
        if not metrics.validation_passed:
            metric_definitions.append({
                "Name": "ValidationFailureCount",
                "Unit": "Count",
                "StorageResolution": 60
            })
            emf_log["ValidationFailureCount"] = 1
            emf_log["ValidationReason"] = metrics.validation_reason or "unknown"
        
        # Print EMF JSON to stdout (CloudWatch extracts metrics automatically)
        print(json.dumps(emf_log), file=sys.stdout, flush=True)

    def get_metrics_dict(self, metrics: ConversationMetrics) -> dict:
        """
        Convert metrics to dictionary for serialization.
        
        Args:
            metrics: ConversationMetrics object
            
        Returns:
            Dictionary representation of metrics
        """
        return asdict(metrics)
