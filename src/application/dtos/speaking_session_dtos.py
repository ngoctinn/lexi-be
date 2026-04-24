from typing import List, Optional

from pydantic import Field

from application.dtos.base_dto import BaseDTO


class SpeakingTurnResponse(BaseDTO):
    turn_index: int
    speaker: str
    content: str
    translated_content: str = ""
    audio_url: str = ""
    is_hint_used: bool = False
    is_saved_to_flashcard: bool = False
    is_pending: bool = False
    # Phase 5: Metrics fields
    ttft_ms: float | None = None
    latency_ms: float | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    delivery_cue: str = ""
    quality_score: float = 0.0


class SpeakingScoringResponse(BaseDTO):
    fluency: int
    pronunciation: int
    grammar: int
    vocabulary: int
    overall: int
    feedback: str = ""


class SpeakingSessionResponse(BaseDTO):
    session_id: str
    user_id: str
    scenario_id: str
    learner_role_id: str = ""
    ai_role_id: str = ""
    ai_gender: str
    level: str
    prompt_snapshot: str
    selected_goals: List[str] = Field(default_factory=list)
    total_turns: int = 0
    user_turns: int = 0
    hint_used_count: int = 0
    turns: List[SpeakingTurnResponse] = Field(default_factory=list)
    scoring: Optional[SpeakingScoringResponse] = None
    connection_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    status: str = "ACTIVE"
    # Metrics (Phase 5)
    assigned_model: str = ""
    avg_ttft_ms: float = 0.0
    avg_latency_ms: float = 0.0
    avg_output_tokens: int = 0
    total_cost_usd: float = 0.0


class CreateSpeakingSessionCommand(BaseDTO):
    user_id: str
    scenario_id: str
    learner_role_id: Optional[str] = None
    ai_role_id: Optional[str] = None
    ai_gender: str
    level: str
    selected_goals: List[str] = Field(default_factory=list)
    prompt_snapshot: str
    connection_id: Optional[str] = None


class CreateSpeakingSessionResponse(BaseDTO):
    success: bool = True
    session_id: str
    session: SpeakingSessionResponse


class SubmitSpeakingTurnCommand(BaseDTO):
    user_id: str
    session_id: str
    text: str
    is_hint_used: bool = False
    audio_url: Optional[str] = None


class SubmitSpeakingTurnResponse(BaseDTO):
    success: bool = True
    session: SpeakingSessionResponse
    user_turn: SpeakingTurnResponse
    ai_turn: SpeakingTurnResponse
    analysis_keywords: List[str] = Field(default_factory=list)


class CompleteSpeakingSessionCommand(BaseDTO):
    user_id: str
    session_id: str


class CompleteSpeakingSessionResponse(BaseDTO):
    success: bool = True
    session: SpeakingSessionResponse
    scoring: SpeakingScoringResponse


class GetSpeakingSessionResponse(BaseDTO):
    success: bool = True
    session: SpeakingSessionResponse


class ListSpeakingSessionsResponse(BaseDTO):
    success: bool = True
    sessions: List[SpeakingSessionResponse] = Field(default_factory=list)
