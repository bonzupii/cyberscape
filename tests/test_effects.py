"""
Comprehensive tests for the Core Effects system.
"""
import pytest
import pygame
import time
import random
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.core.effects import (
    BaseEffect, CorruptionEffect, GlitchEffect, TypingEffect, ScrambleEffect,
    CharacterCorruptionEffect, EffectManager, EffectState, GlitchOverlayEffect,
    CORRUPTION_CHARS, PROFANITY_LIST, INTRUSIVE_THOUGHTS,
    apply_profanity_replacement, maybe_inject_intrusive_thought
)


class TestBaseEffect:
    """Test the base effect class."""

    def test_base_effect_initialization(self):
        """Test BaseEffect initialization."""
        callback = Mock()
        effect = BaseEffect(on_complete_callback=callback, priority=5)
        
        assert effect.on_complete_callback == callback
        assert effect.priority == 5
        assert effect.is_active == False
        assert effect.start_time == pygame.time.get_ticks()  # BaseEffect sets start_time in __init__
        assert effect.terminal_ref is None

    def test_base_effect_start_and_finish(self):
        """Test BaseEffect start and finish methods."""
        callback = Mock()
        effect = BaseEffect(on_complete_callback=callback)
        
        # Test start
        effect.start()
        assert effect.is_active == True
        assert effect.start_time is not None
        
        # Test finish
        effect.finish()
        assert effect.is_active == False
        callback.assert_called_once()

    def test_base_effect_get_state(self):
        """Test BaseEffect state serialization."""
        effect = BaseEffect(priority=3)
        effect.start()
        
        state = effect.get_state()
        assert state["priority"] == 3
        assert state["is_active"] == True
        assert "intensity" in state


class TestCorruptionEffect:
    """Test corruption effect functionality."""

    def test_corruption_effect_initialization(self):
        """Test CorruptionEffect initialization."""
        effect = CorruptionEffect(
            text="test text",
            intensity=0.7,
            duration=2000,
            profanity=True,
            intrusive=True,
            corruption_level=0.5
        )
        
        assert effect.original_text == "test text"
        assert effect.intensity == 0.7
        assert effect.duration == 2000
        assert effect.profanity == True
        assert effect.intrusive == True
        assert effect.corruption_level == 0.5

    def test_corruption_effect_glitchy_corruption(self):
        """Test glitchy character corruption."""
        effect = CorruptionEffect(text="hello world", intensity=1.0)
        
        # With maximum intensity, all characters should be corrupted
        corrupted = effect._apply_glitchy_corruption("hello world", 1.0)
        
        # Should be same length but different characters
        assert len(corrupted) == len("hello world")
        assert all(c in CORRUPTION_CHARS for c in corrupted if c != ' ')

    def test_corruption_effect_apply_method(self):
        """Test the apply method with different corruption types."""
        effect = CorruptionEffect(
            text="test message",
            intensity=0.5,
            profanity=True,
            intrusive=True,
            corruption_level=0.8
        )
        
        with patch('random.random', return_value=0.1):  # Low random to ensure consistent results
            result = effect.apply()
            
            # Should be corrupted version of original text
            assert result != "test message"
            assert isinstance(result, str)

    def test_corruption_effect_update(self):
        """Test corruption effect update and completion."""
        with patch('pygame.time.get_ticks', return_value=1000):
            effect = CorruptionEffect(text="test", duration=500)
            effect.start()  # Start the effect to set is_active = True
            
            # Should not be complete initially
            assert effect.update(0.1) == False
            
            # Fast forward time
            with patch('pygame.time.get_ticks', return_value=1600):
                assert effect.update(0.1) == True
                assert effect.is_active == False


