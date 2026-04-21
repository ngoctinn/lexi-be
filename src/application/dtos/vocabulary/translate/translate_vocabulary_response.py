from application.dtos.base_dto import BaseDTO


class TranslateVocabularyResponse(BaseDTO):
    word: str
    translation_vi: str
    part_of_speech: str
    definition_vi: str
    phonetic: str = ""
    audio_url: str = ""
    example_sentence: str = ""
    source_api: str = ""
