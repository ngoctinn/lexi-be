"""Unit tests for FlashCard SM-2 algorithm integration."""

import pytest
from datetime import datetime, timezone, timedelta

from src.domain.entities.flashcard import FlashCard


class TestApplySM2Review:
    """Unit tests for apply_sm2_review() method."""
    
    @pytest.fixture
    def flashcard(self):
        """Create a test flashcard."""
        return FlashCard(
            flashcard_id="test-001",
            user_id="user-001",
            word="example",
            translation_vi="ví dụ",
            phonetic="/ɪɡˈzæmpəl/",
            audio_url="https://example.com/audio.mp3",
            example_sentence="This is an example."
        )
    
    def test_forgot_rating_resets_progress(self, flashcard):
        """Test that 'forgot' rating resets repetition_count and sets interval to 1."""
        # Setup: simulate some progress
        flashcard.repetition_count = 5
        flashcard.ease_factor = 2.3
        flashcard.interval_days = 30
        
        # Apply forgot rating
        flashcard.apply_sm2_review("forgot")
        
        # Verify reset
        assert flashcard.repetition_count == 0, "Forgot should reset repetition_count to 0"
        assert flashcard.interval_days == 1, "Forgot should reset interval to 1"
        assert flashcard.review_count == 1, "Review count should increment"
        assert flashcard.last_reviewed_at is not None
        assert flashcard.next_review_at is not None
    
    def test_hard_rating_quality_3(self, flashcard):
        """Test 'hard' rating with quality=3."""
        flashcard.repetition_count = 0
        flashcard.ease_factor = 2.5
        flashcard.interval_days = 1
        
        flashcard.apply_sm2_review("hard")
        
        # Quality 3 should increment repetition_count
        assert flashcard.repetition_count == 1, "Hard rating should increment repetition_count"
        assert flashcard.interval_days == 1, "First interval should be 1"
        assert flashcard.review_count == 1
    
    def test_good_rating_quality_4(self, flashcard):
        """Test 'good' rating with quality=4."""
        flashcard.repetition_count = 1
        flashcard.ease_factor = 2.5
        flashcard.interval_days = 1
        
        flashcard.apply_sm2_review("good")
        
        # Quality 4, repetition_count 1 -> should set interval to 6
        assert flashcard.repetition_count == 2, "Good rating should increment repetition_count"
        assert flashcard.interval_days == 6, "Second interval should be 6"
        assert flashcard.review_count == 1
    
    def test_easy_rating_quality_5(self, flashcard):
        """Test 'easy' rating with quality=5."""
        flashcard.repetition_count = 2
        flashcard.ease_factor = 2.5
        flashcard.interval_days = 6
        
        flashcard.apply_sm2_review("easy")
        
        # Quality 5, repetition_count 2 -> should calculate interval = round(6 * new_ease_factor)
        # Ease factor increases with quality 5, so interval will be > 15
        assert flashcard.repetition_count == 3, "Easy rating should increment repetition_count"
        assert flashcard.interval_days > 15, "Third interval should be > 15 (ease factor increased)"
        assert flashcard.ease_factor > 2.5, "Ease factor should increase with quality 5"
        assert flashcard.review_count == 1
    
    def test_ease_factor_updates_correctly(self, flashcard):
        """Test that ease_factor updates correctly based on quality."""
        flashcard.ease_factor = 2.5
        
        # Quality 5 should increase ease_factor
        flashcard.apply_sm2_review("easy")
        ease_after_easy = flashcard.ease_factor
        assert ease_after_easy > 2.5, "Quality 5 should increase ease_factor"
        
        # Reset and test quality 0
        flashcard.ease_factor = 2.5
        flashcard.review_count = 0
        flashcard.apply_sm2_review("forgot")
        ease_after_forgot = flashcard.ease_factor
        assert ease_after_forgot < 2.5, "Quality 0 should decrease ease_factor"
        assert ease_after_forgot >= 1.3, "Ease factor should not go below 1.3"
    
    def test_review_count_increments(self, flashcard):
        """Test that review_count increments with each review."""
        assert flashcard.review_count == 0
        
        flashcard.apply_sm2_review("good")
        assert flashcard.review_count == 1
        
        flashcard.apply_sm2_review("good")
        assert flashcard.review_count == 2
        
        flashcard.apply_sm2_review("forgot")
        assert flashcard.review_count == 3
    
    def test_timestamps_updated(self, flashcard):
        """Test that last_reviewed_at and next_review_at are updated."""
        before = datetime.now(timezone.utc)
        flashcard.apply_sm2_review("good")
        after = datetime.now(timezone.utc)
        
        assert flashcard.last_reviewed_at is not None
        assert before <= flashcard.last_reviewed_at <= after
        
        # next_review_at should be last_reviewed_at + interval_days
        expected_next = flashcard.last_reviewed_at + timedelta(days=flashcard.interval_days)
        assert abs((flashcard.next_review_at - expected_next).total_seconds()) < 1
    
    def test_multiple_reviews_sequence(self, flashcard):
        """Test a sequence of reviews following SM-2 algorithm."""
        # Initial state
        assert flashcard.repetition_count == 0
        assert flashcard.ease_factor == 2.5
        assert flashcard.interval_days == 1
        
        # First review - good (quality 4)
        flashcard.apply_sm2_review("good")
        assert flashcard.repetition_count == 1
        assert flashcard.interval_days == 1
        
        # Second review - good (quality 4)
        flashcard.apply_sm2_review("good")
        assert flashcard.repetition_count == 2
        assert flashcard.interval_days == 6
        
        # Third review - easy (quality 5)
        flashcard.apply_sm2_review("easy")
        assert flashcard.repetition_count == 3
        assert flashcard.interval_days == round(6 * flashcard.ease_factor)
        
        # Fourth review - forgot (quality 0)
        flashcard.apply_sm2_review("forgot")
        assert flashcard.repetition_count == 0
        assert flashcard.interval_days == 1
    
    def test_invalid_rating_raises_error(self, flashcard):
        """Test that invalid rating raises ValueError."""
        with pytest.raises(ValueError, match="Invalid rating"):
            flashcard.apply_sm2_review("invalid")
    
    def test_all_valid_ratings(self, flashcard):
        """Test that all valid ratings work without error."""
        valid_ratings = ["forgot", "hard", "good", "easy"]
        
        for rating in valid_ratings:
            flashcard.review_count = 0
            flashcard.repetition_count = 0
            flashcard.ease_factor = 2.5
            flashcard.interval_days = 1
            
            # Should not raise
            flashcard.apply_sm2_review(rating)
            assert flashcard.review_count == 1