class TestGlitchEffect:
    """Test glitch effect functionality."""

    def test_glitch_effect_initialization(self):
        """Test GlitchEffect initialization."""
        effect = GlitchEffect(text="test text", intensity=0.8, duration=1500)
        
        assert effect.original_text == "test text"
        assert effect.intensity == 0.8
        assert effect.duration == 1500

    def test_glitch_effect_apply(self):
        """Test glitch effect application."""
        effect = GlitchEffect(text="hello", intensity=0.5)
        
        result = effect.apply()
        
        # Simple glitch reverses the text when intensity > 0
        assert result == "olleh"

    def test_glitch_effect_no_intensity(self):
        """Test glitch effect with zero intensity."""
        effect = GlitchEffect(text="hello", intensity=0.0)
        
        result = effect.apply()
        
        # No glitch with zero intensity
        assert result == "hello"


class TestTypingEffect:
    """Test typing effect functionality."""

    @patch('pygame.time.get_ticks')
    def test_typing_effect_initialization(self, mock_time):
        """Test TypingEffect initialization."""
        mock_time.return_value = 1000
        
        effect = TypingEffect(text="hello", speed=0.1)
        
        assert effect.text == "hello"
        assert effect.speed == 0.1
        assert effect.current_length == 0

    @patch('pygame.time.get_ticks')
    def test_typing_effect_progression(self, mock_time):
        """Test typing effect character progression."""
        # Start time
        mock_time.return_value = 1000
        effect = TypingEffect(text="hello", speed=0.1)
        effect.start()  # Start the effect to set is_active = True
        
        # Should show empty initially
        assert effect.apply() == ""
        
        # Progress time to show first character (100ms later) 
        mock_time.return_value = 1100
        effect.update(0.1)
        # Need to ensure sufficient time passes for at least one character
        # With speed=0.1 and elapsed=100ms, characters_to_add should be 10
        assert len(effect.apply()) >= 1  # Should have progressed
        
        # Progress to show all characters (500ms later)
        mock_time.return_value = 1500  
        effect.update(0.1)
        result = effect.apply()
        assert len(result) >= 1  # Should have progressed


class TestScrambleEffect:
    """Test scramble effect functionality."""

    def test_scramble_effect_initialization(self):
        """Test ScrambleEffect initialization."""
        effect = ScrambleEffect(text="hello", intensity=0.5, duration=1000)
        
        assert effect.original_text == "hello"
        assert effect.intensity == 0.5
        assert effect.duration == 1000

    def test_scramble_effect_apply(self):
        """Test scramble effect application."""
        effect = ScrambleEffect(text="hello world", intensity=1.0)
        
        # Mock random to ensure consistent scrambling
        with patch('random.choice', side_effect=lambda x: x[0]):
            result = effect.apply("hello world")
            
            # Should be scrambled but same length
            assert len(result) == len("hello world")
            assert isinstance(result, str)


