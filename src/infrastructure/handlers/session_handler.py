import logging

from application.use_cases.speaking_session_use_cases import (
    CompleteSpeakingSessionUseCase,
    CreateSpeakingSessionUseCase,
    GetSpeakingSessionUseCase,
    ListSpeakingSessionsUseCase,
    SubmitSpeakingTurnUseCase,
)
from domain.services.conversation_orchestrator import ConversationOrchestrator
from domain.services.model_router import ModelRouter
from domain.services.prompt_builder import OptimizedPromptBuilder
from domain.services.streaming_response import StreamingResponse
from domain.services.response_validator import ResponseValidator
from domain.services.metrics_logger import MetricsLogger
from domain.services.scaffolding_system import ScaffoldingSystem
from domain.services.speaking_performance_scorer import SpeakingPerformanceScorer
from infrastructure.persistence.dynamo_scoring_repo import DynamoScoringRepo
from infrastructure.persistence.dynamo_scenario_repo import DynamoScenarioRepository
from infrastructure.persistence.dynamo_session_repo import DynamoSessionRepo
from infrastructure.persistence.dynamo_turn_repo import DynamoTurnRepo
from infrastructure.services.speaking_pipeline_services import (
    BedrockConversationGenerationService,
    ComprehendTranscriptAnalysisService,
    PollySpeechSynthesisService,
)
from infrastructure.services.bedrock_scorer_adapter import BedrockScorerAdapter
from infrastructure.logging.config import configure_logging
from interfaces.controllers.session_controller import SessionController
from interfaces.presenters.http_presenter import HttpPresenter

# Configure logging
configure_logging("lambda")
logger = logging.getLogger(__name__)

# Module-level singleton (AWS best practice)
# Initialized once per Lambda container, reused across invocations
_session_controller = None


def build_session_controller(
    session_repo=None,
    turn_repo=None,
    scoring_repo=None,
    scenario_repo=None,
    transcript_analysis_service=None,
    conversation_generation_service=None,
    speech_synthesis_service=None,
    conversation_orchestrator=None,
    performance_scorer=None,
) -> SessionController:
    session_repo = session_repo or DynamoSessionRepo()
    turn_repo = turn_repo or DynamoTurnRepo()
    scoring_repo = scoring_repo or DynamoScoringRepo()
    scenario_repo = scenario_repo or DynamoScenarioRepository()
    transcript_analysis_service = transcript_analysis_service or ComprehendTranscriptAnalysisService()
    conversation_generation_service = conversation_generation_service or BedrockConversationGenerationService()
    speech_synthesis_service = speech_synthesis_service or PollySpeechSynthesisService()
    
    # Build ConversationOrchestrator (without QualityScorer)
    if conversation_orchestrator is None:
        conversation_orchestrator = ConversationOrchestrator(
            model_router=ModelRouter(),
            prompt_builder=OptimizedPromptBuilder(),
            streaming_response=StreamingResponse(),
            response_validator=ResponseValidator(),
            metrics_logger=MetricsLogger(),
            scaffolding_system=ScaffoldingSystem(),
        )
    
    # Build SpeakingPerformanceScorer with Bedrock adapter
    if performance_scorer is None:
        bedrock_adapter = BedrockScorerAdapter()
        performance_scorer = SpeakingPerformanceScorer(external_scorer=bedrock_adapter)

    create_use_case = CreateSpeakingSessionUseCase(session_repo, scenario_repo)
    get_use_case = GetSpeakingSessionUseCase(session_repo, turn_repo, scoring_repo)
    list_use_case = ListSpeakingSessionsUseCase(session_repo, scoring_repo)
    submit_turn_use_case = SubmitSpeakingTurnUseCase(
        session_repo,
        turn_repo,
        transcript_analysis_service,
        conversation_generation_service,
        speech_synthesis_service,
        conversation_orchestrator=conversation_orchestrator,
    )
    complete_use_case = CompleteSpeakingSessionUseCase(
        session_repo,
        turn_repo,
        scoring_repo,
        performance_scorer=performance_scorer,
    )

    return SessionController(
        create_use_case=create_use_case,
        get_use_case=get_use_case,
        list_use_case=list_use_case,
        submit_turn_use_case=submit_turn_use_case,
        complete_use_case=complete_use_case,
    )


def _get_or_build_controller() -> SessionController:
    """
    Lazy initialization of session controller (singleton pattern).
    
    AWS best practice: Initialize SDK clients and dependencies outside handler
    to take advantage of execution environment reuse. This function is called
    once per Lambda container and the result is cached for subsequent invocations.
    
    Returns:
        SessionController: Reusable controller instance
    """
    global _session_controller
    if _session_controller is None:
        logger.info("Building session controller (first invocation in this container)")
        _session_controller = build_session_controller()
    return _session_controller


def _unauthorized_response():
    return {
        "statusCode": 401,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": '{"error": "Unauthorized"}',
    }


def handler(event, context):
    session_controller = _get_or_build_controller()
    presenter = HttpPresenter()
    
    try:
        user_id = event["requestContext"]["authorizer"]["claims"]["sub"]
        logger.info("Session handler invoked", extra={"context": {"user_id": user_id}})
    except KeyError:
        logger.warning("Unauthorized access attempt")
        return _unauthorized_response()

    method = event.get("httpMethod", "").upper()
    resource = event.get("resource") or event.get("path") or ""
    path_parameters = event.get("pathParameters") or {}
    query_parameters = event.get("queryStringParameters") or {}

    try:
        if method == "POST" and resource == "/sessions":
            result = session_controller.create_session(user_id, event.get("body"))
            if result.is_success:
                return presenter.present_created(result.success)
            else:
                return presenter._format_response(400, {"error": result.error.message, "code": result.error.code})

        if method == "GET" and resource == "/sessions":
            limit = int(query_parameters.get("limit", 10) or 10)
            result = session_controller.list_sessions(user_id, limit)
            if result.is_success:
                return presenter.present_success(result.success)
            else:
                return presenter._format_response(400, {"error": result.error.message, "code": result.error.code})

        session_id = path_parameters.get("session_id") or path_parameters.get("id")
        if not session_id:
            logger.warning("Session ID not provided")
            return presenter.present_not_found("Session not found")

        if method == "GET" and resource == "/sessions/{session_id}":
            result = session_controller.get_session(user_id, session_id)
            if result.is_success:
                return presenter.present_success(result.success)
            else:
                return presenter._format_response(400, {"error": result.error.message, "code": result.error.code})

        if method == "POST" and resource == "/sessions/{session_id}/turns":
            result = session_controller.submit_turn(user_id, session_id, event.get("body"))
            if result.is_success:
                return presenter.present_success(result.success)
            else:
                return presenter._format_response(400, {"error": result.error.message, "code": result.error.code})

        if method == "POST" and resource == "/sessions/{session_id}/complete":
            result = session_controller.complete_session(user_id, session_id)
            if result.is_success:
                return presenter.present_success(result.success)
            else:
                return presenter._format_response(400, {"error": result.error.message, "code": result.error.code})

        logger.warning("Route not found", extra={"context": {"method": method, "resource": resource}})
        return presenter.present_not_found("Not Found")
    except Exception as e:
        logger.exception("Error in session handler", extra={"context": {"user_id": user_id, "error": str(e)}})
        return presenter._format_response(500, {"success": False, "message": "Internal server error", "error": str(e)})
