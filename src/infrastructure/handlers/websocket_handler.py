from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, replace
from functools import lru_cache
from typing import Any, Callable

import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from jwt import InvalidTokenError, PyJWKClient, decode

from application.dtos.speaking_session_dtos import (
    CompleteSpeakingSessionCommand,
    SubmitSpeakingTurnCommand,
)
from application.use_cases.speaking_session_use_cases import (
    CompleteSpeakingSessionUseCase,
    SubmitSpeakingTurnUseCase,
)
from domain.entities.session import Session
from infrastructure.persistence.dynamo_scoring_repo import DynamoScoringRepo
from infrastructure.persistence.dynamo_session_repo import DynamoSessionRepo
from infrastructure.persistence.dynamo_turn_repo import DynamoTurnRepo
from infrastructure.services.speaking_pipeline_services import (
    BedrockConversationGenerationService,
    ComprehendTranscriptAnalysisService,
    PollySpeechSynthesisService,
)
from infrastructure.services.transcribe_presigned_url import TranscribePresignedUrlGenerator
from domain.services.speaking_performance_scorer import SpeakingPerformanceScorer
from infrastructure.services.bedrock_scorer_adapter import BedrockScorerAdapter
from domain.services.conversation_orchestrator import ConversationOrchestrator
from domain.services.model_router import ModelRouter
from domain.services.response_validator import ResponseValidator
from domain.services.metrics_logger import MetricsLogger
from shared.utils.ulid_util import new_ulid
from shared.http_utils import dumps

logger = logging.getLogger(__name__)

# ============================================================================
# AWS Best Practice: Initialize SDK clients outside handler (module-level)
# Reference: https://docs.aws.amazon.com/amazonq/detector-library/python/lambda-client-reuse/
# ============================================================================

# Configure retry with exponential backoff + jitter (AWS recommended)
_RETRY_CONFIG = Config(
    retries={
        "max_attempts": 3,  # Total attempts (1 initial + 2 retries)
        "mode": "adaptive",  # Exponential backoff with jitter
    }
)

# Module-level Bedrock client (reused across Lambda invocations)
# Region is automatically set from AWS_REGION environment variable in Lambda
_bedrock_client = boto3.client("bedrock-runtime", config=_RETRY_CONFIG)


def _response(status: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": dumps(body),
    }


def _parse_json_body(body: Any) -> dict[str, Any]:
    if isinstance(body, dict):
        return body
    try:
        return json.loads(body or "{}")
    except json.JSONDecodeError:
        return {}


def _extract_bearer_token(headers: dict[str, Any], query_params: dict[str, Any] | None = None) -> str:
    """Extract bearer token from headers or query parameters.
    
    For WebSocket connections, token is passed as query parameter.
    For HTTP requests, token is passed in Authorization header.
    """
    # Try query parameters first (WebSocket connections)
    if query_params:
        token = query_params.get("token") or ""
        if isinstance(token, str) and token.strip():
            return token.strip()
    
    # Fall back to Authorization header (HTTP requests)
    if not headers:
        return ""

    auth_value = headers.get("Authorization") or headers.get("authorization") or ""
    if not isinstance(auth_value, str):
        return ""

    if auth_value.startswith("Bearer "):
        return auth_value[7:].strip()
    return auth_value.strip()