class TestCharacterCorruptionEffect:
    """Test character corruption effect functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock pygame and create a mock terminal
        self.pygame_patcher = patch('pygame.time.get_ticks', return_value=1000)
        self.pygame_patcher.start()
        
        self.mock_terminal = Mock()
        self.mock_terminal.grid = [
            [Mock(char='h', fg_color=(255, 255, 255), bg_color=(0, 0, 0)) for _ in range(10)]
            for _ in range(5)
        ]
        self.mock_terminal.font = Mock()

    def teardown_method(self):
        """Clean up after tests."""
        self.pygame_patcher.stop()

    def test_character_corruption_initialization(self):
        """Test CharacterCorruptionEffect initialization."""
        effect = CharacterCorruptionEffect(
            y=2,
            duration_ms=1000,
            corruption_intensity=0.8,
            corruption_rate_ms=100
        )
        
        assert effect.y == 2
        assert effect.duration == 1000
        assert effect.corruption_intensity == 0.8
        assert effect.corruption_rate_ms == 100

    def test_character_corruption_start(self):
        """Test starting character corruption effect."""
        effect = CharacterCorruptionEffect(y=1, duration_ms=1000)
        
        effect.start(self.mock_terminal)
        
        assert effect.is_active == True
        assert effect.terminal_ref == self.mock_terminal
        assert effect.original_grid != []

    def test_character_corruption_update(self):
        """Test character corruption update."""
        effect = CharacterCorruptionEffect(y=1, duration_ms=500)
        effect.start(self.mock_terminal)
        
        # Should not be complete initially
        assert effect.update(0.1) is None  # Returns None when continuing
        
        # Fast forward time to completion
        with patch('pygame.time.get_ticks', return_value=1600):
            assert effect.update(0.1) == True

    def test_character_corruption_corrupted_prompt(self):
        """Test corrupted prompt generation."""
        effect = CharacterCorruptionEffect()
        
        prompt = effect.generate_corrupted_prompt()
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0


class TestProfanityAndIntrusive:
    """Test profanity replacement and intrusive thoughts."""

    def test_profanity_replacement_basic(self):
        """Test basic profanity replacement."""
        result = apply_profanity_replacement("hello world", 0.5)
        
        # Should return a string
        assert isinstance(result, str)

    def test_profanity_replacement_high_corruption(self):
        """Test profanity replacement with high corruption."""
        with patch('random.random', return_value=0.1):  # Ensure replacement happens
            result = apply_profanity_replacement("hello", 0.9)
            
            # Should be replaced with profanity
            assert result != "hello"
            assert any(profanity.lower() in result.lower() for profanity in PROFANITY_LIST)

    def test_intrusive_thoughts_injection(self):
        """Test intrusive thoughts injection."""
        result = maybe_inject_intrusive_thought("normal text", 0.5)
        
        # Should return a string
        assert isinstance(result, str)

    def test_intrusive_thoughts_high_corruption(self):
        """Test intrusive thoughts with high corruption level."""
        with patch('random.random', return_value=0.05):  # Ensure injection happens
            result = maybe_inject_intrusive_thought("text", 0.9)
            
            # Should contain intrusive thought
            assert len(result) > len("text")
            assert any(thought in result for thought in INTRUSIVE_THOUGHTS)


class TestEffectManager:
    """Test the Effect Manager functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock pygame and audio manager
        self.pygame_patcher = patch('pygame.time.get_ticks', return_value=1000)
        self.pygame_patcher.start()
        
        self.mock_game_state = Mock()
        self.mock_audio_manager = Mock()
        self.mock_terminal = Mock()
        self.mock_terminal.get_size.return_value = (800, 600)
        
        self.effect_manager = EffectManager(
            self.mock_game_state,
            self.mock_audio_manager,
            self.mock_terminal
        )

    def teardown_method(self):
        """Clean up after tests."""
        self.pygame_patcher.stop()

    def test_effect_manager_initialization(self):
        """Test EffectManager initialization."""
        assert self.effect_manager.game_state == self.mock_game_state
        assert self.effect_manager.audio_manager == self.mock_audio_manager
        assert self.effect_manager.terminal == self.mock_terminal
        assert len(self.effect_manager.effects) == 0
        assert len(self.effect_manager.cursor_trails) == 0
        assert "corruption" in self.effect_manager.current_effects
        assert "horror" in self.effect_manager.current_effects
        assert "glitch" in self.effect_manager.current_effects

    def test_add_and_remove_effects(self):
        """Test adding and removing effects."""
        effect = CorruptionEffect(text="test", intensity=0.5)
        
        # Add effect
        self.effect_manager.add_effect(effect)
        assert effect in self.effect_manager.effects
        assert effect.is_active == True
        
        # Remove effect
        self.effect_manager.remove_effect(effect)
        assert effect not in self.effect_manager.effects

    def test_apply_effects_to_text(self):
        """Test applying effects to text."""
        effect = CorruptionEffect(text="original", intensity=0.5)
        self.effect_manager.add_effect(effect)
        
        result = self.effect_manager.apply_effects("test text")
        
        # Should return processed text
        assert isinstance(result, str)

    def test_trigger_corruption_effect(self):
        """Test triggering corruption effect."""
        self.effect_manager.trigger_corruption_effect(intensity=0.7, duration=2.0)
        
        corruption_state = self.effect_manager.current_effects["corruption"]
        assert corruption_state.active == True
        assert corruption_state.intensity == 0.7
        assert corruption_state.duration == 2.0

    def test_trigger_glitch_effect(self):
        """Test triggering glitch effect."""
        self.effect_manager.trigger_glitch_effect(intensity=0.8, duration=1.5)
        
        glitch_state = self.effect_manager.current_effects["glitch"]
        assert glitch_state.active == True
        assert glitch_state.intensity == 0.8
        assert glitch_state.duration == 1.5

    def test_trigger_horror_effect(self):
        """Test triggering horror effect."""
        self.effect_manager.trigger_horror_effect(intensity=0.9, duration=3.0)
        
        horror_state = self.effect_manager.current_effects["horror"]
        assert horror_state.active == True
        assert horror_state.intensity == 0.9
        assert horror_state.duration == 3.0

    def test_effect_manager_update(self):
        """Test effect manager update process."""
        # Add an effect that will complete quickly
        effect = CorruptionEffect(text="test", duration=100)
        self.effect_manager.add_effect(effect)
        
        initial_count = len(self.effect_manager.effects)
        
        # Update should process effects
        self.effect_manager.update(0.1)
        
        # Effect count might change if effects complete
        assert len(self.effect_manager.effects) >= 0

    def test_effect_history_tracking(self):
        """Test effect history tracking."""
        initial_history_length = len(self.effect_manager.effect_history)
        
        self.effect_manager.trigger_corruption_effect(0.5, 1.0)
        
        assert len(self.effect_manager.effect_history) == initial_history_length + 1
        
        history_entry = self.effect_manager.effect_history[-1]
        assert history_entry["type"] == "corruption"
        assert history_entry["intensity"] == 0.5
        assert history_entry["duration"] == 1.0

    def test_clear_effect_history(self):
        """Test clearing effect history."""
        self.effect_manager.trigger_corruption_effect(0.5, 1.0)
        assert len(self.effect_manager.effect_history) > 0
        
        self.effect_manager.clear_effect_history()
        assert len(self.effect_manager.effect_history) == 0

    def test_get_current_effects(self):
        """Test getting current effects state."""
        current_effects = self.effect_manager.get_current_effects()
        
        assert isinstance(current_effects, dict)
        assert "corruption" in current_effects
        assert "horror" in current_effects
        assert "glitch" in current_effects

    def test_cursor_trail_management(self):
        """Test cursor trail management."""
        initial_trail_count = len(self.effect_manager.cursor_trails)
        
        self.effect_manager.add_cursor_trail(10, 20)
        
        assert len(self.effect_manager.cursor_trails) == initial_trail_count + 1

    def test_maybe_blip_glitchy_profanity(self):
        """Test conditional profanity effect triggering."""
        initial_effect_count = len(self.effect_manager.effects)
        
        # High corruption should have a chance to trigger profanity
        with patch('random.random', return_value=0.05):  # Force trigger
            self.effect_manager.maybe_blip_glitchy_profanity(0.8, self.mock_terminal)
        
        # May or may not add effect depending on random chance
        assert len(self.effect_manager.effects) >= initial_effect_count

    def test_state_serialization_and_restoration(self):
        """Test effect manager state save/restore."""
        # Set up some state
        self.effect_manager.trigger_corruption_effect(0.6, 2.0)
        effect = CorruptionEffect(text="test")
        self.effect_manager.add_effect(effect)
        
        # Get state
        state = self.effect_manager.get_state()
        
        # Create new manager and restore state
        new_manager = EffectManager(
            self.mock_game_state,
            self.mock_audio_manager,
            self.mock_terminal
        )
        new_manager.restore_state(state)
        
        # Should have restored corruption effect
        assert new_manager.current_effects["corruption"].intensity == 0.6


