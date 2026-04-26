from functools import lru_cache

from application.use_cases.speaking_session_use_cases import (
    CompleteSpeakingSessionUseCase,
    CreateSpeakingSessionUseCase,
    GetSpeakingSessionUseCase,
    ListSpeakingSessionsUseCase,
    SubmitSpeakingTurnUseCase,
)
from domain.services.conversation_orchestrator import ConversationOrchestrator
from domain.services.greeting_generator import GreetingGenerator
from domain.services.model_router import ModelRouter
from domain.services.prompt_builder import OptimizedPromptBuilder
from domain.services.streaming_response import StreamingResponse
from domain.services.response_validator import ResponseValidator
from domain.services.metrics_logger import MetricsLogger
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
from interfaces.controllers.session_controller import SessionController


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
    
    # Build ConversationOrchestrator with bedrock client
    if conversation_orchestrator is None:
        from infrastructure.services.speaking_pipeline_services import _bedrock_client
        
        conversation_orchestrator = ConversationOrchestrator(
            model_router=ModelRouter(),
            streaming_response=StreamingResponse(bedrock_client=_bedrock_client),
            response_validator=ResponseValidator(),
            metrics_logger=MetricsLogger(),
            bedrock_client=_bedrock_client,
        )
    
    # Build SpeakingPerformanceScorer with Bedrock adapter
    if performance_scorer is None:
        bedrock_adapter = BedrockScorerAdapter()
        performance_scorer = SpeakingPerformanceScorer(external_scorer=bedrock_adapter)

    # Create GreetingGenerator with bedrock client
    from infrastructure.services.speaking_pipeline_services import _bedrock_client
    greeting_generator = GreetingGenerator(bedrock_client=_bedrock_client)

    create_use_case = CreateSpeakingSessionUseCase(
        session_repo,
        scenario_repo,
        turn_repo,
        greeting_generator,
        speech_synthesis_service,
    )
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


@lru_cache(maxsize=1)
def get_session_controller() -> SessionController:
    return build_session_controller()


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
    session_controller = get_session_controller()
    try:
        user_id = event["requestContext"]["authorizer"]["claims"]["sub"]
    except KeyError:
        return _unauthorized_response()

    method = event.get("httpMethod", "").upper()
    resource = event.get("resource") or event.get("path") or ""
    path_parameters = event.get("pathParameters") or {}
    query_parameters = event.get("queryStringParameters") or {}

    if method == "POST" and resource == "/sessions":
        return session_controller.create_session(user_id, event.get("body"))

    if method == "GET" and resource == "/sessions":
        limit = int(query_parameters.get("limit", 10) or 10)
        return session_controller.list_sessions(user_id, limit)

    session_id = path_parameters.get("session_id") or path_parameters.get("id")
    if not session_id:
        return {
            "statusCode": 404,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": '{"error": "Not Found"}',
        }

    if method == "GET" and resource == "/sessions/{session_id}":
        return session_controller.get_session(user_id, session_id)

    if method == "POST" and resource == "/sessions/{session_id}/turns":
        return session_controller.submit_turn(user_id, session_id, event.get("body"))

    if method == "POST" and resource == "/sessions/{session_id}/complete":
        return session_controller.complete_session(user_id, session_id)

    return {
        "statusCode": 404,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": '{"error": "Not Found"}',
    }
