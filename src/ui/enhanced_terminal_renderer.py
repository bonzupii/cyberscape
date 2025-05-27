"""Enhanced Terminal Renderer with Integrated Effects System.

This module extends the terminal renderer with comprehensive character-level effects,
line/layout effects, animation effects, color/noise effects, contextual effects,
and subliminal effects integration.

Priority implementation from executive tasks:
- Character-level effects (decay, stuttering, corruption)
- Line/layout effects (breaks, jitter, screen tear)
- Animation effects (typing speed, flicker, breathing)
- Color/noise effects (spikes, scanlines, bleeding)
- Contextual effects (redactions, thoughts, errors)
- Subliminal effects (patterns, messages, faces)
"""

import pygame
import time
import random
import math
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum

from .terminal import TerminalRenderer, TerminalStyle, TextLine
from .border_effects import BorderRegion # Ensure BorderRegion is imported
from ..core.effects import (
    EffectManager, CharacterDecayEffect, CharacterStutterEffect, 
    ScreenTearEffect, CharacterJitterEffect, TextBreathingEffect,
    ScanlineEffect, CorruptionEffect, BaseEffect, TypingEffect
)

logger = logging.getLogger(__name__)


class EffectPriority(Enum):
    """Effect priority levels for conflict resolution."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class EffectLayer(Enum):
    """Effect layering system for proper stacking."""
    BACKGROUND = 1      # Scanlines, breathing
    CHARACTER = 2       # Decay, corruption, stutter
    LAYOUT = 3         # Screen tear, jitter
    OVERLAY = 4        # Redactions, thoughts
    SUBLIMINAL = 5     # Hidden patterns, messages


@dataclass
class RenderContext:
    """Context information for effect rendering."""
    corruption_level: float = 0.0
    role: str = "unknown"
    game_state: str = "normal"
    line_index: int = -1
    column_index: int = -1
    timestamp: float = 0.0
    is_input_line: bool = False
    is_prompt: bool = False


class SubliminalEffect:
    """Handles subliminal patterns and hidden messages."""
    
    def __init__(self):
        self.hidden_patterns = [
            "OBEY", "CONSUME", "WATCH", "FEAR", "SUBMIT",
            "YOU ARE BEING WATCHED", "TRUST NO ONE", "ESCAPE",
            "THE SCOURGE SEES ALL", "VOSS REMEMBERS", "DIGITAL HELL"
        ]
        self.face_patterns = [
            "  O   O  ", " \\_____/ ", "   ---   ",
            " ◉     ◉ ", "    ◊    ", "  ╱___╲  "
        ]
        self.pattern_timer = 0.0
        self.active_pattern = None
        self.pattern_opacity = 0.0

    def update(self, dt: float, corruption_level: float):
        """Update subliminal patterns based on corruption level."""
        self.pattern_timer += dt
        
        # Trigger patterns based on corruption level
        trigger_chance = corruption_level * 0.1  # Up to 10% chance at max corruption
        
        if self.pattern_timer > 5.0 and random.random() < trigger_chance:
            if corruption_level > 0.8:
                # High corruption - use disturbing patterns
                self.active_pattern = random.choice(self.face_patterns)
                self.pattern_opacity = 0.3
            elif corruption_level > 0.5:
                # Medium corruption - use messages
                self.active_pattern = random.choice(self.hidden_patterns)
                self.pattern_opacity = 0.2
            else:
                # Low corruption - subtle hints
                self.active_pattern = random.choice(["...", "---", "   "])
                self.pattern_opacity = 0.1
                
            self.pattern_timer = 0.0

    def apply_to_line(self, line: str, line_index: int) -> str:
        """Apply subliminal patterns to a line of text."""
        if not self.active_pattern or self.pattern_opacity <= 0:
            return line
            
        # Fade out pattern over time
        self.pattern_opacity *= 0.95
        if self.pattern_opacity < 0.05:
            self.active_pattern = None
            return line
            
        # Inject pattern based on opacity and line position
        if random.random() < self.pattern_opacity and len(line) > 10:
            # Find a suitable position to inject the pattern
            pattern_start = random.randint(0, max(0, len(line) - len(self.active_pattern)))
            
            # Overlay pattern with original text
            result = list(line)
            for i, char in enumerate(self.active_pattern):
                pos = pattern_start + i
                if pos < len(result) and char != ' ':
                    # Blend characters for subliminal effect
                    if random.random() < 0.7:  # 70% visibility
                        result[pos] = char
                        
            return ''.join(result)
            
        return line


class ContextualEffectRenderer:
    """Handles contextual effects like redactions, thoughts, and errors."""
    
    def __init__(self):
        self.redaction_chars = ['█', '▓', '▒', '░', '■', '●', '◆', '▲']
        self.thought_patterns = [
            "[...]", "(why?)", "{ERROR}", "<HELP>", "[LOST]", "(remember?)",
            "{FAIL}", "<STOP>", "[VOID]", "(alone)", "{WATCH}", "<RUN>"
        ]
        self.error_patterns = [
            "ERR:", "FAIL:", "NULL:", "VOID:", "LOST:", "DEAD:",
            "STOP:", "HELP:", "PAIN:", "FEAR:", "DARK:", "END:"
        ]
        
    def apply_redaction(self, text: str, redaction_level: float) -> str:
        """Apply redaction effects to sensitive content."""
        if redaction_level <= 0:
            return text
            
        result_chars = list(text)
        redaction_chance = min(redaction_level, 0.8)  # Max 80% redaction
        
        # Redact complete words for sensitive content
        sensitive_keywords = [
            "password", "key", "secret", "admin", "root", "hack",
            "exploit", "vulnerability", "breach", "attack", "virus"
        ]
        
        text_lower = text.lower()
        for keyword in sensitive_keywords:
            if keyword in text_lower:
                # Redact the keyword completely
                start_idx = text_lower.find(keyword)
                if start_idx != -1:
                    redaction_char = random.choice(self.redaction_chars)
                    for i in range(start_idx, start_idx + len(keyword)):
                        if i < len(result_chars):
                            result_chars[i] = redaction_char
        
        # Apply random character redaction
        for i, char in enumerate(result_chars):
            if char.isalnum() and random.random() < redaction_chance:
                result_chars[i] = random.choice(self.redaction_chars)
                
        return ''.join(result_chars)
    
    def apply_thought_overlay(self, text: str, thought_intensity: float) -> str:
        """Apply intrusive thought overlays."""
        if thought_intensity <= 0 or len(text) < 10:
            return text
            
        # Insert thought patterns at random positions
        insertion_chance = thought_intensity * 0.3
        if random.random() < insertion_chance:
            thought = random.choice(self.thought_patterns)
            insert_pos = random.randint(0, max(0, len(text) - len(thought)))
            
            # Insert with spacing
            return text[:insert_pos] + f" {thought} " + text[insert_pos:]
            
        return text
    
    def apply_error_corruption(self, text: str, error_level: float) -> str:
        """Apply error-style corruption to text."""
        if error_level <= 0:
            return text
            
        result = text
        error_chance = error_level * 0.2
        
        # Insert error patterns
        if random.random() < error_chance:
            error_pattern = random.choice(self.error_patterns)
            words = result.split()
            if words:
                insert_pos = random.randint(0, len(words))
                words.insert(insert_pos, error_pattern)
                result = ' '.join(words)
        
        # Corrupt random characters with error-style symbols
        if random.random() < error_level * 0.1:
            error_chars = ['!', '?', '#', '%', '&', '*', '@', '$']
            result_chars = list(result)
            for i, char in enumerate(result_chars):
                if char.isalnum() and random.random() < error_level * 0.05:
                    result_chars[i] = random.choice(error_chars)
            result = ''.join(result_chars)
            
        return result


class ColorNoiseRenderer:
    """Handles color spikes, scanlines, and bleeding effects."""
    
    def __init__(self):
        self.scanline_pattern = 0
        self.color_spike_timer = 0.0
        self.bleeding_intensity = 0.0
        
    def apply_color_spikes(self, color: Tuple[int, int, int], spike_intensity: float) -> Tuple[int, int, int]:
        """Apply color spikes and distortion."""
        if spike_intensity <= 0:
            return color
            
        r, g, b = color
        spike_chance = spike_intensity * 0.1
        
        if random.random() < spike_chance:
            # Random color spike
            spike_type = random.choice(['red', 'green', 'blue', 'white', 'random'])
            
            if spike_type == 'red':
                return (min(255, r + int(spike_intensity * 100)), g // 2, b // 2)
            elif spike_type == 'green':
                return (r // 2, min(255, g + int(spike_intensity * 100)), b // 2)
            elif spike_type == 'blue':
                return (r // 2, g // 2, min(255, b + int(spike_intensity * 100)))
            elif spike_type == 'white':
                boost = int(spike_intensity * 80)
                return (min(255, r + boost), min(255, g + boost), min(255, b + boost))
            else:  # random
                noise = int(spike_intensity * 60)
                return (
                    max(0, min(255, r + random.randint(-noise, noise))),
                    max(0, min(255, g + random.randint(-noise, noise))),
                    max(0, min(255, b + random.randint(-noise, noise)))
                )
                
        return color
    
    def apply_scanlines(self, line_index: int, color: Tuple[int, int, int], 
                       scanline_intensity: float) -> Tuple[int, int, int]:
        """Apply scanline effects to text color."""
        if scanline_intensity <= 0:
            return color
            
        # Create moving scanline pattern
        scanline_offset = int(time.time() * 10) % 6  # Moving pattern
        if (line_index + scanline_offset) % 3 == 0:
            # Dim the line
            dim_factor = 1.0 - (scanline_intensity * 0.4)
            r, g, b = color
            return (
                int(r * dim_factor),
                int(g * dim_factor),
                int(b * dim_factor)
            )
        elif (line_index + scanline_offset) % 6 == 0:
            # Brighten occasional lines
            bright_factor = 1.0 + (scanline_intensity * 0.3)
            r, g, b = color
            return (
                min(255, int(r * bright_factor)),
                min(255, int(g * bright_factor)),
                min(255, int(b * bright_factor))
            )
            
        return color
    
    def apply_color_bleeding(self, color: Tuple[int, int, int], 
                           bleeding_intensity: float) -> Tuple[int, int, int]:
        """Apply color bleeding effects."""
        if bleeding_intensity <= 0:
            return color
            
        r, g, b = color
        bleed_amount = int(bleeding_intensity * 30)
        
        # Simulate chromatic aberration/bleeding
        if random.random() < bleeding_intensity * 0.2:
            # Red channel bleeding
            r = min(255, r + random.randint(-bleed_amount, bleed_amount))
            # Green channel stays more stable
            g = min(255, max(0, g + random.randint(-bleed_amount//2, bleed_amount//2)))
            # Blue channel bleeding in opposite direction
            b = min(255, max(0, b + random.randint(-bleed_amount, bleed_amount)))
            
        return (r, g, b)


class EnhancedTerminalRenderer(TerminalRenderer):
    """Enhanced terminal renderer with comprehensive effects integration."""
    
    DEFAULT_FONT_NAME = "OpenDyslexicMono-Regular.otf"
    DEFAULT_FONT_SIZE = 18
    # BASE_FONT_PATH is inherited from TerminalRenderer and defaults to "assets/fonts/"

    def __init__(self, effect_manager=None, game_state_manager=None):
        # The parent __init__ now calls _init_font. 
        # _init_font in the parent is designed to look for DEFAULT_FONT_NAME and DEFAULT_FONT_SIZE
        # on `self` first, so it will pick up the values defined in this class.
        super().__init__(effect_manager)
        self.game_state_manager = game_state_manager
        
        # Font and char dimensions are now set by the parent's _init_font method,
        # which is called by parent's __init__.

        # Enhanced effect systems
        self.subliminal_effect = SubliminalEffect()
        self.contextual_renderer = ContextualEffectRenderer()
        self.color_noise_renderer = ColorNoiseRenderer()
        
        # Effect timing and scheduling
        self.effect_scheduler = {}
        self.effect_priorities = {}
        self.effect_layers = {layer: [] for layer in EffectLayer}
        
        # Performance tracking
        self.frame_time = 0.0
        self.effect_render_time = 0.0
        
        # Enhanced cursor effects
        self.cursor_trail_positions = []
        self.cursor_trail_max_length = 10
        
        # Use self.font.name if available, otherwise provide a fallback string.
        # Pygame's font objects from pygame.font.Font() don't have a .name attribute directly.
        # We rely on the logging within _init_font for detailed load status.
        font_display_name = "N/A"
        if self.font:
            # Attempt to get a name, might be path for file-loaded fonts or name for SysFont
            # This is tricky as pygame.font.Font objects don't store the original name/path reliably.
            # The logger in _init_font provides more accurate loading details.
            font_display_name = getattr(self.font, 'name', 'Font Loaded (name not directly accessible)')

        logger.info(f"Enhanced Terminal Renderer initialized. Attempted Font: {self.DEFAULT_FONT_NAME}, Actual Font object: {font_display_name}, Char Height: {self.char_height}")

    def schedule_effect(self, effect: BaseEffect, delay: float, priority: EffectPriority = EffectPriority.NORMAL):
        """Schedule an effect to trigger after a delay."""
        trigger_time = time.time() + delay
        self.effect_scheduler[trigger_time] = {
            'effect': effect,
            'priority': priority
        }

    def update_effect_scheduling(self):
        """Update scheduled effects."""
        current_time = time.time()
        triggered_times = []
        
        for trigger_time, effect_data in self.effect_scheduler.items():
            if current_time >= trigger_time:
                effect = effect_data['effect']
                priority = effect_data['priority']
                
                # Add to appropriate layer based on effect type
                if isinstance(effect, (CharacterDecayEffect, CharacterStutterEffect, CorruptionEffect)):
                    self.effect_layers[EffectLayer.CHARACTER].append(effect)
                elif isinstance(effect, (ScreenTearEffect, CharacterJitterEffect)):
                    self.effect_layers[EffectLayer.LAYOUT].append(effect)
                elif isinstance(effect, (TextBreathingEffect, ScanlineEffect)):
                    self.effect_layers[EffectLayer.BACKGROUND].append(effect)
                
                self.effect_priorities[effect] = priority
                self.effect_manager.add_effect(effect)
                triggered_times.append(trigger_time)
        
        # Clean up triggered effects
        for trigger_time in triggered_times:
            del self.effect_scheduler[trigger_time]

    def apply_layered_effects(self, text: str, context: RenderContext) -> str:
        """Apply effects in proper layering order."""
        result = text
        
        # Apply effects by layer priority
        for layer in EffectLayer:
            layer_effects = self.effect_layers[layer]
            # Sort by priority within layer
            layer_effects.sort(key=lambda e: self.effect_priorities.get(e, EffectPriority.NORMAL).value, reverse=True)
            
            for effect in layer_effects:
                if effect.is_active:
                    applied = effect.apply(result)
                    if applied is not None:
                        result = applied
                        
        return result

    def apply_contextual_effects(self, text: str, context: RenderContext) -> str:
        """Apply contextual effects based on game state and corruption level."""
        result = text
        
        # Apply redaction for sensitive content
        if context.corruption_level < 0.3:  # Low corruption = more redaction
            redaction_level = (0.3 - context.corruption_level) * 2
            result = self.contextual_renderer.apply_redaction(result, redaction_level)
        
        # Apply thought overlays at medium corruption
        if 0.4 < context.corruption_level < 0.8:
            thought_intensity = context.corruption_level - 0.4
            result = self.contextual_renderer.apply_thought_overlay(result, thought_intensity)
        
        # Apply error corruption at high corruption
        if context.corruption_level > 0.6:
            error_level = context.corruption_level - 0.6
            result = self.contextual_renderer.apply_error_corruption(result, error_level)
        
        return result

    def apply_subliminal_effects(self, text: str, context: RenderContext) -> str:
        """Apply subliminal patterns and hidden messages."""
        if not self.subliminal_effect.active_pattern:
            return text
            
        # Embed subliminal patterns subtly
        if context.corruption_level > 0.5 and len(text) > 20:
            # Insert pattern at random position
            pattern = self.subliminal_effect.active_pattern
            if len(pattern) < len(text):
                insert_pos = random.randint(0, len(text) - len(pattern))
                # Create subtle overlay (barely visible characters)
                overlay_chars = []
                for i, char in enumerate(pattern):
                    if char.isalnum():
                        overlay_chars.append('.')  # Subtle dots instead of letters
                    else:
                        overlay_chars.append(char)
                
                overlay_pattern = ''.join(overlay_chars)
                # Insert with reduced visibility
                if random.random() < self.subliminal_effect.pattern_opacity:
                    text = text[:insert_pos] + overlay_pattern + text[insert_pos + len(overlay_pattern):]
        
        return text

    def apply_character_effects(self, text: str, context: RenderContext) -> str:
        """Apply character-level effects like decay and stuttering."""
        result = text
        
        # Character decay at high corruption
        if context.corruption_level > 0.4:
            decay_chars = ['▓', '▒', '░', '█', '§', 'Æ', '¿', '¡']
            decay_chance = context.corruption_level * 0.1
            
            result_chars = list(result)
            for i, char in enumerate(result_chars):
                if char.isalnum() and random.random() < decay_chance:
                    result_chars[i] = random.choice(decay_chars)
            result = ''.join(result_chars)
        
        # Character stuttering
        if context.corruption_level > 0.3:
            stutter_chance = context.corruption_level * 0.05
            result_chars = list(result)
            i = 0
            while i < len(result_chars):
                if random.random() < stutter_chance:
                    char = result_chars[i]
                    # Insert 1-3 repetitions
                    repeats = random.randint(1, 3)
                    for _ in range(repeats):
                        result_chars.insert(i + 1, char)
                    i += repeats + 1
                else:
                    i += 1
            result = ''.join(result_chars[:len(text) * 2])  # Limit growth
        
        return result

    def apply_layout_effects(self, text: str, context: RenderContext) -> str:
        """Apply line and layout effects like breaks and jitter."""
        result = text
        
        # Line breaks and fragmentation
        if context.corruption_level > 0.6 and len(text) > 10:
            break_chance = (context.corruption_level - 0.6) * 0.1
            if random.random() < break_chance:
                # Insert line break characters
                break_pos = random.randint(len(text) // 3, len(text) * 2 // 3)
                result = text[:break_pos] + "|||" + text[break_pos:]
        
        # Character displacement (simple jitter)
        if context.corruption_level > 0.5:
            jitter_chance = context.corruption_level * 0.03
            result_chars = list(result)
            for i in range(len(result_chars) - 1):
                if random.random() < jitter_chance:
                    # Swap adjacent characters
                    result_chars[i], result_chars[i + 1] = result_chars[i + 1], result_chars[i]
            result = ''.join(result_chars)
        
        return result

    def apply_animation_effects(self, style: TerminalStyle, context: RenderContext) -> TerminalStyle:
        """Apply animation effects to text style."""
        enhanced_style = style
        
        # Breathing effect (color intensity oscillation)
        if context.corruption_level > 0.2:
            time_factor = context.timestamp * 2  # Breathing speed
            intensity = 0.5 + 0.5 * math.sin(time_factor)
            
            r, g, b = enhanced_style.fg_color
            # Apply breathing to color intensity
            breathing_r = int(r * (0.7 + 0.3 * intensity))
            breathing_g = int(g * (0.7 + 0.3 * intensity))
            breathing_b = int(b * (0.7 + 0.3 * intensity))
            
            enhanced_style = TerminalStyle(
                fg_color=(breathing_r, breathing_g, breathing_b),
                bg_color=enhanced_style.bg_color,
                bold=enhanced_style.bold,
                blink=enhanced_style.blink or (context.corruption_level > 0.7 and intensity > 0.8)
            )
        
        # Flicker effect
        if context.corruption_level > 0.6:
            flicker_chance = context.corruption_level * 0.1
            if random.random() < flicker_chance:
                # Temporarily dim or brighten
                multiplier = 0.3 if random.random() < 0.5 else 1.7
                r, g, b = enhanced_style.fg_color
                enhanced_style = TerminalStyle(
                    fg_color=(
                        min(255, max(0, int(r * multiplier))),
                        min(255, max(0, int(g * multiplier))),
                        min(255, max(0, int(b * multiplier)))
                    ),
                    bg_color=enhanced_style.bg_color,
                    bold=enhanced_style.bold,
                    blink=True
                )
        
        return enhanced_style

    def update_performance_tracking(self):
        """Update performance metrics and optimization."""
        current_time = time.time()
        
        # Track frame rate
        if hasattr(self, 'last_frame_time'):
            frame_delta = current_time - self.last_frame_time
            self.frame_rate = 1.0 / frame_delta if frame_delta > 0 else 60.0
        else:
            self.frame_rate = 60.0
            
        self.last_frame_time = current_time
        
        # Performance optimization: reduce effect frequency if frame rate drops
        if self.frame_rate < 30:
            self.performance_mode = "reduced"
            # Reduce effect frequencies
            for effect_list in self.effect_layers.values():
                for effect in effect_list:
                    if hasattr(effect, 'update_frequency'):
                        effect.update_frequency *= 0.8
        elif self.frame_rate > 45:
            self.performance_mode = "normal"

    def get_render_stats(self) -> dict:
        """Get rendering performance statistics."""
        return {
            'frame_rate': getattr(self, 'frame_rate', 60.0),
            'effect_render_time': self.effect_render_time,
            'active_effects': sum(len(effects) for effects in self.effect_layers.values()),
            'performance_mode': getattr(self, 'performance_mode', 'normal'),
            'scheduled_effects': len(self.effect_scheduler)
        }
