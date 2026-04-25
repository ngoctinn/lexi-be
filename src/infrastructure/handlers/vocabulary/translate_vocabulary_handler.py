import logging

from application.use_cases.vocabulary_use_cases import TranslateVocabularyUseCase
from infrastructure.service_factory import ServiceFactory
from infrastructure.logging.config import configure_logging
from interfaces.controllers.vocabulary_controller import VocabularyController
from interfaces.presenters.http_presenter import HttpPresenter

# Configure logging
configure_logging("lambda")
logger = logging.getLogger(__name__)

translate_service = ServiceFactory.create_translation_service()
translate_vocabulary_uc = TranslateVocabularyUseCase(translate_service)
vocabulary_controller = VocabularyController(translate_vocabulary_uc)


def handler(event, context):
    """Handler for vocabulary translation API.
    
    Authentication is handled by API Gateway Cognito Authorizer.
    User ID is available in event["requestContext"]["authorizer"]["claims"]["sub"].
    """
    try:
        # Get user_id from Cognito claims (validated by API Gateway)
        user_id = event["requestContext"]["authorizer"]["claims"]["sub"]
        logger.info("Processing vocabulary translation", extra={"context": {"user_id": user_id}})
    except KeyError:
        # This should never happen if API Gateway Cognito Authorizer is configured correctly
        logger.error("Missing Cognito claims - check API Gateway authorizer configuration")
        return {
            "statusCode": 401,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": '{"error": "Unauthorized"}',
        }
    
    try:
        body_str = event.get("body")
        presenter = HttpPresenter()
        result = vocabulary_controller.translate(body_str)
        
        if result.is_success:
            return presenter.present_success(result.success)
        else:
            error = result.error
            return presenter._format_response(400, {
                "error": error.message,
                "code": error.code or "ERROR"
            })
    except Exception as e:
        logger.exception("Error in vocabulary translation", extra={"context": {"error": str(e)}})
        raise
