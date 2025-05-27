"""
Shared test fixtures and configuration for pytest.
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def mock_pygame():
    """Fixture to mock pygame for tests."""
    with patch('pygame.init'), \
         patch('pygame.display.set_mode'), \
         patch('pygame.mixer.init'), \
         patch('pygame.event.get', return_value=[]), \
         patch('pygame.time.Clock'):
        yield


@pytest.fixture
def mock_llm_handler():
    """Fixture to create a mock LLM handler."""
    mock_handler = Mock()
    mock_handler.generate_rusty_response.return_value = "Mock response"
    mock_handler.generate_entity_interaction_response.return_value = "Mock entity response"
    mock_handler.get_corruption_level.return_value = 0.0
    mock_handler.set_corruption_level.return_value = None
    mock_handler.is_takeover_active.return_value = False
    return mock_handler


@pytest.fixture
def mock_terminal_renderer():
    """Fixture to create a mock terminal renderer."""
    mock_renderer = Mock()
    mock_renderer.width = 80
    mock_renderer.height = 24
    mock_renderer.add_to_buffer.return_value = None
    mock_renderer.print_info.return_value = None
    mock_renderer.print_error.return_value = None
    return mock_renderer


@pytest.fixture
def mock_file_system():
    """Fixture to create a mock file system handler."""
    mock_fs = Mock()
    mock_fs.current_directory = "/"
    mock_fs.current_path = []
    mock_fs.execute_cd.return_value = (True, "Directory changed")
    mock_fs.list_items.return_value = [("file1.txt", "file"), ("dir1", "directory")]
    mock_fs.get_current_directory_path.return_value = "/"
    return mock_fs


@pytest.fixture
def mock_effect_manager():
    """Fixture to create a mock effect manager."""
    mock_manager = Mock()
    mock_manager.trigger_rusty_response.return_value = None
    return mock_manager


@pytest.fixture
def mock_game_components(mock_llm_handler, mock_terminal_renderer, mock_file_system, mock_effect_manager):
    """Fixture to create all mock game components."""
    return {
        'llm_handler': mock_llm_handler,
        'terminal_renderer': mock_terminal_renderer,
        'file_system': mock_file_system,
        'effect_manager': mock_effect_manager,
        'puzzle_manager': Mock(),
        'story_manager': Mock()
    }
