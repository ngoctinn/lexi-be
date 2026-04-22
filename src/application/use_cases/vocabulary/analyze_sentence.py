from application.dtos.vocabulary.analyze.analyze_sentence_command import AnalyzeSentenceCommand
from application.dtos.vocabulary.analyze.analyze_sentence_response import (
    AnalyzeSentenceItem,
    AnalyzeSentenceResponse,
)
from application.services.phrasal_verb_detection_service import PhrasalVerbDetectionService
from shared.result import Result


class AnalyzeSentenceUC:
    def __init__(self, detection_service: PhrasalVerbDetectionService):
        self._detection_service = detection_service

    def execute(self, command: AnalyzeSentenceCommand) -> Result[AnalyzeSentenceResponse, Exception]:
        try:
            analyzed_tokens = self._detection_service.analyze(command.text)
            response = AnalyzeSentenceResponse(
                items=[
                    AnalyzeSentenceItem(
                        text=item.text,
                        type=item.token_type,
                        base=item.base,
                        definition_vi=item.definition_vi,
                    )
                    for item in analyzed_tokens
                ]
            )
            return Result.success(response)
        except Exception as exc:
            return Result.failure(exc)