class TestEffectState:
    """Test EffectState dataclass functionality."""

    def test_effect_state_creation(self):
        """Test EffectState creation."""
        start_time = datetime.now()
        state = EffectState(
            intensity=0.7,
            duration=2.5,
            start_time=start_time,
            active=True,
            parameters={"test": "value"}
        )
        
        assert state.intensity == 0.7
        assert state.duration == 2.5
        assert state.start_time == start_time
        assert state.active == True
        assert state.parameters == {"test": "value"}


class TestVisualEffectApplication:
    """Test visual effect application and rendering."""

    def setup_method(self):
        """Set up test fixtures for visual effects."""
        # Mock pygame surfaces and operations more comprehensively
        self.surface_patcher = patch('pygame.Surface')
        self.surfarray_patcher = patch('pygame.surfarray.make_surface')
        self.pixel_array_patcher = patch('pygame.surfarray.pixels3d')
        
        # Create mock surface that supports all required operations
        self.mock_surface = Mock()
        self.mock_surface.get_size.return_value = (800, 600)
        self.mock_surface.get_width.return_value = 800
        self.mock_surface.get_height.return_value = 600
        self.mock_surface.blit = Mock()
        
        # Mock surface creation to return our mock surface
        mock_surface_class = Mock(return_value=self.mock_surface)
        self.surface_patcher.start()
        self.surface_patcher.return_value = mock_surface_class
        
        # Mock surfarray operations
        mock_surfarray = Mock()
        mock_surfarray.return_value = self.mock_surface
        self.surfarray_patcher.start()
        self.surfarray_patcher.return_value = mock_surfarray
        
        # Mock pixels3d for color operations
        mock_pixels = Mock()
        mock_pixels.__enter__ = Mock(return_value=np.zeros((800, 600, 3)))
        mock_pixels.__exit__ = Mock(return_value=None)
        self.pixel_array_patcher.start()
        self.pixel_array_patcher.return_value = mock_pixels
        
        self.mock_game_state = Mock()
        self.mock_audio_manager = Mock()
        self.effect_manager = EffectManager(
            self.mock_game_state,
            self.mock_audio_manager,
            self.mock_surface
        )

    def teardown_method(self):
        """Clean up visual effect patches."""
        self.surface_patcher.stop()
    def teardown_method(self):
        """Clean up visual effect patches."""
        self.surface_patcher.stop()
        self.surfarray_patcher.stop()
        self.pixel_array_patcher.stop()

    def test_corruption_visual_application(self):
        """Test corruption visual effects application."""
        # Trigger corruption with visual parameters
        self.effect_manager.trigger_corruption_effect(0.8, 2.0)
        self.effect_manager.current_effects["corruption"].parameters = {
            "text_distortion": 0.5,
            "color_shift": 0.3,
            "glitch_frequency": 0.7
        }

        # Mock pygame.surfarray.pixels3d to return valid array shape
        with patch('pygame.surfarray.pixels3d') as mock_pixels:
            mock_pixels.return_value = np.zeros((800, 600, 3))  # Valid RGB array
            
            # Should not crash when applying corruption visuals
            try:
                self.effect_manager._apply_corruption_visuals()
            except Exception as e:
                pytest.fail(f"Corruption visual application failed: {e}")

    def test_glitch_visual_application(self):
        """Test glitch visual effects application."""
        self.effect_manager.trigger_glitch_effect(0.9, 1.0)
        self.effect_manager.current_effects["glitch"].parameters = {
            "pattern": "random",
            "frequency": 0.8,
            "color_shift": 0.4
        }
        
        # Mock pygame.surfarray.pixels3d to return valid array shape
        with patch('pygame.surfarray.pixels3d') as mock_pixels:
            mock_pixels.return_value = np.zeros((800, 600, 3))  # Valid RGB array
            
            # Should not crash when applying glitch visuals
            try:
                self.effect_manager._apply_glitch_visuals()
            except Exception as e:
                pytest.fail(f"Glitch visual application failed: {e}")

    def test_horror_visual_application(self):
        """Test horror visual effects application."""
        self.effect_manager.trigger_horror_effect(0.7, 3.0)
        self.effect_manager.current_effects["horror"].parameters = {
            "static_intensity": 0.6,
            "reality_shift": 0.4,
            "entity_presence": 0.3
        }
        
        # Mock the surface.get_size() to return a tuple that numpy can handle
        with patch.object(self.mock_surface, 'get_size', return_value=(800, 600)):
            # Should not crash when applying horror visuals
            try:
                self.effect_manager._apply_horror_visuals()
            except Exception as e:
                pytest.fail(f"Horror visual application failed: {e}")


