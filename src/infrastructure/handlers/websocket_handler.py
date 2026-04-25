from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, replace
from functools import lru_cache
from typing import Any, Callable

import boto3
from botocore.exceptions import ClientError
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
    TranscribeSTTService,
)
from infrastructure.services.streaming_stt_service_sync import StreamingSTTServiceSync
from domain.services.speaking_performance_scorer import SpeakingPerformanceScorer
from infrastructure.services.bedrock_scorer_adapter import BedrockScorerAdapter
from shared.utils.ulid_util import new_ulid
from shared.http_utils import dumps

logger = logging.getLogger(__name__)


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
    stt_service: TranscribeSTTService
    streaming_stt_service: StreamingSTTServiceSync
    submit_turn_use_case: SubmitSpeakingTurnUseCase
    complete_use_case: CompleteSpeakingSessionUseCase
    build_upload_payload: Callable[[str], tuple[str, str]]
    send_message: Callable[[dict[str, Any]], None]
    verify_token: Callable[[str], dict[str, Any]]

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

    def audio_uploaded(self, session_id: str, connection_id: str, body: dict[str, Any]) -> dict[str, Any]:
        session = self._get_session(session_id)
        if not session:
            return _response(404, {"message": "Session không tồn tại."})

        self._sync_connection(session, connection_id)

        s3_key = body.get("s3_key", "")
        bucket = os.environ.get("SPEAKING_AUDIO_BUCKET_NAME", "")

        if not s3_key or not bucket:
            try:
                self.send_message({"event": "STT_LOW_CONFIDENCE", "confidence": 0.0})
            except Exception as exc:
                print(f"[ws] Failed to send STT_LOW_CONFIDENCE: {exc}")
            return _response(400, {"message": "Thiếu s3_key hoặc bucket."})

        # Gọi Transcribe để chuyển audio → text
        text, confidence = self.stt_service.transcribe(bucket, s3_key)

        if not text or confidence < 0.5:
            try:
                self.send_message({"event": "STT_LOW_CONFIDENCE", "confidence": float(confidence)})
            except Exception as exc:
                print(f"[ws] Failed to send STT_LOW_CONFIDENCE: {exc}")
            return _response(200, {"message": "STT low confidence"})

        # Gửi kết quả STT về client
        try:
            self.send_message({"event": "STT_RESULT", "text": text, "confidence": float(confidence)})
        except Exception as exc:
            print(f"[ws] Failed to send STT_RESULT: {exc}")

        # Tiếp tục pipeline với text đã transcribe
        result = self.submit_turn_use_case.execute(
            SubmitSpeakingTurnCommand(
                user_id=session.user_id,
                session_id=session_id,
                text=text,
                is_hint_used=False,
                audio_url=f"s3://{bucket}/{s3_key}",
            )
        )
        if not result.is_success or result.value is None:
            try:
                self.send_message({"event": "ERROR", "message": result.error or "Lỗi xử lý lượt nói."})
            except Exception as exc:
                print(f"[ws] Failed to send error message: {exc}")
            return _response(422, {"message": result.error or "Lỗi xử lý lượt nói."})

        response = result.value
        try:
            self.send_message({"event": "TURN_SAVED", "turn_index": response.user_turn.turn_index})
            self.send_message({"event": "AI_TEXT_CHUNK", "chunk": response.ai_turn.content, "done": True})
            if response.ai_turn.audio_url:
                self.send_message({
                    "event": "AI_AUDIO_URL",
                    "url": response.ai_turn.audio_url,
                    "text": response.ai_turn.content,
                })
        except Exception as exc:
            print(f"[ws] Failed to send response messages: {exc}")

        return _response(200, {"message": "Audio processed"})

    def use_hint(self, session_id: str, connection_id: str) -> dict[str, Any]:
        session = self._get_session(session_id)
        if not session:
            return _response(404, {"message": "Session không tồn tại."})

        self._sync_connection(session, connection_id)
        turns = self.turn_repo.list_by_session(session_id)
        hint = self._generate_contextual_hint(session, turns)
        try:
            self.send_message({"event": "HINT_TEXT", "hint": hint})
        except Exception as exc:
            print(f"[ws] Failed to send hint: {exc}")
            return _response(500, {"message": "Lỗi gửi gợi ý."})
        return _response(200, {"message": "Hint sent"})

    def _generate_contextual_hint(self, session: Session, turns: list) -> str:
        """Tạo hint có ngữ cảnh dùng Bedrock LLM (Amazon Nova Micro)."""
        from domain.value_objects.enums import Speaker as SpeakerEnum
        last_ai = next(
            (t for t in reversed(turns) if (t.speaker.value if hasattr(t.speaker, "value") else t.speaker) == SpeakerEnum.AI.value),
            None,
        )
        goal = session.selected_goals[0] if session.selected_goals else "continue the conversation"
        level = session.level.value if hasattr(session.level, "value") else str(session.level)

        hint_prompt = (
            f"The learner is stuck in an English conversation. "
            f"Last AI message: '{last_ai.content if last_ai else 'Start of conversation'}'. "
            f"Current goal: {goal}. Learner level: {level}. "
            f"Give a 1-sentence hint starting with 'You could say:' using simple English appropriate for {level}."
        )

        try:
            import boto3
            bedrock = boto3.client("bedrock-runtime")
            # Amazon Nova format (per AWS docs: https://docs.aws.amazon.com/nova/latest/userguide/complete-request-schema.html)
            body = dumps({
                "system": [{"text": "You are a helpful English tutor providing hints to learners."}],
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": hint_prompt}]
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": 60,
                    "temperature": 0.5
                }
            })
            response = bedrock.invoke_model(
                modelId="apac.amazon.nova-micro-v1:0",  # Use inference profile for APAC regions
                body=body,
            )
            result = json.loads(response["body"].read())
            # Nova response format: {"output": {"message": {"content": [{"text": "..."}]}}}
            return result["output"]["message"]["content"][0]["text"].strip()
        except Exception as e:
            print(f"[ws] Hint generation failed: {e}")
            return f"You could say something about: {goal}"

    def send_message_turn(self, session_id: str, connection_id: str, body: dict[str, Any]) -> dict[str, Any]:
        session = self._get_session(session_id)
        if not session:
            return _response(404, {"message": "Session không tồn tại."})

        text = str(body.get("text") or body.get("content") or "").strip()
        if not text:
            return _response(422, {"message": "Nội dung lượt nói không được để trống."})

        self._sync_connection(session, connection_id)
        result = self.submit_turn_use_case.execute(
            SubmitSpeakingTurnCommand(
                user_id=session.user_id,
                session_id=session_id,
                text=text,
                is_hint_used=bool(body.get("is_hint_used", False)),
                audio_url=str(body.get("audio_url") or "") or None,
            )
        )
        if not result.is_success or result.value is None:
            try:
                self.send_message({"event": "ERROR", "message": result.error or "Lỗi xử lý lượt nói."})
            except Exception as exc:
                print(f"[ws] Failed to send error message: {exc}")
            return _response(422, {"message": result.error or "Lỗi xử lý lượt nói."})

        response = result.value
        try:
            self.send_message({"event": "TURN_SAVED", "turn_index": response.user_turn.turn_index})
            self.send_message(
                {
                    "event": "AI_TEXT_CHUNK",
                    "chunk": response.ai_turn.content,
                    "done": True,
                }
            )
            if response.ai_turn.audio_url:
                self.send_message(
                    {
                        "event": "AI_AUDIO_URL",
                        "url": response.ai_turn.audio_url,
                        "text": response.ai_turn.content,
                    }
                )
        except Exception as exc:
            print(f"[ws] Failed to send response messages: {exc}")
            return _response(500, {"message": "Lỗi gửi phản hồi."})

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
                self.send_message({"event": "ERROR", "message": result.error or "Không thể kết thúc session."})
            except Exception as exc:
                print(f"[ws] Failed to send error message: {exc}")
            return _response(422, {"message": result.error or "Không thể kết thúc session."})

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

    def start_streaming(self, session_id: str, connection_id: str) -> dict[str, Any]:
        """Initialize streaming transcription session."""
        session = self._get_session(session_id)
        if not session:
            return _response(404, {"message": "Session không tồn tại."})

        self._sync_connection(session, connection_id)

        try:
            # Initialize Transcribe stream
            stream_id = self.streaming_stt_service.start_stream(
                stream_id=session_id,
                language_code="en-US",
                sample_rate=16000,
                media_encoding="opus",
            )

            # Store stream_id in session
            session.transcribe_stream_id = stream_id
            session.last_audio_timestamp = 0.0
            self.session_repo.save(session)

            try:
                self.send_message({"event": "STREAMING_READY", "session_id": session_id})
            except Exception as exc:
                print(f"[ws] Failed to send STREAMING_READY: {exc}")
            return _response(200, {"message": "Streaming ready"})

        except Exception as exc:
            logger.exception("Failed to start streaming", extra={"session_id": session_id})
            try:
                self.send_message({"event": "STT_ERROR", "message": "Không thể khởi động streaming."})
            except Exception as send_exc:
                print(f"[ws] Failed to send STT_ERROR: {send_exc}")
            return _response(500, {"message": str(exc)})

    def audio_chunk(self, session_id: str, connection_id: str, body: dict[str, Any]) -> dict[str, Any]:
        """Forward audio chunk to Transcribe stream."""
        session = self._get_session(session_id)
        if not session:
            return _response(404, {"message": "Session không tồn tại."})

        if not session.transcribe_stream_id:
            return _response(400, {"message": "No active stream"})

        self._sync_connection(session, connection_id)

        try:
            audio_data = body.get("data")
            if not audio_data:
                return _response(400, {"message": "Missing audio data"})

            # Convert array to bytes
            audio_bytes = bytes(audio_data)

            # Forward to Transcribe
            self.streaming_stt_service.send_audio_chunk(
                stream_id=session.transcribe_stream_id,
                audio_bytes=audio_bytes,
            )

            # Update timestamp for timeout tracking
            import time
            session.last_audio_timestamp = time.time()
            self.session_repo.save(session)

            # Check for transcripts (non-blocking)
            transcripts = self.streaming_stt_service.get_transcripts(session.transcribe_stream_id)
            for transcript in transcripts:
                try:
                    if transcript.is_partial:
                        self.send_message(
                            {
                                "event": "PARTIAL_TRANSCRIPT",
                                "text": transcript.text,
                                "confidence": float(transcript.confidence),
                            }
                        )
                    else:
                        self.send_message(
                            {
                                "event": "FINAL_TRANSCRIPT",
                                "text": transcript.text,
                                "confidence": float(transcript.confidence),
                            }
                        )
                except Exception as exc:
                    print(f"[ws] Failed to send transcript: {exc}")

            return _response(200, {"message": "Chunk processed"})

        except Exception as exc:
            logger.exception("Failed to process audio chunk", extra={"session_id": session_id})
            try:
                self.send_message({"event": "STT_ERROR", "message": "Lỗi xử lý audio chunk."})
            except Exception as send_exc:
                print(f"[ws] Failed to send STT_ERROR: {send_exc}")
            return _response(500, {"message": str(exc)})

    def end_streaming(self, session_id: str, connection_id: str) -> dict[str, Any]:
        """Close Transcribe stream and trigger LLM pipeline."""
        session = self._get_session(session_id)
        if not session:
            return _response(404, {"message": "Session không tồn tại."})

        if not session.transcribe_stream_id:
            return _response(400, {"message": "No active stream"})

        self._sync_connection(session, connection_id)

        try:
            # Close stream and get final transcript
            final_transcript = self.streaming_stt_service.close_stream(session.transcribe_stream_id)
            session.transcribe_stream_id = None
            session.last_audio_timestamp = 0.0
            self.session_repo.save(session)

            if not final_transcript or final_transcript.confidence < 0.5:
                confidence = float(final_transcript.confidence) if final_transcript else 0.0
                try:
                    self.send_message({"event": "STT_LOW_CONFIDENCE", "confidence": confidence})
                except Exception as exc:
                    print(f"[ws] Failed to send STT_LOW_CONFIDENCE: {exc}")
                return _response(200, {"message": "Low confidence"})

            # Send final transcript
            try:
                self.send_message(
                    {
                        "event": "FINAL_TRANSCRIPT",
                        "text": final_transcript.text,
                        "confidence": float(final_transcript.confidence),
                    }
                )
            except Exception as exc:
                print(f"[ws] Failed to send final transcript: {exc}")

            # Log and track metrics
            logger.info(
                "Streaming transcription completed",
                extra={
                    "session_id": session_id,
                    "confidence": final_transcript.confidence,
                    "transcript_length": len(final_transcript.text),
                },
            )
            _put_cloudwatch_metric("TranscriptConfidence", final_transcript.confidence)
            _put_cloudwatch_metric("TranscriptLength", len(final_transcript.text), "Count")

            # Continue with existing LLM pipeline
            result = self.submit_turn_use_case.execute(
                SubmitSpeakingTurnCommand(
                    user_id=session.user_id,
                    session_id=session_id,
                    text=final_transcript.text,
                    is_hint_used=False,
                    audio_url=None,  # No S3 URL for streaming
                )
            )

            if not result.is_success or result.value is None:
                try:
                    self.send_message({"event": "ERROR", "message": result.error or "Lỗi xử lý lượt nói."})
                except Exception as exc:
                    print(f"[ws] Failed to send error message: {exc}")
                return _response(422, {"message": result.error or "Lỗi xử lý lượt nói."})

            response = result.value
            try:
                self.send_message({"event": "TURN_SAVED", "turn_index": response.user_turn.turn_index})
                self.send_message({"event": "AI_TEXT_CHUNK", "chunk": response.ai_turn.content, "done": True})
                if response.ai_turn.audio_url:
                    self.send_message(
                        {
                            "event": "AI_AUDIO_URL",
                            "url": response.ai_turn.audio_url,
                            "text": response.ai_turn.content,
                        }
                    )
            except Exception as exc:
                print(f"[ws] Failed to send response messages: {exc}")

            return _response(200, {"message": "Streaming ended"})

        except Exception as exc:
            logger.exception("Failed to end streaming", extra={"session_id": session_id})
            _put_cloudwatch_metric("StreamErrors", 1, "Count")
            try:
                self.send_message({"event": "STT_ERROR", "message": "Lỗi kết thúc streaming."})
            except Exception as send_exc:
                print(f"[ws] Failed to send STT_ERROR: {send_exc}")
            return _response(500, {"message": str(exc)})

    def submit_transcript(self, session_id: str, connection_id: str, body: dict[str, Any]) -> dict[str, Any]:
        """Process final transcript from client-side streaming."""
        session = self._get_session(session_id)
        if not session:
            return _response(404, {"message": "Session không tồn tại."})

        text = str(body.get("text") or "").strip()
        confidence = float(body.get("confidence") or 0.0)

        if not text or confidence < 0.5:
            try:
                self.send_message({"event": "STT_LOW_CONFIDENCE", "confidence": confidence})
            except Exception as exc:
                print(f"[ws] Failed to send STT_LOW_CONFIDENCE: {exc}")
            return _response(200, {"message": "Low confidence"})

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
                    self.send_message({"event": "ERROR", "message": result.error or "Lỗi xử lý lượt nói."})
                except Exception as exc:
                    print(f"[ws] Failed to send error message: {exc}")
                return _response(422, {"message": result.error or "Lỗi xử lý lượt nói."})

            response = result.value
            try:
                self.send_message({"event": "TURN_SAVED", "turn_index": response.user_turn.turn_index})
                self.send_message({"event": "AI_TEXT_CHUNK", "chunk": response.ai_turn.content, "done": True})
                if response.ai_turn.audio_url:
                    self.send_message(
                        {
                            "event": "AI_AUDIO_URL",
                            "url": response.ai_turn.audio_url,
                            "text": response.ai_turn.content,
                        }
                    )
            except Exception as exc:
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

    def _build_hint(self, session: Session) -> str:
        # Kept for backward compatibility — use_hint now calls _generate_contextual_hint
        if session.selected_goals:
            return f"Hãy thử nói ngắn gọn về: {session.selected_goals[0]}"
        return "Hãy trả lời bằng một câu ngắn, rõ ý."


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
    submit_turn_use_case = SubmitSpeakingTurnUseCase(
        session_repo,
        turn_repo,
        ComprehendTranscriptAnalysisService(),
        BedrockConversationGenerationService(),
        PollySpeechSynthesisService(),
    )
    complete_use_case = CompleteSpeakingSessionUseCase(session_repo, turn_repo, scoring_repo, BedrockScorerAdapter())

    return WebSocketSessionController(
        session_repo=session_repo,
        turn_repo=turn_repo,
        stt_service=TranscribeSTTService(),
        streaming_stt_service=StreamingSTTServiceSync(),
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
            return controller.start_session(str(session_id), connection_id)
        if action == "AUDIO_UPLOADED":
            return controller.audio_uploaded(str(session_id), connection_id, body)
        if action == "START_STREAMING":
            return controller.start_streaming(str(session_id), connection_id)
        if action == "AUDIO_CHUNK":
            return controller.audio_chunk(str(session_id), connection_id, body)
        if action == "END_STREAMING":
            return controller.end_streaming(str(session_id), connection_id)
        if action == "SUBMIT_TRANSCRIPT":
            return controller.submit_transcript(str(session_id), connection_id, body)
        if action == "USE_HINT":
            return controller.use_hint(str(session_id), connection_id)
        if action == "END_SESSION":
            return controller.end_session(str(session_id), connection_id)
        if action == "SEND_MESSAGE":
            return controller.send_message_turn(str(session_id), connection_id, body)

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