def _verify_cognito_jwt(token: str) -> dict[str, Any]:
    if not token:
        raise ValueError("Token không hợp lệ.")

    region = os.environ.get("AWS_REGION", "")
    user_pool_id = os.environ.get("COGNITO_USER_POOL_ID", "")
    app_client_id = os.environ.get("COGNITO_APP_CLIENT_ID", "")
    
    print(f"[ws] Token verification: region={region}, user_pool_id={user_pool_id}, app_client_id={app_client_id}")
    
    if not region or not user_pool_id:
        raise ValueError("Thiếu cấu hình Cognito để xác thực token.")

    issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
    print(f"[ws] Issuer: {issuer}")
    
    try:
        jwks_client = PyJWKClient(f"{issuer}/.well-known/jwks.json")
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # Decode JWT - verify signature, issuer, expiration, and token_use
        # Per AWS docs: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html
        # ID tokens have 'aud' claim, access tokens have 'client_id' claim
        # We disable aud verification here because we'll verify it manually below
        # to handle both ID tokens (aud) and access tokens (client_id)
        claims = decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=issuer,
            options={"require": ["exp", "iss", "token_use", "sub"], "verify_aud": False},
        )
        print(f"[ws] Token decoded: token_use={claims.get('token_use')}, aud={claims.get('aud')}, client_id={claims.get('client_id')}, sub={claims.get('sub')}")
    except InvalidTokenError as exc:
        print(f"[ws] JWT decode error: {exc}")
        raise ValueError("Token không hợp lệ.") from exc
    except Exception as exc:
        print(f"[ws] Unexpected error during token verification: {exc}")
        raise ValueError("Token không hợp lệ.") from exc

    # Verify token_use claim (AWS best practice)
    token_use = claims.get("token_use")
    if token_use not in {"access", "id"}:
        print(f"[ws] Invalid token_use: {token_use}")
        raise ValueError("token_use không hợp lệ.")

    # Verify audience/client_id matches app_client_id (AWS best practice)
    # Per AWS docs: 
    # - ID tokens have 'aud' claim that should match app client ID
    # - Access tokens have 'client_id' claim that should match app client ID
    if app_client_id:
        if token_use == "id":
            aud = claims.get("aud")
            if not aud:
                print(f"[ws] ID token missing 'aud' claim")
                raise ValueError("Token không hợp lệ.")
            if aud != app_client_id:
                print(f"[ws] ID token aud mismatch: expected={app_client_id}, got={aud}")
                raise ValueError("aud không hợp lệ.")
            print(f"[ws] ID token aud verified: {aud}")
        elif token_use == "access":
            client_id = claims.get("client_id")
            if not client_id:
                print(f"[ws] Access token missing 'client_id' claim")
                raise ValueError("Token không hợp lệ.")
            if client_id != app_client_id:
                print(f"[ws] Access token client_id mismatch: expected={app_client_id}, got={client_id}")
                raise ValueError("client_id không hợp lệ.")
            print(f"[ws] Access token client_id verified: {client_id}")
    else:
        print(f"[ws] Warning: COGNITO_APP_CLIENT_ID not configured, skipping audience verification")

    return claims


def _session_gateway_endpoint(event: dict[str, Any]) -> str:
    request_context = event.get("requestContext") or {}
    domain_name = request_context.get("domainName")
    stage = request_context.get("stage")
    if not domain_name or not stage:
        raise ValueError("WebSocket requestContext thiếu domainName hoặc stage.")
    return f"https://{domain_name}/{stage}"


def _put_cloudwatch_metric(metric_name: str, value: float, unit: str = "None") -> None:
    """Put a metric to CloudWatch for monitoring."""
    try:
        cloudwatch = boto3.client("cloudwatch")
        cloudwatch.put_metric_data(
            Namespace="Lexi/Transcription",
            MetricData=[
                {
                    "MetricName": metric_name,
                    "Value": value,
                    "Unit": unit,
                }
            ],
        )
    except Exception as exc:
        logger.warning(f"Failed to put CloudWatch metric {metric_name}: {exc}")

