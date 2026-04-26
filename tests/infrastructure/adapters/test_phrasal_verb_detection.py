"""Unit tests for phrasal verb detection in DictionaryServiceAdapter."""

import pytest
from infrastructure.adapters.dictionary_service_adapter import DictionaryServiceAdapter


@pytest.fixture
def adapter():
    """Create DictionaryServiceAdapter without dependencies."""
    return DictionaryServiceAdapter()


class TestFindWordInContext:
    """Test _find_word_in_context method for flexible word matching."""
    
    def test_exact_match_base_form(self, adapter):
        """Test exact match with base form."""
        context = "I get up at 6 AM"
        idx = adapter._find_word_in_context("get", context)
        assert idx == 1  # "get" is at index 1
    
    def test_exact_match_particle(self, adapter):
        """Test exact match with particle."""
        context = "I got off the bus"
        idx = adapter._find_word_in_context("off", context)
        assert idx == 2  # "off" is at index 2
    
    def test_inflected_form_matching_got(self, adapter):
        """Test matching inflected form 'got' when looking for 'get'."""
        context = "I got off the bus"
        idx = adapter._find_word_in_context("get", context)
        # Should find "got" at index 1 because lemma of "got" is "get"
        assert idx == 1
    
    def test_inflected_form_matching_getting(self, adapter):
        """Test matching inflected form 'getting' when looking for 'get'."""
        context = "I'm getting up now"
        idx = adapter._find_word_in_context("get", context)
        # Should find "getting" because lemma of "getting" is "get"
        # "I'm" is at index 0, "getting" is at index 1
        assert idx == 1
    
    def test_inflected_form_matching_gets(self, adapter):
        """Test matching inflected form 'gets' when looking for 'get'."""
        context = "He gets up early"
        idx = adapter._find_word_in_context("get", context)
        # Should find "gets" because lemma of "gets" is "get"
        assert idx == 1
    
    def test_word_not_found(self, adapter):
        """Test when word is not found in context."""
        context = "I read a book"
        idx = adapter._find_word_in_context("get", context)
        assert idx == -1
    
    def test_case_insensitive_matching(self, adapter):
        """Test case-insensitive matching."""
        context = "I GET up at 6 AM"
        idx = adapter._find_word_in_context("get", context)
        assert idx == 1


class TestFindPhrasalVerbCandidates:
    """Test find_phrasal_verb_candidates method."""
    
    def test_verb_followed_by_particle_base_form(self, adapter):
        """Test verb (base form) followed by particle."""
        candidates = adapter.find_phrasal_verb_candidates("get", "I get up at 6 AM")
        # Should try "get up" first
        assert "get up" in candidates
        assert candidates[0] == "get up"
    
    def test_verb_followed_by_particle_inflected_form(self, adapter):
        """Test inflected verb form followed by particle."""
        candidates = adapter.find_phrasal_verb_candidates("got", "I got off the bus")
        # Should try "got off" and "get off" (lemmatized)
        assert "got off" in candidates or "get off" in candidates
    
    def test_particle_preceded_by_verb_base_form(self, adapter):
        """Test particle preceded by verb (base form)."""
        candidates = adapter.find_phrasal_verb_candidates("up", "I get up at 6 AM")
        # Should try "get up" first
        assert "get up" in candidates
        assert candidates[0] == "get up"
    
    def test_particle_preceded_by_verb_inflected_form(self, adapter):
        """Test particle preceded by inflected verb form."""
        candidates = adapter.find_phrasal_verb_candidates("off", "I got off the bus")
        # Should try "got off" and "get off" (lemmatized)
        assert "got off" in candidates or "get off" in candidates
    
    def test_particle_preceded_by_getting(self, adapter):
        """Test particle preceded by 'getting' (present participle)."""
        candidates = adapter.find_phrasal_verb_candidates("up", "I'm getting up now")
        # Should try "get up" (lemmatized from "getting")
        assert "get up" in candidates
    
    def test_standalone_word_no_particle(self, adapter):
        """Test standalone word without particle."""
        candidates = adapter.find_phrasal_verb_candidates("book", "I read a book")
        # Should just lemmatize the word
        assert "book" in candidates
    
    def test_word_not_in_context_fallback(self, adapter):
        """Test fallback when word not found in context."""
        candidates = adapter.find_phrasal_verb_candidates("get", "I read a book")
        # Should just lemmatize the word
        assert "get" in candidates
    
    def test_no_duplicates_in_candidates(self, adapter):
        """Test that candidates list has no duplicates."""
        candidates = adapter.find_phrasal_verb_candidates("get", "I get up at 6 AM")
        assert len(candidates) == len(set(candidates))
    
    def test_candidates_ordered_by_priority(self, adapter):
        """Test that phrasal verb candidates come before standalone word."""
        candidates = adapter.find_phrasal_verb_candidates("get", "I get up at 6 AM")
        # Phrasal verb should come first
        assert candidates[0] == "get up"
        # Standalone word should come later
        assert "get" in candidates
        assert candidates.index("get up") < candidates.index("get")
    
    def test_multiple_particles_not_matched(self, adapter):
        """Test that non-particle words are not treated as particles."""
        candidates = adapter.find_phrasal_verb_candidates("get", "I get the book")
        # "the" is not a particle, so should not create "get the"
        assert "get the" not in candidates
    
    def test_all_supported_particles(self, adapter):
        """Test detection with all supported particles."""
        particles = ["up", "down", "off", "on", "out", "in", "away", "back", 
                    "over", "through", "around", "along", "by", "into", "onto", "upon"]
        
        for particle in particles:
            context = f"I get {particle} now"
            candidates = adapter.find_phrasal_verb_candidates("get", context)
            assert f"get {particle}" in candidates, f"Failed for particle: {particle}"
    
    def test_complex_sentence_with_multiple_verbs(self, adapter):
        """Test in complex sentence with multiple verbs."""
        context = "When I got off the bus, I saw my friend"
        candidates = adapter.find_phrasal_verb_candidates("off", context)
        # Should find "got off" (or "get off" lemmatized)
        assert "got off" in candidates or "get off" in candidates
    
    def test_verb_at_end_of_sentence(self, adapter):
        """Test verb at end of sentence (no particle after)."""
        context = "I like to get"
        candidates = adapter.find_phrasal_verb_candidates("get", context)
        # Should just lemmatize, no phrasal verb
        assert "get" in candidates
        assert len(candidates) == 1


class TestLemmatizeWord:
    """Test lemmatize_word method."""
    
    def test_base_form_returns_itself(self, adapter):
        """Test that base form returns itself."""
        lemmas = adapter.lemmatize_word("get")
        assert "get" in lemmas
    
    def test_past_tense_lemmatizes_to_base(self, adapter):
        """Test that past tense lemmatizes to base form."""
        lemmas = adapter.lemmatize_word("got")
        assert "get" in lemmas
    
    def test_present_participle_lemmatizes_to_base(self, adapter):
        """Test that present participle lemmatizes to base form."""
        lemmas = adapter.lemmatize_word("getting")
        assert "get" in lemmas
    
    def test_third_person_singular_lemmatizes_to_base(self, adapter):
        """Test that 3rd person singular lemmatizes to base form."""
        lemmas = adapter.lemmatize_word("gets")
        assert "get" in lemmas
    
    def test_no_duplicates_in_lemmas(self, adapter):
        """Test that lemmas list has no duplicates."""
        lemmas = adapter.lemmatize_word("get")
        assert len(lemmas) == len(set(lemmas))