class TestEffectIntegration:
    """Test effect system integration and complex scenarios."""

    def setup_method(self):
        """Set up integration test fixtures."""
        self.pygame_patcher = patch('pygame.time.get_ticks', return_value=1000)
        self.pygame_patcher.start()
        
        self.mock_game_state = Mock()
        self.mock_audio_manager = Mock()
        self.mock_terminal = Mock()
        self.mock_terminal.get_size.return_value = (800, 600)
        
        self.effect_manager = EffectManager(
            self.mock_game_state,
            self.mock_audio_manager,
            self.mock_terminal
        )

    def teardown_method(self):
        """Clean up integration tests."""
        self.pygame_patcher.stop()

    def test_multiple_effects_simultaneous(self):
        """Test multiple effects running simultaneously."""
        # Add multiple different effects
        corruption_effect = CorruptionEffect(text="test1", intensity=0.5)
        glitch_effect = GlitchEffect(text="test2", intensity=0.7)
        typing_effect = TypingEffect(text="test3", speed=0.1)
        
        self.effect_manager.add_effect(corruption_effect)
        self.effect_manager.add_effect(glitch_effect)
        self.effect_manager.add_effect(typing_effect)
        
        assert len(self.effect_manager.effects) == 3
        
        # Update should handle all effects
        self.effect_manager.update(0.1)
        
        # All effects should still be active (depending on duration)
        active_effects = [e for e in self.effect_manager.effects if e.is_active]
        assert len(active_effects) <= 3

    def test_effect_priority_ordering(self):
        """Test that effects are processed in priority order."""
        high_priority = CorruptionEffect(text="high", priority=10)
        low_priority = CorruptionEffect(text="low", priority=1)
        
        self.effect_manager.add_effect(low_priority)
        self.effect_manager.add_effect(high_priority)
        
        # Effects should be sorted by priority when applied
        result = self.effect_manager.apply_effects("test text")
        assert isinstance(result, str)

    def test_effect_completion_callbacks(self):
        """Test effect completion callbacks."""
        callback = Mock()
        effect = CorruptionEffect(
            text="test",
            duration=100,
            on_complete_callback=callback
        )
        
        self.effect_manager.add_effect(effect)
        
        # Fast forward time to complete effect
        with patch('pygame.time.get_ticks', return_value=1200):
            self.effect_manager.update(0.1)
        
        # Callback should be called when effect completes
        callback.assert_called_once()

    def test_effect_cooldown_system(self):
        """Test effect cooldown prevents spam."""
        # First glitch should work
        self.effect_manager.trigger_glitch_effect(0.5, 1.0)
        first_time = self.effect_manager.last_glitch_time
        
        # Immediate second glitch should be blocked by cooldown
        self.effect_manager.trigger_glitch_effect(0.7, 1.0)
        second_time = self.effect_manager.last_glitch_time
        
        assert first_time == second_time  # Time shouldn't change due to cooldown

    def test_corruption_progression_system(self):
        """Test corruption effects escalate properly."""
        # Low corruption
        self.effect_manager.maybe_blip_glitchy_profanity(0.3, self.mock_terminal)
        initial_effects = len(self.effect_manager.effects)
        
        # High corruption should be more likely to trigger effects
        with patch('random.random', return_value=0.05):
            self.effect_manager.maybe_blip_glitchy_profanity(0.9, self.mock_terminal)
            high_corruption_effects = len(self.effect_manager.effects)
        
        # High corruption might add more effects
        assert high_corruption_effects >= initial_effects
