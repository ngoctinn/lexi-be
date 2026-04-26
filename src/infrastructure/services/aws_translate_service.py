import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from application.service_ports.translation_service import TranslationService

logger = logging.getLogger(__name__)

# Reuse boto3 client — tránh tạo mới mỗi lần gọi (Lambda warm start)
_client = None

# Max concurrent requests (AWS Translate limit ~30 req/s, use 10 for safety)
MAX_WORKERS = 10


def _get_client():
    global _client
    if _client is None:
        region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
        _client = boto3.client("translate", region_name=region) if region else boto3.client("translate")
    return _client


class AwsTranslateService(TranslationService):
    """Adapter: AWS Translate → TranslationService port.
    
    Uses ThreadPoolExecutor for parallel translation to reduce latency:
    - Single text: Direct translation
    - Multiple texts: Parallel translation with max 10 concurrent requests
    - Graceful error handling: Returns original text on failure
    """

    def translate_en_to_vi(self, text: str) -> str:
        """Translate single text from English to Vietnamese.
        
        Args:
            text: English text to translate
        
        Returns:
            Translated Vietnamese text, or original text if translation fails
        """
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

    def translate_batch(self, texts: list[str]) -> list[str]:
        """Translate multiple texts in parallel using ThreadPoolExecutor.
        
        Args:
            texts: List of texts to translate
        
        Returns:
            List of translated texts (same order as input)
        
        Behavior:
            - Empty list → returns empty list
            - Single item → translates directly (no threading overhead)
            - Multiple items → parallel translation with ThreadPoolExecutor
            - On error → returns original text for failed items (graceful degradation)
        
        Performance:
            - 7 items: ~200-400ms (vs 1200ms sequential)
            - Uses max 10 concurrent workers (AWS Translate limit ~30 req/s)
        """
        if not texts:
            return []
        
        # Single item: translate directly (no threading overhead)
        if len(texts) == 1:
            return [self.translate_en_to_vi(texts[0])]
        
        # Multiple items: parallel translation
        logger.info(f"Parallel translating {len(texts)} items")
        
        results = [None] * len(texts)
        
        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(texts))) as executor:
            # Submit all translation tasks
            future_to_index = {
                executor.submit(self.translate_en_to_vi, text): i
                for i, text in enumerate(texts)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    results[index] = future.result()
                except Exception as e:
                    logger.error(f"Translation failed for item {index}: {e}")
                    results[index] = texts[index]  # Fallback to original text
        
        logger.info(f"Parallel translation completed: {len(texts)} items")
        return results
