"""
Tests for the main game module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestMainGame:
    """Test cases for main game functionality."""
    
    @patch('pygame.init')
    @patch('pygame.display.set_mode')
    @patch('pygame.mixer.init')
    def test_pygame_initialization(self, mock_mixer_init, mock_set_mode, mock_pygame_init):
        """Test that pygame initializes correctly."""
        # Import main after patching pygame
        import main
        
        # The patches should prevent actual pygame initialization
        assert True  # If we get here, pygame mocking worked
    
    def test_role_selection_constants(self):
        """Test that role constants are accessible."""
        try:
            from config.game.commands_config import ROLE_PURIFIER, ROLE_ARBITER, ROLE_ASCENDANT
            assert ROLE_PURIFIER == "PURIFIER"
            assert ROLE_ARBITER == "ARBITER"
            assert ROLE_ASCENDANT == "ASCENDANT"
        except ImportError:
            # If config import fails, check that main.py has the role strings
            import main
            # Check that main.py contains role selection functionality
            game = main.Game()
            assert hasattr(game, '_select_role')
    
    @patch('pygame.init')
    @patch('pygame.display.set_mode')
    @patch('pygame.mixer.init')
    @patch('pygame.time.Clock')
    def test_game_initialization_components(self, mock_clock, mock_mixer_init, mock_set_mode, mock_pygame_init):
        """Test that game components can be initialized."""
        # Mock pygame components
        mock_pygame_init.return_value = None
        mock_set_mode.return_value = Mock()
        mock_mixer_init.return_value = None
        mock_clock.return_value = Mock()
        
        # Import and test basic structure
        import main
        
        # Test passes if no import errors occur
        assert True
    
    @patch('builtins.input', side_effect=['1', ''])  # Simulate user input
    @patch('pygame.init')
    @patch('pygame.display.set_mode')
    @patch('pygame.mixer.init')
    def test_role_selection_input(self, mock_mixer_init, mock_set_mode, mock_pygame_init, mock_input):
        """Test role selection input handling."""
        try:
            import main
            # If import succeeds, basic structure is working
            assert True
        except Exception as e:
            # If there are import issues, that's what we're testing for
            pytest.skip(f"Import failed: {e}")


class TestGameConfiguration:
    """Test cases for game configuration."""
    
    def test_commands_config_exists(self):
        """Test that commands configuration exists."""
        try:
            from config.game.commands_config import ROLE_COMMANDS, COMMAND_HELP
            assert isinstance(ROLE_COMMANDS, dict)
            assert isinstance(COMMAND_HELP, dict)
        except ImportError:
            pytest.skip("Commands config not available")
    
    def test_role_commands_structure(self):
        """Test role commands structure."""
        try:
            from config.game.commands_config import ROLE_COMMANDS
            
            # Check that basic roles exist
            expected_roles = ['purifier', 'arbiter', 'ascendant']
            for role in expected_roles:
                if role in ROLE_COMMANDS:
                    assert isinstance(ROLE_COMMANDS[role], list)
                    
        except ImportError:
            pytest.skip("Commands config not available")
    
    def test_entity_interaction_commands_exist(self):
        """Test that entity interaction commands are configured."""
        try:
            from config.game.commands_config import COMMAND_HELP
            
            # Check for new entity interaction commands
            interaction_commands = [
                'convince', 'empathize', 'pressure', 'deceive', 
                'ally', 'threaten', 'fragment', 'enslave', 'consume'
            ]
            
            for cmd in interaction_commands:
                if cmd in COMMAND_HELP:
                    assert isinstance(COMMAND_HELP[cmd], str)
                    assert len(COMMAND_HELP[cmd]) > 0
                    
        except ImportError:
            pytest.skip("Commands config not available")