@dataclass
class WebSocketSessionController:
    session_repo: DynamoSessionRepo
    turn_repo: DynamoTurnRepo
    transcribe_url_generator: TranscribePresignedUrlGenerator
    submit_turn_use_case: SubmitSpeakingTurnUseCase
    complete_use_case: CompleteSpeakingSessionUseCase
    build_upload_payload: Callable[[str], tuple[str, str]]
    send_message: Callable[[dict[str, Any]], None]
    verify_token: Callable[[str], dict[str, Any]]

    def _send_ai_response(self, text: str) -> None:
        """Send full AI response to client via WebSocket (non-streaming)."""
        self.send_message({
            "event": "AI_RESPONSE",
            "text": text or "",
        })

    def connect(self, session_id: str, token: str, connection_id: str) -> dict[str, Any]:
        print(f"[ws] connect() called: session_id={session_id} token_len={len(token) if token else 0} connection_id={connection_id}")
        
        if not session_id:
            print(f"[ws] connect() failed: missing session_id")
            return _response(400, {"message": "Thiếu session_id."})

        session = self.session_repo.get_by_id(session_id)
        if not session:
            print(f"[ws] connect() failed: session not found for session_id={session_id}")
            return _response(404, {"message": "Session không tồn tại."})

        try:
            print(f"[ws] Verifying token...")
            claims = self.verify_token(token)
            print(f"[ws] Token verified successfully: token_use={claims.get('token_use')} sub={claims.get('sub')}")
        except ValueError as exc:
            print(f"[ws] Token verification failed: {exc} (token_length={len(token) if token else 0})")
            return _response(401, {"message": str(exc)})
        except Exception as exc:
            print(f"[ws] Unexpected error during token verification: {type(exc).__name__}: {exc}")
            import traceback
            traceback.print_exc()
            return _response(401, {"message": "Token verification error"})

        user_id = str(claims.get("sub") or "")
        if not user_id:
            print(f"[ws] Token missing 'sub' claim")
            return _response(401, {"message": "Token không hợp lệ."})
        
        if session.user_id != user_id:
            print(f"[ws] Session user_id mismatch: session.user_id={session.user_id} token.sub={user_id}")
            return _response(403, {"message": "Session không thuộc về người dùng này."})

        session.connection_id = connection_id
        self.session_repo.save(session)
        print(f"[ws] Connected successfully: session_id={session_id} user_id={user_id} connection_id={connection_id}")
        return _response(200, {"message": "Connected"})

    def disconnect(self, session_id: str | None, connection_id: str) -> dict[str, Any]:
        if not session_id:
            return _response(200, {"message": "Disconnected"})

        session = self.session_repo.get_by_id(session_id)
        if session and session.connection_id == connection_id:
            session.connection_id = ""
            self.session_repo.save(session)

        return _response(200, {"message": "Disconnected"})

    def start_session(self, session_id: str, connection_id: str) -> dict[str, Any]:
        session = self._get_session(session_id)
        if not session:
            return _response(404, {"message": "Session không tồn tại."})

        self._sync_connection(session, connection_id)
        upload_url, upload_key = self.build_upload_payload(session_id)
        try:
            self.send_message(
                {
                    "event": "SESSION_READY",
                    "upload_url": upload_url,
                    "s3_key": upload_key,
                    "session_id": session_id,
                }
            )
        except Exception as exc:
            print(f"[ws] Failed to send SESSION_READY: {exc}")
            return _response(500, {"message": "Lỗi gửi thông tin session."})
        return _response(200, {"message": "Session ready"})

    def use_hint(self, session_id: str, connection_id: str) -> dict[str, Any]:
        session = self._get_session(session_id)
        if not session:
            logger.warning(f"Session not found: {session_id}")
            return _response(404, {"message": "Session không tồn tại."})

        self._sync_connection(session, connection_id)
        
        # Use StructuredHintGenerator for ALL levels (A1-C2)
        try:
            logger.info(f"Generating hint for session: {session_id}")
            # AWS best practice: Limit to last 10 turns for context (avoid fetching entire history)
            # Reference: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Query.Pagination.html
            turns = self.turn_repo.list_by_session(session_id, limit=10)
            logger.info(f"Using {len(turns)} turns (limited to 10) for session {session_id}")
            
            # Extract last AI message (what learner needs to respond to)
            from domain.value_objects.enums import Speaker as SpeakerEnum
            ai_turns = [t for t in turns if (t.speaker.value if hasattr(t.speaker, "value") else t.speaker) == SpeakerEnum.AI.value]
            last_ai_turn = ai_turns[-1] if ai_turns else None
            
            if last_ai_turn:
                logger.info(f"Last AI turn content: {last_ai_turn.content[:100]}...")
            else:
                logger.warning("No AI turns found")
            
            # Generate structured hint using LLM
            from domain.services.structured_hint_generator import StructuredHintGenerator
            hint_generator = StructuredHintGenerator(_bedrock_client)
            
            logger.info("Calling hint generator...")
            hint = hint_generator.generate(
                session=session,
                last_ai_turn=last_ai_turn,
                turn_history=turns,
            )
            logger.info(f"Hint generated successfully: {hint.type if hint else 'None'}")
            
            if hint:
                try:
                    self.send_message({
                        "event": "HINT_TEXT",
                        "hint": hint.to_dict(),
                    })
                except Exception as exc:
                    print(f"[ws] Failed to send structured hint: {exc}")
                    return _response(500, {"message": "Lỗi gửi gợi ý."})
                
                return _response(200, {"message": "Hint sent"})
            else:
                # Fallback: send empty hint with correct structure
                fallback_hint = {
                    "markdown": {
                        "vi": "💡 Không có gợi ý nào khả dụng lúc này. Vui lòng thử lại sau.",
                        "en": "💡 No hint available at this moment. Please try again later.",
                    }
                }
                try:
                    self.send_message({
                        "event": "HINT_TEXT",
                        "hint": fallback_hint,
                    })
                except Exception as exc:
                    print(f"[ws] Failed to send fallback hint: {exc}")
                return _response(200, {"message": "No hint available"})
                
        except Exception as e:
            logger.error(
                f"Failed to generate hint: {e}",
                extra={"session_id": session_id, "error": str(e), "error_type": type(e).__name__},
                exc_info=True  # Include full traceback
            )
            # Fallback: send error hint with correct structure
            fallback_hint = {
                "markdown": {
                    "vi": "💡 Hệ thống gợi ý đang gặp sự cố tạm thời. Vui lòng thử lại sau vài giây.",
                    "en": "💡 Hint system is temporarily unavailable. Please try again in a few seconds.",
                }
            }
            try:
                self.send_message({
                    "event": "HINT_TEXT",
                    "hint": fallback_hint,
                })
            except Exception as exc:
                print(f"[ws] Failed to send error hint: {exc}")
            return _response(500, {"message": "Lỗi tạo gợi ý."})

    def analyze_turn(self, session_id: str, turn_index: int, connection_id: str) -> dict[str, Any]:
        """Analyze a specific turn for formative assessment.
        
        Args:
            session_id: Session ID
            turn_index: Index of the USER turn to analyze (must be even: 0, 2, 4...)
            connection_id: WebSocket connection ID
            
        Returns:
            Response dict with status and message
        """
        session = self._get_session(session_id)
        if not session:
            return _response(404, {"message": "Session không tồn tại."})

        self._sync_connection(session, connection_id)
        
        try:
            # Validate turn_index
            if turn_index < 0:
                return _response(400, {"message": "turn_index phải >= 0"})
            
            # Get turns for this session (sorted by turn_index)
            # AWS best practice: Limit to last 20 turns for context (avoid fetching entire history)
            # Reference: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Query.Pagination.html
            turns = self.turn_repo.list_by_session(session_id, limit=20)
            sorted_turns = sorted(turns, key=lambda t: t.turn_index)
            
            # Check turn_index exists
            if turn_index >= len(sorted_turns):
                return _response(404, {
                    "message": f"Turn {turn_index} không tồn tại (session chỉ có {len(sorted_turns)} turns)"
                })
            
            # Find the requested USER turn and its corresponding AI response
            from domain.value_objects.enums import Speaker as SpeakerEnum
            learner_turn = None
            ai_turn = None
            
            for i, turn in enumerate(sorted_turns):
                speaker_val = turn.speaker.value if hasattr(turn.speaker, "value") else turn.speaker
                
                # Found the USER turn at requested index
                if turn.turn_index == turn_index and speaker_val == SpeakerEnum.USER.value:
                    learner_turn = turn
                    
                    # Find next AI turn (should be at index i+1)
                    if i + 1 < len(sorted_turns):
                        next_turn = sorted_turns[i + 1]
                        next_speaker = next_turn.speaker.value if hasattr(next_turn.speaker, "value") else next_turn.speaker
                        if next_speaker == SpeakerEnum.AI.value:
                            ai_turn = next_turn
                    break
            
            # Validate that turn_index is a USER turn
            if not learner_turn:
                return _response(404, {
                    "message": f"Turn {turn_index} không phải là USER turn hoặc không tồn tại"
                })
            
            # Get AI response (may be None if turn is incomplete)
            ai_response = ai_turn.content if ai_turn else "No AI response yet"
            
            # Analyze turn using ConversationAnalyzer
            from domain.services.conversation_analyzer import ConversationAnalyzer
            analyzer = ConversationAnalyzer(bedrock_client=_bedrock_client)
            
            level_str = session.level.value if hasattr(session.level, "value") else str(session.level)
            scenario_context = f"{session.scenario_title or 'Conversation'}"
            
            analysis = analyzer.analyze_turn(
                learner_message=learner_turn.content,
                ai_response=ai_response,
                level=level_str,
                scenario_context=scenario_context,
            )
            
            # Send analysis via WebSocket
            try:
                self.send_message({
                    "event": "TURN_ANALYSIS",
                    "analysis": {
                        "markdown": {
                            "vi": analysis.markdown_vi,
                            "en": analysis.markdown_en,
                        }
                    }
                })
            except Exception as exc:
                print(f"[ws] Failed to send analysis: {exc}")
                return _response(500, {"message": "Lỗi gửi phân tích."})
            
            return _response(200, {"message": "Analysis sent"})
            
        except Exception as e:
            logger.exception(f"Failed to analyze turn: {e}")
            # Send fallback analysis event to prevent FE timeout
            fallback_analysis = {
                "markdown_vi": "## 🎯 Phân tích tạm thời không khả dụng\n\nXin lỗi, hệ thống phân tích đang gặp sự cố. Vui lòng thử lại sau.",
                "markdown_en": "## 🎯 Analysis Temporarily Unavailable\n\nSorry, the analysis system is experiencing issues. Please try again later.",
            }
            try:
                self.send_message({
                    "event": "TURN_ANALYSIS",
                    "analysis": {
                        "markdown": {
                            "vi": fallback_analysis["markdown_vi"],
                            "en": fallback_analysis["markdown_en"],
                        }
                    }
                })
            except Exception as send_exc:
                print(f"[ws] Failed to send fallback analysis: {send_exc}")
            return _response(500, {"message": "Lỗi phân tích turn."})



    def send_message_turn(self, session_id: str, connection_id: str, body: dict[str, Any]) -> dict[str, Any]:
        print(f"[ws] send_message_turn called: session_id={session_id}, connection_id={connection_id}")
        print(f"[ws] send_message_turn body: {body}")
        
        session = self._get_session(session_id)
        if not session:
            print(f"[ws] send_message_turn: session not found")
            return _response(404, {"message": "Session không tồn tại."})

        text = str(body.get("text") or body.get("content") or "").strip()
        print(f"[ws] send_message_turn: extracted text='{text}' (length={len(text)})")
        
        if not text:
            print(f"[ws] send_message_turn: text is empty, returning 422")
            return _response(422, {"message": "Nội dung lượt nói không được để trống."})

        self._sync_connection(session, connection_id)
        
        print(f"[ws] send_message_turn: calling submit_turn_use_case.execute()")
        result = self.submit_turn_use_case.execute(
            SubmitSpeakingTurnCommand(
                user_id=session.user_id,
                session_id=session_id,
                text=text,
                is_hint_used=bool(body.get("is_hint_used", False)),
                audio_url=str(body.get("audio_url") or "") or None,
            )
        )
        print(f"[ws] send_message_turn: submit_turn_use_case returned, is_success={result.is_success}")
        
        # ✅ FIX: Use result.value (same as submit_transcript) instead of result.success
        if not result.is_success or result.value is None:
            print(f"[ws] send_message_turn: use case failed, error={result.error}")
            try:
                self.send_message({"event": "ERROR", "message": result.error or "Lỗi xử lý lượt nói."})
            except Exception as exc:
                print(f"[ws] Failed to send error message: {exc}")
            return _response(422, {"message": result.error or "Lỗi xử lý lượt nói."})

        response = result.value  # ✅ FIX: Changed from result.success to result.value
        print(f"[ws] send_message_turn: use case succeeded, user_turn_index={response.user_turn.turn_index}")
        print(f"[ws] send_message_turn: AI response text length={len(response.ai_turn.content)}")
        
        try:
            print(f"[ws] send_message_turn: sending TURN_SAVED event")
            self.send_message({"event": "TURN_SAVED", "turn_index": response.user_turn.turn_index})
            
            print(f"[ws] send_message_turn: sending AI_RESPONSE event")
            self._send_ai_response(response.ai_turn.content)
            
            if response.ai_turn.audio_url:
                print(f"[ws] send_message_turn: sending AI_AUDIO_URL event")
                self.send_message(
                    {
                        "event": "AI_AUDIO_URL",
                        "url": response.ai_turn.audio_url,
                        "text": response.ai_turn.content,
                    }
                )
            else:
                print(f"[ws] send_message_turn: no audio_url, skipping AI_AUDIO_URL event")
                
            print(f"[ws] send_message_turn: all events sent successfully")
        except Exception as exc:
            print(f"[ws] Failed to send response messages: {exc}")
            import traceback
            traceback.print_exc()
            return _response(500, {"message": "Lỗi gửi phản hồi."})

        print(f"[ws] send_message_turn: returning 200 OK")
        return _response(
            200,
            {
                "message": "Turn processed",
                "turn_index": response.user_turn.turn_index,
            },
        )

    def end_session(self, session_id: str, connection_id: str) -> dict[str, Any]:
        session = self._get_session(session_id)
        if not session:
            return _response(404, {"message": "Session không tồn tại."})

        self._sync_connection(session, connection_id)
        result = self.complete_use_case.execute(
            CompleteSpeakingSessionCommand(user_id=session.user_id, session_id=session_id)
        )
        if not result.is_success or result.value is None:
            try:
                self.send_message({"event": "ERROR", "message": result.error})
            except Exception as exc:
                print(f"[ws] Failed to send error message: {exc}")
            return _response(422, {"message": result.error})

        try:
            self.send_message(
                {
                    "event": "SCORING_COMPLETE",
                    "session_id": session_id,
                }
            )
        except Exception as exc:
            print(f"[ws] Failed to send SCORING_COMPLETE: {exc}")
        return _response(200, {"message": "Session completed"})

    def get_transcribe_url(self, session_id: str, connection_id: str) -> dict[str, Any]:
        """
        Generate presigned WebSocket URL for client-side Transcribe streaming.
        
        This is the AWS recommended approach for browser clients:
        - Browser connects directly to Transcribe WebSocket
        - Lower latency (no Lambda hop)
        - No Lambda timeout issues
        - No deprecated SDK dependency
        
        Reference: https://docs.aws.amazon.com/transcribe/latest/dg/streaming-setting-up.html#streaming-websocket
        """
        session = self._get_session(session_id)
        if not session:
            return _response(404, {"message": "Session không tồn tại."})

        self._sync_connection(session, connection_id)

        try:
            # Generate presigned URL for Transcribe WebSocket
            # Use PCM encoding (AWS recommended for best compatibility)
            url_data = self.transcribe_url_generator.generate(
                language_code="en-US",
                media_encoding="pcm",  # AWS Transcribe recommended encoding
                sample_rate=16000,
                expires_in=300,  # 5 minutes (AWS max)
            )

            # Send URL to client via WebSocket
            try:
                self.send_message({
                    "event": "TRANSCRIBE_URL",
                    "url": url_data["url"],
                    "expires_in": url_data["expires_in"],
                    "language_code": url_data["language_code"],
                    "media_encoding": url_data["media_encoding"],
                    "sample_rate": url_data["sample_rate"],
                })
            except Exception as exc:
                logger.error(f"Failed to send TRANSCRIBE_URL: {exc}")
                return _response(500, {"message": "Lỗi gửi URL."})

            logger.info(
                "Generated Transcribe presigned URL",
                extra={
                    "session_id": session_id,
                    "expires_in": url_data["expires_in"],
                },
            )

            return _response(200, {"message": "URL generated"})

        except Exception as exc:
            logger.exception("Failed to generate Transcribe URL", extra={"session_id": session_id})
            try:
                self.send_message({"event": "STT_ERROR", "message": "Không thể tạo Transcribe URL."})
            except Exception as send_exc:
                logger.error(f"Failed to send STT_ERROR: {send_exc}")
            return _response(500, {"message": str(exc)})

    def submit_transcript(self, session_id: str, connection_id: str, body: dict[str, Any]) -> dict[str, Any]:
        """Process final transcript from client-side streaming."""
        session = self._get_session(session_id)
        if not session:
            logger.warning(f"Session not found: {session_id}")
            return _response(404, {"message": "Session không tồn tại."})

        text = str(body.get("text") or "").strip()
        confidence = float(body.get("confidence") or 0.0)

        # Accept all transcripts regardless of confidence
        # Low confidence is better than no transcript
        if not text:
            text = ""

        self._sync_connection(session, connection_id)

        try:
            # Log and track metrics
            logger.info(
                "Client-side streaming transcription completed",
                extra={
                    "session_id": session_id,
                    "confidence": confidence,
                    "transcript_length": len(text),
                    "mode": "client-side-streaming",
                },
            )
            _put_cloudwatch_metric("TranscriptConfidence", confidence)
            _put_cloudwatch_metric("TranscriptLength", len(text), "Count")

            # Continue with existing LLM pipeline
            result = self.submit_turn_use_case.execute(
                SubmitSpeakingTurnCommand(
                    user_id=session.user_id,
                    session_id=session_id,
                    text=text,
                    is_hint_used=False,
                    audio_url=None,  # No S3 URL for streaming
                )
            )

            if not result.is_success or result.value is None:
                try:
                    self.send_message({"event": "ERROR", "message": result.error})
                except Exception as exc:
                    print(f"[ws] Failed to send error message: {exc}")
                return _response(422, {"message": result.error})

            response = result.value
            try:
                self.send_message({"event": "TURN_SAVED", "turn_index": response.user_turn.turn_index})
                self._send_ai_response(response.ai_turn.content)
                if response.ai_turn.audio_url:
                    self.send_message(
                        {
                            "event": "AI_AUDIO_URL",
                            "url": response.ai_turn.audio_url,
                            "text": response.ai_turn.content,
                        }
                    )
            except Exception as exc:
                logger.exception(f"Failed to send response messages: {exc}")
                print(f"[ws] Failed to send response messages: {exc}")

            return _response(200, {"message": "Transcript processed"})

        except Exception as exc:
            logger.exception("Failed to process transcript", extra={"session_id": session_id})
            try:
                self.send_message({"event": "ERROR", "message": "Lỗi xử lý transcript."})
            except Exception as send_exc:
                print(f"[ws] Failed to send error message: {send_exc}")
            return _response(500, {"message": str(exc)})

    def unsupported(self, action: str) -> dict[str, Any]:
        self.send_message({"event": "ERROR", "message": f"Hành động '{action}' chưa được hỗ trợ."})
        return _response(400, {"message": f"Hành động '{action}' chưa được hỗ trợ."})

    def _get_session(self, session_id: str) -> Session | None:
        if not session_id:
            return None
        return self.session_repo.get_by_id(session_id)

    def _sync_connection(self, session: Session, connection_id: str) -> None:
        if session.connection_id != connection_id:
            session.connection_id = connection_id
            self.session_repo.save(session)




