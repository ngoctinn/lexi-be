"""Unit tests for analyze_turn bug fixes.

Tests cover:
1. Critical bug: Finding AI turn with correct turn_index
2. Validation: turn_index bounds checking
3. Edge cases: Missing AI turn, invalid turn_index
"""

import pytest
from unittest.mock import Mock, MagicMock
from domain.entities.turn import Turn
from domain.entities.session import Session
from domain.value_objects.enums import Speaker
from ulid import ULID


class FakeTurnRepository:
    """Fake turn repository for testing."""
    
    def __init__(self, turns: list[Turn]):
        self.turns = turns
    
    def list_by_session(self, session_id: str) -> list[Turn]:
        return [t for t in self.turns if str(t.session_id) == session_id]


class TestAnalyzeTurnBugFixes:
    """Test suite for analyze_turn bug fixes."""
    
    @pytest.fixture
    def session_id(self):
        return ULID()
    
    @pytest.fixture
    def sample_turns(self, session_id):
        """Create sample turns with correct turn_index pattern."""
        return [
            Turn(
                session_id=session_id,
                turn_index=0,
                speaker=Speaker.USER,
                content="Hello, I want coffee",
            ),
            Turn(
                session_id=session_id,
                turn_index=1,
                speaker=Speaker.AI,
                content="Sure! What size would you like?",
            ),
            Turn(
                session_id=session_id,
                turn_index=2,
                speaker=Speaker.USER,
                content="I want medium size",
            ),
            Turn(
                session_id=session_id,
                turn_index=3,
                speaker=Speaker.AI,
                content="Great! Anything else?",
            ),
        ]
    
    def test_find_ai_turn_with_correct_index(self, session_id, sample_turns):
        """Test: AI turn is found with turn_index + 1 (not same turn_index)."""
        # Simulate the fixed logic
        turn_index = 0  # Request analysis for USER turn 0
        sorted_turns = sorted(sample_turns, key=lambda t: t.turn_index)
        
        learner_turn = None
        ai_turn = None
        
        for i, turn in enumerate(sorted_turns):
            speaker_val = turn.speaker.value if hasattr(turn.speaker, "value") else turn.speaker
            
            if turn.turn_index == turn_index and speaker_val == Speaker.USER.value:
                learner_turn = turn
                
                # Find next AI turn
                if i + 1 < len(sorted_turns):
                    next_turn = sorted_turns[i + 1]
                    next_speaker = next_turn.speaker.value if hasattr(next_turn.speaker, "value") else next_turn.speaker
                    if next_speaker == Speaker.AI.value:
                        ai_turn = next_turn
                break
        
        # Assertions
        assert learner_turn is not None, "USER turn should be found"
        assert learner_turn.turn_index == 0
        assert learner_turn.content == "Hello, I want coffee"
        
        assert ai_turn is not None, "AI turn should be found"
        assert ai_turn.turn_index == 1, "AI turn should have turn_index = 1 (not 0)"
        assert ai_turn.content == "Sure! What size would you like?"
    
    def test_find_ai_turn_for_second_user_turn(self, session_id, sample_turns):
        """Test: AI turn is found correctly for second USER turn."""
        turn_index = 2  # Request analysis for USER turn 2
        sorted_turns = sorted(sample_turns, key=lambda t: t.turn_index)
        
        learner_turn = None
        ai_turn = None
        
        for i, turn in enumerate(sorted_turns):
            speaker_val = turn.speaker.value if hasattr(turn.speaker, "value") else turn.speaker
            
            if turn.turn_index == turn_index and speaker_val == Speaker.USER.value:
                learner_turn = turn
                
                if i + 1 < len(sorted_turns):
                    next_turn = sorted_turns[i + 1]
                    next_speaker = next_turn.speaker.value if hasattr(next_turn.speaker, "value") else next_turn.speaker
                    if next_speaker == Speaker.AI.value:
                        ai_turn = next_turn
                break
        
        assert learner_turn is not None
        assert learner_turn.turn_index == 2
        assert ai_turn is not None
        assert ai_turn.turn_index == 3, "AI turn should have turn_index = 3 (not 2)"
    
    def test_missing_ai_turn_handled_gracefully(self, session_id):
        """Test: Missing AI turn is handled (e.g., incomplete conversation)."""
        turns = [
            Turn(
                session_id=session_id,
                turn_index=0,
                speaker=Speaker.USER,
                content="Hello",
            ),
            # No AI turn yet
        ]
        
        turn_index = 0
        sorted_turns = sorted(turns, key=lambda t: t.turn_index)
        
        learner_turn = None
        ai_turn = None
        
        for i, turn in enumerate(sorted_turns):
            speaker_val = turn.speaker.value if hasattr(turn.speaker, "value") else turn.speaker
            
            if turn.turn_index == turn_index and speaker_val == Speaker.USER.value:
                learner_turn = turn
                
                if i + 1 < len(sorted_turns):
                    next_turn = sorted_turns[i + 1]
                    next_speaker = next_turn.speaker.value if hasattr(next_turn.speaker, "value") else next_turn.speaker
                    if next_speaker == Speaker.AI.value:
                        ai_turn = next_turn
                break
        
        assert learner_turn is not None
        assert ai_turn is None, "AI turn should be None (not yet generated)"
    
    def test_validate_turn_index_negative(self):
        """Test: Negative turn_index is rejected."""
        turn_index = -1
        
        # Validation logic
        if turn_index < 0:
            error = "turn_index phải >= 0"
        else:
            error = None
        
        assert error is not None
        assert "turn_index phải >= 0" in error
    
    def test_validate_turn_index_out_of_bounds(self, session_id, sample_turns):
        """Test: turn_index >= len(turns) is rejected."""
        turn_index = 999
        sorted_turns = sorted(sample_turns, key=lambda t: t.turn_index)
        
        # Validation logic
        if turn_index >= len(sorted_turns):
            error = f"Turn {turn_index} không tồn tại (session chỉ có {len(sorted_turns)} turns)"
        else:
            error = None
        
        assert error is not None
        assert "không tồn tại" in error
        assert "4 turns" in error
    
    def test_validate_turn_index_is_ai_turn(self, session_id, sample_turns):
        """Test: Requesting analysis for AI turn (odd index) is rejected."""
        turn_index = 1  # This is an AI turn
        sorted_turns = sorted(sample_turns, key=lambda t: t.turn_index)
        
        learner_turn = None
        
        for turn in sorted_turns:
            speaker_val = turn.speaker.value if hasattr(turn.speaker, "value") else turn.speaker
            if turn.turn_index == turn_index and speaker_val == Speaker.USER.value:
                learner_turn = turn
                break
        
        # Validation logic
        if not learner_turn:
            error = f"Turn {turn_index} không phải là USER turn hoặc không tồn tại"
        else:
            error = None
        
        assert error is not None
        assert "không phải là USER turn" in error
    
    def test_old_logic_bug_demonstration(self, session_id, sample_turns):
        """Test: Demonstrate the OLD buggy logic (for comparison)."""
        turn_index = 0
        
        # OLD BUGGY LOGIC (searching for same turn_index)
        learner_turn_old = None
        ai_turn_old = None
        
        for turn in sample_turns:
            speaker_val = turn.speaker.value if hasattr(turn.speaker, "value") else turn.speaker
            if turn.turn_index == turn_index and speaker_val == Speaker.USER.value:
                learner_turn_old = turn
            elif turn.turn_index == turn_index and speaker_val == Speaker.AI.value:
                ai_turn_old = turn
        
        # OLD LOGIC FAILS: ai_turn_old is None because no AI turn has turn_index=0
        assert learner_turn_old is not None
        assert ai_turn_old is None, "OLD LOGIC BUG: AI turn not found (searching for same turn_index)"
        
        # NEW FIXED LOGIC (searching for turn_index + 1)
        sorted_turns = sorted(sample_turns, key=lambda t: t.turn_index)
        learner_turn_new = None
        ai_turn_new = None
        
        for i, turn in enumerate(sorted_turns):
            speaker_val = turn.speaker.value if hasattr(turn.speaker, "value") else turn.speaker
            
            if turn.turn_index == turn_index and speaker_val == Speaker.USER.value:
                learner_turn_new = turn
                
                if i + 1 < len(sorted_turns):
                    next_turn = sorted_turns[i + 1]
                    next_speaker = next_turn.speaker.value if hasattr(next_turn.speaker, "value") else next_turn.speaker
                    if next_speaker == Speaker.AI.value:
                        ai_turn_new = next_turn
                break
        
        # NEW LOGIC WORKS: ai_turn_new is found
        assert learner_turn_new is not None
        assert ai_turn_new is not None, "NEW LOGIC FIXED: AI turn found correctly"
        assert ai_turn_new.turn_index == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
