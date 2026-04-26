"""Integration tests for vocabulary translation with phrasal verb detection."""

import pytest
from unittest.mock import Mock, patch

from application.dtos.vocabulary_dtos import TranslateVocabularyCommand
from application.use_cases.vocabulary_use_cases import TranslateVocabularyUseCase
from infrastructure.adapters.dictionary_service_adapter import DictionaryServiceAdapter
from domain.entities.vocabulary import Vocabulary, Meaning


@pytest.fixture
def dictionary_adapter():
    """Create DictionaryServiceAdapter for integration tests."""
    return DictionaryServiceAdapter()


@pytest.fixture
def mock_translation_service():
    """Mock TranslationService."""
    service = Mock()
    
    # Mock translate_en_to_vi to return Vietnamese translations as strings
    def translate_side_effect(item):
        # Simple mock translations - return strings not Mock objects
        if "get up" in item.lower():
            return "thức dậy"
        elif "got off" in item.lower() or "get off" in item.lower():
            return "xuống"
        elif "get" in item.lower():
            return "nhận"
        elif "off" in item.lower():
            return "tắt"
        elif "rise from bed" in item.lower():
            return "thức dậy từ giường"
        elif "descend from a vehicle" in item.lower():
            return "xuống từ một phương tiện"
        elif "set of printed pages" in item.lower():
            return "một tập hợp các trang in"
        else:
            return f"translated: {item}"
    
    service.translate_en_to_vi.side_effect = translate_side_effect
    return service


class TestVocabularyTranslationPhrasalVerbs:
    """Integration tests for phrasal verb translation."""
    
    @patch('infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen')
    def test_translate_phrasal_verb_get_up_clicking_verb(
        self, mock_urlopen, dictionary_adapter, mock_translation_service
    ):
        """Test translating 'get up' when user clicks 'get'."""
        # Mock Dictionary API response for "get up"
        mock_response = Mock()
        mock_response.read.return_value = b'[{"word": "get up", "phonetic": "/get up/", "phonetics": [{"text": "/get up/", "audio": null}], "meanings": [{"partOfSpeech": "phrasal verb", "definitions": [{"definition": "to rise from bed", "example": "I get up at 6 AM"}]}]}]'
        mock_urlopen.return_value = mock_response
        
        # Create use case
        use_case = TranslateVocabularyUseCase(
            dictionary_service=dictionary_adapter,
            translation_service=mock_translation_service
        )
        
        # Execute: User clicks "get" in "I get up at 6 AM"
        command = TranslateVocabularyCommand(
            word="get",
            context="I get up at 6 AM"
        )
        result = use_case.execute(command)
        
        # Verify: Should translate "get up" not just "get"
        assert result.is_success
        response = result.value
        assert response.word == "get up"
        assert response.translate_vi == "thức dậy"
    
    @patch('infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen')
    def test_translate_phrasal_verb_get_up_clicking_particle(
        self, mock_urlopen, dictionary_adapter, mock_translation_service
    ):
        """Test translating 'get up' when user clicks 'up'."""
        # Mock Dictionary API response for "get up"
        mock_response = Mock()
        mock_response.read.return_value = b'[{"word": "get up", "phonetic": "/get up/", "phonetics": [{"text": "/get up/", "audio": null}], "meanings": [{"partOfSpeech": "phrasal verb", "definitions": [{"definition": "to rise from bed", "example": "I get up at 6 AM"}]}]}]'
        mock_urlopen.return_value = mock_response
        
        # Create use case
        use_case = TranslateVocabularyUseCase(
            dictionary_service=dictionary_adapter,
            translation_service=mock_translation_service
        )
        
        # Execute: User clicks "up" in "I get up at 6 AM"
        command = TranslateVocabularyCommand(
            word="up",
            context="I get up at 6 AM"
        )
        result = use_case.execute(command)
        
        # Verify: Should translate "get up" not just "up"
        assert result.is_success
        response = result.value
        assert response.word == "get up"
        assert response.translate_vi == "thức dậy"
    
    @patch('infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen')
    def test_translate_phrasal_verb_got_off_inflected_form(
        self, mock_urlopen, dictionary_adapter, mock_translation_service
    ):
        """Test translating 'got off' when user clicks 'got' (inflected form)."""
        # Mock Dictionary API response for "get off"
        mock_response = Mock()
        mock_response.read.return_value = b'[{"word": "get off", "phonetic": "/get off/", "phonetics": [{"text": "/get off/", "audio": null}], "meanings": [{"partOfSpeech": "phrasal verb", "definitions": [{"definition": "to descend from a vehicle", "example": "I got off the bus"}]}]}]'
        mock_urlopen.return_value = mock_response
        
        # Create use case
        use_case = TranslateVocabularyUseCase(
            dictionary_service=dictionary_adapter,
            translation_service=mock_translation_service
        )
        
        # Execute: User clicks "got" in "I got off the bus"
        command = TranslateVocabularyCommand(
            word="got",
            context="I got off the bus"
        )
        result = use_case.execute(command)
        
        # Verify: Should translate "get off" (lemmatized from "got")
        assert result.is_success
        response = result.value
        assert response.word == "get off"
        assert response.translate_vi == "xuống"
    
    @patch('infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen')
    def test_translate_phrasal_verb_getting_up_present_participle(
        self, mock_urlopen, dictionary_adapter, mock_translation_service
    ):
        """Test translating 'get up' when user clicks 'getting' (present participle)."""
        # Mock Dictionary API response for "get up"
        mock_response = Mock()
        mock_response.read.return_value = b'[{"word": "get up", "phonetic": "/get up/", "phonetics": [{"text": "/get up/", "audio": null}], "meanings": [{"partOfSpeech": "phrasal verb", "definitions": [{"definition": "to rise from bed", "example": "I\'m getting up now"}]}]}]'
        mock_urlopen.return_value = mock_response
        
        # Create use case
        use_case = TranslateVocabularyUseCase(
            dictionary_service=dictionary_adapter,
            translation_service=mock_translation_service
        )
        
        # Execute: User clicks "getting" in "I'm getting up now"
        command = TranslateVocabularyCommand(
            word="getting",
            context="I'm getting up now"
        )
        result = use_case.execute(command)
        
        # Verify: Should translate "get up" (lemmatized from "getting")
        assert result.is_success
        response = result.value
        assert response.word == "get up"
        assert response.translate_vi == "thức dậy"
    
    @patch('infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen')
    def test_translate_standalone_word_no_phrasal_verb(
        self, mock_urlopen, dictionary_adapter, mock_translation_service
    ):
        """Test translating standalone word without phrasal verb."""
        # Mock Dictionary API response for "book"
        mock_response = Mock()
        mock_response.read.return_value = b'[{"word": "book", "phonetic": "/buk/", "phonetics": [{"text": "/buk/", "audio": null}], "meanings": [{"partOfSpeech": "noun", "definitions": [{"definition": "a set of printed pages bound together", "example": "I read a book"}]}]}]'
        mock_urlopen.return_value = mock_response
        
        # Create use case
        use_case = TranslateVocabularyUseCase(
            dictionary_service=dictionary_adapter,
            translation_service=mock_translation_service
        )
        
        # Execute: User clicks "book" in "I read a book"
        command = TranslateVocabularyCommand(
            word="book",
            context="I read a book"
        )
        result = use_case.execute(command)
        
        # Verify: Should translate "book" (no phrasal verb)
        assert result.is_success
        response = result.value
        assert response.word == "book"
