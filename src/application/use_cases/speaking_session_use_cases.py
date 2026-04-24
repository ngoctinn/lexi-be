from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import List, Optional

from application.dtos.speaking_session_dtos import (
    CompleteSpeakingSessionCommand,
    CompleteSpeakingSessionResponse,
    CreateSpeakingSessionCommand,
    CreateSpeakingSessionResponse,
    GetSpeakingSessionResponse,
    ListSpeakingSessionsResponse,
    SpeakingScoringResponse,
    SpeakingSessionResponse,
    SpeakingTurnResponse,
    SubmitSpeakingTurnCommand,
    SubmitSpeakingTurnResponse,
)
from application.repositories.scoring_repository import ScoringRepository

logger = logging.getLogger(__name__)
from application.repositories.scenario_repository import ScenarioRepository
from application.repositories.session_repository import SessionRepository
from application.repositories.turn_repository import TurnRepository
from application.service_ports.speaking_services import (
    ConversationGenerationService,
    SpeakingAnalysis,
    SpeechSynthesisService,
    TranscriptAnalysisService,
)
from domain.entities.scoring import Scoring
from domain.entities.scenario import Scenario
from domain.entities.session import Session
from domain.entities.turn import Turn
from domain.services.prompt_builder import build_session_prompt
from domain.value_objects.enums import Gender, ProficiencyLevel, Speaker
from shared.result import Result
from shared.utils.ulid_util import new_ulid


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _enum_value(value: object) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _clamp(value: int, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(maximum, value))


def _is_user_turn(turn: Turn) -> bool:
    return _enum_value(turn.speaker) == Speaker.USER.value


def _scenario_roles(scenario: Scenario) -> list[str]:
    roles: list[str] = []
    for role in scenario.roles:
        cleaned = str(role).strip()
        if cleaned and cleaned not in roles:
            roles.append(cleaned)
    return roles


def _turn_to_response(turn: Turn) -> SpeakingTurnResponse:
    return SpeakingTurnResponse(
        turn_index=turn.turn_index,
        speaker=_enum_value(turn.speaker),
        content=turn.content,
        translated_content=turn.translated_content,
        audio_url=turn.audio_url,
        is_hint_used=turn.is_hint_used,
        # Metrics (Phase 5) - Keep Decimal, DecimalEncoder will handle JSON serialization
        ttft_ms=turn.ttft_ms,
        latency_ms=turn.latency_ms,
        input_tokens=turn.input_tokens,
        output_tokens=turn.output_tokens,
        cost_usd=turn.cost_usd,
        delivery_cue=turn.delivery_cue,
    )


def _scoring_to_response(scoring: Scoring) -> SpeakingScoringResponse:
    return SpeakingScoringResponse(
        fluency=scoring.fluency_score,
        pronunciation=scoring.pronunciation_score,
        grammar=scoring.grammar_score,
        vocabulary=scoring.vocabulary_score,
        overall=scoring.overall_score,
        feedback=scoring.feedback,
    )


def _session_to_response(
    session: Session,
    turns: Optional[List[Turn]] = None,
    scoring: Optional[Scoring] = None,
) -> SpeakingSessionResponse:
    ordered_turns = sorted(turns or [], key=lambda item: item.turn_index)
    return SpeakingSessionResponse(
        session_id=str(session.session_id),
        user_id=session.user_id,
        scenario_id=str(session.scenario_id),
        learner_role_id=session.learner_role_id,
        ai_role_id=session.ai_role_id,
        ai_gender=_enum_value(session.ai_gender),
        level=_enum_value(session.level),
        prompt_snapshot=session.prompt_snapshot,
        selected_goals=list(session.selected_goals),
        total_turns=session.total_turns,
        user_turns=session.user_turns,
        hint_used_count=session.hint_used_count,
        turns=[_turn_to_response(turn) for turn in ordered_turns],
        scoring=_scoring_to_response(scoring) if scoring else None,
        connection_id=session.connection_id or None,
        created_at=session.created_at or None,
        updated_at=session.updated_at or None,
        status=session.status,
        # Metrics (Phase 5) - Keep Decimal, DecimalEncoder will handle JSON serialization
        assigned_model=session.assigned_model,
        avg_ttft_ms=session.avg_ttft_ms,
        avg_latency_ms=session.avg_latency_ms,
        avg_output_tokens=session.avg_output_tokens,
        total_cost_usd=session.total_cost_usd,
    )


