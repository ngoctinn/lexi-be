from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from application.dtos.speaking_session_dtos import (
    CompleteSpeakingSessionCommand,
    CreateSpeakingSessionCommand,
    SubmitSpeakingTurnCommand,
)
from application.services.speaking_services import SpeakingAnalysis
from application.use_cases.speaking_session_use_cases import (
    CompleteSpeakingSessionUseCase,
    CreateSpeakingSessionUseCase,
    SubmitSpeakingTurnUseCase,
)
from domain.entities.scoring import Scoring
from domain.entities.scenario import Scenario
from domain.entities.session import Session
from domain.entities.turn import Turn
from domain.value_objects.enums import Gender, ProficiencyLevel, Speaker
from shared.utils.ulid_util import new_ulid


class FakeSessionRepository:
    def __init__(self, session: Session | None = None):
        self.sessions: dict[str, Session] = {}
        self.saved_sessions: list[Session] = []
        if session:
            self.sessions[str(session.session_id)] = session

    def save(self, session: Session) -> None:
        self.sessions[str(session.session_id)] = session
        self.saved_sessions.append(session)

    def get_by_id(self, session_id: str):
        return self.sessions.get(session_id)

    def get_active_session(self, user_id: str):
        for session in self.sessions.values():
            if session.user_id == user_id and session.status != "COMPLETED":
                return session
        return None

    def list_by_user(self, user_id: str, limit: int = 10):
        sessions = [session for session in self.sessions.values() if session.user_id == user_id]
        return sessions[:limit]


class FakeScenarioRepository:
    def __init__(self, scenario: Scenario | None = None):
        self.scenarios: dict[str, Scenario] = {}
        self.saved_scenarios: list[Scenario] = []
        if scenario:
            self.scenarios[str(scenario.scenario_id)] = scenario

    def list_active(self):
        return [scenario for scenario in self.scenarios.values() if scenario.is_active]

    def get_by_id(self, scenario_id: str):
        return self.scenarios.get(str(scenario_id))

    def save(self, scenario: Scenario) -> None:
        self.scenarios[str(scenario.scenario_id)] = scenario
        self.saved_scenarios.append(scenario)


class FakeTurnRepository:
    def __init__(self, turns: list[Turn] | None = None):
        self.turns_by_session: dict[str, list[Turn]] = {}
        self.saved_turns: list[Turn] = []
        for turn in turns or []:
            self.turns_by_session.setdefault(str(turn.session_id), []).append(turn)

    def save(self, turn: Turn) -> None:
        self.turns_by_session.setdefault(str(turn.session_id), []).append(turn)
        self.saved_turns.append(turn)

    def list_by_session(self, session_id: str):
        return sorted(self.turns_by_session.get(session_id, []), key=lambda item: item.turn_index)

    def delete_by_session(self, session_id: str) -> None:
        self.turns_by_session.pop(session_id, None)


class FakeScoringRepository:
    def __init__(self, scoring: Scoring | None = None):
        self.scorings_by_session: dict[str, list[Scoring]] = {}
        self.saved_scoring: list[Scoring] = []
        if scoring:
            self.scorings_by_session.setdefault(str(scoring.session_id), []).append(scoring)

    def save(self, score: Scoring) -> None:
        self.scorings_by_session.setdefault(str(score.session_id), []).append(score)
        self.saved_scoring.append(score)

    def get_by_session(self, session_id: str):
        return self.scorings_by_session.get(session_id, [])

    def get_user_progress(self, user_id: str, limit: int = 50):
        progress: list[Scoring] = []
        for scores in self.scorings_by_session.values():
            for score in scores:
                if score.user_id == user_id:
                    progress.append(score)
        return progress[:limit]


class FakeAnalysisService:
    def __init__(self, analysis: SpeakingAnalysis | None = None):
        self.analysis = analysis or SpeakingAnalysis(key_phrases=["coffee order"], word_count=4, unique_word_count=4, sentence_count=1)

    def analyze(self, text: str) -> SpeakingAnalysis:
        return self.analysis


class FakeConversationService:
    def __init__(self, reply: str = "Please tell me more."):
        self.reply = reply

    def generate_reply(self, session, user_turn, analysis, turn_history):
        return self.reply


class FakeSpeechService:
    def __init__(self, audio_url: str = "data:audio/mpeg;base64,ZmFrZQ=="):
        self.audio_url = audio_url
        self.calls: list[tuple[str, str, str | None]] = []

    def synthesize(self, text: str, ai_gender: str, object_key: str | None = None) -> str:
        self.calls.append((text, ai_gender, object_key))
        return self.audio_url


