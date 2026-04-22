from application.use_cases.vocabulary.analyze_sentence import AnalyzeSentenceUC
from infrastructure.services.rule_based_phrasal_verb_detection_service import (
    RuleBasedPhrasalVerbDetectionService,
)
from interfaces.controllers.vocabulary_controller import VocabularyController


detection_service = RuleBasedPhrasalVerbDetectionService()
analyze_sentence_uc = AnalyzeSentenceUC(detection_service)
vocabulary_controller = VocabularyController(analyze_use_case=analyze_sentence_uc)


def handler(event, context):
    body_str = event.get("body")
    return vocabulary_controller.analyze(body_str)
