#!/usr/bin/env python3
"""Enhanced Terminal Integration Example.

This script demonstrates how to integrate the enhanced terminal renderer
into the main game. Can be imported and used to replace the standard
terminal renderer.
"""

import logging
from src.ui.terminal_integration import create_terminal_renderer, upgrade_terminal_renderer

logger = logging.getLogger(__name__)


def integrate_enhanced_terminal(game_state_manager=None, effect_manager=None):
    """Create an enhanced terminal renderer for the game.
    
    Args:
        game_state_manager: Game state manager instance
        effect_manager: Effect manager instance
        
    Returns:
        EnhancedTerminalRenderer: Configured enhanced terminal renderer
    """
    logger.info("Integrating enhanced terminal renderer into game")
    
    # Create enhanced terminal renderer
    enhanced_terminal = create_terminal_renderer(
        enhanced=True,
        effect_manager=effect_manager,
        game_state_manager=game_state_manager
    )
    
    # Configure default effect settings
    if hasattr(enhanced_terminal, '_effect_config'):
        from src.ui.terminal_integration import configure_enhanced_effects
        configure_enhanced_effects(
            enhanced_terminal,
            corruption_sensitivity=1.2,  # Slightly more sensitive to corruption
            effect_intensity=1.0,        # Standard intensity
            subliminal_frequency=0.8     # Slightly less frequent subliminal effects
        )
    
    logger.info("Enhanced terminal renderer integration complete")
    return enhanced_terminal


def patch_main_game():
    """Demonstration of how to patch the main game to use enhanced terminal renderer.
    
    This function shows the pattern for replacing the standard terminal renderer
    in main.py with the enhanced version.
    """
    logger.info("Patching main game to use enhanced terminal renderer")
    
    # Example integration code (not executed, just for reference)
    integration_code = '''
    # In main.py, replace this line:
    # terminal_renderer = TerminalRenderer()
    
    # With this:
    from src.ui.terminal_integration import create_terminal_renderer
    
    terminal_renderer = create_terminal_renderer(
        enhanced=True,
        effect_manager=None,  # Will be set later
        game_state_manager=game_state  # Pass game state manager
    )
    '''
    
    print("Integration pattern:")
    print(integration_code)
    
    # Another option is to upgrade existing renderer after creation
    upgrade_code = '''
    # Alternative approach - upgrade existing renderer:
    from src.ui.terminal_integration import upgrade_terminal_renderer
    
    # After creating standard renderer and effect manager:
    terminal_renderer = TerminalRenderer()
    effect_manager = EffectManager(game_state, audio_manager, terminal_renderer)
    
    # Upgrade to enhanced version:
    terminal_renderer = upgrade_terminal_renderer(
        terminal_renderer, 
        game_state_manager=game_state
    )
    terminal_renderer.effect_manager = effect_manager
    '''
    
    print("\nUpgrade pattern:")
    print(upgrade_code)


def test_enhanced_integration():
    """Test the enhanced terminal integration.
    
    This function demonstrates the enhanced terminal renderer capabilities
    and can be used for testing the integration.
    """
    logger.info("Testing enhanced terminal integration")
    
    try:
        # Create a mock game state manager for testing
        class MockGameStateManager:
            def __init__(self):
                self.role = "purifier"
                self.corruption_level = 0.3
                self.state = "normal"
            
            def get_role(self):
                return self.role
            
            def get_corruption_level(self):
                return self.corruption_level
            
            def get_state(self):
                return self.state
        
        # Create enhanced terminal
        mock_game_state = MockGameStateManager()
        enhanced_terminal = integrate_enhanced_terminal(
            game_state_manager=mock_game_state
        )
        
        # Test capabilities
        from src.ui.terminal_integration import get_renderer_capabilities
        capabilities = get_renderer_capabilities(enhanced_terminal)
        
        logger.info("Enhanced terminal capabilities:")
        for capability, available in capabilities.items():
            logger.info(f"  {capability}: {'✓' if available else '✗'}")
        
        # Test effect scheduling
        if hasattr(enhanced_terminal, 'schedule_effect'):
            from src.core.effects import CharacterDecayEffect
            from src.ui.enhanced_terminal_renderer import EffectPriority
            
            decay_effect = CharacterDecayEffect(
                text="Test corruption",
                intensity=0.5,
                duration=1000
            )
            enhanced_terminal.schedule_effect(
                decay_effect, 
                delay=0.5, 
                priority=EffectPriority.HIGH
            )
            logger.info("Effect scheduling test successful")
        
        # Test performance tracking
        if hasattr(enhanced_terminal, 'get_performance_stats'):
            stats = enhanced_terminal.get_performance_stats()
            logger.info(f"Performance stats: {stats}")
        
        logger.info("Enhanced terminal integration test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Enhanced terminal integration test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    # Set up logging for standalone testing
    logging.basicConfig(level=logging.INFO)
    
    # Run integration tests
    print("Enhanced Terminal Integration Example")
    print("=" * 40)
    
    # Show integration patterns
    patch_main_game()
    
    print("\n" + "=" * 40)
    
    # Test integration
    success = test_enhanced_integration()
    if success:
        print("✓ Enhanced terminal integration working correctly")
    else:
        print("✗ Enhanced terminal integration test failed")
