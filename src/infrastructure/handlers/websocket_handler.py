from __future__ import annotations

import json
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
    ComprehendTranscriptAnalysisService,
    PollySpeechSynthesisService,
    RuleBasedConversationGenerationService,
)
from shared.utils.ulid_util import new_ulid


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


def _extract_bearer_token(headers: dict[str, Any]) -> str:
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
    if not region or not user_pool_id:
        raise ValueError("Thiếu cấu hình Cognito để xác thực token.")

    issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
    jwks_client = PyJWKClient(f"{issuer}/.well-known/jwks.json")

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        claims = decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=issuer,
            options={"require": ["exp", "iss", "token_use", "sub"]},
        )
    except InvalidTokenError as exc:
        raise ValueError("Token không hợp lệ.") from exc

    token_use = claims.get("token_use")
    if token_use not in {"access", "id"}:
        raise ValueError("token_use không hợp lệ.")

    if app_client_id:
        if token_use == "access" and claims.get("client_id") != app_client_id:
            raise ValueError("client_id không hợp lệ.")
        if token_use == "id" and claims.get("aud") != app_client_id:
            raise ValueError("aud không hợp lệ.")

    return claims


def _session_gateway_endpoint(event: dict[str, Any]) -> str:
    request_context = event.get("requestContext") or {}
    domain_name = request_context.get("domainName")
    stage = request_context.get("stage")
    if not domain_name or not stage:
        raise ValueError("WebSocket requestContext thiếu domainName hoặc stage.")
    return f"https://{domain_name}/{stage}"


@dataclass
class WebSocketSessionController:
    session_repo: DynamoSessionRepo
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
            return _response(401, {"message": str(exc)})

        user_id = str(claims.get("sub") or "")
        if not user_id:
            return _response(401, {"message": "Token không hợp lệ."})
        if session.user_id != user_id:
            return _response(403, {"message": "Session không thuộc về người dùng này."})

        session.connection_id = connection_id
        self.session_repo.save(session)
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
        self.send_message(
            {
                "event": "STT_LOW_CONFIDENCE",
                "confidence": 0.0,
            }
        )
        return _response(200, {"message": "Audio uploaded"})

    def use_hint(self, session_id: str, connection_id: str) -> dict[str, Any]:
        session = self._get_session(session_id)
        if not session:
            return _response(404, {"message": "Session không tồn tại."})

        self._sync_connection(session, connection_id)
        hint = self._build_hint(session)
        self.send_message({"event": "HINT_TEXT", "hint": hint})
        return _response(200, {"message": "Hint sent"})

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
        if session.selected_goals:
            return f"Hãy thử nói ngắn gọn về: {session.selected_goals[0]}"
        return "Hãy trả lời bằng một câu ngắn, rõ ý."


def _build_upload_payload(session_id: str) -> tuple[str, str]:
    bucket_name = os.environ.get("SPEAKING_AUDIO_BUCKET_NAME")
    if not bucket_name:
        raise RuntimeError("Thiếu SPEAKING_AUDIO_BUCKET_NAME.")

    upload_key = f"speaking/audio/{session_id}/{new_ulid()}.webm"
    client = boto3.client("s3")
    upload_url = client.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": bucket_name, "Key": upload_key},
        ExpiresIn=900,
    )
    return upload_url, upload_key


@lru_cache(maxsize=1)
def get_websocket_controller() -> WebSocketSessionController:
    session_repo = DynamoSessionRepo()
    turn_repo = DynamoTurnRepo()
    scoring_repo = DynamoScoringRepo()
    submit_turn_use_case = SubmitSpeakingTurnUseCase(
        session_repo,
        turn_repo,
        ComprehendTranscriptAnalysisService(),
        RuleBasedConversationGenerationService(),
        PollySpeechSynthesisService(),
    )
    complete_use_case = CompleteSpeakingSessionUseCase(session_repo, turn_repo, scoring_repo)

    return WebSocketSessionController(
        session_repo=session_repo,
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

    # Extract params from queryStringParameters or body
    query_params = event.get("queryStringParameters") or {}
    session_id = body.get("session_id") or query_params.get("session_id")
    token = _extract_bearer_token(headers)

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
    if action == "USE_HINT":
        return controller.use_hint(str(session_id), connection_id)
    if action == "END_SESSION":
        return controller.end_session(str(session_id), connection_id)
    if action == "SEND_MESSAGE":
        return controller.send_message_turn(str(session_id), connection_id, body)

    return controller.unsupported(action or route_key or body.get("action", "UNKNOWN"))