def _build_upload_payload(session_id: str) -> tuple[str, str]:
    bucket_name = os.environ.get("SPEAKING_AUDIO_BUCKET_NAME")
    region = os.environ.get("AWS_REGION", "ap-southeast-1")
    
    if not bucket_name:
        raise RuntimeError("Thiếu SPEAKING_AUDIO_BUCKET_NAME.")

    upload_key = f"speaking/audio/{session_id}/{new_ulid()}.webm"
    
    try:
        # Create S3 client with explicit configuration for presigned URLs
        # Use signature version 4 and virtual-hosted style addressing (AWS best practices)
        from botocore.config import Config
        
        config = Config(
            signature_version='s3v4',
            s3={'addressing_style': 'virtual'},
            region_name=region
        )
        
        client = boto3.client("s3", config=config)
        
        # Generate presigned URL WITHOUT ContentType parameter
        # This allows the client to send any Content-Type header without signature mismatch
        # The Content-Type will be determined by what the client sends
        upload_url = client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": bucket_name,
                "Key": upload_key,
                # DO NOT include ContentType here - it causes signature mismatch
                # if the client's Content-Type header doesn't match exactly
            },
            ExpiresIn=900,
            HttpMethod="PUT",
        )
        print(f"[s3] Presigned URL generated: key={upload_key}, bucket={bucket_name}, region={region}, signature=s3v4, url_length={len(upload_url)}")
        return upload_url, upload_key
    except Exception as exc:
        print(f"[s3] Error generating presigned URL: {exc}")
        raise


