"""Tests for ConversationOrchestrator."""

import pytest
from unittest.mock import Mock, MagicMock
from src.domain.services.conversation_orchestrator import (
    ConversationOrchestrator,
    ConversationGenerationRequest,
    ConversationGenerationResponse,
)
from src.domain.entities.session import Session
from src.domain.entities.turn import Turn
from src.domain.value_objects.enums import Speaker, ProficiencyLevel, Gender
from ulid import ULID


class TestConversationOrchestrator:
    """Test ConversationOrchestrator."""
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "model_router": Mock(),
            "prompt_builder": Mock(),
            "streaming_response": Mock(),
            "response_validator": Mock(),
            "metrics_logger": Mock(),
            "scaffolding_system": Mock(),
        }
    
    @pytest.fixture
    def orchestrator(self, mock_services):
        """Create orchestrator with mocks."""
        return ConversationOrchestrator(
            model_router=mock_services["model_router"],
            prompt_builder=mock_services["prompt_builder"],
            streaming_response=mock_services["streaming_response"],
            response_validator=mock_services["response_validator"],
            metrics_logger=mock_services["metrics_logger"],
            scaffolding_system=mock_services["scaffolding_system"],
        )
    
    @pytest.fixture
    def sample_session(self):
        """Create sample session."""
        return Session(
            session_id=ULID(),
            scenario_id=ULID(),
            user_id="user123",
            learner_role_id="role1",
            ai_role_id="role2",
            ai_gender=Gender.FEMALE,
            level=ProficiencyLevel.A1,
        )
    
    @pytest.fixture
    def sample_user_turn(self, sample_session):
        """Create sample user turn."""
        return Turn(
            session_id=sample_session.session_id,
            turn_index=0,
            speaker=Speaker.USER,
            content="Hello, how are you?",
        )
    
    def test_generate_response_success(self, orchestrator, mock_services, sample_session, sample_user_turn):
        """Test successful response generation."""
        # Setup mocks
        mock_routing = Mock()
        mock_routing.primary_model = "amazon.nova-micro-v1:0"
        mock_routing.fallback_model = "amazon.nova-lite-v1:0"
        mock_routing.max_tokens = 40
        mock_routing.temperature = 0.7
        mock_services["model_router"].route.return_value = mock_routing
        
        mock_services["prompt_builder"].build_optimized_prompt.return_value = "System prompt"
        
        mock_services["streaming_response"].invoke_with_streaming.return_value = {
            "text": "Hello! How are you? [warmly]",
            "ttft_ms": 350.0,
            "latency_ms": 1800.0,
            "input_tokens": 100,
            "output_tokens": 20,
        }
        
        mock_services["response_validator"].validate.return_value = True
        mock_services["metrics_logger"]._calculate_cost.return_value = 0.008
        mock_services["metrics_logger"].create_metrics.return_value = Mock()
        
        # Execute
        request = ConversationGenerationRequest(
            session=sample_session,
            user_turn=sample_user_turn,
            turn_history=[],
        )
        
        response = orchestrator.generate_response(request)
        
        # Verify
        assert isinstance(response, ConversationGenerationResponse)
        assert response.ai_text == "Hello! How are you? [warmly]"
        assert response.delivery_cue == "[warmly]"
        assert response.ttft_ms == 350.0
        assert response.latency_ms == 1800.0
        assert response.output_tokens == 20
        assert response.model_source == "primary"
        assert response.fallback_reason is None
        assert response.validation_passed is True
    
    def test_generate_response_with_fallback(self, orchestrator, mock_services, sample_session, sample_user_turn):
        """Test response generation with fallback."""
        # Setup mocks
        mock_routing = Mock()
        mock_routing.primary_model = "amazon.nova-micro-v1:0"
        mock_routing.fallback_model = "amazon.nova-lite-v1:0"
        mock_routing.max_tokens = 40
        mock_routing.temperature = 0.7
        mock_services["model_router"].route.return_value = mock_routing
        
        mock_services["prompt_builder"].build_optimized_prompt.return_value = "System prompt"
        
        # Primary fails
        mock_services["streaming_response"].invoke_with_streaming.side_effect = [
            Exception("Timeout"),
            {
                "text": "Thanks for asking!",
                "ttft_ms": 400.0,
                "latency_ms": 2000.0,
                "input_tokens": 100,
                "output_tokens": 15,
            }
        ]
        
        mock_services["response_validator"].validate.return_value = True
        mock_services["metrics_logger"]._calculate_cost.return_value = 0.015
        mock_services["metrics_logger"].create_metrics.return_value = Mock()
        
        # Execute
        request = ConversationGenerationRequest(
            session=sample_session,
            user_turn=sample_user_turn,
            turn_history=[],
        )
        
        response = orchestrator.generate_response(request)
        
        # Verify fallback was used
        assert response.model_source == "fallback"
        assert response.fallback_reason == "Timeout"
    
    def test_extract_delivery_cue(self, orchestrator):
        """Test delivery cue extraction."""
        # With cue
        cue = orchestrator._extract_delivery_cue("Hello! How are you? [warmly]")
        assert cue == "[warmly]"
        
        # Without cue
        cue = orchestrator._extract_delivery_cue("Hello! How are you?")
        assert cue == ""
        
        # Multiple cues (extracts first)
        cue = orchestrator._extract_delivery_cue("Hello [warmly] world [encouragingly]")
        assert cue == "[warmly]"
    
    def test_get_hint(self, orchestrator, mock_services, sample_session):
        """Test getting hint."""
        mock_services["scaffolding_system"].get_hint.return_value = "Try saying: 'I am fine'"
        
        hint = orchestrator.get_hint(sample_session, silence_duration_seconds=10)
        
        assert hint == "Try saying: 'I am fine'"
        mock_services["scaffolding_system"].get_hint.assert_called_once_with(
            level=sample_session.level,
            silence_duration_seconds=10,
        )
    
    def test_response_validation_failure_triggers_fallback(self, orchestrator, mock_services, sample_session, sample_user_turn):
        """Test that validation failure triggers fallback."""
        # Setup mocks
        mock_routing = Mock()
        mock_routing.primary_model = "amazon.nova-micro-v1:0"
        mock_routing.fallback_model = "amazon.nova-lite-v1:0"
        mock_routing.max_tokens = 40
        mock_routing.temperature = 0.7
        mock_services["model_router"].route.return_value = mock_routing
        
        mock_services["prompt_builder"].build_optimized_prompt.return_value = "System prompt"
        
        # Primary succeeds but validation fails
        mock_services["streaming_response"].invoke_with_streaming.side_effect = [
            {
                "text": "Too short",
                "ttft_ms": 350.0,
                "latency_ms": 1800.0,
                "input_tokens": 100,
                "output_tokens": 2,
            },
            {
                "text": "This is a better response with more content.",
                "ttft_ms": 400.0,
                "latency_ms": 2000.0,
                "input_tokens": 100,
                "output_tokens": 10,
            }
        ]
        
        # Validation fails for primary, passes for fallback
        mock_services["response_validator"].validate.side_effect = [False, True]
        mock_services["metrics_logger"]._calculate_cost.return_value = 0.015
        mock_services["metrics_logger"].create_metrics.return_value = Mock()
        
        # Execute
        request = ConversationGenerationRequest(
            session=sample_session,
            user_turn=sample_user_turn,
            turn_history=[],
        )
        
        response = orchestrator.generate_response(request)
        
        # Verify fallback was triggered
        assert response.model_source == "fallback"
        assert response.fallback_reason == "validation_failed"
        assert response.validation_passed is True
    
    def test_metrics_logged(self, orchestrator, mock_services, sample_session, sample_user_turn):
        """Test that metrics are logged."""
        # Setup mocks
        mock_routing = Mock()
        mock_routing.primary_model = "amazon.nova-micro-v1:0"
        mock_routing.fallback_model = "amazon.nova-lite-v1:0"
        mock_routing.max_tokens = 40
        mock_routing.temperature = 0.7
        mock_services["model_router"].route.return_value = mock_routing
        
        mock_services["prompt_builder"].build_optimized_prompt.return_value = "System prompt"
        mock_services["streaming_response"].invoke_with_streaming.return_value = {
            "text": "Hello!",
            "ttft_ms": 350.0,
            "latency_ms": 1800.0,
            "input_tokens": 100,
            "output_tokens": 5,
        }
        mock_services["response_validator"].validate.return_value = True
        mock_services["metrics_logger"]._calculate_cost.return_value = 0.005
        mock_services["metrics_logger"].create_metrics.return_value = Mock()
        
        # Execute
        request = ConversationGenerationRequest(
            session=sample_session,
            user_turn=sample_user_turn,
            turn_history=[],
        )
        
        orchestrator.generate_response(request)
        
        # Verify metrics were logged
        mock_services["metrics_logger"].create_metrics.assert_called_once()
        mock_services["metrics_logger"].log_metrics.assert_called_once()
