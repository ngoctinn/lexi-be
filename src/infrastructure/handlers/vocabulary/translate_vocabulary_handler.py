from application.use_cases.vocabulary.translate_vocabulary import TranslateVocabularyUC
from infrastructure.persistence.dynamo_vocabulary_repo import DynamoVocabularyRepo
from infrastructure.services.dictionary_translate_vocabulary_service import DictionaryTranslateVocabularyService
from interfaces.controllers.vocabulary_controller import VocabularyController


vocabulary_repo = DynamoVocabularyRepo()
vocabulary_source_service = DictionaryTranslateVocabularyService()
translate_vocabulary_uc = TranslateVocabularyUC(vocabulary_repo, vocabulary_source_service)
vocabulary_controller = VocabularyController(translate_vocabulary_uc)


def handler(event, context):
    """Handler cho API dịch từ vựng trong ngữ cảnh câu."""
    body_str = event.get("body")
    return vocabulary_controller.translate(body_str)
