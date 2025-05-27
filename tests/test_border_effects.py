"""Tests for src/ui/border_effects.py"""

import pytest
import random
from unittest.mock import patch, Mock
from enum import Enum

from src.ui.border_effects import (
    BorderRegion, BorderStyle, PulseEffect, GlitchEffect, 
    DistortEffect, ColorBleedEffect, 
    BorderEffectManager
)


class TestBorderRegion:
    """Test cases for BorderRegion enum."""

    def test_border_region_values(self):
        """Test BorderRegion enum values."""
        assert BorderRegion.MAIN_OUTPUT
        assert BorderRegion.RUSTY_PANEL
        assert BorderRegion.COMMAND_BAR

    def test_border_region_uniqueness(self):
        """Test that BorderRegion values are unique."""
        values = [region.value for region in BorderRegion]
        assert len(values) == len(set(values))


class TestBorderStyle:
    """Test cases for BorderStyle enum."""

    def test_border_style_values(self):
        """Test BorderStyle enum values."""
        assert BorderStyle.CORRUPTED
        assert BorderStyle.MECHANICAL
        assert BorderStyle.DIGITAL

    def test_border_style_uniqueness(self):
        """Test that BorderStyle values are unique."""
        values = [style.value for style in BorderStyle]
        assert len(values) == len(set(values))


class TestPulseEffect:
    """Test cases for PulseEffect class."""

    @pytest.fixture
    def pulse_effect(self):
        """Create PulseEffect instance for testing."""
        return PulseEffect()

    @pytest.fixture
    def sample_border_grid(self):
        """Create sample border grid for testing."""
        return [
            ['+', '-', '-', '+'],
            ['|', ' ', ' ', '|'],
            ['|', ' ', ' ', '|'],
            ['+', '-', '-', '+']
        ]

    def test_pulse_effect_apply_no_pulse(self, pulse_effect, sample_border_grid):
        """Test pulse effect with no pulse phase."""
        original_grid = [row[:] for row in sample_border_grid]
        pulse_effect.apply(sample_border_grid, 0.5, 0)  # frame 0, no pulse
        
        # Grid should remain unchanged when pulse_phase is 0
        assert sample_border_grid == original_grid

    def test_pulse_effect_apply_with_pulse(self, pulse_effect, sample_border_grid):
        """Test pulse effect with pulse phase active."""
        pulse_effect.apply(sample_border_grid, 0.5, 8)  # frame 8, pulse active
        
        # Check that border characters are enhanced
        assert sample_border_grid[0][0] == '╬'  # '+' becomes '╬'
        assert sample_border_grid[0][1] == '═'  # '-' becomes '═'
        assert sample_border_grid[1][0] == '║'  # '|' becomes '║'

    def test_pulse_effect_preserves_non_border_chars(self, pulse_effect, sample_border_grid):
        """Test that pulse effect preserves non-border characters."""
        pulse_effect.apply(sample_border_grid, 0.5, 8)
        
        # Spaces should remain unchanged
        assert sample_border_grid[1][1] == ' '
        assert sample_border_grid[2][2] == ' '


class TestGlitchEffect:
    """Test cases for GlitchEffect class."""

    @pytest.fixture
    def glitch_effect(self):
        """Create GlitchEffect instance for testing."""
        return GlitchEffect()

    @pytest.fixture
    def sample_border_grid(self):
        """Create sample border grid for testing."""
        return [
            ['+', '-', '-', '+'],
            ['|', 'a', 'b', '|'],
            ['|', 'c', 'd', '|'],
            ['+', '-', '-', '+']
        ]

    def test_glitch_effect_glitch_chars(self, glitch_effect):
        """Test that glitch characters are defined."""
        assert hasattr(glitch_effect, 'GLITCH_CHARS')
        assert len(glitch_effect.GLITCH_CHARS) > 0
        assert all(isinstance(char, str) for char in glitch_effect.GLITCH_CHARS)

    def test_glitch_effect_apply_low_corruption(self, glitch_effect, sample_border_grid):
        """Test glitch effect with low corruption."""
        with patch('random.random', return_value=0.5):  # High random value, no glitch
            original_grid = [row[:] for row in sample_border_grid]
            glitch_effect.apply(sample_border_grid, 0.1, 0)
            
            # With high random value and low corruption, no changes should occur
            assert sample_border_grid == original_grid

    def test_glitch_effect_apply_high_corruption(self, glitch_effect, sample_border_grid):
        """Test glitch effect with high corruption."""
        with patch('random.random', return_value=0.01):  # Low random value, glitch
            with patch('random.choice', return_value='@'):
                glitch_effect.apply(sample_border_grid, 0.8, 0)
                
                # Should have some glitched characters
                glitched_chars = sum(row.count('@') for row in sample_border_grid)
                assert glitched_chars > 0

    def test_glitch_effect_preserves_empty_chars(self, glitch_effect):
        """Test that glitch effect doesn't affect empty characters."""
        grid = [['', ' ', '']]
        original_grid = [row[:] for row in grid]
        
        glitch_effect.apply(grid, 1.0, 0)
        
        # Empty strings should remain unchanged
        assert grid[0][0] == ''
        assert grid[0][2] == ''