class TestUpdateFlashcard:
    """Unit tests for update flashcard operation."""
    
    @pytest.fixture
    def flashcard(self):
        """Create a test flashcard."""
        return FlashCard(
            flashcard_id="test-001",
            user_id="user-001",
            word="example",
            translation_vi="ví dụ",
            phonetic="/ɪɡˈzæmpəl/",
            audio_url="https://example.com/audio.mp3",
            example_sentence="This is an example."
        )
    
    def test_update_translation_vi(self, flashcard):
        """Test updating translation_vi field."""
        original_phonetic = flashcard.phonetic
        original_ease_factor = flashcard.ease_factor
        
        flashcard.translation_vi = "ví dụ mới"
        
        assert flashcard.translation_vi == "ví dụ mới"
        assert flashcard.phonetic == original_phonetic, "Other fields should not change"
        assert flashcard.ease_factor == original_ease_factor, "SRS data should not change"
    
    def test_update_phonetic(self, flashcard):
        """Test updating phonetic field."""
        original_translation = flashcard.translation_vi
        original_ease_factor = flashcard.ease_factor
        
        flashcard.phonetic = "/ɪɡˈzæmpəl/ (new)"
        
        assert flashcard.phonetic == "/ɪɡˈzæmpəl/ (new)"
        assert flashcard.translation_vi == original_translation, "Other fields should not change"
        assert flashcard.ease_factor == original_ease_factor, "SRS data should not change"
    
    def test_update_audio_url(self, flashcard):
        """Test updating audio_url field."""
        original_example = flashcard.example_sentence
        original_repetition_count = flashcard.repetition_count
        
        flashcard.audio_url = "https://example.com/new-audio.mp3"
        
        assert flashcard.audio_url == "https://example.com/new-audio.mp3"
        assert flashcard.example_sentence == original_example, "Other fields should not change"
        assert flashcard.repetition_count == original_repetition_count, "SRS data should not change"
    
    def test_update_example_sentence(self, flashcard):
        """Test updating example_sentence field."""
        original_word = flashcard.word
        original_ease_factor = flashcard.ease_factor
        
        flashcard.example_sentence = "This is a new example sentence."
        
        assert flashcard.example_sentence == "This is a new example sentence."
        assert flashcard.word == original_word, "Other fields should not change"
        assert flashcard.ease_factor == original_ease_factor, "SRS data should not change"
    
    def test_update_multiple_fields(self, flashcard):
        """Test updating multiple fields at once."""
        original_ease_factor = flashcard.ease_factor
        original_repetition_count = flashcard.repetition_count
        
        flashcard.translation_vi = "dịch mới"
        flashcard.phonetic = "/new/"
        flashcard.example_sentence = "New example"
        
        assert flashcard.translation_vi == "dịch mới"
        assert flashcard.phonetic == "/new/"
        assert flashcard.example_sentence == "New example"
        assert flashcard.ease_factor == original_ease_factor, "SRS data should not change"
        assert flashcard.repetition_count == original_repetition_count, "SRS data should not change"
    
    def test_srs_data_never_modified_by_content_update(self, flashcard):
        """Test that SRS data is never modified by content updates."""
        # Set some SRS state
        flashcard.ease_factor = 2.2
        flashcard.repetition_count = 3
        flashcard.interval_days = 15
        
        # Update content
        flashcard.translation_vi = "new translation"
        flashcard.phonetic = "/new/"
        flashcard.audio_url = "https://new.com/audio.mp3"
        flashcard.example_sentence = "New example"
        
        # Verify SRS data unchanged
        assert flashcard.ease_factor == 2.2
        assert flashcard.repetition_count == 3
        assert flashcard.interval_days == 15



