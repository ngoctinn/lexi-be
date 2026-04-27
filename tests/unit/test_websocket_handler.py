from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from application.service_ports.speaking_services import SpeakingAnalysis
from application.use_cases.speaking_session_use_cases import (
    CompleteSpeakingSessionUseCase,
    SubmitSpeakingTurnUseCase,
)
from domain.entities.scenario import Scenario
from domain.entities.session import Session
from domain.entities.turn import Turn
from domain.value_objects.enums import Gender, ProficiencyLevel, Speaker
from infrastructure.handlers.websocket_handler import WebSocketSessionController
from shared.utils.ulid_util import new_ulid


class FakeSessionRepository:
    def __init__(self, session: Session):
        self.sessions: dict[str, Session] = {str(session.session_id): session}
        self.saved_sessions: list[Session] = []

    def save(self, session: Session) -> None:
        self.sessions[str(session.session_id)] = session
        self.saved_sessions.append(session)

    def get_by_id(self, session_id: str):
        return self.sessions.get(session_id)


class FakeTurnRepository:
    def __init__(self):
        self.turns: dict[str, list[Turn]] = {}
        self.saved_turns: list[Turn] = []

    def save(self, turn: Turn) -> None:
        self.turns.setdefault(str(turn.session_id), []).append(turn)
        self.saved_turns.append(turn)

    def list_by_session(self, session_id: str):
        return sorted(self.turns.get(session_id, []), key=lambda item: item.turn_index)

    def delete_by_session(self, session_id: str) -> None:
        self.turns.pop(session_id, None)


class FakeScoringRepository:
    def __init__(self):
        self.saved_scoring = []

    def save(self, score) -> None:
        self.saved_scoring.append(score)

    def get_by_session(self, session_id: str):
        return []

    def get_user_progress(self, user_id: str, limit: int = 50):
        return []


class FakeAnalysisService:
    def analyze(self, text: str) -> SpeakingAnalysis:
        return SpeakingAnalysis(key_phrases=["coffee"], word_count=4, unique_word_count=4, sentence_count=1)


class FakeConversationService:
    def generate_reply(self, session, user_turn, analysis, turn_history):
        return "Sure, what size would you like?"


class FakeSpeechService:
    def synthesize(self, text: str, ai_character: str, object_key: str | None = None) -> str:
        return "https://audio.example.com/reply.mp3"


def build_controller(session: Session):
    session_repo = FakeSessionRepository(session)
    turn_repo = FakeTurnRepository()
    scoring_repo = FakeScoringRepository()
    sender_payloads: list[dict] = []

    submit_use_case = SubmitSpeakingTurnUseCase(
        session_repo,
        turn_repo,
        FakeAnalysisService(),
        FakeConversationService(),
        FakeSpeechService(),
    )
    complete_use_case = CompleteSpeakingSessionUseCase(session_repo, turn_repo, scoring_repo)

    controller = WebSocketSessionController(
        session_repo=session_repo,
        turn_repo=turn_repo,
        stt_service=None,  # Not used in these tests
        transcribe_url_generator=None,  # Not used in these tests
        submit_turn_use_case=submit_use_case,
        complete_use_case=complete_use_case,
        build_upload_payload=lambda session_id: ("https://upload.example.com", f"sessions/{session_id}/audio.webm"),
        send_message=lambda payload: sender_payloads.append(payload),
        verify_token=lambda token: {"sub": "user-1"} if token == "valid-token" else (_ for _ in ()).throw(ValueError("Token không hợp lệ.")),
    )
    return controller, session_repo, turn_repo, scoring_repo, sender_payloads


def test_connect_accepts_valid_token_and_persists_connection_id():
    session = Session(
        session_id=new_ulid(),
        scenario_id="scenario-1",
        user_id="user-1",
        learner_role_id="customer",
        ai_role_id="barista",
        ai_character="Sarah",
        level=ProficiencyLevel.B1,
        selected_goal="order drink",
        prompt_snapshot="Prompt",
    )
    controller, session_repo, _, _, _ = build_controller(session)

    response = controller.connect(str(session.session_id), "valid-token", "conn-1")

    assert response["statusCode"] == 200
    assert session_repo.saved_sessions[-1].connection_id == "conn-1"


def test_start_session_emits_session_ready_payload():
    session = Session(
        session_id=new_ulid(),
        scenario_id="scenario-1",
        user_id="user-1",
        learner_role_id="customer",
        ai_role_id="barista",
        ai_character="Sarah",
        level=ProficiencyLevel.B1,
        selected_goal="order drink",
        prompt_snapshot="Prompt",
    )
    controller, _, _, _, sender_payloads = build_controller(session)

    response = controller.start_session(str(session.session_id), "conn-1")

    assert response["statusCode"] == 200
    assert sender_payloads[0]["event"] == "SESSION_READY"
    assert sender_payloads[0]["upload_url"] == "https://upload.example.com"
    assert sender_payloads[0]["s3_key"] == f"sessions/{session.session_id}/audio.webm"


def test_send_message_emits_turn_saved_and_ai_response():
    session = Session(
        session_id=new_ulid(),
        scenario_id="scenario-1",
        user_id="user-1",
        learner_role_id="customer",
        ai_role_id="barista",
        ai_character="Sarah",
        level=ProficiencyLevel.B1,
        selected_goal="order drink",
        prompt_snapshot="Prompt",
    )
    controller, session_repo, turn_repo, _, sender_payloads = build_controller(session)

    response = controller.send_message_turn(
        str(session.session_id),
        "conn-1",
        {"text": "I want a medium coffee."},
    )

    assert response["statusCode"] == 200
    assert session_repo.saved_sessions[-1].connection_id == "conn-1"
    assert len(turn_repo.saved_turns) == 2
    assert sender_payloads[0]["event"] == "TURN_SAVED"
    assert sender_payloads[1]["event"] == "AI_RESPONSE"
    assert "text" in sender_payloads[1]


def test_end_session_emits_scoring_complete():
    session = Session(
        session_id=new_ulid(),
        scenario_id="scenario-1",
        user_id="user-1",
        learner_role_id="customer",
        ai_role_id="barista",
        ai_character="Sarah",
        level=ProficiencyLevel.B1,
        selected_goal="order drink",
        prompt_snapshot="Prompt",
    )
    controller, _, _, scoring_repo, sender_payloads = build_controller(session)

    response = controller.end_session(str(session.session_id), "conn-1")

    assert response["statusCode"] == 200
    assert sender_payloads[-1]["event"] == "SCORING_COMPLETE"
    assert sender_payloads[-1]["session_id"] == str(session.session_id)
    assert scoring_repo.saved_scoring
