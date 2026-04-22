import json
import os
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from application.exceptions.vocabulary_errors import VocabularyLookupError, VocabularyNotFoundError
from application.services.vocabulary_lookup_service import VocabularyLookupService
from domain.entities.vocabulary import Vocabulary
from domain.value_objects.enums import VocabType


class DictionaryTranslateVocabularyService(VocabularyLookupService):
    """
    Adapter hạ tầng kết hợp dictionaryapi.dev và Amazon Translate.

    Dictionary API cung cấp phonetic, part of speech, audio và example.
    Amazon Translate chỉ dùng để dịch nghĩa sang tiếng Việt.
    """

    def __init__(self, translate_client=None, timeout_seconds: int = 5):
        self._translate_client = translate_client
        self._timeout_seconds = timeout_seconds

    def lookup(self, word: str) -> Vocabulary:
        normalized_word = word.strip().lower()
        entry = self._fetch_dictionary_entry(normalized_word)
        part_of_speech, definition_en, example_sentence, phonetic, audio_url = self._extract_primary_data(entry)

        if not definition_en:
            raise VocabularyNotFoundError(f"Không tìm thấy nghĩa phù hợp cho từ '{normalized_word}'.")

        translation_vi = self._translate_text(normalized_word)
        definition_vi = self._translate_text(definition_en)

        # Lấy tất cả meanings và dịch
        all_meanings = self._extract_all_meanings(entry)

        return Vocabulary(
            word=normalized_word,
            word_type=self._map_part_of_speech(part_of_speech),
            translation_vi=translation_vi,
            definition_vi=definition_vi,
            phonetic=phonetic,
            audio_url=audio_url,
            example_sentence=example_sentence,
            source_api="dictionaryapi.dev+amazon-translate",
            all_meanings=all_meanings,
        )

    def _extract_all_meanings(self, entry: Dict[str, Any]) -> List[Dict[str, str]]:
        """Lấy tất cả meanings, dịch definition sang tiếng Việt."""
        result = []
        seen_pos = set()  # Tránh duplicate cùng part_of_speech

        for meaning in entry.get("meanings", []):
            pos = str(meaning.get("partOfSpeech", "")).strip().lower()
            if pos in seen_pos:
                continue
            seen_pos.add(pos)

            first_def = self._first_definition(meaning.get("definitions", []))
            if not first_def:
                continue

            definition_en = str(first_def.get("definition", "")).strip()
            example = str(first_def.get("example", "")).strip()

            if not definition_en:
                continue

            definition_vi = self._translate_text(definition_en)
            result.append({
                "part_of_speech": pos,
                "definition_vi": definition_vi,
                "example_sentence": example,
            })

        return result

    def _fetch_dictionary_entry(self, word: str) -> Dict[str, Any]:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{quote(word)}"
        request = Request(url, headers={"Accept": "application/json", "User-Agent": "Lexi/1.0"})

        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                payload = response.read().decode("utf-8")
        except HTTPError as exc:
            if exc.code == 404:
                raise VocabularyNotFoundError(f"Không tìm thấy từ vựng '{word}' trong dictionaryapi.dev.") from exc
            raise VocabularyLookupError(f"Không thể tra cứu từ '{word}': HTTP {exc.code}") from exc
        except URLError as exc:
            raise VocabularyLookupError(f"Không thể kết nối dictionaryapi.dev: {str(exc)}") from exc

        try:
            entries = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise VocabularyLookupError("Phản hồi từ dictionaryapi.dev không hợp lệ.") from exc

        if not isinstance(entries, list) or not entries:
            raise VocabularyNotFoundError(f"Không tìm thấy từ vựng '{word}'.")

        first_entry = entries[0]
        if not isinstance(first_entry, dict):
            raise VocabularyLookupError("Định dạng dữ liệu từ dictionaryapi.dev không hợp lệ.")

        return first_entry

    def _extract_primary_data(self, entry: Dict[str, Any]) -> tuple[str, str, str, str, str]:
        phonetic = entry.get("phonetic") or self._first_non_empty(self._collect_phonetic_texts(entry.get("phonetics", [])))
        audio_url = self._normalize_audio_url(self._first_non_empty(self._collect_audio_urls(entry.get("phonetics", []))))

        meanings = entry.get("meanings", [])
        selected_meaning = self._first_meaning_with_definition(meanings)
        if not selected_meaning:
            return "noun", "", "", phonetic or "", audio_url or ""

        part_of_speech = str(selected_meaning.get("partOfSpeech", "noun")).strip().lower()
        selected_definition = self._first_definition(selected_meaning.get("definitions", []))
        if not selected_definition:
            return part_of_speech, "", "", phonetic or "", audio_url or ""

        definition_en = str(selected_definition.get("definition", "")).strip()
        example_sentence = str(selected_definition.get("example", "")).strip()

        if not example_sentence:
            example_sentence = self._first_example_from_meanings(meanings) or ""

        return part_of_speech, definition_en, example_sentence, phonetic or "", audio_url or ""

    def _translate_text(self, text: str) -> str:
        if not text:
            return ""

        try:
            response = self._get_translate_client().translate_text(
                SourceLanguageCode="en",
                TargetLanguageCode="vi",
                Text=text,
            )
        except (ClientError, BotoCoreError) as exc:
            raise VocabularyLookupError(f"Không thể dịch nghĩa sang tiếng Việt: {str(exc)}") from exc

        translated_text = response.get("TranslatedText", "")
        if not translated_text:
            raise VocabularyLookupError("Amazon Translate không trả về nội dung dịch hợp lệ.")
        return translated_text

    def _get_translate_client(self):
        if self._translate_client is None:
            region_name = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
            if region_name:
                self._translate_client = boto3.client("translate", region_name=region_name)
            else:
                self._translate_client = boto3.client("translate")
        return self._translate_client

    def _map_part_of_speech(self, part_of_speech: str) -> VocabType:
        normalized = part_of_speech.strip().lower()
        mapping = {
            "noun": VocabType.NOUN,
            "verb": VocabType.VERB,
            "adjective": VocabType.ADJECTIVE,
            "adverb": VocabType.ADVERB,
            "pronoun": VocabType.PRONOUN,
            "preposition": VocabType.PREPOSITION,
            "conjunction": VocabType.CONJUNCTION,
            "interjection": VocabType.INTERJECTION,
            "exclamation": VocabType.INTERJECTION,
            "phrase": VocabType.PHRASE,
            "idiom": VocabType.IDIOM,
        }
        return mapping.get(normalized, VocabType.NOUN)

    def _first_non_empty(self, values: List[str]) -> str:
        for value in values:
            if value:
                return value
        return ""

    def _collect_phonetic_texts(self, phonetics: List[Dict[str, Any]]) -> List[str]:
        texts: List[str] = []
        for phonetic in phonetics:
            text = str(phonetic.get("text", "")).strip()
            if text:
                texts.append(text)
        return texts

    def _collect_audio_urls(self, phonetics: List[Dict[str, Any]]) -> List[str]:
        urls: List[str] = []
        for phonetic in phonetics:
            audio = str(phonetic.get("audio", "")).strip()
            if audio:
                urls.append(audio)
        return urls

    def _normalize_audio_url(self, audio_url: str) -> str:
        if audio_url.startswith("//"):
            return f"https:{audio_url}"
        return audio_url

    def _first_meaning_with_definition(self, meanings: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        for meaning in meanings:
            definitions = meaning.get("definitions", [])
            if self._first_definition(definitions):
                return meaning
        return meanings[0] if meanings else None

    def _first_definition(self, definitions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        for definition in definitions:
            definition_text = str(definition.get("definition", "")).strip()
            if definition_text:
                return definition
        return None

    def _first_example_from_meanings(self, meanings: List[Dict[str, Any]]) -> str:
        for meaning in meanings:
            for definition in meaning.get("definitions", []):
                example = str(definition.get("example", "")).strip()
                if example:
                    return example
        return ""
