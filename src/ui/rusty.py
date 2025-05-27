"""Rusty's dedicated visual system for rendering his responses and effects.

This module provides a custom buffer and border system for Rusty's responses,
separate from the main terminal. It includes:
- Custom text buffer with glitch effects
- Dynamic border with mechanical animations
- Overlay effects for annotations
- Corruption-based visual distortions
"""

import pygame
import random
import math
import time
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class RustyLine:
    """Represents a single line in Rusty's buffer."""
    text: str
    glitch: bool
    timestamp: float
    annotations: List[str]
    corruption_level: float = 0.0
    displacement: Tuple[int, int] = (0, 0)
    overlay_char: Optional[str] = None
    overlay_color: Optional[Tuple[int, int, int]] = None
    trail_alpha: float = 1.0

class RustyTextBuffer:
    """Manages Rusty's dedicated text buffer with effects."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.lines: List[RustyLine] = []
        self.visible: bool = False
        self.decay_timer: float = 6.0  # seconds before fading
        self.active_border_state = "locked"
        self.corruption_level: float = 0.0
        self.font = None  # Will be set by renderer
        self.char_width = 0
        self.char_height = 0
        self.max_lines = height // 20  # Approximate lines that fit
        self.mechanical_symbols = ['⚙', '⚡', '⚛', '⚜', '⚝', '⚞', '⚟', '⚡', '⚢', '⚣']
        self.corruption_symbols = ['▒', '▓', '█', '░', '▄', '▀', '▌', '▐', '■', '□']
        
    def add_line(self, text: str, annotations: List[str] = None) -> None:
        """Add a new line to the buffer with optional annotations."""
        if annotations is None:
            annotations = []
            
        line = RustyLine(
            text=text,
            glitch=random.random() < 0.3,
            timestamp=time.time(),
            annotations=annotations,
            corruption_level=self.corruption_level
        )
        
        self.lines.append(line)
        if len(self.lines) > self.max_lines:
            self.lines.pop(0)
            
    def update(self, dt: float) -> None:
        """Update buffer state and effects."""
        current_time = time.time()
        
        # Update decay timer
        if self.visible and not self.lines:
            self.decay_timer -= dt
            if self.decay_timer <= 0:
                self.visible = False
                self.decay_timer = 6.0
                
        # Update line effects
        for line in self.lines:
            # Apply corruption effects
            if random.random() < self.corruption_level * 0.3:
                line.overlay_char = random.choice(self.corruption_symbols)
                line.overlay_color = (255, 0, 85)  # Scourge red
                
            # Apply displacement
            if line.glitch:
                max_offset = int(3 * self.corruption_level)
                line.displacement = (
                    random.randint(-max_offset, max_offset),
                    random.randint(-max_offset, max_offset)
                )
                
            # Update trail alpha
            age = current_time - line.timestamp
            line.trail_alpha = max(0.0, 1.0 - (age / 2.0))
            
    def render(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        """Render the buffer contents with effects."""
        if not self.visible or not self.lines:
            return
            
        self.font = font
        self.char_width = font.size(' ')[0]
        self.char_height = font.size(' ')[1]
        
        y_offset = 0
        for line in self.lines:
            # Calculate position with displacement
            x = 10 + line.displacement[0]
            y = y_offset + line.displacement[1]
            
            # Render main text
            text_surface = font.render(line.text, True, (200, 200, 200))
            surface.blit(text_surface, (x, y))
            
            # Render overlay if present
            if line.overlay_char and line.overlay_color:
                overlay_surface = font.render(line.overlay_char, True, line.overlay_color)
                surface.blit(overlay_surface, (x, y))
                
            # Render annotations
            if line.annotations:
                for i, annotation in enumerate(line.annotations):
                    ann_y = y + (i + 1) * self.char_height
                    ann_surface = font.render(annotation, True, (150, 150, 150))
                    surface.blit(ann_surface, (x + 20, ann_y))
                    
            y_offset += self.char_height * (1 + len(line.annotations))
            
    def set_corruption_level(self, level: float) -> None:
        """Set the corruption level for visual effects."""
        self.corruption_level = max(0.0, min(1.0, level))
        
    def clear(self) -> None:
        """Clear all lines from the buffer."""
        self.lines.clear()
        
    def show(self) -> None:
        """Make the buffer visible."""
        self.visible = True
        self.decay_timer = 6.0
        
    def hide(self) -> None:
        """Hide the buffer."""
        self.visible = False

class RustyBorder:
    """Rusty's custom border with mechanical animations."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.corruption_level: float = 0.0
        self.pulse_intensity: float = 0.0
        self.scanline_offset: float = 0.0
        self.glitch_cascade: List[Tuple[int, int, float]] = []  # x, y, progress
        self.mechanical_symbols = ['⚙', '⚡', '⚛', '⚜', '⚝', '⚞', '⚟', '⚡', '⚢', '⚣']
        self.border_thickness = 2
        
    def update(self, dt: float) -> None:
        """Update border animations."""
        # Update pulse
        self.pulse_intensity = max(0.0, self.pulse_intensity - dt)
        
        # Update scanline
        self.scanline_offset = (self.scanline_offset + dt * 100) % self.height
        
        # Update glitch cascade
        self.glitch_cascade = [(x, y, p + dt) for x, y, p in self.glitch_cascade if p < 1.0]
        
    def render(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        """Render the border with effects."""
        # Draw main border
        border_color = (200, 200, 200)
        if self.pulse_intensity > 0:
            pulse_factor = 1.0 + 0.2 * math.sin(time.time() * 5) * self.pulse_intensity
            border_color = tuple(min(255, int(c * pulse_factor)) for c in border_color)
            
        # Draw border lines
        pygame.draw.rect(surface, border_color, (0, 0, self.width, self.height), self.border_thickness)
        
        # Draw mechanical symbols at corners
        for x, y in [(0, 0), (self.width - 20, 0), (0, self.height - 20), (self.width - 20, self.height - 20)]:
            symbol = random.choice(self.mechanical_symbols)
            symbol_surface = font.render(symbol, True, border_color)
            surface.blit(symbol_surface, (x, y))
            
        # Draw scanline
        if self.corruption_level > 0.3:
            scanline_y = int(self.scanline_offset)
            scanline_alpha = int(128 * (0.5 + 0.5 * math.sin(time.time() * 10)))
            scanline_surface = pygame.Surface((self.width, 2), pygame.SRCALPHA)
            pygame.draw.line(scanline_surface, (*border_color, scanline_alpha), 
                           (0, 0), (self.width, 0), 2)
            surface.blit(scanline_surface, (0, scanline_y))
            
        # Draw glitch cascade
        for x, y, progress in self.glitch_cascade:
            if random.random() < 0.3:
                glitch_char = random.choice(['▒', '▓', '█', '░'])
                glitch_surface = font.render(glitch_char, True, (255, 0, 85))
                surface.blit(glitch_surface, (x, y))
                
    def trigger_pulse(self) -> None:
        """Trigger a border pulse effect."""
        self.pulse_intensity = 1.0
        
    def trigger_scanline(self) -> None:
        """Trigger a scanline effect."""
        self.scanline_offset = 0
        
    def trigger_glitch_cascade(self) -> None:
        """Trigger a glitch cascade effect."""
        start_x = random.randint(0, self.width)
        start_y = random.randint(0, self.height)
        self.glitch_cascade.append((start_x, start_y, 0.0))
        
    def set_corruption_level(self, level: float) -> None:
        """Set the corruption level for visual effects."""
        self.corruption_level = max(0.0, min(1.0, level))

class RustyRenderer:
    """Main renderer for Rusty's visual system."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.buffer = RustyTextBuffer(width - 40, height - 40)
        self.border = RustyBorder(width, height)
        self.font = None  # Will be set by main game
        
    def set_font(self, font: pygame.font.Font) -> None:
        """Set the font for rendering."""
        self.font = font
        
    def update(self, dt: float) -> None:
        """Update all visual components."""
        self.buffer.update(dt)
        self.border.update(dt)
        
    def render(self, surface: pygame.Surface) -> None:
        """Render Rusty's complete visual system."""
        if not self.font:
            return
            
        # Create a subsurface for Rusty's content
        content_surface = surface.subsurface((20, 20, self.width - 40, self.height - 40))
        
        # Render buffer
        self.buffer.render(content_surface, self.font)
        
        # Render border
        self.border.render(surface, self.font)
        
    def add_response(self, text: str, annotations: List[str] = None) -> None:
        """Add a new response to Rusty's buffer."""
        self.buffer.add_line(text, annotations)
        self.buffer.show()
        
    def set_corruption_level(self, level: float) -> None:
        """Set corruption level for all components."""
        self.buffer.set_corruption_level(level)
        self.border.set_corruption_level(level)
        
    def trigger_effects(self) -> None:
        """Trigger various visual effects."""
        self.border.trigger_pulse()
        if random.random() < 0.3:
            self.border.trigger_scanline()
        if random.random() < 0.2:
            self.border.trigger_glitch_cascade() 