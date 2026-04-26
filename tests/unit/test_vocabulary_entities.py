"""Unit tests for vocabulary domain entities."""

import pytest
from src.domain.entities.vocabulary import Vocabulary, Meaning, Phonetic


class TestPhonetic:
    """Tests for Phonetic entity."""

    def test_phonetic_with_audio(self):
        """Test creating Phonetic with audio URL."""
        phonetic = Phonetic(text="/həˈləʊ/", audio="https://example.com/hello.mp3")
        
        assert phonetic.text == "/həˈləʊ/"
        assert phonetic.audio == "https://example.com/hello.mp3"

    def test_phonetic_without_audio(self):
        """Test creating Phonetic without audio URL."""
        phonetic = Phonetic(text="/həˈləʊ/")
        
        assert phonetic.text == "/həˈləʊ/"
        assert phonetic.audio is None


class TestMeaning:
    """Tests for Meaning entity."""

    def test_meaning_with_all_fields(self):
        """Test creating Meaning with all fields populated."""
        meaning = Meaning(
            part_of_speech="noun",
            definition="a greeting",
            definition_vi="lời chào",
            example="She said hello",
            example_vi="Cô ấy nói xin chào"
        )
        
        assert meaning.part_of_speech == "noun"
        assert meaning.definition == "a greeting"
        assert meaning.definition_vi == "lời chào"
        assert meaning.example == "She said hello"
        assert meaning.example_vi == "Cô ấy nói xin chào"

    def test_meaning_without_translations(self):
        """Test creating Meaning without Vietnamese translations."""
        meaning = Meaning(
            part_of_speech="verb",
            definition="to greet someone"
        )
        
        assert meaning.part_of_speech == "verb"
        assert meaning.definition == "to greet someone"
        assert meaning.definition_vi == ""
        assert meaning.example == ""
        assert meaning.example_vi == ""

    def test_meaning_with_example_no_translation(self):
        """Test creating Meaning with example but no translation."""
        meaning = Meaning(
            part_of_speech="exclamation",
            definition="used as a greeting",
            example="Hello there!"
        )
        
        assert meaning.example == "Hello there!"
        assert meaning.example_vi == ""


class TestVocabulary:
    """Tests for Vocabulary entity."""

    def test_vocabulary_with_all_fields(self):
        """Test creating Vocabulary with all fields populated."""
        meanings = [
            Meaning(
                part_of_speech="noun",
                definition="a greeting",
                definition_vi="lời chào"
            )
        ]
        
        vocab = Vocabulary(
            word="hello",
            translate_vi="xin chào",
            phonetic="/həˈləʊ/",
            audio_url="https://example.com/hello.mp3",
            meanings=meanings,
            origin="Old English"
        )
        
        assert vocab.word == "hello"
        assert vocab.translate_vi == "xin chào"
        assert vocab.phonetic == "/həˈləʊ/"
        assert vocab.audio_url == "https://example.com/hello.mp3"
        assert len(vocab.meanings) == 1
        assert vocab.origin == "Old English"

    def test_vocabulary_minimal_fields(self):
        """Test creating Vocabulary with only required fields."""
        vocab = Vocabulary(
            word="test",
            translate_vi="kiểm tra",
            phonetic="/test/"
        )
        
        assert vocab.word == "test"
        assert vocab.translate_vi == "kiểm tra"
        assert vocab.phonetic == "/test/"
        assert vocab.audio_url is None
        assert vocab.meanings == []
        assert vocab.origin is None

    def test_vocabulary_with_multiple_meanings(self):
        """Test creating Vocabulary with multiple meanings."""
        meanings = [
            Meaning(part_of_speech="noun", definition="definition 1"),
            Meaning(part_of_speech="verb", definition="definition 2"),
            Meaning(part_of_speech="adjective", definition="definition 3")
        ]
        
        vocab = Vocabulary(
            word="run",
            translate_vi="chạy",
            phonetic="/rʌn/",
            meanings=meanings
        )
        
        assert len(vocab.meanings) == 3
        assert vocab.meanings[0].part_of_speech == "noun"
        assert vocab.meanings[1].part_of_speech == "verb"
        assert vocab.meanings[2].part_of_speech == "adjective"

    def test_vocabulary_phrasal_verb(self):
        """Test creating Vocabulary for phrasal verb."""
        vocab = Vocabulary(
            word="get off",
            translate_vi="xuống xe",
            phonetic="/ɡet ɒf/"
        )
        
        assert vocab.word == "get off"
        assert vocab.translate_vi == "xuống xe"