class CreateSpeakingSessionUseCase:
    def __init__(self, session_repo: SessionRepository, scenario_repo: ScenarioRepository):
        self._session_repo = session_repo
        self._scenario_repo = scenario_repo

    def execute(
        self, request: CreateSpeakingSessionCommand
    ) -> Result[CreateSpeakingSessionResponse, str]:
        try:
            scenario = self._scenario_repo.get_by_id(request.scenario_id)
            if not scenario:
                return Result.failure("Kịch bản không tồn tại.")
            if not scenario.is_active:
                return Result.failure("Kịch bản đã bị vô hiệu hóa.")

            allowed_roles = _scenario_roles(scenario)
            if len(allowed_roles) < 2:
                return Result.failure("Kịch bản phải có ít nhất 2 vai để tạo session.")

            selected_goals = list(request.selected_goals or [])
            if not selected_goals:
                selected_goals = list(scenario.goals)
            if not selected_goals:
                return Result.failure("Kịch bản không có goal hợp lệ để tạo session.")

            invalid_goals = [goal for goal in selected_goals if goal not in scenario.goals]
            if invalid_goals:
                return Result.failure("Selected goals phải nằm trong danh sách goals của kịch bản.")

            learner_role_id = (request.learner_role_id or allowed_roles[0]).strip()
            if request.ai_role_id:
                ai_role_id = request.ai_role_id.strip()
            else:
                ai_role_id = next((role for role in allowed_roles if role != learner_role_id), "")
            if learner_role_id == ai_role_id:
                return Result.failure("learner_role_id và ai_role_id phải khác nhau.")
            if learner_role_id not in allowed_roles or ai_role_id not in allowed_roles:
                return Result.failure("Vai được chọn không thuộc kịch bản.")

            session_id = new_ulid()
            now = _now_iso()
            prompt_snapshot = build_session_prompt(
                scenario_title=scenario.scenario_title,
                context=scenario.context,
                learner_role=learner_role_id,
                ai_role=ai_role_id,
                level=request.level,
                selected_goals=selected_goals,
                ai_gender=request.ai_gender,
            )

            session = Session(
                session_id=session_id,
                scenario_id=request.scenario_id,
                user_id=request.user_id,
                learner_role_id=learner_role_id,
                ai_role_id=ai_role_id,
                ai_gender=Gender(request.ai_gender),
                level=ProficiencyLevel(request.level),
                selected_goals=selected_goals,
                prompt_snapshot=prompt_snapshot,
                status="ACTIVE",
                connection_id=request.connection_id or "",
                created_at=now,
                updated_at=now,
            )

            self._session_repo.save(session)
            response = CreateSpeakingSessionResponse(
                success=True,
                session_id=session_id,
                session=_session_to_response(session, []),
            )
            return Result.success(response)
        except Exception as exc:
            return Result.failure(str(exc))


class GetSpeakingSessionUseCase:
    def __init__(
        self,
        session_repo: SessionRepository,
        turn_repo: TurnRepository,
        scoring_repo: ScoringRepository,
    ):
        self._session_repo = session_repo
        self._turn_repo = turn_repo
        self._scoring_repo = scoring_repo

    def execute(
        self, user_id: str, session_id: str
    ) -> Result[GetSpeakingSessionResponse, str]:
        try:
            session = self._session_repo.get_by_id(session_id)
            if not session:
                return Result.failure("Phiên học không tồn tại.")
            if session.user_id != user_id:
                return Result.failure("Phiên học không thuộc về người dùng này.")

            turns = self._turn_repo.list_by_session(session_id)
            scoring_items = self._scoring_repo.get_by_session(session_id)
            scoring = scoring_items[0] if scoring_items else None
            response = GetSpeakingSessionResponse(
                success=True,
                session=_session_to_response(session, turns, scoring),
            )
            return Result.success(response)
        except Exception as exc:
            return Result.failure(str(exc))


class ListSpeakingSessionsUseCase:
    def __init__(
        self,
        session_repo: SessionRepository,
        scoring_repo: ScoringRepository,
    ):
        self._session_repo = session_repo
        self._scoring_repo = scoring_repo

    def execute(
        self, user_id: str, limit: int = 10
    ) -> Result[ListSpeakingSessionsResponse, str]:
        try:
            sessions = self._session_repo.list_by_user(user_id, limit=limit)
            session_responses = []
            for session in sessions:
                try:
                    scoring_items = self._scoring_repo.get_by_session(str(session.session_id))
                    scoring = scoring_items[0] if scoring_items else None
                except Exception as e:
                    logger.warning(f"Failed to get scoring for session {session.session_id}: {e}")
                    scoring = None
                
                session_responses.append(_session_to_response(session, [], scoring))

            return Result.success(
                ListSpeakingSessionsResponse(
                    success=True, 
                    sessions=session_responses,
                    total=len(session_responses)
                )
            )
        except Exception as exc:
            logger.exception(f"ListSpeakingSessionsUseCase failed: {exc}")
            return Result.failure(str(exc))


