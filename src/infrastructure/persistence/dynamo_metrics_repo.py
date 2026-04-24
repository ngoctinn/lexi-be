"""DynamoDB repository for conversation metrics."""

import os
import logging
from datetime import datetime, timezone
from typing import List, Optional
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

from domain.services.metrics_logger import ConversationMetrics, QualityMetrics, HintMetrics

logger = logging.getLogger(__name__)


class MetricsRepository:
    """Stores and retrieves conversation metrics from DynamoDB."""

    def __init__(self, table=None):
        """
        Initialize metrics repository.
        
        Args:
            table: Optional DynamoDB table resource (for testing)
        """
        self._table = table or boto3.resource("dynamodb").Table(
            os.environ.get("LEXI_TABLE_NAME", "Lexi")
        )

    def save_metrics(self, metrics: ConversationMetrics) -> None:
        """
        Save metrics to DynamoDB.
        
        Args:
            metrics: ConversationMetrics object to save
        """
        try:
            item = self._metrics_to_item(metrics)
            self._table.put_item(Item=item)
            logger.debug(
                f"Saved metrics: session={metrics.session_id} "
                f"turn={metrics.turn_index} cost=${metrics.cost_usd:.4f}"
            )
        except Exception as e:
            logger.exception(f"Failed to save metrics: {e}")
            raise

    def get_metrics_by_session(
        self,
        session_id: str,
        limit: int = 100,
    ) -> List[ConversationMetrics]:
        """
        Get all metrics for a session.
        
        Args:
            session_id: Session ID
            limit: Maximum number of items to return
            
        Returns:
            List of ConversationMetrics
        """
        try:
            response = self._table.query(
                IndexName="GSI1-SessionMetrics",
                KeyConditionExpression=Key("GSI1PK").eq(f"SESSION#{session_id}"),
                ScanIndexForward=False,  # Most recent first
                Limit=limit,
            )
            
            metrics_list = []
            for item in response.get("Items", []):
                try:
                    metrics = self._item_to_metrics(item)
                    metrics_list.append(metrics)
                except Exception as e:
                    logger.warning(f"Failed to parse metrics item: {e}")
                    continue
            
            return metrics_list
        except Exception as e:
            logger.exception(f"Failed to get metrics for session {session_id}: {e}")
            return []

    def get_metrics_by_level(
        self,
        proficiency_level: str,
        limit: int = 100,
    ) -> List[ConversationMetrics]:
        """
        Get metrics for a proficiency level.
        
        Args:
            proficiency_level: Proficiency level (A1-C2)
            limit: Maximum number of items to return
            
        Returns:
            List of ConversationMetrics
        """
        try:
            response = self._table.query(
                IndexName="GSI2-LevelMetrics",
                KeyConditionExpression=Key("GSI2PK").eq(f"LEVEL#{proficiency_level}"),
                ScanIndexForward=False,  # Most recent first
                Limit=limit,
            )
            
            metrics_list = []
            for item in response.get("Items", []):
                try:
                    metrics = self._item_to_metrics(item)
                    metrics_list.append(metrics)
                except Exception as e:
                    logger.warning(f"Failed to parse metrics item: {e}")
                    continue
            
            return metrics_list
        except Exception as e:
            logger.exception(f"Failed to get metrics for level {proficiency_level}: {e}")
            return []

    def _metrics_to_item(self, metrics: ConversationMetrics) -> dict:
        """
        Convert ConversationMetrics to DynamoDB item.
        
        Args:
            metrics: ConversationMetrics object
            
        Returns:
            Dictionary for DynamoDB put_item
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        
        item = {
            "PK": f"METRICS#{metrics.session_id}#{metrics.turn_index}",
            "SK": f"TURN#{timestamp}",
            "GSI1PK": f"SESSION#{metrics.session_id}",
            "GSI1SK": timestamp,
            "GSI2PK": f"LEVEL#{metrics.proficiency_level}",
            "GSI2SK": timestamp,
            "EntityType": "METRICS",
            
            # Timing
            "ttft_ms": Decimal(str(metrics.ttft_ms)) if metrics.ttft_ms else None,
            "total_latency_ms": Decimal(str(metrics.total_latency_ms)) if metrics.total_latency_ms else None,
            
            # Tokens
            "input_tokens": metrics.input_tokens,
            "output_tokens": metrics.output_tokens,
            "cache_read_tokens": metrics.cache_read_tokens,
            "cache_write_tokens": metrics.cache_write_tokens,
            
            # Model
            "model_used": metrics.model_used,
            "model_source": metrics.model_source,
            "fallback_reason": metrics.fallback_reason,
            
            # Context
            "proficiency_level": metrics.proficiency_level,
            "scenario_title": metrics.scenario_title,
            "session_id": metrics.session_id,
            "turn_index": metrics.turn_index,
            
            # Cost
            "cost_usd": Decimal(str(metrics.cost_usd)) if metrics.cost_usd else Decimal("0"),
            
            # Validation
            "response_length": metrics.response_length,
            "validation_passed": metrics.validation_passed,
            "validation_reason": metrics.validation_reason,
            
            # Timestamp
            "timestamp": timestamp,
        }
        
        # Add quality metrics if present
        if metrics.quality_metrics:
            qm = metrics.quality_metrics
            item.update({
                "quality_has_markdown": qm.has_markdown,
                "quality_delivery_cues_count": qm.delivery_cues_count,
                "quality_question_count": qm.question_count,
                "quality_sentence_count": qm.sentence_count,
                "quality_word_count": qm.word_count,
                "quality_score": Decimal(str(qm.quality_score)),
                "quality_format_compliant": qm.format_compliant,
                "quality_length_compliant": qm.length_compliant,
                "quality_has_question": qm.has_question,
            })
        
        # Add hint metrics if present
        if metrics.hint_metrics:
            hm = metrics.hint_metrics
            item.update({
                "hint_level": hm.hint_level,
                "hint_provided": hm.hint_provided,
                "hint_accepted": hm.hint_accepted,
                "hint_scaffolding_effectiveness": Decimal(str(hm.scaffolding_effectiveness)),
                "hint_count_in_session": hm.hint_count_in_session,
                "hint_vietnamese_detected": hm.vietnamese_detected,
                "hint_vietnamese_redirect_provided": hm.vietnamese_redirect_provided,
                "hint_off_topic_detected": hm.off_topic_detected,
                "hint_off_topic_redirect_provided": hm.off_topic_redirect_provided,
            })
        
        return item

    def _item_to_metrics(self, item: dict) -> ConversationMetrics:
        """
        Convert DynamoDB item to ConversationMetrics.
        
        Args:
            item: DynamoDB item
            
        Returns:
            ConversationMetrics object
        """
        # Parse quality metrics
        quality_metrics = QualityMetrics(
            has_markdown=item.get("quality_has_markdown", False),
            delivery_cues_count=item.get("quality_delivery_cues_count", 0),
            question_count=item.get("quality_question_count", 0),
            sentence_count=item.get("quality_sentence_count", 0),
            word_count=item.get("quality_word_count", 0),
            quality_score=float(item.get("quality_score", 0)),
            format_compliant=item.get("quality_format_compliant", True),
            length_compliant=item.get("quality_length_compliant", True),
            has_question=item.get("quality_has_question", False),
        )
        
        # Parse hint metrics
        hint_metrics = HintMetrics(
            hint_level=item.get("hint_level"),
            hint_provided=item.get("hint_provided", False),
            hint_accepted=item.get("hint_accepted", False),
            scaffolding_effectiveness=float(item.get("hint_scaffolding_effectiveness", 0)),
            hint_count_in_session=item.get("hint_count_in_session", 0),
            vietnamese_detected=item.get("hint_vietnamese_detected", False),
            vietnamese_redirect_provided=item.get("hint_vietnamese_redirect_provided", False),
            off_topic_detected=item.get("hint_off_topic_detected", False),
            off_topic_redirect_provided=item.get("hint_off_topic_redirect_provided", False),
        )
        
        # Parse timing
        ttft_ms = item.get("ttft_ms")
        if isinstance(ttft_ms, Decimal):
            ttft_ms = float(ttft_ms)
        
        total_latency_ms = item.get("total_latency_ms")
        if isinstance(total_latency_ms, Decimal):
            total_latency_ms = float(total_latency_ms)
        
        # Parse cost
        cost_usd = item.get("cost_usd", 0)
        if isinstance(cost_usd, Decimal):
            cost_usd = float(cost_usd)
        
        return ConversationMetrics(
            ttft_ms=ttft_ms,
            total_latency_ms=total_latency_ms,
            input_tokens=item.get("input_tokens", 0),
            output_tokens=item.get("output_tokens", 0),
            cache_read_tokens=item.get("cache_read_tokens", 0),
            cache_write_tokens=item.get("cache_write_tokens", 0),
            model_used=item.get("model_used", ""),
            model_source=item.get("model_source", "primary"),
            fallback_reason=item.get("fallback_reason"),
            proficiency_level=item.get("proficiency_level", ""),
            scenario_title=item.get("scenario_title", ""),
            session_id=item.get("session_id", ""),
            turn_index=item.get("turn_index", 0),
            cost_usd=cost_usd,
            response_length=item.get("response_length", 0),
            validation_passed=item.get("validation_passed", True),
            validation_reason=item.get("validation_reason"),
            quality_metrics=quality_metrics,
            hint_metrics=hint_metrics,
            timestamp=item.get("timestamp", ""),
        )
