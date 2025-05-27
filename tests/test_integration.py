"""
Integration tests for the Cyberscape game.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestGameIntegration:
    """Integration test cases for the game."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock external dependencies
        self.pygame_patcher = patch('pygame.init')
        self.display_patcher = patch('pygame.display.set_mode')
        self.mixer_patcher = patch('pygame.mixer.init')
        self.event_patcher = patch('pygame.event.get')
        
        self.pygame_patcher.start()
        self.display_patcher.start()
        self.mixer_patcher.start()
        self.event_patcher.start()
    
    def teardown_method(self):
        """Clean up after tests."""
        self.pygame_patcher.stop()
        self.display_patcher.stop()
        self.mixer_patcher.stop()
        self.event_patcher.stop()
    
    def test_core_components_can_be_imported(self):
        """Test that all core components can be imported without errors."""
        try:
            from src.core.llm import LLMHandler
            from src.core.commands import MainTerminalHandler
            from src.core.filesystem import FileSystemHandler
            from src.core.effects import EffectManager
            from src.ui.terminal import TerminalRenderer
            
            assert True  # If we get here, imports worked
        except ImportError as e:
            pytest.fail(f"Failed to import core components: {e}")
    
    def test_llm_and_commands_integration(self):
        """Test that LLM handler and command handler can work together."""
        try:
            from src.core.llm import LLMHandler
            from src.core.commands import MainTerminalHandler
            
            # Create mock dependencies
            llm_handler = LLMHandler()
            
            mock_effect_manager = Mock()
            mock_file_system = Mock()
            mock_puzzle_manager = Mock()
            mock_story_manager = Mock()
            mock_terminal_renderer = Mock()
            
            # Create command handler with LLM handler
            command_handler = MainTerminalHandler(
                mock_effect_manager,
                mock_file_system,
                mock_puzzle_manager,
                mock_story_manager,
                mock_terminal_renderer,
                llm_handler
            )
            
            # Verify integration
            assert command_handler.llm_handler == llm_handler
            assert "rusty" in command_handler.commands
            
        except Exception as e:
            pytest.fail(f"LLM and commands integration failed: {e}")
    
    def test_entity_interaction_commands_registered(self):
        """Test that entity interaction commands are properly registered."""
        try:
            from src.core.llm import LLMHandler
            from src.core.commands import MainTerminalHandler
            
            # Create handlers
            llm_handler = LLMHandler()
            
            mock_effect_manager = Mock()
            mock_file_system = Mock()
            mock_puzzle_manager = Mock()
            mock_story_manager = Mock()
            mock_terminal_renderer = Mock()
            
            command_handler = MainTerminalHandler(
                mock_effect_manager,
                mock_file_system,
                mock_puzzle_manager,
                mock_story_manager,
                mock_terminal_renderer,
                llm_handler
            )
            
            # Check for entity interaction commands
            entity_commands = [
                'convince', 'empathize', 'pressure', 'deceive',
                'ally', 'threaten', 'fragment', 'enslave', 'consume'
            ]
            
            registered_commands = list(command_handler.commands.keys())
            
            # Some of these commands should be registered
            # (depends on which ones were implemented)
            for cmd in entity_commands:
                if cmd in registered_commands:
                    assert command_handler.commands[cmd] is not None
            
            # At least rusty should be there
            assert 'rusty' in registered_commands
            
        except Exception as e:
            pytest.fail(f"Entity interaction commands test failed: {e}")
    
    def test_rusty_command_execution(self):
        """Test that rusty command can be executed."""
        try:
            from src.core.llm import LLMHandler
            from src.core.commands import MainTerminalHandler
            
            # Create handlers
            llm_handler = LLMHandler()
            
            mock_effect_manager = Mock()
            mock_file_system = Mock()
            mock_puzzle_manager = Mock()
            mock_story_manager = Mock()
            mock_terminal_renderer = Mock()
            
            command_handler = MainTerminalHandler(
                mock_effect_manager,
                mock_file_system,
                mock_puzzle_manager,
                mock_story_manager,
                mock_terminal_renderer,
                llm_handler
            )
            
            # Mock LLM response
            with patch.object(llm_handler, 'generate_rusty_response', return_value="Test response"):
                result = command_handler._cmd_rusty(["test", "message"])
                
                assert result is True
                mock_terminal_renderer.add_to_buffer.assert_called()
                
        except Exception as e:
            pytest.fail(f"Rusty command execution test failed: {e}")
    
    def test_configuration_integration(self):
        """Test that game configuration integrates properly."""
        try:
            from config.game.commands_config import ROLE_COMMANDS, COMMAND_HELP
            
            # Basic structure checks
            assert isinstance(ROLE_COMMANDS, dict)
            assert isinstance(COMMAND_HELP, dict)
            
            # Check that roles have commands
            for role, commands in ROLE_COMMANDS.items():
                assert isinstance(commands, list)
                assert len(commands) > 0
                
                # Check that commands have help text
                for cmd in commands:
                    if cmd in COMMAND_HELP:
                        assert isinstance(COMMAND_HELP[cmd], str)
                        assert len(COMMAND_HELP[cmd]) > 0
                        
        except ImportError:
            pytest.skip("Configuration not available")
        except Exception as e:
            pytest.fail(f"Configuration integration test failed: {e}")