class SubmitSpeakingTurnUseCase:
    def __init__(
        self,
        session_repo: SessionRepository,
        turn_repo: TurnRepository,
        transcript_analysis_service: TranscriptAnalysisService,
        conversation_generation_service: ConversationGenerationService,
        speech_synthesis_service: SpeechSynthesisService,
        conversation_orchestrator: "ConversationOrchestrator | None" = None,
    ):
        self._session_repo = session_repo
        self._turn_repo = turn_repo
        self._transcript_analysis_service = transcript_analysis_service
        self._conversation_generation_service = conversation_generation_service
        self._speech_synthesis_service = speech_synthesis_service
        self._conversation_orchestrator = conversation_orchestrator

    def execute(
        self, request: SubmitSpeakingTurnCommand
    ) -> Result[SubmitSpeakingTurnResponse, str]:
        try:
            session = self._session_repo.get_by_id(request.session_id)
            if not session:
                return Result.failure("Phiên học không tồn tại.")
            if session.user_id != request.user_id:
                return Result.failure("Phiên học không thuộc về người dùng này.")

            content = request.text.strip()
            if not content:
                return Result.failure("Nội dung lượt nói không được để trống.")

            existing_turns = self._turn_repo.list_by_session(request.session_id)
            turn_index = len(existing_turns)

            try:
                analysis = self._transcript_analysis_service.analyze(content)
            except Exception:
                analysis = SpeakingAnalysis()

            user_turn = Turn(
                session_id=session.session_id,
                turn_index=turn_index,
                speaker=Speaker.USER,
                content=content,
                audio_url=request.audio_url or "",
                translated_content="",
                is_hint_used=request.is_hint_used,
            )
            self._turn_repo.save(user_turn)

            # Generate AI response with orchestrator or fallback
            ai_text, delivery_cue, ttft_ms, latency_ms, input_tokens, output_tokens, cost_usd = self._generate_ai_response(
                session=session,
                user_turn=user_turn,
                analysis=analysis,
                turn_history=existing_turns,
            )

            try:
                ai_audio_url = self._speech_synthesis_service.synthesize(
                    ai_text,
                    _enum_value(session.ai_gender),
                    object_key=f"speaking/audio/{session.session_id}/{turn_index + 1}.mp3",
                )
            except Exception:
                ai_audio_url = ""

            ai_turn = Turn(
                session_id=session.session_id,
                turn_index=turn_index + 1,
                speaker=Speaker.AI,
                content=ai_text,
                audio_url=ai_audio_url,
                translated_content="",
                is_hint_used=False,
                # Metrics (Phase 5)
                delivery_cue=delivery_cue,
                ttft_ms=ttft_ms,
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
            )
            self._turn_repo.save(ai_turn)

            user_turn_count = len([turn for turn in existing_turns if _is_user_turn(turn)]) + 1
            hint_used_count = len([turn for turn in existing_turns if turn.is_hint_used])
            if request.is_hint_used:
                hint_used_count += 1

            session.total_turns = turn_index + 2
            session.user_turns = user_turn_count
            session.hint_used_count = hint_used_count
            session.updated_at = _now_iso()
            
            # Phase 5: Update session metrics (aggregation)
            self._update_session_metrics(session, ai_turn)
            
            self._session_repo.save(session)

            updated_turns = self._turn_repo.list_by_session(request.session_id)
            response = SubmitSpeakingTurnResponse(
                success=True,
                session=_session_to_response(session, updated_turns),
                user_turn=_turn_to_response(user_turn),
                ai_turn=_turn_to_response(ai_turn),
                analysis_keywords=list(analysis.key_phrases),
            )
            return Result.success(response)
        except Exception as exc:
            return Result.failure(str(exc))

    def _update_session_metrics(self, session: Session, ai_turn: Turn) -> None:
        """
        Update session metrics with new AI turn metrics.
        Calculates running averages for TTFT, latency, and total cost.
        """
        from decimal import Decimal
        
        # Count AI turns (every other turn starting from index 1)
        ai_turn_count = (session.total_turns + 1) // 2
        
        if ai_turn_count == 0:
            return
        
        # Update TTFT average
        if ai_turn.ttft_ms is not None:
            old_avg = session.avg_ttft_ms
            session.avg_ttft_ms = Decimal(str((float(old_avg) * (ai_turn_count - 1) + float(ai_turn.ttft_ms)) / ai_turn_count))
        
        # Update latency average
        if ai_turn.latency_ms is not None:
            old_avg = session.avg_latency_ms
            session.avg_latency_ms = Decimal(str((float(old_avg) * (ai_turn_count - 1) + float(ai_turn.latency_ms)) / ai_turn_count))
        
        # Update output tokens average
        old_avg = session.avg_output_tokens
        session.avg_output_tokens = int((old_avg * (ai_turn_count - 1) + ai_turn.output_tokens) / ai_turn_count)
        
        # Update total cost
        session.total_cost_usd += ai_turn.cost_usd

    def _generate_ai_response(
        self,
        session: Session,
        user_turn: Turn,
        analysis: SpeakingAnalysis,
        turn_history: list[Turn],
    ) -> tuple[str, str, Decimal | None, Decimal | None, int, int, Decimal]:
        """
        Generate AI response using orchestrator or fallback service.
        
        Returns: (ai_text, delivery_cue, ttft_ms, latency_ms, input_tokens, output_tokens, cost_usd)
        """
        from decimal import Decimal
        
        # Try orchestrator first (Phase 5)
        if self._conversation_orchestrator is not None:
            try:
                from domain.services.conversation_orchestrator import ConversationGenerationRequest
                
                orch_request = ConversationGenerationRequest(
                    session=session,
                    user_turn=user_turn,
                    turn_history=turn_history,
                    analysis=analysis,
                )
                orch_response = self._conversation_orchestrator.generate_response(orch_request)
                
                return (
                    orch_response.ai_text,
                    orch_response.delivery_cue,
                    orch_response.ttft_ms,
                    orch_response.latency_ms,
                    orch_response.input_tokens,
                    orch_response.output_tokens,
                    orch_response.cost_usd,
                )
            except Exception as e:
                logger.exception(f"ConversationOrchestrator failed: {str(e)}, using fallback service")
        
        # Fallback to conversation_generation_service
        try:
            ai_text = self._conversation_generation_service.generate_reply(
                session=session,
                user_turn=user_turn,
                analysis=analysis,
                turn_history=turn_history,
            )
        except Exception as e:
            logger.exception(f"ConversationGenerationService failed: {str(e)}, using default response")
            ai_text = "Thanks. Could you say a bit more about that?"
        
        # Return with no metrics (fallback mode) - use Decimal for consistency
        return (ai_text, "", None, None, 0, 0, Decimal("0.0"))


