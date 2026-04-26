from typing import Any, Dict

from application.dtos.speaking_session_dtos import (
    CompleteSpeakingSessionCommand,
    CreateSpeakingSessionCommand,
    SubmitSpeakingTurnCommand,
)


class SessionMapper:
    @staticmethod
    def _as_list(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]
        text = str(value).strip()
        return [text] if text else []

    @staticmethod
    def to_create_command(user_id: str, body: Dict[str, Any]) -> CreateSpeakingSessionCommand:
        return CreateSpeakingSessionCommand(
            user_id=user_id,
            scenario_id=body.get("scenario_id", ""),
            learner_role_id=body.get("learner_role_id") or None,
            ai_role_id=body.get("ai_role_id") or None,
            ai_gender=body.get("ai_gender", "female"),
            level=body.get("level", "B1"),
            selected_goal=body.get("selected_goal", ""),
            prompt_snapshot=body.get("prompt_snapshot", ""),
            connection_id=body.get("connection_id") or None,
        )

    @staticmethod
    def to_submit_turn_command(
        user_id: str,
        session_id: str,
        body: Dict[str, Any],
    ) -> SubmitSpeakingTurnCommand:
        text = body.get("text") or body.get("transcript") or body.get("content") or ""
        return SubmitSpeakingTurnCommand(
            user_id=user_id,
            session_id=session_id,
            text=text,
            is_hint_used=bool(body.get("is_hint_used", False)),
            audio_url=body.get("audio_url") or None,
        )

    @staticmethod
    def to_complete_command(user_id: str, session_id: str) -> CompleteSpeakingSessionCommand:
        return CompleteSpeakingSessionCommand(user_id=user_id, session_id=session_id)
