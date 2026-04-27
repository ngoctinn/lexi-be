"""
Unit tests for SM-2 SRS Engine.
"""
import pytest
from src.domain.services.srs_engine import SRSEngine


class TestMapRatingToQuality:
    """Test rating to quality mapping."""
    
    def test_forgot_maps_to_zero(self):
        assert SRSEngine.map_rating_to_quality("forgot") == 0
    
    def test_hard_maps_to_three(self):
        assert SRSEngine.map_rating_to_quality("hard") == 3
    
    def test_good_maps_to_four(self):
        assert SRSEngine.map_rating_to_quality("good") == 4
    
    def test_easy_maps_to_five(self):
        assert SRSEngine.map_rating_to_quality("easy") == 5
    
    def test_invalid_rating_raises_error(self):
        with pytest.raises(ValueError, match="Invalid rating: invalid"):
            SRSEngine.map_rating_to_quality("invalid")


class TestUpdateEaseFactor:
    """Test ease factor updates."""
    
    def test_quality_zero_decreases_ease_factor(self):
        result = SRSEngine.update_ease_factor(2.5, 0)
        assert result < 2.5
    
    def test_quality_five_increases_ease_factor(self):
        result = SRSEngine.update_ease_factor(2.5, 5)
        assert result > 2.5
    
    def test_minimum_ease_factor_is_1_3(self):
        # Quality 0 with low EF should not go below 1.3
        result = SRSEngine.update_ease_factor(1.3, 0)
        assert result == 1.3
    
    def test_ease_factor_formula_quality_4(self):
        # EF + (0.1 - (5 - 4) * (0.08 + (5 - 4) * 0.02))
        # = 2.5 + (0.1 - 1 * (0.08 + 1 * 0.02))
        # = 2.5 + (0.1 - 0.1) = 2.5
        result = SRSEngine.update_ease_factor(2.5, 4)
        assert result == 2.5
    
    def test_ease_factor_formula_quality_3(self):
        # EF + (0.1 - (5 - 3) * (0.08 + (5 - 3) * 0.02))
        # = 2.5 + (0.1 - 2 * (0.08 + 2 * 0.02))
        # = 2.5 + (0.1 - 2 * 0.12) = 2.5 + (0.1 - 0.24) = 2.36
        result = SRSEngine.update_ease_factor(2.5, 3)
        assert abs(result - 2.36) < 0.01


class TestCalculateNextInterval:
    """Test SM-2 interval calculation."""
    
    def test_quality_less_than_3_resets_repetition_count(self):
        interval, rep_count, ef = SRSEngine.calculate_next_interval(
            quality=2,
            repetition_count=5,
            ease_factor=2.5,
            previous_interval=10
        )
        assert rep_count == 0
        assert interval == 1
    
    def test_quality_less_than_3_sets_interval_to_1(self):
        interval, rep_count, ef = SRSEngine.calculate_next_interval(
            quality=0,
            repetition_count=3,
            ease_factor=2.0,
            previous_interval=20
        )
        assert interval == 1
    
    def test_first_successful_review_interval_is_1(self):
        interval, rep_count, ef = SRSEngine.calculate_next_interval(
            quality=4,
            repetition_count=0,
            ease_factor=2.5,
            previous_interval=1
        )
        assert interval == 1
        assert rep_count == 1
    
    def test_second_successful_review_interval_is_6(self):
        interval, rep_count, ef = SRSEngine.calculate_next_interval(
            quality=4,
            repetition_count=1,
            ease_factor=2.5,
            previous_interval=1
        )
        assert interval == 6
        assert rep_count == 2
    
    def test_third_successful_review_uses_ease_factor(self):
        interval, rep_count, ef = SRSEngine.calculate_next_interval(
            quality=4,
            repetition_count=2,
            ease_factor=2.5,
            previous_interval=6
        )
        # 6 * 2.5 = 15
        assert interval == 15
        assert rep_count == 3
    
    def test_subsequent_reviews_multiply_by_ease_factor(self):
        interval, rep_count, ef = SRSEngine.calculate_next_interval(
            quality=4,
            repetition_count=3,
            ease_factor=2.0,
            previous_interval=15
        )
        # 15 * 2.0 = 30
        assert interval == 30
        assert rep_count == 4
    
    def test_ease_factor_updates_on_every_review(self):
        _, _, ef = SRSEngine.calculate_next_interval(
            quality=5,
            repetition_count=0,
            ease_factor=2.5,
            previous_interval=1
        )
        # Quality 5 should increase ease factor
        assert ef > 2.5
    
    def test_quality_3_is_successful(self):
        interval, rep_count, ef = SRSEngine.calculate_next_interval(
            quality=3,
            repetition_count=0,
            ease_factor=2.5,
            previous_interval=1
        )
        assert rep_count == 1
        assert interval == 1
    
    def test_interval_rounds_to_integer(self):
        # Test with ease factor that produces non-integer
        interval, rep_count, ef = SRSEngine.calculate_next_interval(
            quality=4,
            repetition_count=2,
            ease_factor=2.3,
            previous_interval=7
        )
        # 7 * 2.3 = 16.1, should round to 16
        assert interval == 16
        assert isinstance(interval, int)


