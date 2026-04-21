from __future__ import annotations

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
from application.repositories.scenario_repository import ScenarioRepository
from application.repositories.session_repository import SessionRepository
from application.repositories.turn_repository import TurnRepository
from application.services.speaking_services import (
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
    for role in [scenario.my_character, scenario.ai_character, *scenario.user_roles, *scenario.ai_roles]:
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

            learner_role_id = (request.learner_role_id or scenario.my_character or allowed_roles[0]).strip()
            ai_role_id = (request.ai_role_id or scenario.ai_character or allowed_roles[1]).strip()
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
                scoring_items = self._scoring_repo.get_by_session(str(session.session_id))
                scoring = scoring_items[0] if scoring_items else None
                session_responses.append(_session_to_response(session, [], scoring))

            return Result.success(
                ListSpeakingSessionsResponse(success=True, sessions=session_responses)
            )
        except Exception as exc:
            return Result.failure(str(exc))


class SubmitSpeakingTurnUseCase:
    def __init__(
        self,
        session_repo: SessionRepository,
        turn_repo: TurnRepository,
        transcript_analysis_service: TranscriptAnalysisService,
        conversation_generation_service: ConversationGenerationService,
        speech_synthesis_service: SpeechSynthesisService,
    ):
        self._session_repo = session_repo
        self._turn_repo = turn_repo
        self._transcript_analysis_service = transcript_analysis_service
        self._conversation_generation_service = conversation_generation_service
        self._speech_synthesis_service = speech_synthesis_service

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

            try:
                ai_text = self._conversation_generation_service.generate_reply(
                    session=session,
                    user_turn=user_turn,
                    analysis=analysis,
                    turn_history=existing_turns,
                )
            except Exception:
                ai_text = "Thanks. Could you say a bit more about that?"

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


class CompleteSpeakingSessionUseCase:
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
        self, request: CompleteSpeakingSessionCommand
    ) -> Result[CompleteSpeakingSessionResponse, str]:
        try:
            session = self._session_repo.get_by_id(request.session_id)
            if not session:
                return Result.failure("Phiên học không tồn tại.")
            if session.user_id != request.user_id:
                return Result.failure("Phiên học không thuộc về người dùng này.")

            turns = self._turn_repo.list_by_session(request.session_id)
            scoring_items = self._scoring_repo.get_by_session(request.session_id)
            scoring = scoring_items[0] if scoring_items else self._build_scoring(session, turns)

            scoring.feedback = scoring.feedback or self._build_feedback(scoring)
            scoring.calculate_overall()
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
            return Result.failure(str(exc))

    def _build_scoring(self, session: Session, turns: List[Turn]) -> Scoring:
        user_turns = [turn for turn in turns if _is_user_turn(turn)]
        user_text = " ".join(turn.content for turn in user_turns).strip()
        words = re.findall(r"[A-Za-z']+", user_text.lower())
        unique_words = len(set(words))
        word_count = len(words)
        turn_count = max(1, len(user_turns))
        sentence_count = max(1, len(re.findall(r"[.!?]", user_text)) or 1)

        fluency_score = _clamp(64 + turn_count * 4 - session.hint_used_count * 3)
        pronunciation_score = _clamp(68 + min(16, word_count // 3) - session.hint_used_count * 2)
        grammar_score = _clamp(60 + min(24, unique_words // 2) + min(10, sentence_count * 2))
        vocabulary_score = _clamp(62 + min(26, unique_words // 2) + min(8, word_count // 20))
        overall_score = round(
            (fluency_score + pronunciation_score + grammar_score + vocabulary_score) / 4
        )

        feedback = self._build_feedback(
            fluency_score=fluency_score,
            pronunciation_score=pronunciation_score,
            grammar_score=grammar_score,
            vocabulary_score=vocabulary_score,
        )

        scoring = Scoring(
            scoring_id=new_ulid(),
            session_id=session.session_id,
            user_id=session.user_id,
            fluency_score=fluency_score,
            pronunciation_score=pronunciation_score,
            grammar_score=grammar_score,
            vocabulary_score=vocabulary_score,
            overall_score=overall_score,
            feedback=feedback,
        )
        return scoring

    def _build_feedback(
        self,
        fluency_score: int,
        pronunciation_score: int,
        grammar_score: int,
        vocabulary_score: int,
    ) -> str:
        feedback_parts: List[str] = []
        if fluency_score < 75:
            feedback_parts.append("Hãy nói dài hơn và giữ nhịp câu ổn định hơn.")
        if pronunciation_score < 75:
            feedback_parts.append("Hãy chú ý nhấn âm rõ hơn khi luyện đọc.")
        if grammar_score < 75:
            feedback_parts.append("Hãy kiểm tra lại cấu trúc câu và thì động từ.")
        if vocabulary_score < 75:
            feedback_parts.append("Hãy thử dùng thêm từ nối và từ vựng đa dạng hơn.")

        if not feedback_parts:
            feedback_parts.append("Bạn làm tốt. Hãy tiếp tục luyện để phản xạ tự nhiên hơn.")

        return " ".join(feedback_parts)
