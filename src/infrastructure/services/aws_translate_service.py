import os
import logging

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from application.services.translation_service import TranslationService

logger = logging.getLogger(__name__)

# Reuse boto3 client — tránh tạo mới mỗi lần gọi (Lambda warm start)
_client = None


def _get_client():
    global _client
    if _client is None:
        region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
        _client = boto3.client("translate", region_name=region) if region else boto3.client("translate")
    return _client


class AwsTranslateService(TranslationService):
    """Adapter: AWS Translate → TranslationService port."""

    def translate_en_to_vi(self, text: str) -> str:
        if not text:
            return text
        try:
            response = _get_client().translate_text(
                Text=text,
                SourceLanguageCode="en",
                TargetLanguageCode="vi",
            )
            return response.get("TranslatedText", text)
        except (ClientError, BotoCoreError):
            logger.exception("AWS Translate failed for text: %.50s", text)
            return text