@lru_cache(maxsize=1)
def get_websocket_controller() -> WebSocketSessionController:
    session_repo = DynamoSessionRepo()
    turn_repo = DynamoTurnRepo()
    scoring_repo = DynamoScoringRepo()
    
    # AWS Best Practice: Enable ConversationOrchestrator for Phase 5 metrics
    # This enables latency, cost tracking, and quality validation
    conversation_orchestrator = ConversationOrchestrator(
        model_router=ModelRouter(),
        response_validator=ResponseValidator(),
        metrics_logger=MetricsLogger(),
    )
    
    submit_turn_use_case = SubmitSpeakingTurnUseCase(
        session_repo,
        turn_repo,
        ComprehendTranscriptAnalysisService(),
        BedrockConversationGenerationService(),
        PollySpeechSynthesisService(),
        conversation_orchestrator=conversation_orchestrator,  # ✅ ENABLED
    )
    complete_use_case = CompleteSpeakingSessionUseCase(session_repo, turn_repo, scoring_repo, BedrockScorerAdapter())

    return WebSocketSessionController(
        session_repo=session_repo,
        turn_repo=turn_repo,
        transcribe_url_generator=TranscribePresignedUrlGenerator(),
        submit_turn_use_case=submit_turn_use_case,
        complete_use_case=complete_use_case,
        build_upload_payload=_build_upload_payload,
        send_message=lambda payload: None,
        verify_token=_verify_cognito_jwt,
    )


