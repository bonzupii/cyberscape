"""
Tests for the LLM handler module.
"""
import pytest
from unittest.mock import Mock, patch
from src.core.llm import LLMHandler


class TestLLMHandler:
    """Test cases for LLMHandler class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.llm_handler = LLMHandler()
    
    def test_initialization(self):
        """Test LLM handler initialization."""
        assert self.llm_handler.rusty_mood == 0.0
        assert self.llm_handler.rusty_mood_history == []
        assert isinstance(self.llm_handler.rusty_personality_traits, dict)
        assert self.llm_handler.rusty_takeover_active is False
        assert isinstance(self.llm_handler.mechanical_sounds, dict)
    
    def test_set_dependencies(self):
        """Test setting dependencies."""
        mock_game_state = Mock()
        mock_effect_manager = Mock()
        mock_terminal = Mock()
        
        self.llm_handler.set_dependencies(mock_game_state, mock_effect_manager, mock_terminal)
        
        assert self.llm_handler.game_state_manager == mock_game_state
        assert self.llm_handler.effect_manager == mock_effect_manager
        assert self.llm_handler.terminal == mock_terminal
    
    def test_corruption_level_setting(self):
        """Test setting and getting corruption level."""
        # Test normal range
        self.llm_handler.set_corruption_level(0.5)
        assert self.llm_handler.get_corruption_level() == 0.5
        
        # Test bounds
        self.llm_handler.set_corruption_level(-0.5)
        assert self.llm_handler.get_corruption_level() == 0.0
        
        self.llm_handler.set_corruption_level(1.5)
        assert self.llm_handler.get_corruption_level() == 1.0
    
    def test_takeover_state(self):
        """Test takeover state management."""
        assert not self.llm_handler.is_takeover_active()
        
        self.llm_handler.rusty_takeover_active = True
        assert self.llm_handler.is_takeover_active()
        
        self.llm_handler.end_takeover()
        assert not self.llm_handler.is_takeover_active()
    
    @patch('src.core.llm.requests')
    def test_call_ollama_success(self, mock_requests):
        """Test successful Ollama API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Test response"}
        mock_requests.post.return_value = mock_response
        
        result = self.llm_handler.call_ollama("test prompt")
        assert result == "Test response"
    
    @patch('src.core.llm.requests')
    def test_call_ollama_failure(self, mock_requests):
        """Test failed Ollama API call."""
        mock_requests.post.side_effect = Exception("Network error")
        
        result = self.llm_handler.call_ollama("test prompt")
        assert result == "__NETWORK_ERROR__"
    
    def test_get_random_sound_effects(self):
        """Test sound effect generation."""
        context = {'corruption_level': 0.0}
        sounds = self.llm_handler._get_random_sound_effects(context, count=2)
        
        assert len(sounds) == 2
        assert all(isinstance(sound, str) for sound in sounds)
        assert all(sound.startswith('*') and sound.endswith('*') for sound in sounds)
    
    def test_format_rusty_response(self):
        """Test Rusty response formatting."""
        context = {'corruption_level': 0.0}
        response = "Test response"
        
        formatted = self.llm_handler._format_rusty_response(response, context)
        assert "Test response" in formatted
        assert any(char in formatted for char in ['*'])
    
    def test_generate_entity_interaction_response(self):
        """Test entity interaction response generation."""
        with patch.object(self.llm_handler, 'get_response') as mock_get_response:
            mock_get_response.return_value = "Mocked response"
            
            context = {
                'role': 'purifier',
                'corruption_level': 0.0,
                'location': 'test_location'
            }
            
            result = self.llm_handler.generate_entity_interaction_response(
                'voss', 'convince', 'test message', context
            )
            
            assert result == "Mocked response"
            mock_get_response.assert_called_once()
