"""Async hint and analyzer service using SQS + Lambda callback pattern.

AWS best practice: Use SQS for async processing to avoid blocking WebSocket connections.
Reference: https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-retain-records.html
"""

import json
import logging
import os
from typing import Any

import boto3

logger = logging.getLogger(__name__)

# Module-level SQS client (reused across Lambda invocations)
_sqs_client = boto3.client("sqs")
_apigw_client = boto3.client("apigatewaymanagementapi")


class AsyncHintAnalyzerService:
    """Service for async hint and analyzer processing via SQS."""

    def __init__(self, sqs_client=None, apigw_client=None):
        """Initialize service with SQS and API Gateway clients.
        
        Args:
            sqs_client: SQS client (optional, uses module-level if not provided)
            apigw_client: API Gateway Management API client (optional)
        """
        self.sqs_client = sqs_client or _sqs_client
        self.apigw_client = apigw_client or _apigw_client
        self.hint_queue_url = os.environ.get("HINT_QUEUE_URL")
        self.analyzer_queue_url = os.environ.get("ANALYZER_QUEUE_URL")

    def send_hint_request_async(
        self,
        session_id: str,
        connection_id: str,
        session: Any,
        last_ai_turn: Any,
        turn_history: list[Any],
    ) -> bool:
        """Send hint generation request to SQS queue.
        
        AWS best practice: Use SQS for async processing to avoid blocking.
        
        Args:
            session_id: Session ID
            connection_id: WebSocket connection ID (for callback)
            session: Session entity
            last_ai_turn: Last AI turn
            turn_history: Turn history
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.hint_queue_url:
            logger.error("HINT_QUEUE_URL not configured")
            return False

        try:
            message = {
                "action": "generate_hint",
                "session_id": session_id,
                "connection_id": connection_id,
                "session": {
                    "session_id": str(session.session_id),
                    "level": session.level.value if hasattr(session.level, "value") else str(session.level),
                    "scenario_title": session.scenario_title,
                    "ai_character": session.ai_character,
                },
                "last_ai_turn": {
                    "content": last_ai_turn.content if last_ai_turn else None,
                } if last_ai_turn else None,
                "turn_history_count": len(turn_history),
            }

            self.sqs_client.send_message(
                QueueUrl=self.hint_queue_url,
                MessageBody=json.dumps(message),
                MessageGroupId=session_id,  # FIFO queue: ensure ordering per session
            )

            logger.info(
                "Hint request sent to SQS",
                extra={
                    "session_id": session_id,
                    "connection_id": connection_id,
                    "queue_url": self.hint_queue_url,
                }
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to send hint request to SQS: {e}",
                extra={
                    "session_id": session_id,
                    "connection_id": connection_id,
                    "error": str(e),
                }
            )
            return False

    def send_analyzer_request_async(
        self,
        session_id: str,
        connection_id: str,
        turn_index: int,
        learner_message: str,
        ai_response: str,
        level: str,
        scenario_context: str,
    ) -> bool:
        """Send analyzer request to SQS queue.
        
        Args:
            session_id: Session ID
            connection_id: WebSocket connection ID (for callback)
            turn_index: Turn index to analyze
            learner_message: Learner's message
            ai_response: AI's response
            level: CEFR level
            scenario_context: Scenario context
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.analyzer_queue_url:
            logger.error("ANALYZER_QUEUE_URL not configured")
            return False

        try:
            message = {
                "action": "analyze_turn",
                "session_id": session_id,
                "connection_id": connection_id,
                "turn_index": turn_index,
                "learner_message": learner_message,
                "ai_response": ai_response,
                "level": level,
                "scenario_context": scenario_context,
            }

            self.sqs_client.send_message(
                QueueUrl=self.analyzer_queue_url,
                MessageBody=json.dumps(message),
                MessageGroupId=session_id,  # FIFO queue: ensure ordering per session
            )

            logger.info(
                "Analyzer request sent to SQS",
                extra={
                    "session_id": session_id,
                    "connection_id": connection_id,
                    "turn_index": turn_index,
                    "queue_url": self.analyzer_queue_url,
                }
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to send analyzer request to SQS: {e}",
                extra={
                    "session_id": session_id,
                    "connection_id": connection_id,
                    "turn_index": turn_index,
                    "error": str(e),
                }
            )
            return False

    def send_websocket_message(
        self,
        connection_id: str,
        message: dict[str, Any],
        domain_name: str = None,
        stage: str = None,
    ) -> bool:
        """Send message to WebSocket client via @connections API.
        
        AWS best practice: Use @connections API for WebSocket callbacks.
        Reference: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-how-to-call-websocket-api-connections.html
        
        Args:
            connection_id: WebSocket connection ID
            message: Message dict to send
            domain_name: API Gateway domain name (optional, uses env var if not provided)
            stage: API Gateway stage (optional, uses env var if not provided)
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not domain_name:
            domain_name = os.environ.get("APIGW_DOMAIN_NAME")
        if not stage:
            stage = os.environ.get("APIGW_STAGE", "prod")

        if not domain_name:
            logger.error("APIGW_DOMAIN_NAME not configured")
            return False

        try:
            # Create API Gateway Management API client with correct endpoint
            endpoint_url = f"https://{domain_name}/{stage}"
            apigw = boto3.client("apigatewaymanagementapi", endpoint_url=endpoint_url)

            apigw.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps(message),
            )

            logger.info(
                "WebSocket message sent",
                extra={
                    "connection_id": connection_id,
                    "endpoint": endpoint_url,
                }
            )
            return True

        except apigw.exceptions.GoneException:
            logger.warning(
                "WebSocket connection gone (client disconnected)",
                extra={"connection_id": connection_id}
            )
            return False

        except Exception as e:
            logger.error(
                f"Failed to send WebSocket message: {e}",
                extra={
                    "connection_id": connection_id,
                    "error": str(e),
                }
            )
            return False
