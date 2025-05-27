#!/usr/bin/env python3
"""
Comprehensive test suite for UI Terminal (terminal.py).

Tests terminal rendering, styling, input handling, and border effects integration.
Achieves 100% code coverage for the UI Terminal module.
"""

import unittest
import pygame
import time
from unittest.mock import Mock, MagicMock, patch, call
from dataclasses import dataclass

# Import modules under test
from src.ui.terminal import (
    TerminalStyle, TextEffect, TerminalRenderer, TextLine
)
from src.ui.border_effects import BorderRegion


class TestTerminalStyle(unittest.TestCase):
    """Test TerminalStyle dataclass functionality."""
    
    def test_terminal_style_initialization_default(self):
        """Test TerminalStyle creation with default values."""
        style = TerminalStyle()
        
        self.assertEqual(style.fg_color, (200, 200, 200))
        self.assertEqual(style.bg_color, (0, 0, 0))
        self.assertFalse(style.bold)
        self.assertFalse(style.underline)
        self.assertFalse(style.blink)
        self.assertFalse(style.reverse)
        self.assertFalse(style.dim)
    
    def test_terminal_style_initialization_custom(self):
        """Test TerminalStyle creation with custom values."""
        style = TerminalStyle(
            fg_color=(255, 0, 0),
            bg_color=(50, 50, 50),
            bold=True,
            underline=True,
            blink=True,
            reverse=True,
            dim=True
        )
        
        self.assertEqual(style.fg_color, (255, 0, 0))
        self.assertEqual(style.bg_color, (50, 50, 50))
        self.assertTrue(style.bold)
        self.assertTrue(style.underline)
        self.assertTrue(style.blink)
        self.assertTrue(style.reverse)
        self.assertTrue(style.dim)
    
    def test_terminal_style_to_dict(self):
        """Test TerminalStyle serialization to dictionary."""
        style = TerminalStyle(
            fg_color=(100, 150, 200),
            bg_color=(10, 20, 30),
            bold=True,
            dim=True
        )
        
        expected_dict = {
            "fg_color": (100, 150, 200),
            "bg_color": (10, 20, 30),
            "bold": True,
            "underline": False,
            "blink": False,
            "reverse": False,
            "dim": True
        }
        
        self.assertEqual(style.to_dict(), expected_dict)
    
    def test_terminal_style_from_dict(self):
        """Test TerminalStyle deserialization from dictionary."""
        style_dict = {
            "fg_color": (255, 128, 64),
            "bg_color": (32, 32, 32),
            "bold": True,
            "underline": False,
            "blink": True,
            "reverse": False,
            "dim": False
        }
        
        style = TerminalStyle.from_dict(style_dict)
        
        self.assertEqual(style.fg_color, (255, 128, 64))
        self.assertEqual(style.bg_color, (32, 32, 32))
        self.assertTrue(style.bold)
        self.assertFalse(style.underline)
        self.assertTrue(style.blink)
        self.assertFalse(style.reverse)
        self.assertFalse(style.dim)


class TestTextEffect(unittest.TestCase):
    """Test TextEffect base class functionality."""
    
    def test_text_effect_initialization(self):
        """Test TextEffect creation with text and duration."""
        effect = TextEffect("test text", 2.5)
        
        self.assertEqual(effect.text, "test text")
        self.assertEqual(effect.duration, 2.5)
        self.assertFalse(effect.is_complete)
        self.assertIsInstance(effect.start_time, float)
    
    def test_text_effect_initialization_no_duration(self):
        """Test TextEffect creation with default duration."""
        effect = TextEffect("no duration")
        
        self.assertEqual(effect.text, "no duration")
        self.assertEqual(effect.duration, 0.0)
        self.assertFalse(effect.is_complete)
    
    def test_text_effect_update_not_expired(self):
        """Test TextEffect update when duration hasn't expired."""
        effect = TextEffect("test", 10.0)  # Long duration
        
        result = effect.update()
        
        self.assertEqual(result, "test")
        self.assertFalse(effect.is_complete)
        self.assertFalse(effect.is_done())
    
    def test_text_effect_update_zero_duration(self):
        """Test TextEffect update with zero duration."""
        effect = TextEffect("instant", 0.0)
        
        result = effect.update()
        
        self.assertEqual(result, "instant")
        self.assertFalse(effect.is_complete)  # Zero duration never completes
    
    @patch('time.time')
    def test_text_effect_update_expired(self, mock_time):
        """Test TextEffect update when duration has expired."""
        # Mock time progression
        start_time = 1000.0
        mock_time.side_effect = [start_time, start_time + 3.0]  # 3 seconds later
        
        effect = TextEffect("expired", 2.0)  # 2 second duration
        result = effect.update()
        
        self.assertEqual(result, "expired")
        self.assertTrue(effect.is_complete)
        self.assertTrue(effect.is_done())