def test_create_speaking_session_persists_assignment_and_prompt_snapshot():
    scenario = Scenario(
        scenario_id="scenario-1",
        scenario_title="Gọi cà phê",
        context="Tại quán cà phê",
        my_character="Khách hàng",
        ai_character="Barista",
        goals=["Chọn đồ uống", "Chọn size", "Hỏi về giá"],
        user_roles=["Khách hàng", "Barista"],
        ai_roles=["Khách hàng", "Barista"],
        is_active=True,
        usage_count=1,
    )
    repo = FakeSessionRepository()
    scenario_repo = FakeScenarioRepository(scenario)
    use_case = CreateSpeakingSessionUseCase(repo, scenario_repo)

    result = use_case.execute(
        CreateSpeakingSessionCommand(
            user_id="user-1",
            scenario_id="scenario-1",
            learner_role_id="Khách hàng",
            ai_role_id="Barista",
            ai_gender="female",
            level="B1",
            selected_goals=["Chọn đồ uống"],
            prompt_snapshot="client should be ignored",
        )
    )

    assert result.is_success
    assert result.value is not None
    assert result.value.session_id
    saved_session = repo.saved_sessions[-1]
    assert saved_session.learner_role_id == "Khách hàng"
    assert saved_session.ai_role_id == "Barista"
    assert saved_session.prompt_snapshot.startswith("Prompt version: v1")
    assert "Gọi cà phê" in saved_session.prompt_snapshot
    assert "Chọn đồ uống" in saved_session.prompt_snapshot
    assert saved_session.status == "ACTIVE"


def test_submit_turn_saves_user_and_ai_turns_and_updates_session_counts():
    session_id = new_ulid()
    session = Session(
        session_id=session_id,
        scenario_id="scenario-1",
        user_id="user-1",
        learner_role_id="customer",
        ai_role_id="barista",
        ai_gender=Gender.FEMALE,
        level=ProficiencyLevel.B1,
        selected_goals=["order drink"],
        prompt_snapshot="Scenario: cafe",
    )
    session_repo = FakeSessionRepository(session)
    turn_repo = FakeTurnRepository()
    use_case = SubmitSpeakingTurnUseCase(
        session_repo,
        turn_repo,
        FakeAnalysisService(),
        FakeConversationService("Sure, what size would you like?"),
        FakeSpeechService(),
    )

    result = use_case.execute(
        SubmitSpeakingTurnCommand(
            user_id="user-1",
            session_id=session_id,
            text="I want a medium coffee.",
            is_hint_used=True,
        )
    )

    assert result.is_success
    assert result.value is not None
    assert result.value.session.total_turns == 2
    assert result.value.session.user_turns == 1
    assert result.value.session.hint_used_count == 1
    assert len(turn_repo.saved_turns) == 2
    assert turn_repo.saved_turns[0].speaker == Speaker.USER
    assert turn_repo.saved_turns[1].speaker == Speaker.AI
    assert result.value.ai_turn.audio_url == "data:audio/mpeg;base64,ZmFrZQ=="
    assert turn_repo.saved_turns[0].content == "I want a medium coffee."
    assert use_case._speech_synthesis_service.calls[0][2] == f"speaking/audio/{session_id}/1.mp3"


def test_complete_session_builds_scoring_and_marks_session_completed():
    session_id = new_ulid()
    session = Session(
        session_id=session_id,
        scenario_id="scenario-1",
        user_id="user-1",
        learner_role_id="customer",
        ai_role_id="barista",
        ai_gender=Gender.FEMALE,
        level=ProficiencyLevel.B1,
        selected_goals=["order drink"],
        prompt_snapshot="Scenario: cafe",
        total_turns=2,
        user_turns=1,
    )
    turn_repo = FakeTurnRepository(
        [
            Turn(
                session_id=session_id,
                turn_index=0,
                speaker=Speaker.USER,
                content="I want a medium coffee.",
                is_hint_used=False,
            ),
            Turn(
                session_id=session_id,
                turn_index=1,
                speaker=Speaker.AI,
                content="Sure, what size would you like?",
                is_hint_used=False,
            ),
        ]
    )
    session_repo = FakeSessionRepository(session)
    scoring_repo = FakeScoringRepository()
    use_case = CompleteSpeakingSessionUseCase(session_repo, turn_repo, scoring_repo)

    result = use_case.execute(
        CompleteSpeakingSessionCommand(user_id="user-1", session_id=session_id)
    )

    assert result.is_success
    assert result.value is not None
    assert result.value.session.status == "COMPLETED"
    assert result.value.scoring.overall > 0
    assert scoring_repo.saved_scoring
    assert scoring_repo.saved_scoring[0].feedback
