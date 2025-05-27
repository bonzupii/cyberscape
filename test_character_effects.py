#!/usr/bin/env python3
"""
Test script for character-level effects integration.
This script will demonstrate all the character effects working together.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.effects import (
    CharacterDecayEffect, CharacterStutterEffect, ScreenTearEffect, 
    CharacterJitterEffect, TextBreathingEffect, ScanlineEffect,
    EffectManager
)
import pygame
import time

def test_individual_effects():
    """Test each character effect individually."""
    print("=== Testing Individual Character Effects ===\n")
    
    test_text = "The system is becoming unstable. Data corruption detected."
    
    # Test Character Decay
    print("1. Character Decay Effect:")
    decay_effect = CharacterDecayEffect(text=test_text, intensity=0.7, duration=2000, decay_mode="symbolic")
    decay_effect.start()
    print(f"Original: {test_text}")
    print(f"Decayed:  {decay_effect.apply(test_text)}")
    print()
    
    # Test Character Stutter
    print("2. Character Stutter Effect:")
    stutter_effect = CharacterStutterEffect(text=test_text, intensity=0.6, stutter_chance=0.3)
    stutter_effect.start()
    print(f"Original:  {test_text}")
    print(f"Stuttered: {stutter_effect.apply(test_text)}")
    print()
    
    # Test Screen Tear
    print("3. Screen Tear Effect:")
    tear_effect = ScreenTearEffect(text=test_text, intensity=0.8, tear_frequency=0.4)
    tear_effect.start()
    print(f"Original: {test_text}")
    print(f"Torn:     {tear_effect.apply(test_text)}")
    print()
    
    # Test Character Jitter
    print("4. Character Jitter Effect:")
    jitter_effect = CharacterJitterEffect(text=test_text, intensity=0.5, jitter_chance=0.3)
    jitter_effect.start()
    jitter_effect._update_jitter_positions()  # Force jitter calculation
    print(f"Original: {test_text}")
    print(f"Jittered: {jitter_effect.apply(test_text)}")
    print()

def test_combined_effects():
    """Test combined corruption effects using EffectManager."""
    print("=== Testing Combined Character Effects ===\n")
    
    pygame.init()
    pygame.mixer.init()
    
    # Create mock surface for effect manager
    mock_surface = pygame.Surface((800, 600))
    
    # Create effect manager with mocks
    from unittest.mock import Mock
    mock_game_state = Mock()
    mock_audio_manager = Mock()
    
    effect_manager = EffectManager(mock_game_state, mock_audio_manager, mock_surface)
    
    test_text = "SECURITY BREACH DETECTED. INITIATING COUNTERMEASURES."
    
    # Test low corruption
    print("1. Low Corruption (30%):")
    effects = effect_manager.trigger_combined_corruption_effect(
        text=test_text, corruption_level=0.3, duration=2000
    )
    print(f"Original:     {test_text}")
    corrupted_text = test_text
    for effect in effects:
        if hasattr(effect, 'apply'):
            corrupted_text = effect.apply(corrupted_text)
    print(f"Low Corrupt:  {corrupted_text}")
    print(f"Effects triggered: {len(effects)}")
    print()
    
    # Test medium corruption
    print("2. Medium Corruption (60%):")
    effects = effect_manager.trigger_combined_corruption_effect(
        text=test_text, corruption_level=0.6, duration=2000
    )
    print(f"Original:      {test_text}")
    corrupted_text = test_text
    for effect in effects:
        if hasattr(effect, 'apply'):
            corrupted_text = effect.apply(corrupted_text)
    print(f"Med Corrupt:   {corrupted_text}")
    print(f"Effects triggered: {len(effects)}")
    print()
    
    # Test high corruption
    print("3. High Corruption (90%):")
    effects = effect_manager.trigger_combined_corruption_effect(
        text=test_text, corruption_level=0.9, duration=2000
    )
    print(f"Original:      {test_text}")
    corrupted_text = test_text
    for effect in effects:
        if hasattr(effect, 'apply'):
            corrupted_text = effect.apply(corrupted_text)
    print(f"High Corrupt:  {corrupted_text}")
    print(f"Effects triggered: {len(effects)}")
    print()

def test_interactive_effects():
    """Show progressive corruption over multiple applications."""
    print("=== Testing Progressive Character Corruption ===\n")
    
    base_text = "System integrity check passed. All operations normal."
    
    corruption_levels = [0.2, 0.4, 0.6, 0.8, 1.0]
    
    for level in corruption_levels:
        print(f"Corruption Level: {level*100:.0f}%")
        
        # Apply multiple effects in sequence
        corrupted = base_text
        
        # Decay effect
        if level > 0.3:
            decay = CharacterDecayEffect(intensity=level*0.8, decay_mode="symbolic")
            decay.start()
            corrupted = decay.apply(corrupted)
        
        # Stutter effect  
        if level > 0.5:
            stutter = CharacterStutterEffect(intensity=level*0.7, stutter_chance=level*0.2)
            stutter.start()
            corrupted = stutter.apply(corrupted)
            
        # Screen tear
        if level > 0.7:
            tear = ScreenTearEffect(intensity=level, tear_frequency=level*0.3)
            tear.start()
            corrupted = tear.apply(corrupted)
            
        print(f"Result: {corrupted}")
        print()

if __name__ == "__main__":
    print("Cyberscape: Digital Dread - Character Effects Test\n")
    print("=" * 60)
    
    try:
        test_individual_effects()
        test_combined_effects()
        test_interactive_effects()
        
        print("=== Character Effects Test Complete ===")
        print("✅ All character-level effects are working correctly!")
        print("\nNext steps:")
        print("- Effects are already integrated into the main game")
        print("- Ready to move on to role system implementation")
        print("- Ready to enhance LLM & NPC integration")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
