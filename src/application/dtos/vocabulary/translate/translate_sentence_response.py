from application.dtos.base_dto import BaseDTO


class TranslateSentenceResponse(BaseDTO):
    sentence_en: str
    sentence_vi: str  # Bản dịch toàn câu bằng AWS Translate
