"""Unit tests for SearchFlashcardsUseCase."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, MagicMock

from src.domain.entities.flashcard import FlashCard
from src.application.use_cases.flashcard_use_cases import SearchFlashcardsUseCase


class TestSearchFlashcardsUseCase:
    """Unit tests for SearchFlashcardsUseCase."""
    
    @pytest.fixture
    def mock_repo(self):
        """Create a mock repository."""
        return Mock()
    
    @pytest.fixture
    def search_uc(self, mock_repo):
        """Create a SearchFlashcardsUseCase instance."""
        return SearchFlashcardsUseCase(mock_repo)
    
    @pytest.fixture
    def sample_flashcards(self):
        """Create sample flashcards for testing."""
        now = datetime.now(timezone.utc)
        
        cards = [
            FlashCard(
                flashcard_id="card-001",
                user_id="user-001",
                word="apple",
                translation_vi="quả táo",
                phonetic="/ˈæpəl/",
                audio_url="https://example.com/apple.mp3",
                example_sentence="An apple a day keeps the doctor away.",
                ease_factor=2.5,
                repetition_count=0,
                interval_days=1,
                next_review_at=now + timedelta(days=1),
                last_reviewed_at=now - timedelta(days=1),
                review_count=1
            ),
            FlashCard(
                flashcard_id="card-002",
                user_id="user-001",
                word="application",
                translation_vi="ứng dụng",
                phonetic="/ˌæplɪˈkeɪʃən/",
                audio_url="https://example.com/application.mp3",
                example_sentence="This is a mobile application.",
                ease_factor=2.3,
                repetition_count=1,
                interval_days=3,
                next_review_at=now + timedelta(days=3),
                last_reviewed_at=now - timedelta(days=3),
                review_count=2
            ),
            FlashCard(
                flashcard_id="card-003",
                user_id="user-001",
                word="banana",
                translation_vi="quả chuối",
                phonetic="/bəˈnɑːnə/",
                audio_url="https://example.com/banana.mp3",
                example_sentence="I like to eat bananas.",
                ease_factor=2.5,
                repetition_count=2,
                interval_days=6,
                next_review_at=now + timedelta(days=6),
                last_reviewed_at=now - timedelta(days=6),
                review_count=3
            ),
            FlashCard(
                flashcard_id="card-004",
                user_id="user-001",
                word="cherry",
                translation_vi="quả anh đào",
                phonetic="/ˈtʃeri/",
                audio_url="https://example.com/cherry.mp3",
                example_sentence="Cherry blossoms are beautiful.",
                ease_factor=2.4,
                repetition_count=3,
                interval_days=15,
                next_review_at=now + timedelta(days=15),
                last_reviewed_at=now - timedelta(days=15),
                review_count=4
            ),
            FlashCard(
                flashcard_id="card-005",
                user_id="user-001",
                word="date",
                translation_vi="ngày tháng",
                phonetic="/deɪt/",
                audio_url="https://example.com/date.mp3",
                example_sentence="What is today's date?",
                ease_factor=2.2,
                repetition_count=0,
                interval_days=1,
                next_review_at=now + timedelta(days=1),
                last_reviewed_at=now - timedelta(days=1),
                review_count=1
            ),
        ]
        return cards
    
    def test_search_no_filters_returns_all(self, search_uc, mock_repo, sample_flashcards):
        """Test search with no filters returns all flashcards."""
        mock_repo.list_by_user.return_value = (sample_flashcards, None)
        
        cards, next_cursor, total_count = search_uc.execute("user-001")
        
        assert len(cards) == 5
        assert total_count == 5
        assert next_cursor is None
    
    def test_search_word_prefix_filter_case_insensitive(self, search_uc, mock_repo, sample_flashcards):
        """Test word_prefix filter is case-insensitive."""
        mock_repo.list_by_user.return_value = (sample_flashcards, None)
        
        # Test lowercase prefix
        cards, _, total_count = search_uc.execute("user-001", word_prefix="app")
        assert len(cards) == 2  # apple, application
        assert total_count == 2
        assert cards[0]["word"] == "apple"
        assert cards[1]["word"] == "application"
        
        # Test uppercase prefix
        cards, _, total_count = search_uc.execute("user-001", word_prefix="APP")
        assert len(cards) == 2
        assert total_count == 2
        
        # Test mixed case prefix
        cards, _, total_count = search_uc.execute("user-001", word_prefix="ApP")
        assert len(cards) == 2
        assert total_count == 2
    
    def test_search_word_prefix_filter_exact_match(self, search_uc, mock_repo, sample_flashcards):
        """Test word_prefix filter with exact match."""
        mock_repo.list_by_user.return_value = (sample_flashcards, None)
        
        cards, _, total_count = search_uc.execute("user-001", word_prefix="ban")
        assert len(cards) == 1
        assert total_count == 1
        assert cards[0]["word"] == "banana"
    
    def test_search_word_prefix_filter_no_match(self, search_uc, mock_repo, sample_flashcards):
        """Test word_prefix filter with no matches."""
        mock_repo.list_by_user.return_value = (sample_flashcards, None)
        
        cards, _, total_count = search_uc.execute("user-001", word_prefix="xyz")
        assert len(cards) == 0
        assert total_count == 0
    
    def test_search_min_interval_filter(self, search_uc, mock_repo, sample_flashcards):
        """Test min_interval filter."""
        mock_repo.list_by_user.return_value = (sample_flashcards, None)
        
        # Cards with interval >= 6
        cards, _, total_count = search_uc.execute("user-001", min_interval=6)
        assert len(cards) == 2  # banana (6), cherry (15)
        assert total_count == 2
        assert all(card["interval_days"] >= 6 for card in cards)
    
    def test_search_max_interval_filter(self, search_uc, mock_repo, sample_flashcards):
        """Test max_interval filter."""
        mock_repo.list_by_user.return_value = (sample_flashcards, None)
        
        # Cards with interval <= 3
        cards, _, total_count = search_uc.execute("user-001", max_interval=3)
        assert len(cards) == 3  # apple (1), application (3), date (1)
        assert total_count == 3
        assert all(card["interval_days"] <= 3 for card in cards)
    
    def test_search_interval_range_filter(self, search_uc, mock_repo, sample_flashcards):
        """Test combined min and max interval filters."""
        mock_repo.list_by_user.return_value = (sample_flashcards, None)
        
        # Cards with 3 <= interval <= 10
        cards, _, total_count = search_uc.execute("user-001", min_interval=3, max_interval=10)
        assert len(cards) == 2  # application (3), banana (6)
        assert total_count == 2
        assert all(3 <= card["interval_days"] <= 10 for card in cards)
    
    def test_search_maturity_level_new(self, search_uc, mock_repo, sample_flashcards):
        """Test maturity_level filter for 'new' cards."""
        mock_repo.list_by_user.return_value = (sample_flashcards, None)
        
        cards, _, total_count = search_uc.execute("user-001", maturity_level="new")
        assert len(cards) == 2  # apple (0), date (0)
        assert total_count == 2
        assert all(card["repetition_count"] == 0 for card in cards)
    
    def test_search_maturity_level_learning(self, search_uc, mock_repo, sample_flashcards):
        """Test maturity_level filter for 'learning' cards."""
        mock_repo.list_by_user.return_value = (sample_flashcards, None)
        
        cards, _, total_count = search_uc.execute("user-001", maturity_level="learning")
        assert len(cards) == 2  # application (1), banana (2)
        assert total_count == 2
        assert all(1 <= card["repetition_count"] <= 2 for card in cards)
    
    def test_search_maturity_level_mature(self, search_uc, mock_repo, sample_flashcards):
        """Test maturity_level filter for 'mature' cards."""
        mock_repo.list_by_user.return_value = (sample_flashcards, None)
        
        cards, _, total_count = search_uc.execute("user-001", maturity_level="mature")
        assert len(cards) == 1  # cherry (3)
        assert total_count == 1
        assert all(card["repetition_count"] >= 3 for card in cards)
    
    def test_search_combined_filters(self, search_uc, mock_repo, sample_flashcards):
        """Test multiple filters combined."""
        mock_repo.list_by_user.return_value = (sample_flashcards, None)
        
        # word_prefix="app" AND min_interval=3 AND maturity_level="learning"
        cards, _, total_count = search_uc.execute(
            "user-001",
            word_prefix="app",
            min_interval=3,
            maturity_level="learning"
        )
        assert len(cards) == 1  # application (3, repetition_count=1)
        assert total_count == 1
        assert cards[0]["word"] == "application"
    
    def test_search_pagination_default_limit(self, search_uc, mock_repo, sample_flashcards):
        """Test pagination with default limit (50)."""
        mock_repo.list_by_user.return_value = (sample_flashcards, None)
        
        cards, next_cursor, total_count = search_uc.execute("user-001")
        assert len(cards) == 5
        assert next_cursor is None  # All results fit in one page
        assert total_count == 5
    
    def test_search_pagination_custom_limit(self, search_uc, mock_repo, sample_flashcards):
        """Test pagination with custom limit."""
        mock_repo.list_by_user.return_value = (sample_flashcards, None)
        
        # First page with limit=2
        cards, next_cursor, total_count = search_uc.execute("user-001", limit=2)
        assert len(cards) == 2
        assert next_cursor == "2"
        assert total_count == 5
        
        # Second page
        cards, next_cursor, total_count = search_uc.execute("user-001", limit=2, cursor="2")
        assert len(cards) == 2
        assert next_cursor == "4"
        assert total_count == 5
        
        # Third page
        cards, next_cursor, total_count = search_uc.execute("user-001", limit=2, cursor="4")
        assert len(cards) == 1
        assert next_cursor is None  # Last page
        assert total_count == 5
    
    def test_search_pagination_invalid_cursor(self, search_uc, mock_repo, sample_flashcards):
        """Test pagination with invalid cursor (should default to 0)."""
        mock_repo.list_by_user.return_value = (sample_flashcards, None)
        
        cards, next_cursor, total_count = search_uc.execute("user-001", cursor="invalid")
        assert len(cards) == 5  # Should start from beginning
        assert total_count == 5
    
    def test_search_pagination_cursor_beyond_results(self, search_uc, mock_repo, sample_flashcards):
        """Test pagination with cursor beyond available results."""
        mock_repo.list_by_user.return_value = (sample_flashcards, None)
        
        cards, next_cursor, total_count = search_uc.execute("user-001", cursor="100")
        assert len(cards) == 0
        assert next_cursor is None
        assert total_count == 5
    
    def test_search_empty_results(self, search_uc, mock_repo):
        """Test search with no flashcards."""
        mock_repo.list_by_user.return_value = ([], None)
        
        cards, next_cursor, total_count = search_uc.execute("user-001")
        assert len(cards) == 0
        assert next_cursor is None
        assert total_count == 0
    
    def test_search_result_format(self, search_uc, mock_repo, sample_flashcards):
        """Test that search results have correct format."""
        mock_repo.list_by_user.return_value = (sample_flashcards, None)
        
        cards, _, _ = search_uc.execute("user-001", limit=1)
        assert len(cards) == 1
        
        card = cards[0]
        assert "flashcard_id" in card
        assert "word" in card
        assert "translation_vi" in card
        assert "phonetic" in card
        assert "audio_url" in card
        assert "example_sentence" in card
        assert "ease_factor" in card
        assert "repetition_count" in card
        assert "interval_days" in card
        assert "next_review_at" in card
    
    def test_search_handles_pagination_across_multiple_batches(self, search_uc, mock_repo):
        """Test search handles pagination when repository returns multiple batches."""
        now = datetime.now(timezone.utc)
        
        # Create 150 flashcards (more than one batch of 1000)
        batch1 = [
            FlashCard(
                flashcard_id=f"card-{i:03d}",
                user_id="user-001",
                word=f"word{i:03d}",
                translation_vi=f"từ {i}",
                phonetic="/test/",
                audio_url="https://example.com/test.mp3",
                example_sentence="Test sentence.",
                ease_factor=2.5,
                repetition_count=0,
                interval_days=1,
                next_review_at=now + timedelta(days=1),
                last_reviewed_at=now - timedelta(days=1),
                review_count=1
            )
            for i in range(100)
        ]
        batch2 = [
            FlashCard(
                flashcard_id=f"card-{i:03d}",
                user_id="user-001",
                word=f"word{i:03d}",
                translation_vi=f"từ {i}",
                phonetic="/test/",
                audio_url="https://example.com/test.mp3",
                example_sentence="Test sentence.",
                ease_factor=2.5,
                repetition_count=0,
                interval_days=1,
                next_review_at=now + timedelta(days=1),
                last_reviewed_at=now - timedelta(days=1),
                review_count=1
            )
            for i in range(100, 150)
        ]
        
        # Mock repository to return batches
        mock_repo.list_by_user.side_effect = [
            (batch1, "cursor-1"),
            (batch2, None)
        ]
        
        cards, next_cursor, total_count = search_uc.execute("user-001", limit=50)
        assert len(cards) == 50
        assert next_cursor == "50"
        assert total_count == 150
    
    def test_search_word_prefix_with_pagination(self, search_uc, mock_repo, sample_flashcards):
        """Test word_prefix filter combined with pagination."""
        mock_repo.list_by_user.return_value = (sample_flashcards, None)
        
        # Get first page of "app" results with limit=1
        cards, next_cursor, total_count = search_uc.execute("user-001", word_prefix="app", limit=1)
        assert len(cards) == 1
        assert cards[0]["word"] == "apple"
        assert next_cursor == "1"
        assert total_count == 2
        
        # Get second page
        cards, next_cursor, total_count = search_uc.execute("user-001", word_prefix="app", limit=1, cursor="1")
        assert len(cards) == 1
        assert cards[0]["word"] == "application"
        assert next_cursor is None
        assert total_count == 2
    
    def test_search_maturity_and_interval_filters(self, search_uc, mock_repo, sample_flashcards):
        """Test maturity_level and interval filters together."""
        mock_repo.list_by_user.return_value = (sample_flashcards, None)
        
        # Learning cards with interval >= 3
        cards, _, total_count = search_uc.execute(
            "user-001",
            maturity_level="learning",
            min_interval=3
        )
        assert len(cards) == 2  # application (1, 3), banana (2, 6)
        assert total_count == 2
        assert all(1 <= card["repetition_count"] <= 2 for card in cards)
        assert all(card["interval_days"] >= 3 for card in cards)
