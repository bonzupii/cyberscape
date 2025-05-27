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
        self.redaction_chars = "█▓▒░"
        self.thought_markers = ["*", "~", "°", "·"]
        self.error_patterns = [
            "[ERROR]", "[CORRUPTED]", "[MISSING]", "[REDACTED]",
            "§§§", "!!!ERROR!!!", "***CORRUPTED***"
        ]

    def apply_redaction(self, text: str, redaction_level: float) -> str:
        """Apply redaction effects to sensitive text."""
        if redaction_level <= 0:
            return text
            
        words = text.split()
        result_words = []
        
        for word in words:
            if len(word) > 3 and random.random() < redaction_level:
                # Redact sensitive-looking words
                if any(keyword in word.lower() for keyword in 
                      ["password", "key", "secret", "classified", "admin", "root"]):
                    redacted = random.choice(self.redaction_chars) * len(word)
                    result_words.append(redacted)
                else:
                    result_words.append(word)
            else:
                result_words.append(word)
                
        return " ".join(result_words)

    def apply_thought_overlay(self, text: str, thought_intensity: float) -> str:
        """Apply intrusive thought overlays."""
        if thought_intensity <= 0 or random.random() > thought_intensity * 0.3:
            return text
            
        thoughts = [
            "why are you here?", "this isn't real", "you're being watched",
            "something is wrong", "escape while you can", "trust no one",
            "the system knows", "voss is still here", "digital nightmare"
        ]
        
        thought = random.choice(thoughts)
        marker = random.choice(self.thought_markers)
        
        # Insert thought as overlay
        if len(text) > 20:
            pos = random.randint(5, len(text) - 15)
            return text[:pos] + f" {marker}{thought}{marker} " + text[pos:]
        else:
            return text + f" {marker}{thought}{marker}"

    def apply_error_corruption(self, text: str, error_level: float) -> str:
        """Apply error-based corruption effects."""
        if error_level <= 0 or random.random() > error_level * 0.2:
            return text
            
        error_pattern = random.choice(self.error_patterns)
        
        # Replace parts of text with error patterns
        if len(text) > 10:
            replace_start = random.randint(0, len(text) // 2)
            replace_length = min(len(error_pattern), len(text) - replace_start)
            return text[:replace_start] + error_pattern[:replace_length] + text[replace_start + replace_length:]
        else:
            return error_pattern[:len(text)]


class ColorNoiseRenderer:
    """Handles color spikes, scanlines, and bleeding effects."""
    
    def __init__(self):
        self.scanline_position = 0
        self.color_spike_timer = 0.0
        self.bleeding_colors = {}

    def update(self, dt: float):
        """Update color and noise effects."""
        self.scanline_position = (self.scanline_position + dt * 10) % 100
        self.color_spike_timer += dt
        
        # Decay bleeding colors
        for pos in list(self.bleeding_colors.keys()):
            self.bleeding_colors[pos] = max(0, self.bleeding_colors[pos] - dt * 0.5)
            if self.bleeding_colors[pos] <= 0:
                del self.bleeding_colors[pos]

    def get_scanline_intensity(self, line_index: int) -> float:
        """Get scanline intensity for a given line."""
        distance = abs(line_index - self.scanline_position)
        if distance < 2:
            return 1.0 - (distance / 2)
        return 0.0

    def apply_color_spike(self, style: TerminalStyle, context: RenderContext) -> TerminalStyle:
        """Apply color spike effects."""
        if context.corruption_level > 0.6 and random.random() < 0.05:
            # Red spike
            spiked_style = TerminalStyle(
                fg_color=(255, 0, 0),
                bg_color=style.bg_color,
                bold=True,
                blink=True
            )
            return spiked_style
        elif context.corruption_level > 0.3 and random.random() < 0.02:
            # Green spike
            spiked_style = TerminalStyle(
                fg_color=(0, 255, 0),
                bg_color=style.bg_color,
                bold=style.bold
            )
            return spiked_style
            
        return style

    def apply_color_bleeding(self, style: TerminalStyle, context: RenderContext) -> TerminalStyle:
        """Apply color bleeding from previous lines."""
        line_key = f"{context.line_index}_{context.column_index}"
        
        if context.corruption_level > 0.4 and random.random() < 0.1:
            # Create new bleeding
            self.bleeding_colors[line_key] = 1.0
            
        if line_key in self.bleeding_colors:
            bleeding_intensity = self.bleeding_colors[line_key]
            # Blend colors
            r, g, b = style.fg_color
            br, bg, bb = (255, 0, 100) # Bleeding color
            
            blend_r = int(r * (1 - bleeding_intensity) + br * bleeding_intensity)
            blend_g = int(g * (1 - bleeding_intensity) + bg * bleeding_intensity)
            blend_b = int(b * (1 - bleeding_intensity) + bb * bleeding_intensity)
            
            return TerminalStyle(
                fg_color=(blend_r, blend_g, blend_b),
                bg_color=style.bg_color,
                bold=style.bold,
                blink=bleeding_intensity > 0.5
            )
            
        return style


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
        if context.corruption_level > 0.3:
            # Ensure apply_to_line is called on an instance of SubliminalEffect
            return self.subliminal_effect.apply_to_line(text, context.line_index)
        return text

    def render_enhanced_line(self, surface: pygame.Surface, line: TextLine, x_pos: int, y_pos: int, context: RenderContext): # Added x_pos
        """Render a line with enhanced effects processing."""
        start_time = time.time()
        
        # Build render context
        context.timestamp = start_time
        context.line_index = y_pos // self.char_height if self.char_height > 0 else 0 # Approximate line index for effects
        
        # Apply effects in layers
        processed_text = line.text
        
        # Layer 1: Background effects (example, actual application might vary)
        # This part seems to be handled by self.effect_manager.apply_effects in the original design
        # For now, we assume text comes pre-processed or effects are applied globally by effect_manager
        # processed_text = self.apply_layered_effects(processed_text, context) # Assuming this was a conceptual placeholder

        # Direct application of effects via EffectManager if that's the intended design
        if self.effect_manager:
            # Create a temporary list of effects if needed, or use existing ones
            # This part needs to align with how EffectManager is supposed to be used per line
            # For now, let's assume effects are managed and applied by EffectManager globally or per frame
            pass

        # Layer 2: Contextual effects  
        processed_text = self.apply_contextual_effects(processed_text, context)
        
        # Layer 3: Subliminal effects
        processed_text = self.apply_subliminal_effects(processed_text, context)
        
        # Apply color and noise effects to style
        enhanced_style = line.style # Start with the line's base style
        enhanced_style = self.color_noise_renderer.apply_color_spike(enhanced_style, context)
        enhanced_style = self.color_noise_renderer.apply_color_bleeding(enhanced_style, context)
        
        # Apply scanline effects
        scanline_intensity = self.color_noise_renderer.get_scanline_intensity(context.line_index)
        if scanline_intensity > 0:
            r, g, b = enhanced_style.fg_color
            enhanced_style_dict = enhanced_style.to_dict()
            enhanced_style_dict["fg_color"] = (
                min(255, int(r + scanline_intensity * 50)),
                min(255, int(g + scanline_intensity * 20)),
                min(255, int(b + scanline_intensity * 20))
            )
            enhanced_style = TerminalStyle.from_dict(enhanced_style_dict)
        
        # Render the processed line
        self._render_text(surface, processed_text, x_pos, y_pos, enhanced_style) # Use x_pos
        
        self.effect_render_time += time.time() - start_time

    def render(self, surface: pygame.Surface, effect_manager=None):
        """Enhanced render method with comprehensive effects integration."""
        frame_start = time.time()
        
        self.update_effect_scheduling()
        
        dt = frame_start - self.frame_time if self.frame_time > 0 else 0.016 # Avoid dt=0 on first frame
        self.frame_time = frame_start
        
        current_corruption_level = self.corruption_level # Default if no game_state_manager
        if self.game_state_manager:
            current_corruption_level = self.game_state_manager.get_corruption_level()
            
        self.subliminal_effect.update(dt, current_corruption_level)
        self.color_noise_renderer.update(dt)
        
        surface.fill((0, 0, 0)) # Clear screen with black background

        if self.width <= 0 or self.height <= 0 or self.char_width <= 0 or self.char_height <= 0:
            self.logger.error(f"Cannot render with invalid dimensions: W={self.width}, H={self.height}, CW={self.char_width}, CH={self.char_height}")
            if self.font is None: # Attempt to re-init font if it's missing
                self._init_font() 
            return

        # --- Border Rendering ---
        # Calculate grid dimensions for border
        # The border should occupy the full terminal grid
        border_grid_cols = self.width // self.char_width
        border_grid_rows = self.height // self.char_height
        
        # Generate border lines using the BorderEffectManager
        # These are strings, to be rendered with _render_text
        border_lines = self.border_manager.generate_border(
            border_grid_cols,
            border_grid_rows,
            BorderRegion.MAIN_OUTPUT, # Or an appropriate region
            current_corruption_level,
            int(frame_start * 10) # Animation frame
        )

        # Render the border lines
        for r, border_row_text in enumerate(border_lines):
            # Border text is rendered from the very edge (0,0)
            self._render_text(surface, border_row_text, 0, r * self.char_height, TerminalStyle(fg_color=(0,150,0), dim=True)) # Example style

        # --- Content Area Definition (inside the border) ---
        content_x_offset = self.char_width  # 1 char padding left
        content_y_offset = self.char_height # 1 char padding top
        content_width = self.width - (2 * self.char_width)   # 1 char padding left/right
        content_height = self.height - (2 * self.char_height) # 1 char padding top/bottom

        max_content_cols = content_width // self.char_width
        max_content_rows = content_height // self.char_height
        
        if max_content_cols <= 0 or max_content_rows <=0:
            self.logger.warning("Not enough space for content area within borders.")
            return

        # --- Main Buffer Rendering (Scrollable) ---
        visible_lines = self.buffer[self.scroll_offset:] 
        
        render_context = RenderContext(corruption_level=current_corruption_level, role=self.game_state_manager.get_player_role() if self.game_state_manager else "unknown")

        for i, text_line_obj in enumerate(visible_lines):
            if i >= max_content_rows: # Stop if we run out of vertical space in content area
                break
            
            # Ensure text_line_obj is a TextLine object
            current_line_obj = text_line_obj
            if isinstance(text_line_obj, str): # Convert if it's a plain string (legacy)
                 current_line_obj = TextLine(text=text_line_obj, style=TerminalStyle())


            line_y_pos = content_y_offset + (i * self.char_height)
            render_context.line_index = self.scroll_offset + i # Global line index for effects
            render_context.is_input_line = False
            render_context.is_prompt = False
            
            # Truncate line if it's too long for the content width
            display_text = current_line_obj.text
            if len(display_text) > max_content_cols:
                display_text = display_text[:max_content_cols]
            
            temp_line_for_render = TextLine(text=display_text, style=current_line_obj.style)

            self.render_enhanced_line(surface, temp_line_for_render, content_x_offset, line_y_pos, render_context)

        # --- Prompt and Current Input Rendering ---
        prompt_y_pos = content_y_offset + (max_content_rows * self.char_height) # Position after buffer
        
        # Ensure prompt and input don't exceed available height
        if prompt_y_pos < content_y_offset + content_height - self.char_height: # Check if there's space for at least one more line
            full_prompt_line = self.get_prompt() + self.current_input
            
            # Truncate if too long
            if len(full_prompt_line) > max_content_cols:
                # Prioritize showing the end of the input
                visible_chars = max_content_cols
                full_prompt_line = full_prompt_line[-visible_chars:]

            prompt_text_line = TextLine(text=full_prompt_line, style=TerminalStyle()) # Use default style or a specific prompt style
            
            render_context_prompt = RenderContext(
                corruption_level=current_corruption_level, 
                role=self.game_state_manager.get_player_role() if self.game_state_manager else "unknown",
                line_index = self.scroll_offset + max_content_rows, # Approximate
                is_input_line=True, 
                is_prompt=True
            )
            self.render_enhanced_line(surface, prompt_text_line, content_x_offset, prompt_y_pos, render_context_prompt)

            # --- Cursor Rendering ---
            if self.cursor_visible:
                cursor_char_x = len(self.get_prompt()) + self.cursor_x
                # Ensure cursor does not go beyond max_content_cols if full_prompt_line was truncated
                if len(self.get_prompt()) + self.cursor_x > max_content_cols:
                     #This can happen if input itself is truncated. Cursor should be at the end of visible part.
                     cursor_char_x = max_content_cols 
                
                cursor_pixel_x = content_x_offset + (cursor_char_x * self.char_width)
                
                # Adjust if the line was truncated from the left
                if len(self.get_prompt()) + self.current_input > max_content_cols:
                    prompt_len_in_truncated = len(full_prompt_line) - len(self.current_input.split(' ')[-1]) # approx
                    cursor_pixel_x = content_x_offset + ( (len(full_prompt_line) - len(self.current_input.split(' ')[-1])) + self.cursor_x ) * self.char_width


                cursor_rect = pygame.Rect(cursor_pixel_x, prompt_y_pos, self.char_width, self.char_height)
                pygame.draw.rect(surface, TerminalStyle().fg_color, cursor_rect) # Use default fg_color for cursor

        # --- Completion Suggestions Rendering ---
        if self.completion_suggestions:
            suggestion_y_start = prompt_y_pos + self.char_height 
            for idx, suggestion in enumerate(self.completion_suggestions):
                suggestion_y = suggestion_y_start + (idx * self.char_height)
                if suggestion_y >= content_y_offset + content_height: # Check bounds
                    break
                
                # Truncate suggestion if needed
                if len(suggestion) > max_content_cols:
                    suggestion = suggestion[:max_content_cols]

                suggestion_line = TextLine(text=suggestion, style=TerminalStyle(dim=True)) # Dim style for suggestions
                render_context_suggestion = RenderContext(
                    corruption_level=current_corruption_level,
                     role=self.game_state_manager.get_player_role() if self.game_state_manager else "unknown",
                    line_index = self.scroll_offset + max_content_rows + 1 + idx # Approximate
                )
                self.render_enhanced_line(surface, suggestion_line, content_x_offset, suggestion_y, render_context_suggestion)

        # Update cursor blink state
        if time.time() - self.last_cursor_toggle > self.cursor_blink_time:
            self.cursor_visible = not self.cursor_visible
            self.last_cursor_toggle = time.time()

        # (Any global screen effects like screen tear could be applied here over the whole surface)
        # Example: if self.effect_manager and any(isinstance(e, ScreenTearEffect) for e in self.effect_manager.active_effects):
        # self.effect_manager.apply_global_effects(surface) # Assuming such a method exists

        pygame.display.flip() # Update the full display
