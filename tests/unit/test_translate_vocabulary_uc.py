from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from application.dtos.vocabulary.translate.translate_vocabulary_command import TranslateVocabularyCommand
from application.use_cases.vocabulary.translate_vocabulary import TranslateVocabularyUC
from domain.entities.vocabulary import Vocabulary
from domain.value_objects.enums import VocabType


class FakeVocabularyRepository:
    def __init__(self, cached: Vocabulary | None = None):
        self.cached = cached
        self.saved_items: list[Vocabulary] = []

    def find_by_word(self, word: str):
        return self.cached

    def save(self, vocabulary: Vocabulary) -> None:
        self.saved_items.append(vocabulary)
        self.cached = vocabulary


class FakeVocabularyLookupService:
    def __init__(self, vocabulary: Vocabulary):
        self.vocabulary = vocabulary
        self.looked_up_words: list[str] = []

    def lookup(self, word: str) -> Vocabulary:
        self.looked_up_words.append(word)
        return self.vocabulary


def test_translate_vocabulary_returns_translation_and_definition_on_cache_miss():
    vocabulary = Vocabulary(
        word="hello",
        word_type=VocabType.NOUN,
        translation_vi="xin chào",
        definition_vi="lời chào",
        phonetic="həˈləʊ",
        audio_url="https://audio.example/hello.mp3",
        example_sentence="Hello there",
        source_api="dictionaryapi.dev+amazon-translate",
    )
    repo = FakeVocabularyRepository()
    service = FakeVocabularyLookupService(vocabulary)
    use_case = TranslateVocabularyUC(repo, service)

    result = use_case.execute(TranslateVocabularyCommand(word="hello"))

    assert result.is_success
    assert result.value is not None
    assert result.value.translation_vi == "xin chào"
    assert result.value.definition_vi == "lời chào"
    assert service.looked_up_words == ["hello"]
    assert repo.saved_items and repo.saved_items[0].translation_vi == "xin chào"


def test_translate_vocabulary_refreshes_cached_item_missing_translation():
    cached_vocabulary = Vocabulary(
        word="hello",
        word_type=VocabType.NOUN,
        translation_vi="",
        definition_vi="lời chào",
        source_api="dictionaryapi.dev+amazon-translate",
    )
    refreshed_vocabulary = Vocabulary(
        word="hello",
        word_type=VocabType.NOUN,
        translation_vi="xin chào",
        definition_vi="lời chào",
        source_api="dictionaryapi.dev+amazon-translate",
    )
    repo = FakeVocabularyRepository(cached_vocabulary)
    service = FakeVocabularyLookupService(refreshed_vocabulary)
    use_case = TranslateVocabularyUC(repo, service)

    result = use_case.execute(TranslateVocabularyCommand(word="hello"))

    assert result.is_success
    assert result.value is not None
    assert result.value.translation_vi == "xin chào"
    assert result.value.definition_vi == "lời chào"
    assert service.looked_up_words == ["hello"]
    assert repo.saved_items and repo.saved_items[0].translation_vi == "xin chào"


def test_translate_vocabulary_uses_cache_when_translation_exists():
    cached_vocabulary = Vocabulary(
        word="hello",
        word_type=VocabType.NOUN,
        translation_vi="xin chào",
        definition_vi="lời chào",
        source_api="dictionaryapi.dev+amazon-translate",
    )
    repo = FakeVocabularyRepository(cached_vocabulary)
    service = FakeVocabularyLookupService(
        Vocabulary(
            word="hello",
            word_type=VocabType.NOUN,
            translation_vi="xin chào khác",
            definition_vi="lời chào khác",
            source_api="dictionaryapi.dev+amazon-translate",
        )
    )
    use_case = TranslateVocabularyUC(repo, service)

    result = use_case.execute(TranslateVocabularyCommand(word="hello"))

    assert result.is_success
    assert result.value is not None
    assert result.value.translation_vi == "xin chào"
    assert result.value.definition_vi == "lời chào"
    assert service.looked_up_words == []
    assert repo.saved_items == []