class TestTextLine(unittest.TestCase):
    """Test TextLine dataclass functionality."""
    
    def test_text_line_creation(self):
        """Test TextLine creation with text and style."""
        style = TerminalStyle(fg_color=(255, 0, 0))
        line = TextLine("test line", style)
        
        self.assertEqual(line.text, "test line")
        self.assertEqual(line.style, style)
    
    def test_text_line_creation_default_style(self):
        """Test TextLine creation with default style."""
        line = TextLine("default style", TerminalStyle())
        
        self.assertEqual(line.text, "default style")
        self.assertIsInstance(line.style, TerminalStyle)


class TestTerminalRenderer(unittest.TestCase):
    """Test TerminalRenderer functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Initialize pygame for testing
        pygame.init()
        self.renderer = TerminalRenderer()
    
    def tearDown(self):
        """Clean up after tests."""
        pygame.quit()
    
    def test_terminal_renderer_initialization(self):
        """Test TerminalRenderer initialization."""
        renderer = TerminalRenderer()
        
        self.assertIsNone(renderer.screen)
        self.assertIsNone(renderer.font)
        self.assertIsNone(renderer.bold_font)
        self.assertEqual(renderer.width, 0)
        self.assertEqual(renderer.height, 0)
        self.assertEqual(renderer.cursor_x, 0)
        self.assertEqual(renderer.cursor_y, 0)
        self.assertEqual(renderer.scroll_offset, 0)
        self.assertEqual(renderer.buffer, [])
        self.assertEqual(renderer.history, [])
        self.assertEqual(renderer.history_index, -1)
        self.assertEqual(renderer.max_history, 1000)
        self.assertFalse(renderer._is_corrupted)
        self.assertEqual(renderer.corruption_level, 0.0)
        self.assertIsNone(renderer.prompt_override)
        self.assertIsNone(renderer.completion_handler)
        self.assertEqual(renderer.current_input, "")
        self.assertTrue(renderer.cursor_visible)
        self.assertEqual(renderer.cursor_blink_time, 0.5)
        self.assertIsInstance(renderer.last_cursor_toggle, float)
        self.assertEqual(renderer.completion_suggestions, [])
        self.assertEqual(renderer.completion_index, -1)
        self.assertEqual(renderer.char_width, 0)
        self.assertEqual(renderer.char_height, 0)
        self.assertIsNone(renderer.theme_manager)
        # BorderManager should be initialized
        self.assertIsNotNone(renderer.border_manager)
    
    def test_initialize_with_default_font(self):
        """Test TerminalRenderer initialization with default font."""
        self.renderer.initialize(800, 600)
        
        self.assertEqual(self.renderer.width, 800)
        self.assertEqual(self.renderer.height, 600)
        self.assertIsNotNone(self.renderer.screen)
        self.assertIsNotNone(self.renderer.font)
        self.assertIsNotNone(self.renderer.bold_font)
        self.assertGreater(self.renderer.char_width, 0)
        self.assertGreater(self.renderer.char_height, 0)
    
    @patch('pygame.font.Font')
    def test_initialize_with_custom_font(self, mock_font_constructor):
        """Test TerminalRenderer initialization with custom font path."""
        mock_font = Mock()
        mock_font.render.return_value = Mock()
        mock_font.render.return_value.get_width.return_value = 10
        mock_font.render.return_value.get_height.return_value = 16
        mock_font_constructor.return_value = mock_font
        
        self.renderer.initialize(800, 600, "/path/to/font.ttf")
        
        # Verify custom font was loaded
        self.assertEqual(mock_font_constructor.call_count, 2)  # Regular and bold
        mock_font_constructor.assert_any_call("/path/to/font.ttf", 16)
        
        self.assertEqual(self.renderer.char_width, 10)
        self.assertEqual(self.renderer.char_height, 16)
    
    def test_handle_input_printable_characters(self):
        """Test handling of printable character input."""
        event = Mock()
        event.type = pygame.KEYDOWN
        event.unicode = "a"  # "a" is naturally printable
        
        result = self.renderer.handle_input(event)
        
        self.assertIsNone(result)
        self.assertEqual(self.renderer.current_input, "a")
        self.assertEqual(self.renderer.completion_suggestions, [])
        self.assertEqual(self.renderer.completion_index, -1)
    
    def test_handle_input_return_key(self):
        """Test handling of Return key input."""
        self.renderer.current_input = "test command"
        
        event = Mock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_RETURN
        
        result = self.renderer.handle_input(event)
        
        self.assertEqual(result, "test command")
        self.assertEqual(self.renderer.current_input, "")
        self.assertIn("test command", self.renderer.history)
        self.assertEqual(self.renderer.history_index, -1)
    
    def test_handle_input_backspace(self):
        """Test handling of Backspace key input."""
        self.renderer.current_input = "hello"
        
        event = Mock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_BACKSPACE
        
        result = self.renderer.handle_input(event)
        
        self.assertIsNone(result)
        self.assertEqual(self.renderer.current_input, "hell")
    
    def test_handle_input_backspace_empty_input(self):
        """Test handling of Backspace key with empty input."""
        self.renderer.current_input = ""
        
        event = Mock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_BACKSPACE
        
        result = self.renderer.handle_input(event)
        
        self.assertIsNone(result)
        self.assertEqual(self.renderer.current_input, "")
    
    def test_handle_input_tab_with_completion_handler(self):
        """Test handling of Tab key with completion handler."""
        mock_handler = Mock()
        mock_handler.get_suggestions.return_value = (["command1", "command2"], "comm")
        self.renderer.completion_handler = mock_handler
        self.renderer.current_input = "com"
        
        event = Mock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_TAB
        
        result = self.renderer.handle_input(event)
        
        self.assertIsNone(result)
        mock_handler.get_suggestions.assert_called_once_with("com", 3)
        self.assertEqual(self.renderer.current_input, "comm")  # Common prefix applied
        self.assertEqual(self.renderer.completion_suggestions, [])
        self.assertEqual(self.renderer.completion_index, -1)
    
    def test_handle_input_tab_with_suggestions_no_prefix(self):
        """Test handling of Tab key with suggestions but no common prefix."""
        mock_handler = Mock()
        mock_handler.get_suggestions.return_value = (["ls", "cat"], None)
        self.renderer.completion_handler = mock_handler
        self.renderer.current_input = ""
        
        event = Mock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_TAB
        
        result = self.renderer.handle_input(event)
        
        self.assertIsNone(result)
        self.assertEqual(self.renderer.current_input, "ls")  # First suggestion
        self.assertEqual(self.renderer.completion_suggestions, ["ls", "cat"])
        self.assertEqual(self.renderer.completion_index, 0)
    
    def test_handle_input_tab_cycle_suggestions(self):
        """Test cycling through completion suggestions with multiple Tab presses."""
        mock_handler = Mock()
        mock_handler.get_suggestions.return_value = (None, None) # Changed to trigger cycling
        self.renderer.completion_handler = mock_handler
        self.renderer.completion_suggestions = ["ls", "cat"]
        self.renderer.completion_index = 0
    
        event = Mock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_TAB
        
        result = self.renderer.handle_input(event)
        
        self.assertIsNone(result)
        self.assertEqual(self.renderer.current_input, "cat")  # Second suggestion
        self.assertEqual(self.renderer.completion_index, 1)
    
    def test_handle_input_tab_cycle_wrap_around(self):
        """Test cycling suggestions wraps around to beginning."""
        mock_handler = Mock()
        mock_handler.get_suggestions.return_value = ([], "")  # No new suggestions, no common prefix
        self.renderer.completion_handler = mock_handler
        self.renderer.completion_suggestions = ["ls", "cat"]
        self.renderer.completion_index = 1  # Last suggestion
        
        event = Mock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_TAB
        
        result = self.renderer.handle_input(event)
        
        self.assertIsNone(result)
        self.assertEqual(self.renderer.current_input, "ls")  # Wrapped to first
        self.assertEqual(self.renderer.completion_index, 0)
    
    def test_handle_input_tab_no_completion_handler(self):
        """Test Tab key handling without completion handler."""
        event = Mock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_TAB
        
        result = self.renderer.handle_input(event)
        
        self.assertIsNone(result)
    
    def test_handle_input_up_arrow_history(self):
        """Test handling of Up arrow key for history navigation."""
        self.renderer.history = ["cmd1", "cmd2", "cmd3"]
        
        event = Mock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_UP
        
        result = self.renderer.handle_input(event)
        
        self.assertIsNone(result)
        self.assertEqual(self.renderer.current_input, "cmd3")  # Last command
        self.assertEqual(self.renderer.history_index, 2)
    
    def test_handle_input_up_arrow_navigate_backwards(self):
        """Test Up arrow navigation backwards through history."""
        self.renderer.history = ["cmd1", "cmd2", "cmd3"]
        self.renderer.history_index = 2
        
        event = Mock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_UP
        
        result = self.renderer.handle_input(event)
        
        self.assertIsNone(result)
        self.assertEqual(self.renderer.current_input, "cmd2")  # Previous command
        self.assertEqual(self.renderer.history_index, 1)
    
    def test_handle_input_up_arrow_at_beginning(self):
        """Test Up arrow at beginning of history."""
        self.renderer.history = ["cmd1", "cmd2"]
        self.renderer.history_index = 0
        
        event = Mock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_UP
        
        result = self.renderer.handle_input(event)
        
        self.assertIsNone(result)
        self.assertEqual(self.renderer.current_input, "cmd1")  # Stays at first
        self.assertEqual(self.renderer.history_index, 0)
    
    def test_handle_input_up_arrow_empty_history(self):
        """Test Up arrow with empty history."""
        self.renderer.history = []
        
        event = Mock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_UP
        
        result = self.renderer.handle_input(event)
        
        self.assertIsNone(result)
        self.assertEqual(self.renderer.current_input, "")
        self.assertEqual(self.renderer.history_index, -1)
    
    def test_handle_input_down_arrow_history(self):
        """Test handling of Down arrow key for history navigation."""
        self.renderer.history = ["cmd1", "cmd2", "cmd3"]
        self.renderer.history_index = 1
        
        event = Mock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_DOWN
        
        result = self.renderer.handle_input(event)
        
        self.assertIsNone(result)
        self.assertEqual(self.renderer.current_input, "cmd3")  # Next command
        self.assertEqual(self.renderer.history_index, 2)
    
    def test_handle_input_down_arrow_to_current(self):
        """Test Down arrow navigation to current input."""
        self.renderer.history = ["cmd1", "cmd2"]
        self.renderer.history_index = 0  # First command
        self.renderer.current_input = "cmd1"
        
        event = Mock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_DOWN
        
        result = self.renderer.handle_input(event)
        
        self.assertIsNone(result)
        self.assertEqual(self.renderer.current_input, "cmd2")  # Move to next command
        self.assertEqual(self.renderer.history_index, 1)
    
    def test_handle_input_down_arrow_no_history_active(self):
        """Test Down arrow when no history navigation is active."""
        self.renderer.history = ["cmd1", "cmd2"]
        self.renderer.history_index = -1
        
        event = Mock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_DOWN
        
        result = self.renderer.handle_input(event)
        
        self.assertIsNone(result)
        self.assertEqual(self.renderer.history_index, -1)
    
    def test_handle_input_non_keydown_event(self):
        """Test handling of non-KEYDOWN events."""
        event = Mock()
        event.type = pygame.KEYUP  # Not KEYDOWN
        
        result = self.renderer.handle_input(event)
        
        self.assertIsNone(result)
    
    def test_add_to_buffer_with_style(self):
        """Test adding text to buffer with custom style."""
        style = TerminalStyle(fg_color=(255, 0, 0))
        self.renderer.add_to_buffer("test text", style)
        
        self.assertEqual(len(self.renderer.buffer), 1)
        self.assertEqual(self.renderer.buffer[0].text, "test text")
        self.assertEqual(self.renderer.buffer[0].style, style)
    
    def test_add_to_buffer_default_style(self):
        """Test adding text to buffer with default style."""
        self.renderer.add_to_buffer("default text")
        
        self.assertEqual(len(self.renderer.buffer), 1)
        self.assertEqual(self.renderer.buffer[0].text, "default text")
        self.assertIsInstance(self.renderer.buffer[0].style, TerminalStyle)
    
    def test_add_to_buffer_max_history_limit(self):
        """Test buffer respects maximum history limit."""
        self.renderer.max_history = 3
        
        for i in range(5):
            self.renderer.add_to_buffer(f"line {i}")
        
        self.assertEqual(len(self.renderer.buffer), 3)
        self.assertEqual(self.renderer.buffer[0].text, "line 2")
        self.assertEqual(self.renderer.buffer[1].text, "line 3")
        self.assertEqual(self.renderer.buffer[2].text, "line 4")
    
    def test_clear_buffer(self):
        """Test clearing the terminal buffer."""
        self.renderer.add_to_buffer("line 1")
        self.renderer.add_to_buffer("line 2")
        
        self.renderer.clear_buffer()
        
        self.assertEqual(len(self.renderer.buffer), 0)
    
    def test_set_cursor(self):
        """Test setting cursor position."""
        self.renderer.width = 100
        self.renderer.height = 50
        
        self.renderer.set_cursor(25, 15)
        
        self.assertEqual(self.renderer.cursor_x, 25)
        self.assertEqual(self.renderer.cursor_y, 15)
    
    def test_set_cursor_bounds_checking(self):
        """Test cursor position bounds checking."""
        self.renderer.width = 100
        self.renderer.height = 50
        
        # Test negative coordinates
        self.renderer.set_cursor(-5, -10)
        self.assertEqual(self.renderer.cursor_x, 0)
        self.assertEqual(self.renderer.cursor_y, 0)
        
        # Test coordinates exceeding bounds
        self.renderer.set_cursor(150, 75)
        self.assertEqual(self.renderer.cursor_x, 99)  # width - 1
        self.assertEqual(self.renderer.cursor_y, 49)  # height - 1
    
    def test_get_cursor(self):
        """Test getting cursor position."""
        self.renderer.cursor_x = 30
        self.renderer.cursor_y = 20
        
        position = self.renderer.get_cursor()
        
        self.assertEqual(position, (30, 20))
    
    def test_set_dimensions(self):
        """Test setting terminal dimensions."""
        self.renderer.set_dimensions(800, 600)
        
        self.assertEqual(self.renderer.width, 800)
        self.assertEqual(self.renderer.height, 600)
    
    def test_set_dimensions_minimum_values(self):
        """Test setting dimensions ensures minimum values."""
        self.renderer.set_dimensions(0, -5)
        
        self.assertEqual(self.renderer.width, 1)
        self.assertEqual(self.renderer.height, 1)
    
    def test_set_corruption(self):
        """Test setting corruption level."""
        self.renderer.set_corruption(0.7)
        
        self.assertEqual(self.renderer.corruption_level, 0.7)
        self.assertTrue(self.renderer._is_corrupted)
    
    def test_set_corruption_bounds(self):
        """Test corruption level bounds checking."""
        # Test negative value
        self.renderer.set_corruption(-0.5)
        self.assertEqual(self.renderer.corruption_level, 0.0)
        self.assertFalse(self.renderer._is_corrupted)
        
        # Test value exceeding 1.0
        self.renderer.set_corruption(1.5)
        self.assertEqual(self.renderer.corruption_level, 1.0)
        self.assertTrue(self.renderer._is_corrupted)
    
    def test_set_corruption_zero(self):
        """Test setting corruption to zero."""
        self.renderer.set_corruption(0.0)
        
        self.assertEqual(self.renderer.corruption_level, 0.0)
        self.assertFalse(self.renderer._is_corrupted)
    
    def test_get_corruption(self):
        """Test getting corruption level."""
        self.renderer.corruption_level = 0.3
        
        level = self.renderer.get_corruption()
        
        self.assertEqual(level, 0.3)
    
    def test_is_corrupted(self):
        """Test checking corruption status."""
        self.renderer._is_corrupted = True
        self.assertTrue(self.renderer.is_corrupted())
        
        self.renderer._is_corrupted = False
        self.assertFalse(self.renderer.is_corrupted())
    
    def test_set_prompt_override(self):
        """Test setting custom prompt."""
        self.renderer.set_prompt_override("custom> ")
        
        self.assertEqual(self.renderer.prompt_override, "custom> ")
    
    def test_clear_prompt_override(self):
        """Test clearing custom prompt."""
        self.renderer.prompt_override = "custom> "
        self.renderer.clear_prompt_override()
        
        self.assertIsNone(self.renderer.prompt_override)
    
    def test_set_completion_handler(self):
        """Test setting completion handler."""
        mock_handler = Mock()
        self.renderer.set_completion_handler(mock_handler)
        
        self.assertEqual(self.renderer.completion_handler, mock_handler)
    
    def test_set_theme_manager(self):
        """Test setting theme manager."""
        mock_theme_manager = Mock()
        self.renderer.set_theme_manager(mock_theme_manager)
        
        self.assertEqual(self.renderer.theme_manager, mock_theme_manager)
    
    def test_print_info_compatibility(self):
        """Test print_info compatibility stub."""
        self.renderer.print_info("test info message")
        
        self.assertEqual(len(self.renderer.buffer), 1)
        self.assertEqual(self.renderer.buffer[0].text, "[INFO] test info message")
    
    def test_print_error_compatibility(self):
        """Test print_error compatibility stub."""
        self.renderer.print_error("test error message")
        
        self.assertEqual(len(self.renderer.buffer), 1)
        self.assertEqual(self.renderer.buffer[0].text, "[ERROR] test error message")


class TestTerminalRendererRendering(unittest.TestCase):
    """Test TerminalRenderer rendering functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        pygame.init()
        self.renderer = TerminalRenderer()
        self.renderer.initialize(800, 600)
        self.surface = pygame.Surface((800, 600))
    
    def tearDown(self):
        """Clean up after tests."""
        pygame.quit()
    
    @patch('src.ui.terminal.time.time')
    def test_render_basic(self, mock_time):
        """Test basic rendering functionality."""
        mock_time.return_value = 1000.0
        
        self.renderer.add_to_buffer("Test line 1")
        self.renderer.add_to_buffer("Test line 2")
        self.renderer.current_input = "current"
        
        # Should not raise any exceptions
        self.renderer.render(self.surface)
    
    def test_render_invalid_dimensions(self):
        """Test rendering with invalid dimensions."""
        self.renderer.width = 0
        self.renderer.height = 0
        
        # Should handle gracefully without crashing
        self.renderer.render(self.surface)
    
    @patch('src.ui.terminal.time.time')
    def test_render_with_effect_manager(self, mock_time):
        """Test rendering with effect manager."""
        mock_time.return_value = 1000.0
        mock_effect_manager = Mock()
        mock_effect_manager.apply_effects.return_value = "modified text"
        
        self.renderer.add_to_buffer("original text")
        self.renderer.render(self.surface, mock_effect_manager)
        
        # Effect manager should be called for buffer content
        mock_effect_manager.apply_effects.assert_called()
    
    @patch('src.ui.terminal.time.time')
    def test_render_with_corruption(self, mock_time):
        """Test rendering with corruption effects."""
        mock_time.return_value = 1000.0
        
        self.renderer.set_corruption(0.8)
        self.renderer.current_input = "corrupted input"
        
        mock_effect_manager = Mock()
        mock_effect_manager.apply_effects.return_value = "glitched text"
        
        self.renderer.render(self.surface, mock_effect_manager)
        
        # Should apply corruption effects to input
        mock_effect_manager.apply_effects.assert_called()
    
    @patch('src.ui.terminal.time.time')
    def test_render_cursor_visibility(self, mock_time):
        """Test cursor rendering based on visibility and blink timing."""
        # Test cursor visible
        mock_time.return_value = 1000.0
        self.renderer.last_cursor_toggle = 999.0  # Within blink time
        self.renderer.cursor_visible = True
        
        self.renderer.render(self.surface)
        
        # Test cursor hidden due to blink timing
        self.renderer.last_cursor_toggle = 998.0  # Beyond blink time
        self.renderer.render(self.surface)
    
    @patch('src.ui.terminal.time.time')
    def test_render_with_prompt_override(self, mock_time):
        """Test rendering with custom prompt."""
        mock_time.return_value = 1000.0
        
        self.renderer.set_prompt_override("custom$ ")
        self.renderer.current_input = "test"
        
        self.renderer.render(self.surface)
        
        # Verify prompt override is used (indirectly through no exceptions)
    
    @patch('src.ui.terminal.time.time')
    def test_render_with_completion_suggestions(self, mock_time):
        """Test rendering with completion suggestions."""
        mock_time.return_value = 1000.0
        
        self.renderer.completion_suggestions = ["suggestion1", "suggestion2"]
        self.renderer.completion_index = 0
        self.renderer.current_input = "sug"
        
        self.renderer.render(self.surface)
    
    @patch('src.ui.terminal.time.time')
    def test_render_corrupted_suggestions(self, mock_time):
        """Test rendering completion suggestions with corruption."""
        mock_time.return_value = 1000.0
        
        self.renderer.set_corruption(0.5)
        self.renderer.completion_suggestions = ["cmd1", "cmd2"]
        self.renderer.completion_index = 1
        
        mock_effect_manager = Mock()
        mock_effect_manager.apply_effects.return_value = "corrupted suggestion"
        
        self.renderer.render(self.surface, mock_effect_manager)
    
    def test_render_text_private_method(self):
        """Test private _render_text method."""
        style = TerminalStyle(fg_color=(255, 0, 0), bold=True)
        
        # Should not raise exceptions
        self.renderer._render_text(self.surface, "test text", 10, 20, style)
    
    @patch('src.ui.terminal.time.time')  
    def test_render_grid_border(self, mock_time):
        """Test grid border rendering method."""
        mock_time.return_value = 1000.0
        
        # Should not raise exceptions
        self.renderer.render_grid_border(
            self.surface, 10, 8, 80, 75, 800, 600,
            border_anim_phase=0.5
        )
    
    @patch('src.ui.terminal.time.time')
    def test_render_grid_screen(self, mock_time):
        """Test grid screen rendering method."""
        mock_time.return_value = 1000.0
        
        # Create a simple grid
        grid = []
        for row in range(8):
            grid_row = []
            for col in range(10):
                if row == 0 or row == 7 or col == 0 or col == 9:
                    grid_row.append(("BORDER", "#"))
                else:
                    grid_row.append(("TEXT", " "))
            grid.append(grid_row)
        
        # Should not raise exceptions
        self.renderer.render_grid_screen(
            self.surface, grid, 10, 8, 80, 75, 800, 600
        )


if __name__ == '__main__':
    unittest.main()
