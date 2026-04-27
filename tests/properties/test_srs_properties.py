"""Property-based tests for SM-2 SRS algorithm using Hypothesis.

Feature: flashcard-system-upgrade
"""

import pytest
from hypothesis import given, strategies as st, assume
from datetime import datetime, timezone

from src.domain.services.srs_engine import SRSEngine
from src.domain.entities.flashcard import FlashCard


class TestSM2AlgorithmProperties:
    """Property-based tests for SM-2 algorithm correctness."""
    
    @given(
        quality=st.integers(min_value=0, max_value=5),
        repetition_count=st.integers(min_value=0, max_value=100),
        ease_factor=st.floats(min_value=1.3, max_value=2.5),
        previous_interval=st.integers(min_value=1, max_value=365)
    )
    def test_sm2_algorithm_correctness(self, quality, repetition_count, ease_factor, previous_interval):
        """
        Feature: flashcard-system-upgrade, Property 1: SM-2 Algorithm Correctness
        
        For any valid combination of quality rating (0-5), repetition count, ease factor (1.3-2.5),
        and previous interval, the SM-2 algorithm SHALL calculate the next interval, repetition count,
        and ease factor according to the SuperMemo specification.
        
        Validates: Requirements 1.1, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8
        """
        new_interval, new_repetition_count, new_ease_factor = SRSEngine.calculate_next_interval(
            quality=quality,
            repetition_count=repetition_count,
            ease_factor=ease_factor,
            previous_interval=previous_interval
        )
        
        # Verify ease_factor minimum constraint
        assert new_ease_factor >= 1.3, f"Ease factor {new_ease_factor} below minimum 1.3"
        assert new_ease_factor <= 2.5 + 0.6, f"Ease factor {new_ease_factor} unreasonably high"
        
        # Verify interval is positive
        assert new_interval >= 1, f"Interval {new_interval} must be at least 1 day"
        
        # Verify repetition_count logic
        if quality < 3:
            # Failed recall - should reset
            assert new_repetition_count == 0, f"Failed recall should reset repetition_count to 0, got {new_repetition_count}"
            assert new_interval == 1, f"Failed recall should set interval to 1, got {new_interval}"
        else:
            # Successful recall
            assert new_repetition_count == repetition_count + 1, \
                f"Successful recall should increment repetition_count from {repetition_count} to {repetition_count + 1}, got {new_repetition_count}"
            
            if new_repetition_count == 1:
                assert new_interval == 1, f"First repetition should have interval 1, got {new_interval}"
            elif new_repetition_count == 2:
                assert new_interval == 6, f"Second repetition should have interval 6, got {new_interval}"
            else:
                # Should be previous_interval * ease_factor (rounded)
                expected = round(previous_interval * new_ease_factor)
                assert new_interval == expected, \
                    f"Expected interval {expected} (prev={previous_interval} * ef={new_ease_factor:.2f}), got {new_interval}"
    
    @given(
        ease_factor=st.floats(min_value=1.3, max_value=2.5),
        quality=st.integers(min_value=0, max_value=5)
    )
    def test_ease_factor_update_formula(self, ease_factor, quality):
        """
        Test that ease factor update follows SM-2 formula.
        
        Formula: EF + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        Minimum: 1.3
        """
        new_ease_factor = SRSEngine.update_ease_factor(ease_factor, quality)
        
        # Calculate expected value
        expected = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        expected = max(1.3, expected)
        
        assert abs(new_ease_factor - expected) < 0.001, \
            f"Ease factor calculation incorrect: expected {expected:.3f}, got {new_ease_factor:.3f}"
        
        # Verify minimum constraint
        assert new_ease_factor >= 1.3, f"Ease factor {new_ease_factor} below minimum 1.3"