class CompleteSpeakingSessionUseCase:
    def __init__(
        self,
        session_repo: SessionRepository,
        turn_repo: TurnRepository,
        scoring_repo: ScoringRepository,
        performance_scorer=None,
    ):
        self._session_repo = session_repo
        self._turn_repo = turn_repo
        self._scoring_repo = scoring_repo
        self._performance_scorer = performance_scorer

    def execute(
        self, request: CompleteSpeakingSessionCommand
    ) -> Result[CompleteSpeakingSessionResponse, str]:
        try:
            session = self._session_repo.get_by_id(request.session_id)
            if not session:
                return Result.failure("Phiên học không tồn tại.")
            if session.user_id != request.user_id:
                return Result.failure("Phiên học không thuộc về người dùng này.")

            turns = self._turn_repo.list_by_session(request.session_id)
            
            # Check if scoring already exists
            scoring_items = self._scoring_repo.get_by_session(request.session_id)
            if scoring_items:
                scoring = scoring_items[0]
            else:
                # Use domain service for scoring (with optional external scorer)
                user_turns = [turn for turn in turns if _is_user_turn(turn)]
                scoring_data = self._performance_scorer.score_session(
                    user_turns=user_turns,
                    level=_enum_value(session.level),
                    scenario_title=str(session.scenario_id),
                )
                scoring = Scoring(
                    scoring_id=new_ulid(),
                    session_id=session.session_id,
                    user_id=session.user_id,
                    fluency_score=scoring_data["fluency_score"],
                    pronunciation_score=scoring_data["pronunciation_score"],
                    grammar_score=scoring_data["grammar_score"],
                    vocabulary_score=scoring_data["vocabulary_score"],
                    overall_score=scoring_data["overall_score"],
                    feedback=scoring_data["feedback"],
                )

            self._scoring_repo.save(scoring)

            session.status = "COMPLETED"
            session.updated_at = _now_iso()
            self._session_repo.save(session)

            response = CompleteSpeakingSessionResponse(
                success=True,
                session=_session_to_response(session, turns, scoring),
                scoring=_scoring_to_response(scoring),
            )
            return Result.success(response)
        except Exception as exc:
            logger.exception(f"CompleteSpeakingSessionUseCase failed: {exc}")
            return Result.failure(str(exc))