class TestDeleteFlashcard:
    """Unit tests for delete flashcard operation."""
    
    @pytest.fixture
    def flashcard(self):
        """Create a test flashcard."""
        return FlashCard(
            flashcard_id="test-001",
            user_id="user-001",
            word="example",
            translation_vi="ví dụ",
            phonetic="/ɪɡˈzæmpəl/",
            audio_url="https://example.com/audio.mp3",
            example_sentence="This is an example."
        )
    
    def test_delete_flashcard_success(self, flashcard):
        """Test successful deletion of flashcard."""
        from src.application.use_cases.flashcard_use_cases import DeleteFlashcardUseCase
        from src.infrastructure.persistence.dynamo_flashcard_repo import DynamoFlashCardRepository
        from unittest.mock import MagicMock
        
        # Mock repository
        mock_repo = MagicMock(spec=DynamoFlashCardRepository)
        mock_repo.get_by_user_and_id.return_value = flashcard
        mock_repo.delete.return_value = True
        
        uc = DeleteFlashcardUseCase(mock_repo)
        result = uc.execute("user-001", "test-001")
        
        assert result is True
        mock_repo.delete.assert_called_once_with("user-001", "test-001")
    
    def test_delete_nonexistent_flashcard_raises_keyerror(self):
        """Test that deleting non-existent flashcard raises KeyError."""
        from src.application.use_cases.flashcard_use_cases import DeleteFlashcardUseCase
        from src.infrastructure.persistence.dynamo_flashcard_repo import DynamoFlashCardRepository
        from unittest.mock import MagicMock
        
        # Mock repository returning None
        mock_repo = MagicMock(spec=DynamoFlashCardRepository)
        mock_repo.get_by_user_and_id.return_value = None
        
        uc = DeleteFlashcardUseCase(mock_repo)
        
        with pytest.raises(KeyError):
            uc.execute("user-001", "nonexistent")
    
    def test_delete_other_users_flashcard_raises_permissionerror(self, flashcard):
        """Test that deleting another user's flashcard raises PermissionError."""
        from src.application.use_cases.flashcard_use_cases import DeleteFlashcardUseCase
        from src.infrastructure.persistence.dynamo_flashcard_repo import DynamoFlashCardRepository
        from unittest.mock import MagicMock
        
        # Mock repository returning flashcard owned by different user
        mock_repo = MagicMock(spec=DynamoFlashCardRepository)
        mock_repo.get_by_user_and_id.return_value = flashcard
        
        uc = DeleteFlashcardUseCase(mock_repo)
        
        with pytest.raises(PermissionError):
            uc.execute("different-user", "test-001")
    
    def test_delete_idempotency(self, flashcard):
        """Test that deleting non-existent flashcard is idempotent."""
        from src.application.use_cases.flashcard_use_cases import DeleteFlashcardUseCase
        from src.infrastructure.persistence.dynamo_flashcard_repo import DynamoFlashCardRepository
        from unittest.mock import MagicMock
        
        # Mock repository
        mock_repo = MagicMock(spec=DynamoFlashCardRepository)
        mock_repo.get_by_user_and_id.return_value = None
        
        uc = DeleteFlashcardUseCase(mock_repo)
        
        # First delete should raise KeyError
        with pytest.raises(KeyError):
            uc.execute("user-001", "test-001")
        
        # Second delete should also raise KeyError (idempotent behavior)
        with pytest.raises(KeyError):
            uc.execute("user-001", "test-001")