class TestSM2AlgorithmIntegration:
    """Integration tests for complete SM-2 workflow."""
    
    def test_new_card_first_review_forgot(self):
        """New card reviewed as 'forgot' should reset."""
        quality = SRSEngine.map_rating_to_quality("forgot")
        interval, rep_count, ef = SRSEngine.calculate_next_interval(
            quality=quality,
            repetition_count=0,
            ease_factor=2.5,
            previous_interval=1
        )
        assert interval == 1
        assert rep_count == 0
        assert ef < 2.5
    
    def test_new_card_first_review_good(self):
        """New card reviewed as 'good' should progress."""
        quality = SRSEngine.map_rating_to_quality("good")
        interval, rep_count, ef = SRSEngine.calculate_next_interval(
            quality=quality,
            repetition_count=0,
            ease_factor=2.5,
            previous_interval=1
        )
        assert interval == 1
        assert rep_count == 1
        assert ef == 2.5
    
    def test_complete_successful_sequence(self):
        """Test a complete sequence of successful reviews."""
        # Initial state
        rep_count = 0
        ef = 2.5
        interval = 1
        
        # First review (good)
        quality = SRSEngine.map_rating_to_quality("good")
        interval, rep_count, ef = SRSEngine.calculate_next_interval(
            quality, rep_count, ef, interval
        )
        assert interval == 1
        assert rep_count == 1
        
        # Second review (good)
        interval, rep_count, ef = SRSEngine.calculate_next_interval(
            quality, rep_count, ef, interval
        )
        assert interval == 6
        assert rep_count == 2
        
        # Third review (good)
        interval, rep_count, ef = SRSEngine.calculate_next_interval(
            quality, rep_count, ef, interval
        )
        assert interval == 15  # 6 * 2.5
        assert rep_count == 3
        
        # Fourth review (good)
        interval, rep_count, ef = SRSEngine.calculate_next_interval(
            quality, rep_count, ef, interval
        )
        assert interval == 38  # 15 * 2.5 = 37.5, rounds to 38
        assert rep_count == 4
    
    def test_failure_after_progress_resets(self):
        """Test that failure resets progress."""
        # Start with advanced state
        rep_count = 5
        ef = 2.3
        interval = 50
        
        # Review as 'forgot'
        quality = SRSEngine.map_rating_to_quality("forgot")
        interval, rep_count, ef = SRSEngine.calculate_next_interval(
            quality, rep_count, ef, interval
        )
        assert interval == 1
        assert rep_count == 0
        assert ef < 2.3  # EF should decrease