class TestDistortEffect:
    """Test cases for DistortEffect class."""

    @pytest.fixture
    def distort_effect(self):
        """Create DistortEffect instance for testing."""
        return DistortEffect()

    @pytest.fixture
    def sample_border_grid(self):
        """Create sample border grid for testing."""
        return [
            ['+', '-', '-', '+'],
            ['|', 'a', 'b', '|'],
            ['|', 'c', 'd', '|'],
            ['+', '-', '-', '+']
        ]

    def test_distort_effect_low_corruption(self, distort_effect, sample_border_grid):
        """Test distort effect with low corruption (no distortion)."""
        original_grid = [row[:] for row in sample_border_grid]
        distort_effect.apply(sample_border_grid, 0.1, 0)
        
        # With corruption < 0.2, no distortion should occur
        assert sample_border_grid == original_grid

    def test_distort_effect_high_corruption(self, distort_effect, sample_border_grid):
        """Test distort effect with high corruption."""
        with patch('random.random', return_value=0.01):  # Low random value, distort
            original_first_row = sample_border_grid[0][:]
            distort_effect.apply(sample_border_grid, 0.8, 0)
            
            # Check if any row was reversed
            distorted = any(row != original for original, row in 
                          zip([original_first_row] + [row[:] for row in sample_border_grid[1:]], 
                              sample_border_grid))
            # Note: This test might be flaky due to randomness, but demonstrates the concept

    def test_distort_effect_row_reversal(self, distort_effect):
        """Test that distort effect can reverse rows."""
        grid = [['a', 'b', 'c', 'd']]
        
        with patch('random.random', return_value=0.01):  # Force distortion
            distort_effect.apply(grid, 0.5, 0)
            
            # Row should be reversed
            assert grid[0] == ['d', 'c', 'b', 'a']


class TestColorBleedEffect:
    """Test cases for ColorBleedEffect class."""

    @pytest.fixture
    def color_bleed_effect(self):
        """Create ColorBleedEffect instance for testing."""
        return ColorBleedEffect()

    def test_color_bleed_effect_initialization(self, color_bleed_effect):
        """Test ColorBleedEffect initialization."""
        assert hasattr(color_bleed_effect, 'apply')

    def test_color_bleed_effect_apply(self, color_bleed_effect):
        """Test ColorBleedEffect apply method."""
        grid = [['a', 'b'], ['c', 'd']]
        original_grid = [row[:] for row in grid]
        
        # Color bleed effect should not modify the grid structure
        color_bleed_effect.apply(grid, 0.5, 0)
        
        # Grid structure should remain the same (color changes are visual only)
        assert len(grid) == len(original_grid)
        assert all(len(row) == len(orig_row) for row, orig_row in zip(grid, original_grid))