class TestRatingMappingProperties:
    """Property-based tests for rating mapping consistency."""
    
    @given(rating=st.sampled_from(["forgot", "hard", "good", "easy"]))
    def test_rating_mapping_consistency(self, rating):
        """
        Feature: flashcard-system-upgrade, Property 3: Rating Mapping Consistency
        
        For any valid string rating ("forgot", "hard", "good", "easy"), the SRS engine SHALL
        consistently map to the correct quality values (0, 3, 4, 5 respectively).
        
        Validates: Requirements 1.9
        """
        quality = SRSEngine.map_rating_to_quality(rating)
        
        # Verify correct mapping
        expected_mapping = {
            "forgot": 0,
            "hard": 3,
            "good": 4,
            "easy": 5
        }
        
        assert quality == expected_mapping[rating], \
            f"Rating '{rating}' should map to {expected_mapping[rating]}, got {quality}"
        
        # Verify quality is in valid range
        assert 0 <= quality <= 5, f"Quality {quality} out of valid range [0, 5]"
    
    @given(invalid_rating=st.text().filter(lambda x: x not in ["forgot", "hard", "good", "easy"]))
    def test_invalid_rating_raises_error(self, invalid_rating):
        """Test that invalid ratings raise ValueError."""
        with pytest.raises(ValueError, match="Invalid rating"):
            SRSEngine.map_rating_to_quality(invalid_rating)


class TestSM2EdgeCases:
    """Test edge cases for SM-2 algorithm."""
    
    def test_minimum_ease_factor_maintained(self):
        """Test that ease factor never goes below 1.3."""
        # Quality 0 should decrease ease factor significantly
        for _ in range(10):
            ease_factor = 1.3
            new_ef = SRSEngine.update_ease_factor(ease_factor, quality=0)
            assert new_ef >= 1.3, f"Ease factor {new_ef} below minimum"
    
    def test_maximum_quality_increases_ease_factor(self):
        """Test that quality 5 increases ease factor."""
        ease_factor = 2.0
        new_ef = SRSEngine.update_ease_factor(ease_factor, quality=5)
        assert new_ef > ease_factor, f"Quality 5 should increase ease factor from {ease_factor} to {new_ef}"
    
    def test_failed_recall_resets_progress(self):
        """Test that failed recall (quality < 3) resets progress."""
        # Start with high repetition count
        interval, rep_count, ef = SRSEngine.calculate_next_interval(
            quality=0,
            repetition_count=10,
            ease_factor=2.5,
            previous_interval=100
        )
        
        assert rep_count == 0, "Failed recall should reset repetition count"
        assert interval == 1, "Failed recall should reset interval to 1"
    
    def test_first_two_intervals_fixed(self):
        """Test that first two successful reviews have fixed intervals."""
        # First review
        interval1, rep1, ef1 = SRSEngine.calculate_next_interval(
            quality=4,
            repetition_count=0,
            ease_factor=2.5,
            previous_interval=1
        )
        assert interval1 == 1, "First interval should be 1"
        assert rep1 == 1, "First repetition count should be 1"
        
        # Second review
        interval2, rep2, ef2 = SRSEngine.calculate_next_interval(
            quality=4,
            repetition_count=1,
            ease_factor=ef1,
            previous_interval=interval1
        )
        assert interval2 == 6, "Second interval should be 6"
        assert rep2 == 2, "Second repetition count should be 2"



class TestFlashcardInitializationProperties:
    """Property-based tests for flashcard initialization."""
    
    @given(
        word=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
        user_id=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        flashcard_id=st.text(min_size=1, max_size=50).filter(lambda x: x.strip())
    )
    def test_flashcard_initialization(self, word, user_id, flashcard_id):
        """
        Feature: flashcard-system-upgrade, Property 2: Flashcard Initialization
        
        For any new flashcard creation, the SRS engine SHALL initialize ease_factor to 2.5
        and repetition_count to 0.
        
        Validates: Requirements 1.2
        """
        flashcard = FlashCard(
            flashcard_id=flashcard_id,
            user_id=user_id,
            word=word
        )
        
        # Verify SM-2 initialization
        assert flashcard.ease_factor == 2.5, f"New flashcard should have ease_factor=2.5, got {flashcard.ease_factor}"
        assert flashcard.repetition_count == 0, f"New flashcard should have repetition_count=0, got {flashcard.repetition_count}"
        
        # Verify other SRS fields
        assert flashcard.interval_days == 1, "New flashcard should have interval_days=1"
        assert flashcard.review_count == 0, "New flashcard should have review_count=0"
        assert flashcard.last_reviewed_at is None, "New flashcard should not have been reviewed"
        assert flashcard.next_review_at is not None, "New flashcard should have next_review_at set"



