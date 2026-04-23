from application.use_cases.vocabulary.translate_vocabulary import TranslateVocabularyUC
from infrastructure.services.aws_translate_service import AwsTranslateService
from interfaces.controllers.vocabulary_controller import VocabularyController

translate_vocabulary_uc = TranslateVocabularyUC(AwsTranslateService())
vocabulary_controller = VocabularyController(translate_vocabulary_uc)


def handler(event, context):
    """Handler cho API dịch từ vựng trong ngữ cảnh câu."""
    body_str = event.get("body")
    return vocabulary_controller.translate(body_str)