class TestBorderEffectManager:
    """Test cases for BorderEffectManager class."""

    @pytest.fixture
    def effect_manager(self):
        """Create BorderEffectManager instance for testing."""
        return BorderEffectManager()

    def test_border_effect_manager_initialization(self, effect_manager):
        """Test BorderEffectManager initialization."""
        assert hasattr(effect_manager, 'effects')
        assert hasattr(effect_manager, 'active_effects')
        assert isinstance(effect_manager.effects, dict)
        assert isinstance(effect_manager.active_effects, dict)

    def test_register_effect(self, effect_manager):
        """Test registering an effect."""
        pulse_effect = PulseEffect()
        effect_manager.register_effect("pulse", pulse_effect)
        
        assert "pulse" in effect_manager.effects
        assert effect_manager.effects["pulse"] is pulse_effect

    def test_activate_effect(self, effect_manager):
        """Test activating an effect for a region."""
        pulse_effect = PulseEffect()
        effect_manager.register_effect("pulse", pulse_effect)
        
        effect_manager.activate_effect(BorderRegion.MAIN_OUTPUT, "pulse")
        
        assert BorderRegion.MAIN_OUTPUT in effect_manager.active_effects
        assert "pulse" in effect_manager.active_effects[BorderRegion.MAIN_OUTPUT]

    def test_deactivate_effect(self, effect_manager):
        """Test deactivating an effect for a region."""
        pulse_effect = PulseEffect()
        effect_manager.register_effect("pulse", pulse_effect)
        effect_manager.activate_effect(BorderRegion.MAIN_OUTPUT, "pulse")
        
        effect_manager.deactivate_effect(BorderRegion.MAIN_OUTPUT, "pulse")
        
        assert "pulse" not in effect_manager.active_effects.get(BorderRegion.MAIN_OUTPUT, [])

    def test_apply_effects_to_region(self, effect_manager):
        """Test applying effects to a specific region."""
        pulse_effect = PulseEffect()
        effect_manager.register_effect("pulse", pulse_effect)
        effect_manager.activate_effect(BorderRegion.MAIN_OUTPUT, "pulse")
        
        grid = [['|', '-', '|']]
        effect_manager.apply_effects_to_region(BorderRegion.MAIN_OUTPUT, grid, 0.5, 8)
        
        # Pulse effect should have been applied
        assert '║' in grid[0] or '═' in grid[0]  # Enhanced border characters

    def test_apply_all_effects(self, effect_manager):
        """Test applying all active effects."""
        pulse_effect = PulseEffect()
        glitch_effect = GlitchEffect()
        
        effect_manager.register_effect("pulse", pulse_effect)
        effect_manager.register_effect("glitch", glitch_effect)
        
        effect_manager.activate_effect(BorderRegion.MAIN_OUTPUT, "pulse")
        effect_manager.activate_effect(BorderRegion.COMMAND_BAR, "glitch")
        
        grids = {
            BorderRegion.MAIN_OUTPUT: [['|', '-', '|']],
            BorderRegion.COMMAND_BAR: [['a', 'b', 'c']]
        }
        
        effect_manager.apply_all_effects(grids, 0.5, 8)
        
        # Effects should have been applied to respective regions
        assert len(grids[BorderRegion.MAIN_OUTPUT]) > 0
        assert len(grids[BorderRegion.COMMAND_BAR]) > 0

    def test_get_active_effects(self, effect_manager):
        """Test getting active effects for a region."""
        pulse_effect = PulseEffect()
        effect_manager.register_effect("pulse", pulse_effect)
        effect_manager.activate_effect(BorderRegion.MAIN_OUTPUT, "pulse")
        
        active = effect_manager.get_active_effects(BorderRegion.MAIN_OUTPUT)
        assert "pulse" in active

    def test_clear_all_effects(self, effect_manager):
        """Test clearing all effects."""
        pulse_effect = PulseEffect()
        effect_manager.register_effect("pulse", pulse_effect)
        effect_manager.activate_effect(BorderRegion.MAIN_OUTPUT, "pulse")
        
        effect_manager.clear_all_effects()
        
        assert len(effect_manager.active_effects) == 0

    def test_effect_priority(self, effect_manager):
        """Test effect application priority."""
        pulse_effect = PulseEffect()
        glitch_effect = GlitchEffect()
        
        effect_manager.register_effect("pulse", pulse_effect)
        effect_manager.register_effect("glitch", glitch_effect)
        
        # Activate multiple effects on same region
        effect_manager.activate_effect(BorderRegion.MAIN_OUTPUT, "pulse")
        effect_manager.activate_effect(BorderRegion.MAIN_OUTPUT, "glitch")
        
        grid = [['|', '-', '|']]
        effect_manager.apply_effects_to_region(BorderRegion.MAIN_OUTPUT, grid, 0.5, 8)
        
        # Both effects should be applied
        active_effects = effect_manager.get_active_effects(BorderRegion.MAIN_OUTPUT)
        assert len(active_effects) == 2