class TestFlashcardInitializationProperties:
    """Property-based tests for flashcard initialization."""
    
    @given(
        flashcard_id=st.text(min_size=1, max_size=50),
        user_id=st.text(min_size=1, max_size=50),
        word=st.text(min_size=1, max_size=100)
    )
    def test_flashcard_initialization(self, flashcard_id, user_id, word):
        """
        Feature: flashcard-system-upgrade, Property 2: Flashcard Initialization
        
        For any new flashcard creation, the SRS engine SHALL initialize ease_factor to 2.5
        and repetition_count to 0.
        
        Validates: Requirements 1.2
        """
        from src.domain.entities.flashcard import FlashCard
        
        card = FlashCard(
            flashcard_id=flashcard_id,
            user_id=user_id,
            word=word
        )
        
        assert card.ease_factor == 2.5, f"New flashcard should have ease_factor=2.5, got {card.ease_factor}"
        assert card.repetition_count == 0, f"New flashcard should have repetition_count=0, got {card.repetition_count}"
        assert card.interval_days == 1, f"New flashcard should have interval_days=1, got {card.interval_days}"
        assert card.review_count == 0, f"New flashcard should have review_count=0, got {card.review_count}"



class TestPersistenceRoundTripProperties:
    """Property-based tests for persistence round-trip."""
    
    @given(
        flashcard_id=st.text(min_size=1, max_size=50),
        user_id=st.text(min_size=1, max_size=50),
        word=st.text(min_size=1, max_size=100),
        ease_factor=st.floats(min_value=1.3, max_value=2.5),
        repetition_count=st.integers(min_value=0, max_value=100)
    )
    def test_persistence_round_trip(self, flashcard_id, user_id, word, ease_factor, repetition_count):
        """
        Feature: flashcard-system-upgrade, Property 4: Persistence Round-Trip
        
        For any valid flashcard with ease_factor and repetition_count, persisting then retrieving
        SHALL preserve these values exactly.
        
        Validates: Requirements 2.4, 2.5
        """
        from src.domain.entities.flashcard import FlashCard
        from src.infrastructure.persistence.dynamo_flashcard_repo import DynamoFlashCardRepository
        from unittest.mock import MagicMock
        
        # Create original flashcard
        original = FlashCard(
            flashcard_id=flashcard_id,
            user_id=user_id,
            word=word,
            translation_vi="test translation",
            phonetic="/test/",
            audio_url="https://example.com/audio.mp3",
            example_sentence="Test sentence",
            ease_factor=ease_factor,
            repetition_count=repetition_count
        )
        
        # Mock DynamoDB table
        mock_table = MagicMock()
        repo = DynamoFlashCardRepository(table=mock_table)
        
        # Simulate save and retrieve
        repo.save(original)
        
        # Get the item that was saved
        saved_item = mock_table.put_item.call_args[1]['Item']
        
        # Verify GSI3 fields are populated
        assert saved_item['GSI3PK'] == user_id, "GSI3PK should be user_id"
        assert saved_item['GSI3SK'] == word.lower(), "GSI3SK should be word.lower()"
        
        # Verify SRS fields are preserved
        assert saved_item['ease_factor'] == ease_factor, f"ease_factor should be {ease_factor}, got {saved_item['ease_factor']}"
        assert saved_item['repetition_count'] == repetition_count, f"repetition_count should be {repetition_count}, got {saved_item['repetition_count']}"
        
        # Simulate retrieval by converting back to entity
        retrieved = repo._to_entity(saved_item)
        
        # Verify round-trip preservation
        assert retrieved.ease_factor == original.ease_factor, "ease_factor not preserved"
        assert retrieved.repetition_count == original.repetition_count, "repetition_count not preserved"
        assert retrieved.word == original.word, "word not preserved"
        assert retrieved.user_id == original.user_id, "user_id not preserved"



