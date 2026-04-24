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
from infrastructure.services.bedrock_scoring_service import BedrockScoringService
from infrastructure.services.speaking_pipeline_services import (
    BedrockConversationGenerationService,
    ComprehendTranscriptAnalysisService,
    PollySpeechSynthesisService,
    TranscribeSTTService,
)
from infrastructure.services.streaming_stt_service_sync import StreamingSTTServiceSync
from shared.utils.ulid_util import new_ulid

logger = logging.getLogger(__name__)


def _response(status: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
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
        
        # Decode without audience validation first to check token_use
        claims = decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=issuer,
            options={"require": ["exp", "iss", "token_use", "sub"], "verify_aud": False},
        )
        print(f"[ws] Token decoded: token_use={claims.get('token_use')}, aud={claims.get('aud')}, sub={claims.get('sub')}")
    except InvalidTokenError as exc:
        print(f"[ws] JWT decode error: {exc}")
        raise ValueError("Token không hợp lệ.") from exc
    except Exception as exc:
        print(f"[ws] Unexpected error during token verification: {exc}")
        raise ValueError("Token không hợp lệ.") from exc

    token_use = claims.get("token_use")
    if token_use not in {"access", "id"}:
        print(f"[ws] Invalid token_use: {token_use}")
        raise ValueError("token_use không hợp lệ.")

    # For ID tokens, verify aud matches app_client_id
    # For access tokens, verify client_id matches app_client_id
    if app_client_id:
        if token_use == "id":
            aud = claims.get("aud")
            if aud != app_client_id:
                print(f"[ws] ID token aud mismatch: {aud} != {app_client_id}")
                raise ValueError("aud không hợp lệ.")
        elif token_use == "access":
            client_id = claims.get("client_id")
            if client_id != app_client_id:
                print(f"[ws] Access token client_id mismatch: {client_id} != {app_client_id}")
                raise ValueError("client_id không hợp lệ.")

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
        if not session_id:
            return _response(400, {"message": "Thiếu session_id."})

        session = self.session_repo.get_by_id(session_id)
        if not session:
            return _response(404, {"message": "Session không tồn tại."})

        try:
            claims = self.verify_token(token)
        except ValueError as exc:
            print(f"[ws] Token verification failed: {exc} (token_length={len(token) if token else 0})")
            return _response(401, {"message": str(exc)})

        user_id = str(claims.get("sub") or "")
        if not user_id:
            print(f"[ws] Token missing 'sub' claim")
            return _response(401, {"message": "Token không hợp lệ."})
        if session.user_id != user_id:
            print(f"[ws] Session user_id mismatch: session.user_id={session.user_id} token.sub={user_id}")
            return _response(403, {"message": "Session không thuộc về người dùng này."})

        session.connection_id = connection_id
        self.session_repo.save(session)
        print(f"[ws] Connected: session_id={session_id} user_id={user_id} connection_id={connection_id}")
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
        self.send_message(
            {
                "event": "SESSION_READY",
                "upload_url": upload_url,
                "s3_key": upload_key,
                "session_id": session_id,
            }
        )
        return _response(200, {"message": "Session ready"})

    def audio_uploaded(self, session_id: str, connection_id: str, body: dict[str, Any]) -> dict[str, Any]:
        session = self._get_session(session_id)
        if not session:
            return _response(404, {"message": "Session không tồn tại."})

        self._sync_connection(session, connection_id)

        s3_key = body.get("s3_key", "")
        bucket = os.environ.get("SPEAKING_AUDIO_BUCKET_NAME", "")

        if not s3_key or not bucket:
            self.send_message({"event": "STT_LOW_CONFIDENCE", "confidence": 0.0})
            return _response(400, {"message": "Thiếu s3_key hoặc bucket."})

        # Gọi Transcribe để chuyển audio → text
        text, confidence = self.stt_service.transcribe(bucket, s3_key)

        if not text or confidence < 0.5:
            self.send_message({"event": "STT_LOW_CONFIDENCE", "confidence": confidence})
            return _response(200, {"message": "STT low confidence"})

        # Gửi kết quả STT về client
        self.send_message({"event": "STT_RESULT", "text": text, "confidence": confidence})

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
            self.send_message({"event": "ERROR", "message": result.error or "Lỗi xử lý lượt nói."})
            return _response(422, {"message": result.error or "Lỗi xử lý lượt nói."})

        response = result.value
        self.send_message({"event": "TURN_SAVED", "turn_index": response.user_turn.turn_index})
        self.send_message({"event": "AI_TEXT_CHUNK", "chunk": response.ai_turn.content, "done": True})
        if response.ai_turn.audio_url:
            self.send_message({
                "event": "AI_AUDIO_URL",
                "url": response.ai_turn.audio_url,
                "text": response.ai_turn.content,
            })

        return _response(200, {"message": "Audio processed"})

    def use_hint(self, session_id: str, connection_id: str) -> dict[str, Any]:
        session = self._get_session(session_id)
        if not session:
            return _response(404, {"message": "Session không tồn tại."})

        self._sync_connection(session, connection_id)
        turns = self.turn_repo.list_by_session(session_id)
        hint = self._generate_contextual_hint(session, turns)
        self.send_message({"event": "HINT_TEXT", "hint": hint})
        return _response(200, {"message": "Hint sent"})

    def _generate_contextual_hint(self, session: Session, turns: list) -> str:
        """Tạo hint có ngữ cảnh dùng Bedrock LLM."""
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
            import boto3, json
            bedrock = boto3.client("bedrock-runtime")
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 60,
                "messages": [{"role": "user", "content": hint_prompt}],
                "temperature": 0.5,
            })
            response = bedrock.invoke_model(
                modelId="anthropic.claude-3-haiku-20240307-v1:0",
                body=body,
            )
            result = json.loads(response["body"].read())
            return result["content"][0]["text"].strip()
        except Exception:
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
            self.send_message({"event": "ERROR", "message": result.error or "Lỗi xử lý lượt nói."})
            return _response(422, {"message": result.error or "Lỗi xử lý lượt nói."})

        response = result.value
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
            self.send_message({"event": "ERROR", "message": result.error or "Không thể kết thúc session."})
            return _response(422, {"message": result.error or "Không thể kết thúc session."})

        self.send_message(
            {
                "event": "SCORING_COMPLETE",
                "session_id": session_id,
            }
        )
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

            self.send_message({"event": "STREAMING_READY", "session_id": session_id})
            return _response(200, {"message": "Streaming ready"})

        except Exception as exc:
            logger.exception("Failed to start streaming", extra={"session_id": session_id})
            self.send_message({"event": "STT_ERROR", "message": "Không thể khởi động streaming."})
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
                if transcript.is_partial:
                    self.send_message(
                        {
                            "event": "PARTIAL_TRANSCRIPT",
                            "text": transcript.text,
                            "confidence": transcript.confidence,
                        }
                    )
                else:
                    self.send_message(
                        {
                            "event": "FINAL_TRANSCRIPT",
                            "text": transcript.text,
                            "confidence": transcript.confidence,
                        }
                    )

            return _response(200, {"message": "Chunk processed"})

        except Exception as exc:
            logger.exception("Failed to process audio chunk", extra={"session_id": session_id})
            self.send_message({"event": "STT_ERROR", "message": "Lỗi xử lý audio chunk."})
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
                confidence = final_transcript.confidence if final_transcript else 0.0
                self.send_message({"event": "STT_LOW_CONFIDENCE", "confidence": confidence})
                return _response(200, {"message": "Low confidence"})

            # Send final transcript
            self.send_message(
                {
                    "event": "FINAL_TRANSCRIPT",
                    "text": final_transcript.text,
                    "confidence": final_transcript.confidence,
                }
            )

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
                self.send_message({"event": "ERROR", "message": result.error or "Lỗi xử lý lượt nói."})
                return _response(422, {"message": result.error or "Lỗi xử lý lượt nói."})

            response = result.value
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

            return _response(200, {"message": "Streaming ended"})

        except Exception as exc:
            logger.exception("Failed to end streaming", extra={"session_id": session_id})
            _put_cloudwatch_metric("StreamErrors", 1, "Count")
            self.send_message({"event": "STT_ERROR", "message": "Lỗi kết thúc streaming."})
            return _response(500, {"message": str(exc)})

    def submit_transcript(self, session_id: str, connection_id: str, body: dict[str, Any]) -> dict[str, Any]:
        """Process final transcript from client-side streaming."""
        session = self._get_session(session_id)
        if not session:
            return _response(404, {"message": "Session không tồn tại."})

        text = str(body.get("text") or "").strip()
        confidence = float(body.get("confidence") or 0.0)

        if not text or confidence < 0.5:
            self.send_message({"event": "STT_LOW_CONFIDENCE", "confidence": confidence})
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
                self.send_message({"event": "ERROR", "message": result.error or "Lỗi xử lý lượt nói."})
                return _response(422, {"message": result.error or "Lỗi xử lý lượt nói."})

            response = result.value
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

            return _response(200, {"message": "Transcript processed"})

        except Exception as exc:
            logger.exception("Failed to process transcript", extra={"session_id": session_id})
            self.send_message({"event": "ERROR", "message": "Lỗi xử lý transcript."})
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
    complete_use_case = CompleteSpeakingSessionUseCase(session_repo, turn_repo, scoring_repo, BedrockScoringService())

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
            client.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps(payload).encode("utf-8"),
            )
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code != "GoneException":
                raise

    return send_message


def handler(event, context):
    base_controller = get_websocket_controller()
    route_key = (event.get("requestContext") or {}).get("routeKey", "")
    connection_id = (event.get("requestContext") or {}).get("connectionId", "")
    body = _parse_json_body(event.get("body"))
    headers = event.get("headers") or {}
    query_params = event.get("queryStringParameters") or {}

    # Extract params from queryStringParameters or body
    session_id = body.get("session_id") or query_params.get("session_id")
    token = _extract_bearer_token(headers, query_params)

    action = route_key if route_key not in {"$default"} else str(body.get("action") or "")

    controller = replace(base_controller, send_message=_make_sender(event, connection_id))

    if route_key == "$connect":
        return base_controller.connect(str(session_id or ""), str(token or ""), connection_id)

    if route_key == "$disconnect":
        return base_controller.disconnect(str(session_id or "") or None, connection_id)

    if not session_id:
        return _response(400, {"message": "Thiếu session_id."})

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
