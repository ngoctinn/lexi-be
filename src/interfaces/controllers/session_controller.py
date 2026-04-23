import json
from typing import Any, Dict

from pydantic import ValidationError

from application.dtos.speaking_session_dtos import (
    CompleteSpeakingSessionResponse,
    CreateSpeakingSessionResponse,
    GetSpeakingSessionResponse,
    ListSpeakingSessionsResponse,
    SubmitSpeakingTurnResponse,
)
from application.use_cases.speaking_session_use_cases import (
    CompleteSpeakingSessionUseCase,
    CreateSpeakingSessionUseCase,
    GetSpeakingSessionUseCase,
    ListSpeakingSessionsUseCase,
    SubmitSpeakingTurnUseCase,
)
from interfaces.mapper.session_mapper import SessionMapper
from shared.http_utils import dumps


class SessionController:
    def __init__(
        self,
        create_use_case: CreateSpeakingSessionUseCase,
        get_use_case: GetSpeakingSessionUseCase,
        list_use_case: ListSpeakingSessionsUseCase,
        submit_turn_use_case: SubmitSpeakingTurnUseCase,
        complete_use_case: CompleteSpeakingSessionUseCase,
    ):
        self._create_use_case = create_use_case
        self._get_use_case = get_use_case
        self._list_use_case = list_use_case
        self._submit_turn_use_case = submit_turn_use_case
        self._complete_use_case = complete_use_case

    def _response(self, status: int, body: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "statusCode": status,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": dumps(body),
        }

    def create_session(self, user_id: str, body_str: str | None) -> Dict[str, Any]:
        try:
            body = json.loads(body_str or "{}")
        except json.JSONDecodeError:
            return self._response(400, {"error": "Định dạng JSON không hợp lệ."})

        try:
            command = SessionMapper.to_create_command(user_id, body)
            result = self._create_use_case.execute(command)
            if not result.is_success:
                return self._response(422, {"error": result.error})
            payload: CreateSpeakingSessionResponse = result.value
            return self._response(201, payload.model_dump())
        except ValidationError as exc:
            return self._response(400, {"error": "Dữ liệu yêu cầu không hợp lệ.", "details": exc.errors()})
        except Exception as exc:
            return self._response(500, {"error": f"Lỗi hệ thống: {str(exc)}"})

    def get_session(self, user_id: str, session_id: str) -> Dict[str, Any]:
        result = self._get_use_case.execute(user_id, session_id)
        if not result.is_success:
            return self._response(404, {"error": result.error})

        payload: GetSpeakingSessionResponse = result.value
        return self._response(200, payload.model_dump())

    def list_sessions(self, user_id: str, limit: int = 10) -> Dict[str, Any]:
        result = self._list_use_case.execute(user_id, limit)
        if not result.is_success:
            return self._response(500, {"error": result.error})

        payload: ListSpeakingSessionsResponse = result.value
        return self._response(200, payload.model_dump())

    def submit_turn(self, user_id: str, session_id: str, body_str: str | None) -> Dict[str, Any]:
        try:
            body = json.loads(body_str or "{}")
        except json.JSONDecodeError:
            return self._response(400, {"error": "Định dạng JSON không hợp lệ."})

        try:
            command = SessionMapper.to_submit_turn_command(user_id, session_id, body)
            result = self._submit_turn_use_case.execute(command)
            if not result.is_success:
                return self._response(422, {"error": result.error})

            payload: SubmitSpeakingTurnResponse = result.value
            return self._response(200, payload.model_dump())
        except ValidationError as exc:
            return self._response(400, {"error": "Dữ liệu yêu cầu không hợp lệ.", "details": exc.errors()})
        except Exception as exc:
            return self._response(500, {"error": f"Lỗi hệ thống: {str(exc)}"})

    def complete_session(self, user_id: str, session_id: str) -> Dict[str, Any]:
        try:
            command = SessionMapper.to_complete_command(user_id, session_id)
            result = self._complete_use_case.execute(command)
            if not result.is_success:
                return self._response(422, {"error": result.error})

            payload: CompleteSpeakingSessionResponse = result.value
            return self._response(200, payload.model_dump())
        except Exception as exc:
            return self._response(500, {"error": f"Lỗi hệ thống: {str(exc)}"})