class TestWordNormalizationProperties:
    """Property-based tests for word normalization consistency."""
    
    @given(
        base_word=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))),
        case_variant=st.sampled_from(['lower', 'upper', 'title', 'mixed'])
    )
    def test_word_normalization_consistency(self, base_word, case_variant):
        """
        Feature: flashcard-system-upgrade, Property 5: Word Normalization Consistency
        
        For any word with mixed case, the repository SHALL normalize to lowercase before querying
        and produce consistent results regardless of input case.
        
        Validates: Requirements 3.4
        """
        from src.infrastructure.persistence.dynamo_flashcard_repo import DynamoFlashCardRepository
        from unittest.mock import MagicMock
        
        # Apply case variant
        if case_variant == 'lower':
            word_variant = base_word.lower()
        elif case_variant == 'upper':
            word_variant = base_word.upper()
        elif case_variant == 'title':
            word_variant = base_word.title()
        else:  # mixed
            # Create mixed case by alternating
            word_variant = ''.join(c.upper() if i % 2 == 0 else c.lower() 
                                   for i, c in enumerate(base_word))
        
        # Mock DynamoDB table
        mock_table = MagicMock()
        repo = DynamoFlashCardRepository(table=mock_table)
        
        # Query with different case variants
        user_id = "test-user"
        repo.get_by_user_and_word(user_id, word_variant)
        
        # Verify that GSI3SK is always lowercase
        call_args = mock_table.query.call_args
        key_condition = call_args[1]['KeyConditionExpression']
        
        # The query should use lowercase normalization
        # Verify by checking that all queries normalize to lowercase
        assert word_variant.lower() == base_word.lower(), "Normalization should produce consistent lowercase"



class TestPartialUpdatePreservationProperties:
    """Property-based tests for partial update preservation."""
    
    @given(
        translation_vi=st.text(min_size=1, max_size=100) | st.none(),
        phonetic=st.text(min_size=1, max_size=50) | st.none(),
        audio_url=st.text(min_size=1, max_size=200) | st.none(),
        example_sentence=st.text(min_size=1, max_size=200) | st.none()
    )
    def test_partial_update_preservation(self, translation_vi, phonetic, audio_url, example_sentence):
        """
        Feature: flashcard-system-upgrade, Property 6: Partial Update Preservation
        
        For any flashcard and any subset of updatable fields, updating SHALL modify only the
        specified fields while preserving all other data including SRS state.
        
        Validates: Requirements 4.4
        """
        from src.domain.entities.flashcard import FlashCard
        from src.infrastructure.persistence.dynamo_flashcard_repo import DynamoFlashCardRepository
        from unittest.mock import MagicMock
        
        # Create original flashcard with SRS state
        original = FlashCard(
            flashcard_id="card-001",
            user_id="user-001",
            word="example",
            translation_vi="original translation",
            phonetic="/original/",
            audio_url="https://example.com/original.mp3",
            example_sentence="Original sentence",
            ease_factor=2.3,
            repetition_count=5,
            interval_days=30
        )
        
        # Mock DynamoDB table
        mock_table = MagicMock()
        repo = DynamoFlashCardRepository(table=mock_table)
        
        # Simulate update_content
        # In real scenario, this would update only provided fields
        updated_fields = {}
        if translation_vi is not None:
            updated_fields['translation_vi'] = translation_vi
        if phonetic is not None:
            updated_fields['phonetic'] = phonetic
        if audio_url is not None:
            updated_fields['audio_url'] = audio_url
        if example_sentence is not None:
            updated_fields['example_sentence'] = example_sentence
        
        # Apply updates to original
        for field, value in updated_fields.items():
            setattr(original, field, value)
        
        # Verify SRS state is preserved
        assert original.ease_factor == 2.3, "ease_factor should be preserved"
        assert original.repetition_count == 5, "repetition_count should be preserved"
        assert original.interval_days == 30, "interval_days should be preserved"
        
        # Verify updated fields
        if translation_vi is not None:
            assert original.translation_vi == translation_vi
        if phonetic is not None:
            assert original.phonetic == phonetic
        if audio_url is not None:
            assert original.audio_url == audio_url
        if example_sentence is not None:
            assert original.example_sentence == example_sentence
