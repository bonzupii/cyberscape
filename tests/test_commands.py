"""
Tests for the command handler module.
"""
import pytest
from unittest.mock import Mock, MagicMock
from src.core.commands import MainTerminalHandler, Command, CommandCategory


class TestMainTerminalHandler:
    """Test cases for MainTerminalHandler class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create mock dependencies
        self.mock_effect_manager = Mock()
        self.mock_file_system = Mock()
        self.mock_puzzle_manager = Mock()
        self.mock_story_manager = Mock()
        self.mock_terminal_renderer = Mock()
        self.mock_llm_handler = Mock()
        
        # Initialize handler
        self.handler = MainTerminalHandler(
            self.mock_effect_manager,
            self.mock_file_system,
            self.mock_puzzle_manager,
            self.mock_story_manager,
            self.mock_terminal_renderer,
            self.mock_llm_handler
        )
    
    def test_initialization(self):
        """Test handler initialization."""
        assert self.handler.effect_manager == self.mock_effect_manager
        assert self.handler.file_system == self.mock_file_system
        assert self.handler.puzzle_manager == self.mock_puzzle_manager
        assert self.handler.story_manager == self.mock_story_manager
        assert self.handler.terminal_renderer == self.mock_terminal_renderer
        assert self.handler.llm_handler == self.mock_llm_handler
        
        assert isinstance(self.handler.commands, dict)
        assert len(self.handler.commands) > 0
        assert self.handler.history == []
        assert self.handler.history_index == -1
        assert self.handler.current_command == ""
        assert self.handler.cursor_position == 0
    
    def test_command_registration(self):
        """Test that commands are properly registered."""
        # Check basic commands exist
        assert "help" in self.handler.commands
        assert "quit" in self.handler.commands
        assert "cd" in self.handler.commands
        assert "ls" in self.handler.commands
        assert "rusty" in self.handler.commands
        
        # Check aliases work
        assert "?" in self.handler.commands
        assert "h" in self.handler.commands
        assert "exit" in self.handler.commands
        assert "q" in self.handler.commands
    
    def test_command_execution_success(self):
        """Test successful command execution."""
        self.handler.current_command = "help"
        
        result = self.handler._execute_command()
        
        assert result is True
        assert "help" in self.handler.history
        assert self.handler.current_command == ""
        assert self.handler.cursor_position == 0
    
    def test_command_execution_unknown_command(self):
        """Test execution of unknown command."""
        self.handler.current_command = "nonexistent"
        
        result = self.handler._execute_command()
        
        assert result is False
        self.mock_terminal_renderer.print_error.assert_called_with("Unknown command: nonexistent")
    
    def test_command_execution_empty_command(self):
        """Test execution of empty command."""
        self.handler.current_command = ""
        
        result = self.handler._execute_command()
        
        assert result is False
    
    def test_rusty_command_success(self):
        """Test successful rusty command execution."""
        # Setup mocks
        self.mock_llm_handler.generate_rusty_response.return_value = "Test response"
        
        result = self.handler._cmd_rusty(["test", "prompt"])
        
        assert result is True
        self.mock_llm_handler.generate_rusty_response.assert_called_once()
        self.mock_terminal_renderer.add_to_buffer.assert_called_with("[Rusty] Test response")
    
    def test_rusty_command_no_args(self):
        """Test rusty command with no arguments."""
        result = self.handler._cmd_rusty([])
        
        assert result is False
        self.mock_terminal_renderer.add_to_buffer.assert_called_with("[Rusty] Usage: rusty <prompt>")
    
    def test_rusty_command_llm_error(self):
        """Test rusty command with LLM error."""
        self.mock_llm_handler.generate_rusty_response.side_effect = Exception("LLM Error")
        
        result = self.handler._cmd_rusty(["test"])
        
        assert result is False
        self.mock_terminal_renderer.add_to_buffer.assert_called_with(
            "[Rusty] *mechanical whirring* Error in neural pathways... *static*"
        )
    
    def test_help_command_general(self):
        """Test help command without arguments."""
        result = self.handler._cmd_help([])
        
        assert result is True
        self.mock_terminal_renderer.print_info.assert_called()
    
    def test_help_command_specific(self):
        """Test help command with specific command."""
        result = self.handler._cmd_help(["help"])
        
        assert result is True
        self.mock_terminal_renderer.print_info.assert_called()
    
    def test_help_command_unknown(self):
        """Test help command with unknown command."""
        result = self.handler._cmd_help(["unknown"])
        
        assert result is False
        self.mock_terminal_renderer.print_error.assert_called_with("Unknown command: unknown")
    
    def test_quit_command(self):
        """Test quit command."""
        result = self.handler._cmd_quit([])
        
        assert result is True
        self.mock_terminal_renderer.add_to_buffer.assert_called_with("Goodbye!")
    
    def test_cd_command_success(self):
        """Test successful cd command."""
        self.mock_file_system.execute_cd.return_value = (True, "Changed directory")
        
        result = self.handler._cmd_cd(["test_dir"])
        
        assert result is True
        self.mock_file_system.execute_cd.assert_called_with("test_dir")
        self.mock_terminal_renderer.add_to_buffer.assert_called_with("Changed directory")
    
    def test_cd_command_no_args(self):
        """Test cd command with no arguments."""
        result = self.handler._cmd_cd([])
        
        assert result is False
        self.mock_terminal_renderer.add_to_buffer.assert_called_with("Usage: cd [path]")
    
    def test_ls_command_with_items(self):
        """Test ls command with items."""
        self.mock_file_system.list_items.return_value = [("file1.txt", "file"), ("dir1", "directory")]
        self.mock_terminal_renderer.width = 80
        
        result = self.handler._cmd_ls([])
        
        assert result is True
        self.mock_file_system.list_items.assert_called_with(None)
        self.mock_terminal_renderer.add_to_buffer.assert_called()
    
    def test_ls_command_empty_directory(self):
        """Test ls command with empty directory."""
        self.mock_file_system.list_items.return_value = []
        
        result = self.handler._cmd_ls([])
        
        assert result is True
        self.mock_terminal_renderer.add_to_buffer.assert_called_with("Current directory is empty.")
    
    def test_cursor_movement(self):
        """Test cursor movement methods."""
        self.handler.current_command = "test"
        self.handler.cursor_position = 2
        
        # Test left movement
        self.handler._handle_left()
        assert self.handler.cursor_position == 1
        
        # Test right movement
        self.handler._handle_right()
        assert self.handler.cursor_position == 2
        
        # Test boundaries
        self.handler.cursor_position = 0
        self.handler._handle_left()
        assert self.handler.cursor_position == 0
        
        self.handler.cursor_position = 4
        self.handler._handle_right()
        assert self.handler.cursor_position == 4
    
    def test_character_input(self):
        """Test character input handling."""
        self.handler.current_command = "test"
        self.handler.cursor_position = 2
        
        self.handler._handle_printable("X")
        
        assert self.handler.current_command == "teXst"
        assert self.handler.cursor_position == 3
    
    def test_backspace_handling(self):
        """Test backspace key handling."""
        self.handler.current_command = "test"
        self.handler.cursor_position = 2
        
        self.handler._handle_backspace()
        
        assert self.handler.current_command == "tst"
        assert self.handler.cursor_position == 1
    
    def test_delete_handling(self):
        """Test delete key handling."""
        self.handler.current_command = "test"
        self.handler.cursor_position = 2
        
        self.handler._handle_delete()
        
        assert self.handler.current_command == "tet"
        assert self.handler.cursor_position == 2


class TestCommand:
    """Test cases for Command class."""
    
    def test_command_creation(self):
        """Test command creation."""
        def dummy_handler(args):
            return True
        
        cmd = Command(
            name="test",
            aliases=["t"],
            category=CommandCategory.SYSTEM,
            description="Test command",
            usage="test [args]",
            handler=dummy_handler
        )
        
        assert cmd.name == "test"
        assert cmd.aliases == ["t"]
        assert cmd.category == CommandCategory.SYSTEM
        assert cmd.description == "Test command"
        assert cmd.usage == "test [args]"
        assert cmd.handler == dummy_handler
        assert cmd.requires_role is None
        assert cmd.requires_item is None
        assert cmd.requires_state is None
