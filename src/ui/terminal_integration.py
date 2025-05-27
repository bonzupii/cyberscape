#!/usr/bin/env python3
"""Terminal Renderer Integration Module.

This module provides a factory function to create the appropriate terminal renderer
based on configuration or user preference. Allows switching between standard and
enhanced terminal renderers.
"""

import logging
from typing import Optional

from .terminal import TerminalRenderer
from .enhanced_terminal_renderer import EnhancedTerminalRenderer

logger = logging.getLogger(__name__)


def create_terminal_renderer(
    enhanced: bool = True,
    effect_manager=None,
    game_state_manager=None
) -> TerminalRenderer:
    """Create and return an appropriate terminal renderer.
    
    Args:
        enhanced: If True, create enhanced terminal renderer with effects
        effect_manager: Effect manager instance for terminal integration
        game_state_manager: Game state manager for context-aware rendering
        
    Returns:
        TerminalRenderer: Either standard or enhanced terminal renderer
    """
    if enhanced:
        logger.info("Creating Enhanced Terminal Renderer with comprehensive effects")
        return EnhancedTerminalRenderer(
            effect_manager=effect_manager,
            game_state_manager=game_state_manager
        )
    else:
        logger.info("Creating Standard Terminal Renderer")
        return TerminalRenderer(effect_manager=effect_manager)


def upgrade_terminal_renderer(
    current_renderer: TerminalRenderer,
    game_state_manager=None
) -> EnhancedTerminalRenderer:
    """Upgrade an existing terminal renderer to enhanced version.
    
    Args:
        current_renderer: Existing terminal renderer to upgrade
        game_state_manager: Game state manager for context-aware rendering
        
    Returns:
        EnhancedTerminalRenderer: Upgraded terminal renderer with effects
    """
    logger.info("Upgrading terminal renderer to enhanced version")
    
    # Create enhanced renderer
    enhanced = EnhancedTerminalRenderer(
        effect_manager=current_renderer.effect_manager,
        game_state_manager=game_state_manager
    )
    
    # Transfer state from current renderer
    enhanced.width = current_renderer.width
    enhanced.height = current_renderer.height
    enhanced.cursor_x = current_renderer.cursor_x
    enhanced.cursor_y = current_renderer.cursor_y
    enhanced.scroll_offset = current_renderer.scroll_offset
    enhanced.buffer = current_renderer.buffer.copy()
    enhanced.history = current_renderer.history.copy()
    enhanced.history_index = current_renderer.history_index
    enhanced.max_history = current_renderer.max_history
    enhanced.corruption_level = current_renderer.corruption_level
    enhanced._is_corrupted = current_renderer._is_corrupted
    enhanced.prompt_override = current_renderer.prompt_override
    enhanced.completion_handler = current_renderer.completion_handler
    enhanced.current_input = current_renderer.current_input
    enhanced.cursor_visible = current_renderer.cursor_visible
    enhanced.cursor_blink_time = current_renderer.cursor_blink_time
    enhanced.last_cursor_toggle = current_renderer.last_cursor_toggle
    enhanced.completion_suggestions = current_renderer.completion_suggestions.copy()
    enhanced.completion_index = current_renderer.completion_index
    
    # Transfer pygame objects if initialized
    if hasattr(current_renderer, 'screen'):
        enhanced.screen = current_renderer.screen
    if hasattr(current_renderer, 'font'):
        enhanced.font = current_renderer.font
    if hasattr(current_renderer, 'bold_font'):
        enhanced.bold_font = current_renderer.bold_font
    if hasattr(current_renderer, 'char_width'):
        enhanced.char_width = current_renderer.char_width
    if hasattr(current_renderer, 'char_height'):
        enhanced.char_height = current_renderer.char_height
    if hasattr(current_renderer, 'border_manager'):
        enhanced.border_manager = current_renderer.border_manager
    if hasattr(current_renderer, 'theme_manager'):
        enhanced.theme_manager = current_renderer.theme_manager
    
    logger.info("Terminal renderer upgrade complete")
    return enhanced


def configure_enhanced_effects(
    renderer: EnhancedTerminalRenderer,
    corruption_sensitivity: float = 1.0,
    effect_intensity: float = 1.0,
    subliminal_frequency: float = 1.0
) -> None:
    """Configure enhanced effects settings for the terminal renderer.
    
    Args:
        renderer: Enhanced terminal renderer to configure
        corruption_sensitivity: Multiplier for corruption effect triggers (0.5-2.0)
        effect_intensity: Overall effect intensity multiplier (0.5-2.0)
        subliminal_frequency: Subliminal effect frequency multiplier (0.5-2.0)
    """
    if not isinstance(renderer, EnhancedTerminalRenderer):
        logger.warning("Cannot configure enhanced effects on standard terminal renderer")
        return
    
    logger.info(f"Configuring enhanced effects: sensitivity={corruption_sensitivity}, "
                f"intensity={effect_intensity}, subliminal={subliminal_frequency}")
    
    # Configure subliminal effects
    if hasattr(renderer.subliminal_effect, 'pattern_frequency'):
        renderer.subliminal_effect.pattern_frequency = subliminal_frequency
    
    # Configure effect priorities and intensities
    # These would be implementation-specific based on the actual effect system
    # For now, we'll store them as attributes for future use
    renderer._effect_config = {
        'corruption_sensitivity': corruption_sensitivity,
        'effect_intensity': effect_intensity,
        'subliminal_frequency': subliminal_frequency
    }
    
    logger.info("Enhanced effects configuration complete")


def is_enhanced_renderer(renderer: TerminalRenderer) -> bool:
    """Check if a terminal renderer is the enhanced version.
    
    Args:
        renderer: Terminal renderer to check
        
    Returns:
        bool: True if renderer is enhanced version
    """
    return isinstance(renderer, EnhancedTerminalRenderer)


def get_renderer_capabilities(renderer: TerminalRenderer) -> dict:
    """Get the capabilities of a terminal renderer.
    
    Args:
        renderer: Terminal renderer to analyze
        
    Returns:
        dict: Dictionary of renderer capabilities
    """
    capabilities = {
        'basic_rendering': True,
        'corruption_effects': hasattr(renderer, 'corruption_level'),
        'border_effects': hasattr(renderer, 'border_manager'),
        'enhanced_effects': isinstance(renderer, EnhancedTerminalRenderer),
        'subliminal_effects': False,
        'contextual_effects': False,
        'color_noise_effects': False,
        'effect_scheduling': False,
        'performance_tracking': False
    }
    
    if isinstance(renderer, EnhancedTerminalRenderer):
        capabilities.update({
            'subliminal_effects': hasattr(renderer, 'subliminal_effect'),
            'contextual_effects': hasattr(renderer, 'contextual_renderer'),
            'color_noise_effects': hasattr(renderer, 'color_noise_renderer'),
            'effect_scheduling': hasattr(renderer, 'effect_scheduler'),
            'performance_tracking': hasattr(renderer, 'get_performance_stats')
        })
    
    return capabilities
