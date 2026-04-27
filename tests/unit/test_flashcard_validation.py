"""Unit tests for FlashCard validation."""

import pytest
from src.domain.entities.flashcard import FlashCard


class TestFlashCardValidation:
    """Unit tests for FlashCard entity validation."""
    
    def test_valid_single_word(self):
        """Test that single words are accepted."""
        card = FlashCard(
            flashcard_id="card-001",
            user_id="user-001",
            word="apple"
        )
        assert card.word == "apple"
    
    def test_valid_multi_word_with_spaces(self):
        """Test that multi-word expressions with spaces are accepted."""
        card = FlashCard(
            flashcard_id="card-001",
            user_id="user-001",
            word="give up"
        )
        assert card.word == "give up"
    
    def test_valid_multi_word_with_hyphens(self):
        """Test that words with hyphens are accepted."""
        card = FlashCard(
            flashcard_id="card-001",
            user_id="user-001",
            word="well-known"
        )
        assert card.word == "well-known"
    
    def test_valid_multi_word_with_apostrophes(self):
        """Test that words with apostrophes are accepted."""
        card = FlashCard(
            flashcard_id="card-001",
            user_id="user-001",
            word="don't"
        )
        assert card.word == "don't"
    
    def test_valid_complex_expression(self):
        """Test that complex expressions with multiple special characters are accepted."""
        card = FlashCard(
            flashcard_id="card-001",
            user_id="user-001",
            word="state-of-the-art"
        )
        assert card.word == "state-of-the-art"
    
    def test_valid_expression_with_numbers(self):
        """Test that expressions with numbers are accepted."""
        card = FlashCard(
            flashcard_id="card-001",
            user_id="user-001",
            word="24/7"
        )
        assert card.word == "24/7"
    
    def test_whitespace_trimming_leading(self):
        """Test that leading whitespace is trimmed."""
        card = FlashCard(
            flashcard_id="card-001",
            user_id="user-001",
            word="  apple"
        )
        assert card.word == "apple"
    
    def test_whitespace_trimming_trailing(self):
        """Test that trailing whitespace is trimmed."""
        card = FlashCard(
            flashcard_id="card-001",
            user_id="user-001",
            word="apple  "
        )
        assert card.word == "apple"
    
    def test_whitespace_trimming_both_sides(self):
        """Test that whitespace is trimmed from both sides."""
        card = FlashCard(
            flashcard_id="card-001",
            user_id="user-001",
            word="  apple  "
        )
        assert card.word == "apple"
    
    def test_whitespace_trimming_multi_word(self):
        """Test that whitespace is trimmed from multi-word expressions."""
        card = FlashCard(
            flashcard_id="card-001",
            user_id="user-001",
            word="  give up  "
        )
        assert card.word == "give up"
    
    def test_reject_whitespace_only(self):
        """Test that whitespace-only words are rejected."""
        with pytest.raises(ValueError, match="word là thông tin bắt buộc"):
            FlashCard(
                flashcard_id="card-001",
                user_id="user-001",
                word="   "
            )
    
    def test_reject_empty_word(self):
        """Test that empty words are rejected."""
        with pytest.raises(ValueError, match="word là thông tin bắt buộc"):
            FlashCard(
                flashcard_id="card-001",
                user_id="user-001",
                word=""
            )
    
    def test_reject_word_exceeding_max_length(self):
        """Test that words exceeding 100 characters are rejected."""
        long_word = "a" * 101
        with pytest.raises(ValueError, match="Từ không được vượt quá 100 ký tự"):
            FlashCard(
                flashcard_id="card-001",
                user_id="user-001",
                word=long_word
            )
    
    def test_accept_word_at_max_length(self):
        """Test that words exactly 100 characters are accepted."""
        word_100_chars = "a" * 100
        card = FlashCard(
            flashcard_id="card-001",
            user_id="user-001",
            word=word_100_chars
        )
        assert len(card.word) == 100
    
    def test_reject_word_with_invalid_characters(self):
        """Test that words with invalid characters are rejected."""
        with pytest.raises(ValueError, match="Từ chỉ được chứa"):
            FlashCard(
                flashcard_id="card-001",
                user_id="user-001",
                word="apple@"
            )
    
    def test_reject_word_with_special_symbols(self):
        """Test that words with special symbols are rejected."""
        with pytest.raises(ValueError, match="Từ chỉ được chứa"):
            FlashCard(
                flashcard_id="card-001",
                user_id="user-001",
                word="apple#"
            )
    
    def test_reject_word_with_exclamation(self):
        """Test that words with exclamation marks are rejected."""
        with pytest.raises(ValueError, match="Từ chỉ được chứa"):
            FlashCard(
                flashcard_id="card-001",
                user_id="user-001",
                word="apple!"
            )
    
    def test_reject_word_with_question_mark(self):
        """Test that words with question marks are rejected."""
        with pytest.raises(ValueError, match="Từ chỉ được chứa"):
            FlashCard(
                flashcard_id="card-001",
                user_id="user-001",
                word="apple?"
            )
    
    def test_reject_word_with_comma(self):
        """Test that words with commas are rejected."""
        with pytest.raises(ValueError, match="Từ chỉ được chứa"):
            FlashCard(
                flashcard_id="card-001",
                user_id="user-001",
                word="apple,"
            )
    
    def test_reject_word_with_period(self):
        """Test that words with periods are rejected."""
        with pytest.raises(ValueError, match="Từ chỉ được chứa"):
            FlashCard(
                flashcard_id="card-001",
                user_id="user-001",
                word="apple."
            )
    
    def test_reject_missing_flashcard_id(self):
        """Test that missing flashcard_id is rejected."""
        with pytest.raises(ValueError, match="flashcard_id"):
            FlashCard(
                flashcard_id="",
                user_id="user-001",
                word="apple"
            )
    
    def test_reject_missing_user_id(self):
        """Test that missing user_id is rejected."""
        with pytest.raises(ValueError, match="user_id"):
            FlashCard(
                flashcard_id="card-001",
                user_id="",
                word="apple"
            )
    
    def test_reject_invalid_ease_factor_too_low(self):
        """Test that ease_factor below 1.3 is rejected."""
        with pytest.raises(ValueError, match="Ease factor phải nằm"):
            FlashCard(
                flashcard_id="card-001",
                user_id="user-001",
                word="apple",
                ease_factor=1.2
            )
    
    def test_reject_invalid_ease_factor_too_high(self):
        """Test that ease_factor above 2.5 is rejected."""
        with pytest.raises(ValueError, match="Ease factor phải nằm"):
            FlashCard(
                flashcard_id="card-001",
                user_id="user-001",
                word="apple",
                ease_factor=2.6
            )
    
    def test_accept_valid_ease_factor_min(self):
        """Test that ease_factor at minimum (1.3) is accepted."""
        card = FlashCard(
            flashcard_id="card-001",
            user_id="user-001",
            word="apple",
            ease_factor=1.3
        )
        assert card.ease_factor == 1.3
    
    def test_accept_valid_ease_factor_max(self):
        """Test that ease_factor at maximum (2.5) is accepted."""
        card = FlashCard(
            flashcard_id="card-001",
            user_id="user-001",
            word="apple",
            ease_factor=2.5
        )
        assert card.ease_factor == 2.5
    
    def test_reject_negative_repetition_count(self):
        """Test that negative repetition_count is rejected."""
        with pytest.raises(ValueError, match="Repetition count phải"):
            FlashCard(
                flashcard_id="card-001",
                user_id="user-001",
                word="apple",
                repetition_count=-1
            )
    
    def test_accept_zero_repetition_count(self):
        """Test that zero repetition_count is accepted."""
        card = FlashCard(
            flashcard_id="card-001",
            user_id="user-001",
            word="apple",
            repetition_count=0
        )
        assert card.repetition_count == 0
    
    def test_accept_positive_repetition_count(self):
        """Test that positive repetition_count is accepted."""
        card = FlashCard(
            flashcard_id="card-001",
            user_id="user-001",
            word="apple",
            repetition_count=5
        )
        assert card.repetition_count == 5
    
    def test_reject_invalid_difficulty_too_low(self):
        """Test that difficulty below 0 is rejected."""
        with pytest.raises(ValueError, match="Độ khó phải nằm"):
            FlashCard(
                flashcard_id="card-001",
                user_id="user-001",
                word="apple",
                difficulty=-1
            )
    
    def test_reject_invalid_difficulty_too_high(self):
        """Test that difficulty above 5 is rejected."""
        with pytest.raises(ValueError, match="Độ khó phải nằm"):
            FlashCard(
                flashcard_id="card-001",
                user_id="user-001",
                word="apple",
                difficulty=6
            )
    
    def test_accept_valid_difficulty_min(self):
        """Test that difficulty at minimum (0) is accepted."""
        card = FlashCard(
            flashcard_id="card-001",
            user_id="user-001",
            word="apple",
            difficulty=0
        )
        assert card.difficulty == 0
    
    def test_accept_valid_difficulty_max(self):
        """Test that difficulty at maximum (5) is accepted."""
        card = FlashCard(
            flashcard_id="card-001",
            user_id="user-001",
            word="apple",
            difficulty=5
        )
        assert card.difficulty == 5
    
    def test_phrasal_verb_example(self):
        """Test real-world phrasal verb example."""
        card = FlashCard(
            flashcard_id="card-001",
            user_id="user-001",
            word="break down"
        )
        assert card.word == "break down"
    
    def test_idiom_example(self):
        """Test real-world idiom example."""
        card = FlashCard(
            flashcard_id="card-001",
            user_id="user-001",
            word="piece of cake"
        )
        assert card.word == "piece of cake"
    
    def test_contraction_example(self):
        """Test real-world contraction example."""
        card = FlashCard(
            flashcard_id="card-001",
            user_id="user-001",
            word="it's"
        )
        assert card.word == "it's"
    
    def test_hyphenated_adjective_example(self):
        """Test real-world hyphenated adjective example."""
        card = FlashCard(
            flashcard_id="card-001",
            user_id="user-001",
            word="state-of-the-art"
        )
        assert card.word == "state-of-the-art"
    
    def test_multiple_spaces_between_words(self):
        """Test that multiple spaces between words are preserved after trimming."""
        card = FlashCard(
            flashcard_id="card-001",
            user_id="user-001",
            word="give  up"
        )
        # Note: The word is trimmed but internal spaces are preserved
        assert card.word == "give  up"
    
    def test_internal_whitespace_not_trimmed(self):
        """Test that internal whitespace is not trimmed."""
        card = FlashCard(
            flashcard_id="card-001",
            user_id="user-001",
            word="  give up  "
        )
        # Only leading/trailing whitespace is trimmed
        assert card.word == "give up"