def _make_sender(event: dict[str, Any], connection_id: str) -> Callable[[dict[str, Any]], None]:
    endpoint_url = _session_gateway_endpoint(event)
    client = boto3.client("apigatewaymanagementapi", endpoint_url=endpoint_url)

    def send_message(payload: dict[str, Any]) -> None:
        try:
            print(f"[ws] Sending message to {connection_id}: {payload.get('event', 'UNKNOWN')}")
            # Use dumps() which includes DecimalEncoder to convert Decimal → float
            json_str = dumps(payload)
            client.post_to_connection(
                ConnectionId=connection_id,
                Data=json_str.encode("utf-8"),
            )
            print(f"[ws] Message sent successfully to {connection_id}")
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code == "GoneException":
                print(f"[ws] Connection gone (client disconnected): {connection_id}")
                return  # Normal case - client disconnected, don't re-raise
            print(f"[ws] Failed to send message: {error_code} - {exc}")
            raise  # Re-raise for other errors

    return send_message


def handler(event, context):
    """
    WebSocket Lambda handler with proper error handling per AWS best practices.
    
    AWS Best Practice: Return appropriate status codes for connection lifecycle
    Reference: https://docs.aws.amazon.com/apigateway/latest/developerguide/websocket-api.html
    
    Status codes:
    - 200: Success
    - 401: Unauthorized (auth failure)
    - 403: Forbidden (permission denied)
    - 500: Internal server error
    """
    route_key = (event.get("requestContext") or {}).get("routeKey", "")
    connection_id = (event.get("requestContext") or {}).get("connectionId", "")
    
    try:
        base_controller = get_websocket_controller()
        body = _parse_json_body(event.get("body"))
        headers = event.get("headers") or {}
        query_params = event.get("queryStringParameters") or {}

        # Extract params from queryStringParameters or body
        session_id = body.get("session_id") or query_params.get("session_id")
        token = _extract_bearer_token(headers, query_params)

        print(f"[ws] Handler called: route_key={route_key} connection_id={connection_id} session_id={session_id} has_token={bool(token)}")

        action = route_key if route_key not in {"$default"} else str(body.get("action") or "")

        controller = replace(base_controller, send_message=_make_sender(event, connection_id))

        # AWS Best Practice: Handle $connect with proper auth error codes
        if route_key == "$connect":
            print(f"[ws] Processing $connect: session_id={session_id}")
            return controller.connect(str(session_id or ""), str(token or ""), connection_id)

        # AWS Best Practice: $disconnect always returns 200 (no error propagation)
        if route_key == "$disconnect":
            print(f"[ws] Processing $disconnect: session_id={session_id}")
            return base_controller.disconnect(str(session_id or "") or None, connection_id)

        if not session_id:
            return _response(400, {"message": "Thiếu session_id."})

        # Route actions
        if action == "START_SESSION":
            print(f"[ws] Routing to START_SESSION")
            return controller.start_session(str(session_id), connection_id)
        if action == "GET_TRANSCRIBE_URL":
            print(f"[ws] Routing to GET_TRANSCRIBE_URL")
            return controller.get_transcribe_url(str(session_id), connection_id)
        if action == "SUBMIT_TRANSCRIPT":
            # ✅ Unified handler for both text input and mic input
            print(f"[ws] Routing to SUBMIT_TRANSCRIPT (handles both text and mic input)")
            print(f"[ws] SUBMIT_TRANSCRIPT body: {body}")
            return controller.submit_transcript(str(session_id), connection_id, body)
        if action == "USE_HINT":
            print(f"[ws] Routing to USE_HINT")
            return controller.use_hint(str(session_id), connection_id)
        if action == "ANALYZE_TURN":
            print(f"[ws] Routing to ANALYZE_TURN")
            turn_index = body.get("turn_index")
            if turn_index is None:
                return _response(400, {"message": "Missing turn_index"})
            return controller.analyze_turn(str(session_id), int(turn_index), connection_id)
        if action == "END_SESSION":
            print(f"[ws] Routing to END_SESSION")
            return controller.end_session(str(session_id), connection_id)

        print(f"[ws] Unknown action: {action}")
        return controller.unsupported(action or route_key or body.get("action", "UNKNOWN"))
    
    except ValueError as e:
        # AWS Best Practice: Return 401 for authentication/authorization errors
        # ValueError is raised by _verify_cognito_jwt for auth failures
        logger.warning(f"WebSocket auth error: {str(e)}", extra={"connection_id": connection_id, "route_key": route_key})
        
        # For $connect, return 401 to reject connection
        if route_key == "$connect":
            return _response(401, {"message": "Unauthorized"})
        
        # For other routes, return 403 (connection exists but action forbidden)
        return _response(403, {"message": "Forbidden"})
    
    except Exception as e:
        # AWS Best Practice: Return 500 for unexpected errors
        # Log full exception for debugging
        logger.exception(
            f"WebSocket handler error: {type(e).__name__}",
            extra={"connection_id": connection_id, "route_key": route_key, "error": str(e)}
        )
        
        # For $connect, return 500 to reject connection
        if route_key == "$connect":
            return _response(500, {"message": "Internal server error"})
        
        # For other routes, return 500
        return _response(500, {"message": "Internal server error"})
