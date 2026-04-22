from application.use_cases.vocabulary.translate_sentence import TranslateSentenceUC
from interfaces.controllers.vocabulary_controller import VocabularyController


translate_sentence_uc = TranslateSentenceUC()
vocabulary_controller = VocabularyController(translate_sentence_use_case=translate_sentence_uc)


def handler(event, context):
    """Handler cho API dịch toàn bộ câu."""
    body_str = event.get("body")
    return vocabulary_controller.translate_sentence(body_str)
