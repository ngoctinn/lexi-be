import json
import logging
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
from interfaces.presenters.http_presenter import HttpPresenter
from interfaces.view_models.base import OperationResult
from interfaces.view_models.session_vm import SpeakingSessionViewModel, SessionListViewModel
from shared.http_utils import dumps

logger = logging.getLogger(__name__)


class SessionController:
    def __init__(
        self,
        create_use_case: CreateSpeakingSessionUseCase,
        get_use_case: GetSpeakingSessionUseCase,
        list_use_case: ListSpeakingSessionsUseCase,
        submit_turn_use_case: SubmitSpeakingTurnUseCase,
        complete_use_case: CompleteSpeakingSessionUseCase,
        presenter: HttpPresenter | None = None,
    ):
        self._create_use_case = create_use_case
        self._get_use_case = get_use_case
        self._list_use_case = list_use_case
        self._submit_turn_use_case = submit_turn_use_case
        self._complete_use_case = complete_use_case
        self._presenter = presenter or HttpPresenter()

    def create_session(self, user_id: str, body_str: str | None) -> OperationResult[SpeakingSessionViewModel]:
        try:
            body = json.loads(body_str or "{}")
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in create_session request")
            return OperationResult.fail("Invalid JSON format", "BAD_REQUEST")

        try:
            logger.info("Creating speaking session", extra={"context": {"user_id": user_id}})
            command = SessionMapper.to_create_command(user_id, body)
            result = self._create_use_case.execute(command)
            if not result.is_success:
                logger.warning("Session creation failed", extra={"context": {"user_id": user_id, "error": result.error}})
                return OperationResult.fail(result.error, "CREATION_FAILED")
            
            payload: CreateSpeakingSessionResponse = result.value
            view_model = SpeakingSessionViewModel(
                session_id=payload.session_id,
                user_id=payload.session.user_id,
                scenario_id=payload.session.scenario_id,
                status=payload.session.status,
                created_at=payload.session.created_at,
            )
            logger.info("Session created successfully", extra={"context": {"user_id": user_id, "session_id": payload.session_id}})
            return OperationResult.succeed(view_model)
        except ValidationError as exc:
            logger.warning("Validation error in create_session", extra={"context": {"user_id": user_id, "errors": str(exc)}})
            return OperationResult.fail(f"Invalid request data: {str(exc)}", "VALIDATION_ERROR")
        except Exception as exc:
            logger.exception("Error creating session", extra={"context": {"user_id": user_id, "error": str(exc)}})
            raise

    def get_session(self, user_id: str, session_id: str) -> OperationResult[SpeakingSessionViewModel]:
        try:
            logger.info("Getting session", extra={"context": {"user_id": user_id, "session_id": session_id}})
            result = self._get_use_case.execute(user_id, session_id)
            if not result.is_success:
                logger.warning("Session not found", extra={"context": {"user_id": user_id, "session_id": session_id}})
                return OperationResult.fail(result.error, "NOT_FOUND")

            payload: GetSpeakingSessionResponse = result.value
            view_model = SpeakingSessionViewModel(
                session_id=payload.session.session_id,
                user_id=payload.session.user_id,
                scenario_id=payload.session.scenario_id,
                status=payload.session.status,
                created_at=payload.session.created_at,
            )
            return OperationResult.succeed(view_model)
        except Exception as exc:
            logger.exception("Error getting session", extra={"context": {"user_id": user_id, "session_id": session_id, "error": str(exc)}})
            raise

    def list_sessions(self, user_id: str, limit: int = 10) -> OperationResult[SessionListViewModel]:
        try:
            logger.info("Listing sessions", extra={"context": {"user_id": user_id, "limit": limit}})
            result = self._list_use_case.execute(user_id, limit)
            if not result.is_success:
                logger.error("Failed to list sessions", extra={"context": {"user_id": user_id, "error": result.error}})
                return OperationResult.fail(result.error, "LIST_FAILED")

            payload: ListSpeakingSessionsResponse = result.value
            sessions = [
                SpeakingSessionViewModel(
                    session_id=s.session_id,
                    user_id=s.user_id,
                    scenario_id=s.scenario_id,
                    status=s.status,
                    created_at=s.created_at,
                )
                for s in payload.sessions
            ]
            view_model = SessionListViewModel(sessions=sessions, total=payload.total)
            return OperationResult.succeed(view_model)
        except Exception as exc:
            logger.exception("Error listing sessions", extra={"context": {"user_id": user_id, "error": str(exc)}})
            raise

    def submit_turn(self, user_id: str, session_id: str, body_str: str | None) -> OperationResult[SpeakingSessionViewModel]:
        try:
            body = json.loads(body_str or "{}")
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in submit_turn request")
            return OperationResult.fail("Invalid JSON format", "BAD_REQUEST")

        try:
            logger.info("Submitting turn", extra={"context": {"user_id": user_id, "session_id": session_id}})
            command = SessionMapper.to_submit_turn_command(user_id, session_id, body)
            result = self._submit_turn_use_case.execute(command)
            if not result.is_success:
                logger.warning("Turn submission failed", extra={"context": {"user_id": user_id, "session_id": session_id, "error": result.error}})
                return OperationResult.fail(result.error, "SUBMISSION_FAILED")

            payload: SubmitSpeakingTurnResponse = result.value
            view_model = SpeakingSessionViewModel(
                session_id=payload.session.session_id,
                user_id=payload.session.user_id,
                scenario_id=payload.session.scenario_id,
                status=payload.session.status,
                created_at=payload.session.created_at,
            )
            logger.info("Turn submitted successfully", extra={"context": {"user_id": user_id, "session_id": session_id}})
            return OperationResult.succeed(view_model)
        except ValidationError as exc:
            logger.warning("Validation error in submit_turn", extra={"context": {"user_id": user_id, "session_id": session_id, "errors": str(exc)}})
            return OperationResult.fail(f"Invalid request data: {str(exc)}", "VALIDATION_ERROR")
        except Exception as exc:
            logger.exception("Error submitting turn", extra={"context": {"user_id": user_id, "session_id": session_id, "error": str(exc)}})
            raise

    def complete_session(self, user_id: str, session_id: str) -> OperationResult[SpeakingSessionViewModel]:
        try:
            logger.info("Completing session", extra={"context": {"user_id": user_id, "session_id": session_id}})
            command = SessionMapper.to_complete_command(user_id, session_id)
            result = self._complete_use_case.execute(command)
            if not result.is_success:
                logger.warning("Session completion failed", extra={"context": {"user_id": user_id, "session_id": session_id, "error": result.error}})
                return OperationResult.fail(result.error, "COMPLETION_FAILED")

            payload: CompleteSpeakingSessionResponse = result.value
            view_model = SpeakingSessionViewModel(
                session_id=payload.session.session_id,
                user_id=payload.session.user_id,
                scenario_id=payload.session.scenario_id,
                status=payload.session.status,
                created_at=payload.session.created_at,
            )
            logger.info("Session completed successfully", extra={"context": {"user_id": user_id, "session_id": session_id}})
            return OperationResult.succeed(view_model)
        except Exception as exc:
            logger.exception("Error completing session", extra={"context": {"user_id": user_id, "session_id": session_id, "error": str(exc)}})
            raise
