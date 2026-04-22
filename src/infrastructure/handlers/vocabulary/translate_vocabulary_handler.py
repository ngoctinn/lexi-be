from application.use_cases.vocabulary.translate_vocabulary import TranslateVocabularyUC
from infrastructure.persistence.dynamo_vocabulary_repo import DynamoVocabularyRepo
from infrastructure.services.dictionary_translate_vocabulary_service import DictionaryTranslateVocabularyService
from infrastructure.services.rule_based_phrasal_verb_detection_service import RuleBasedPhrasalVerbDetectionService
from interfaces.controllers.vocabulary_controller import VocabularyController


vocabulary_repo = DynamoVocabularyRepo()
vocabulary_source_service = DictionaryTranslateVocabularyService()
phrase_detector = RuleBasedPhrasalVerbDetectionService()
translate_vocabulary_uc = TranslateVocabularyUC(vocabulary_repo, vocabulary_source_service, phrase_detector)
vocabulary_controller = VocabularyController(translate_vocabulary_uc)


def handler(event, context):
    """Handler cho API dịch từ vựng."""
    body_str = event.get("body")
    return vocabulary_controller.translate(body_str)
