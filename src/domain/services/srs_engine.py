"""
SM-2 Spaced Repetition System Engine.

Implements the SuperMemo SM-2 algorithm for calculating optimal review intervals.
"""


class SRSEngine:
    """
    Implements the SM-2 spaced repetition algorithm.
    
    The SM-2 algorithm calculates optimal review intervals based on:
    - ease_factor: Difficulty multiplier (1.3 to 2.5)
    - repetition_count: Number of consecutive successful reviews
    - quality: User's recall assessment (0-5)
    """
    
    @staticmethod
    def calculate_next_interval(
        quality: int,
        repetition_count: int,
        ease_factor: float,
        previous_interval: int
    ) -> tuple[int, int, float]:
        """
        Calculate next review interval using SM-2 algorithm.
        
        Args:
            quality: Quality rating (0-5)
            repetition_count: Number of consecutive successful reviews
            ease_factor: Current ease factor (1.3-2.5)
            previous_interval: Previous interval in days
            
        Returns:
            Tuple of (new_interval, new_repetition_count, new_ease_factor)
        """
        # Update ease factor
        new_ease_factor = SRSEngine.update_ease_factor(ease_factor, quality)
        
        if quality < 3:
            # Failed recall - reset repetition count
            new_repetition_count = 0
            new_interval = 1
        else:
            # Successful recall
            new_repetition_count = repetition_count + 1
            
            if new_repetition_count == 1:
                new_interval = 1
            elif new_repetition_count == 2:
                new_interval = 6
            else:
                new_interval = round(previous_interval * new_ease_factor)
        
        return new_interval, new_repetition_count, new_ease_factor
    
    @staticmethod
    def map_rating_to_quality(rating: str) -> int:
        """
        Map string ratings to SM-2 quality values.
        
        Args:
            rating: String rating ("forgot", "hard", "good", "easy")
            
        Returns:
            Quality value (0, 3, 4, or 5)
            
        Raises:
            ValueError: If rating is not recognized
        """
        mapping = {
            "forgot": 0,
            "hard": 3,
            "good": 4,
            "easy": 5
        }
        if rating not in mapping:
            raise ValueError(f"Invalid rating: {rating}")
        return mapping[rating]
    
    @staticmethod
    def update_ease_factor(current_ef: float, quality: int) -> float:
        """
        Update ease factor based on recall quality.
        
        Args:
            current_ef: Current ease factor
            quality: Quality rating (0-5)
            
        Returns:
            New ease factor (minimum 1.3)
        """
        new_ef = current_ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        return max(1.3, new_ef)
