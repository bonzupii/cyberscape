"""Terminal renderer for Cyberscape: Digital Dread.

This module handles terminal rendering, including:
- Text rendering with effects
- Screen management
- Input handling
- Terminal styling
"""

import logging
import time
import pygame
import random
from dataclasses import dataclass
from typing import Optional, Tuple
import os # Added import

# --- Cyberscape: Procedural Border Effects Integration ---
from .border_effects import BorderEffectManager, BorderRegion

logger = logging.getLogger(__name__)

@dataclass
class TerminalStyle:
    """Represents terminal text styling."""
    fg_color: tuple = (0, 255, 0)  # Changed to green
    bg_color: tuple = (0, 0, 0)  # RGB tuple
    bold: bool = False
    underline: bool = False
    blink: bool = False
    reverse: bool = False
    dim: bool = False

    def to_dict(self) -> dict:
        return {
            "fg_color": self.fg_color,
            "bg_color": self.bg_color,
            "bold": self.bold,
            "underline": self.underline,
            "blink": self.blink,
            "reverse": self.reverse,
            "dim": self.dim
        }

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            fg_color=tuple(d["fg_color"]),
            bg_color=tuple(d["bg_color"]),
            bold=d["bold"],
            underline=d["underline"],
            blink=d["blink"],
            reverse=d["reverse"],
            dim=d["dim"]
        )

class TextEffect:
    """Base class for text effects."""
    
    def __init__(self, text: str, duration: float = 0.0):
        self.text = text
        self.duration = duration
        self.start_time = time.time()
        self.is_complete = False
    
    def update(self) -> str:
        """Update the effect and return the modified text."""
        if self.duration > 0 and time.time() - self.start_time >= self.duration:
            self.is_complete = True
        return self.text
    
    def is_done(self) -> bool:
        """Check if the effect is complete."""
        return self.is_complete

class TerminalRenderer:
    """Handles terminal rendering and styling using Pygame.
    
    Integrates procedural border effects for all UI regions.
    """
    DEFAULT_FONT_NAME = "monospace"
    DEFAULT_FONT_SIZE = 16
    BASE_FONT_PATH = "assets/fonts/"

    def __init__(self, effect_manager=None):
        pygame.init() # Ensure Pygame (and its font module) is initialized first
        self.screen = None
        self.font = None
        self.bold_font = None
        self.width = 0
        self.height = 0
        self.cursor_x = 0
        self.cursor_y = 0
        self.scroll_offset = 0
        self.buffer = []
        self.history = []
        self.history_index = -1
        self.max_history = 1000
        self._is_corrupted = False
        self.corruption_level = 0.0
        self.prompt_override = None
        self.completion_handler = None
        self.current_input = ""
        self.cursor_visible = True
        self.cursor_blink_time = 0.5
        self.last_cursor_toggle = time.time()
        self.effect_manager = effect_manager
        self.completion_suggestions = []
        
        import logging # Ensure logger is available for _init_font if called early
        self.logger = logging.getLogger("TerminalRenderer")
        self.logger.setLevel(logging.DEBUG)
        self.char_width = 0
        self.char_height = 0
        self.theme_manager = None

        # --- Procedural Border Effects ---
        self.border_manager = BorderEffectManager()

        self._init_font() # Call _init_font during initialization

    def _init_font(self, font_name_param=None, font_size_param=None):
        # Ensure font module is specifically initialized if not done by pygame.init() already
        # Though pygame.init() should cover it.
        if not pygame.font.get_init():
            pygame.font.init()

        logger_instance = getattr(self, 'logger', logging.getLogger(__name__)) # Use self.logger if available

        # Determine font name: parameter > instance default > class default
        if font_name_param:
            font_to_load = font_name_param
            source_of_font_name = "parameter"
        elif hasattr(self, 'DEFAULT_FONT_NAME') and self.DEFAULT_FONT_NAME != TerminalRenderer.DEFAULT_FONT_NAME:
            font_to_load = self.DEFAULT_FONT_NAME
            source_of_font_name = f"instance default ({self.__class__.__name__})"
        else:
            font_to_load = TerminalRenderer.DEFAULT_FONT_NAME
            source_of_font_name = "TerminalRenderer class default"
        logger_instance.info(f"Attempting to load font: '{font_to_load}' (source: {source_of_font_name})")

        # Determine font size: parameter > instance default > class default
        if font_size_param:
            size_to_load = font_size_param
            source_of_font_size = "parameter"
        elif hasattr(self, 'DEFAULT_FONT_SIZE') and self.DEFAULT_FONT_SIZE != TerminalRenderer.DEFAULT_FONT_SIZE:
            size_to_load = self.DEFAULT_FONT_SIZE
            source_of_font_size = f"instance default ({self.__class__.__name__})"
        else:
            size_to_load = TerminalRenderer.DEFAULT_FONT_SIZE
            source_of_font_size = "TerminalRenderer class default"
        logger_instance.info(f"Attempting to load font size: {size_to_load} (source: {source_of_font_size})")
        
        font_path_prefix = getattr(self, 'BASE_FONT_PATH', TerminalRenderer.BASE_FONT_PATH)

        self.font = None
        self.bold_font = None
        actual_path_loaded = "N/A"
        font_load_strategy = "Unknown"

        try:
            if not font_to_load:
                raise ValueError("Font name is None or empty.")

            is_file_path_like = '.' in font_to_load or '/' in font_to_load or '\\\\' in font_to_load
            
            # Attempt 1: Load from assets folder if it's not a path-like string or if it's a relative path
            potential_asset_path = os.path.join(font_path_prefix, font_to_load)
            if os.path.exists(potential_asset_path):
                actual_path_loaded = potential_asset_path
                font_load_strategy = f"Asset path: {actual_path_loaded}"
                logger_instance.info(f"Loading font file from assets: {actual_path_loaded} with size {size_to_load}")
                self.font = pygame.font.Font(actual_path_loaded, size_to_load)
                self.bold_font = pygame.font.Font(actual_path_loaded, size_to_load)
                if self.bold_font: self.bold_font.set_bold(True)
            # Attempt 2: If not found in assets or if it looks like an absolute path, try as direct path / system font
            elif is_file_path_like and os.path.exists(font_to_load): # Direct path
                actual_path_loaded = font_to_load
                font_load_strategy = f"Direct path: {actual_path_loaded}"
                logger_instance.info(f"Loading font file from direct path: {actual_path_loaded} with size {size_to_load}")
                self.font = pygame.font.Font(actual_path_loaded, size_to_load)
                self.bold_font = pygame.font.Font(actual_path_loaded, size_to_load)
                if self.bold_font: self.bold_font.set_bold(True)
            else: # Try as system font
                font_load_strategy = f"System font: {font_to_load}"
                logger_instance.info(f"Font file '{potential_asset_path}' (and direct path if applicable) not found. Attempting as system font: {font_to_load} with size {size_to_load}")
                self.font = pygame.font.SysFont(font_to_load, size_to_load)
                self.bold_font = pygame.font.SysFont(font_to_load, size_to_load, bold=True)
            
            if not self.font:
                raise ValueError(f"Font '{font_to_load}' could not be loaded via strategy: {font_load_strategy}.")

        except Exception as e:
            logger_instance.warning(f"Failed to load font '{font_to_load}' (strategy: {font_load_strategy}, path tried: {actual_path_loaded}): {e}. Falling back to monospace, 16.")
            self.font = pygame.font.SysFont("monospace", 16)
            self.bold_font = pygame.font.SysFont("monospace", 16, bold=True)
            font_to_load = "monospace" # Update for logging
            actual_path_loaded = "Fallback Monospace"

        if self.font:
            char_render_width, _ = self.font.size('X') 
            self.char_width = char_render_width if char_render_width > 0 else 8 # Ensure non-zero
            self.char_height = self.font.get_height() if self.font.get_height() > 0 else 16 # Ensure non-zero
        else: # Should not happen if fallback works
            logger_instance.error("CRITICAL: Font loading failed completely, even fallback. Using hardcoded char dimensions.")
            self.char_width = 8 
            self.char_height = 16
        
        font_name_str = "Unknown Font"
        if self.font:
            try:
                font_name_str = self.font.name # For SysFont
            except AttributeError:
                 if actual_path_loaded != "N/A" and self.font: # For pygame.font.Font
                     font_name_str = os.path.basename(actual_path_loaded) if os.path.exists(actual_path_loaded) else actual_path_loaded
        
        logger_instance.info(f"Font initialization complete. Using: '{font_name_str}' (Loaded from: {actual_path_loaded}). Char dimensions: {self.char_width}x{self.char_height}")

    def render_grid_border(
        self,
        surface,
        grid_cols,
        grid_rows,
        cell_width,
        cell_height,
        width,
        height,
        border_anim_phase=0.0,
        color_single=(120, 120, 120),
        color_double=(200, 80, 80),
        alpha_double=180
    ):
        """
        Render a single/double line border at the grid edges, with breathing overlay.
        """
        import pygame
        for row in range(grid_rows):
            for col in range(grid_cols):
                # For last column/row, align to window edge
                if col == grid_cols - 1:
                    x = width - cell_width
                else:
                    x = col * cell_width
                if row == grid_rows - 1:
                    y = height - cell_height
                else:
                    y = row * cell_height
                # Draw single line border at edges
                border_ch = None
                if row == 0 and col == 0:
                    border_ch = "┌"
                elif row == 0 and col == grid_cols - 1:
                    border_ch = "┐"
                elif row == grid_rows - 1 and col == 0:
                    border_ch = "└"
                elif row == grid_rows - 1 and col == grid_cols - 1:
                    border_ch = "┘"
                elif row == 0 or row == grid_rows - 1:
                    border_ch = "─"
                elif col == 0 or col == grid_cols - 1:
                    border_ch = "│"
                if border_ch:
                    surf = pygame.font.SysFont('monospace', 12).render(border_ch, True, color_single)
                    # For last col/row, right/bottom align the character
                    if col == grid_cols - 1:
                        surf_rect = surf.get_rect(right=x + cell_width, centery=y + cell_height / 2)
                    elif row == grid_rows - 1:
                        surf_rect = surf.get_rect(centerx=x + cell_width / 2, bottom=y + cell_height)
                    else:
                        surf_rect = surf.get_rect(center=(x + cell_width / 2, y + cell_height / 2))
                    surface.blit(surf, surf_rect)
                # Overlay double line border with breathing effect (faster, decoupled)
                double_border_ch = None
                if row == 0 and col == 0:
                    double_border_ch = "╔"
                elif row == 0 and col == grid_cols - 1:
                    double_border_ch = "╗"
                elif row == grid_rows - 1 and col == 0:
                    double_border_ch = "╚"
                elif row == grid_rows - 1 and col == grid_cols - 1:
                    double_border_ch = "╝"
                elif row == 0 or row == grid_rows - 1:
                    double_border_ch = "═"
                elif col == 0 or col == grid_cols - 1:
                    double_border_ch = "║"
                if double_border_ch:
                    import math
                    pulse = 0.5 + 0.5 * math.sin(border_anim_phase * 2.5)
                    overlay_alpha = int(alpha_double * pulse)
                    overlay_font = pygame.font.SysFont('monospace', 12)
                    overlay_surf = overlay_font.render(double_border_ch, True, color_double)
                    overlay_surf.set_alpha(overlay_alpha)
                    if col == grid_cols - 1:
                        overlay_rect = overlay_surf.get_rect(right=x + cell_width, centery=y + cell_height / 2)
                    elif row == grid_rows - 1:
                        overlay_rect = overlay_surf.get_rect(centerx=x + cell_width / 2, bottom=y + cell_height)
                    else:
                        overlay_rect = overlay_surf.get_rect(center=(x + cell_width / 2, y + cell_height / 2))
                    surface.blit(overlay_surf, overlay_rect)

    def render_grid_screen(
        self,
        surface,
        grid,
        grid_cols,
        grid_rows,
        cell_width,
        cell_height,
        width,
        height,
        border_anim_phase=0.0,
        color_single=(120, 120, 120),
        color_double=(200, 80, 80),
        alpha_double=180
    ):
        """
        Render a grid-based terminal screen with border and content.
        """
        # Draw border
        self.render_grid_border(
            surface,
            grid_cols,
            grid_rows,
            cell_width,
            cell_height,
            width,
            height,
            border_anim_phase,
            color_single,
            color_double,
            alpha_double
        )
        # Draw grid content
        import pygame
        for row in range(grid_rows):
            for col in range(grid_cols):
                # For last column/row, align to window edge
                if col == grid_cols - 1:
                    x = width - cell_width
                else:
                    x = col * cell_width
                if row == grid_rows - 1:
                    y = height - cell_height
                else:
                    y = row * cell_height
                cell = grid[row][col]
                if isinstance(cell, tuple):
                    tag, ch = cell
                    if tag == "SKULL":
                        surf = pygame.font.SysFont('monospace', 12).render(ch, True, (200, 0, 0))
                    elif tag == "TEXT":
                        color = (220, 220, 220)
                        surf = pygame.font.SysFont('monospace', 12).render(ch, True, color)
                    elif tag == "PROMPT":
                        color = (255, 255, 255)
                        surf = pygame.font.SysFont('monospace', 12).render(ch, True, color)
                    elif tag == "BLIP":
                        color = (255, 32, 32)
                        surf = pygame.font.SysFont('monospace', 12).render(ch, True, color)
                    elif tag == "TITLE":
                        surf = pygame.font.SysFont('monospace', 12).render(ch, True, (200, 200, 200))
                    elif tag == "ROLE":
                        surf = pygame.font.SysFont('monospace', 12).render(ch, True, (220, 220, 220))
                    elif tag == "DESC":
                        surf = pygame.font.SysFont('monospace', 12).render(ch, True, (150, 150, 150))
                    else:
                        surf = pygame.font.SysFont('monospace', 12).render(ch, True, (120, 120, 120))
                    if col == grid_cols - 1:
                        surf_rect = surf.get_rect(right=x + cell_width, centery=y + cell_height / 2)
                    elif row == grid_rows - 1:
                        surf_rect = surf.get_rect(centerx=x + cell_width / 2, bottom=y + cell_height)
                    else:
                        surf_rect = surf.get_rect(center=(x + cell_width / 2, y + cell_height / 2))
                    surface.blit(surf, surf_rect)

    # --- AI GENERATED: Compatibility stubs for command handlers ---
    def print_info(self, message: str):
        """Stub for compatibility: print informational messages to buffer."""
        self.add_to_buffer(f"[INFO] {message}")

    def print_error(self, message: str):
        """Stub for compatibility: print error messages to buffer."""
        self.add_to_buffer(f"[ERROR] {message}")
    # -------------------------------------------------------------

    def initialize(self, width: int, height: int, font_path: str = None):
        """Initialize the terminal renderer with Pygame."""
        self.width = width
        self.height = height
        self.screen = pygame.Surface((width, height))
        
        # Font initialization is now primarily handled in __init__.
        # This call could be used to re-initialize with a different font if needed,
        # or simply removed if font is set once at construction.
        # For now, let's assume _init_font in __init__ is sufficient.
        # If font_path is provided here, it implies a desire to override.
        if font_path:
             self._init_font(font_name_param=font_path)
        elif not self.font: # If font wasn't loaded in __init__ for some reason
            self._init_font()
        
        if not hasattr(self, 'char_width') or self.char_width <= 0: self.char_width = 8 
        if not hasattr(self, 'char_height') or self.char_height <= 0: self.char_height = 16

    def handle_input(self, event: pygame.event.Event) -> Optional[str]:
        """Handle Pygame input events and return command if Enter is pressed."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                command = self.current_input
                self.current_input = ""
                self.history.append(command)
                self.history_index = -1
                return command
            
            elif event.key == pygame.K_BACKSPACE:
                self.current_input = self.current_input[:-1]
            
            elif event.key == pygame.K_TAB:
                if self.completion_handler:
                    # Get current cursor position
                    cursor_pos = len(self.current_input)
                    # Get suggestions from completion handler
                    new_suggestions, common_prefix = self.completion_handler.get_suggestions(self.current_input, cursor_pos)
                    
                    if common_prefix:
                        # If we have a common prefix, use it
                        self.current_input = common_prefix
                        self.completion_suggestions = [] # Clear old suggestions
                        self.completion_index = -1
                    elif new_suggestions: # Fresh suggestions provided
                        self.completion_suggestions = new_suggestions
                        self.completion_index = 0
                        self.current_input = self.completion_suggestions[self.completion_index]
                    elif self.completion_suggestions: # No new suggestions, but old ones exist - cycle them
                        self.completion_index = (self.completion_index + 1) % len(self.completion_suggestions)
                        self.current_input = self.completion_suggestions[self.completion_index]
                    # If no common_prefix, no new_suggestions, and no existing completion_suggestions, do nothing.
            
            elif event.key == pygame.K_UP:
                if self.history:
                    if self.history_index == -1:
                        self.history_index = len(self.history) - 1
                    else:
                        self.history_index = max(0, self.history_index - 1)
                    self.current_input = self.history[self.history_index]
            
            elif event.key == pygame.K_DOWN:
                if self.history_index != -1:
                    self.history_index = min(len(self.history) - 1, self.history_index + 1)
                    if self.history_index == len(self.history):
                        self.current_input = ""
                        self.history_index = -1
                    else:
                        self.current_input = self.history[self.history_index]
            
            elif event.unicode.isprintable():
                self.current_input += event.unicode
                self.completion_suggestions = []
                self.completion_index = -1
        
        return None

    def render(self, surface: pygame.Surface, effect_manager=None):
        """Render the terminal buffer and input line to the given surface.
        
        Integrates procedural border effects for all UI regions.
        """
        self.logger.debug(f"RENDER CALLED: width={self.width}, height={self.height}, buffer_len={len(self.buffer)}")
        self.logger.debug(f"Buffer contents: {[line.text for line in self.buffer]}")
        self.logger.debug(f"Current input: {self.current_input!r}, Prompt override: {self.prompt_override!r}")
        
        # If width or height is zero, we can't render anything
        if self.width <= 0 or self.height <= 0:
            self.logger.error(f"Cannot render with invalid dimensions: width={self.width}, height={self.height}")
            return

        # Clear the surface
        surface.fill((0, 0, 0))
        
        # Initialize font if not already initialized
        if not hasattr(self, 'font') or self.font is None:
            self.font = pygame.font.Font(None, 16) # Default font
            self.char_width = 8
            self.char_height = 16

        # --- Procedural Borders: Main Output ---
        # Avoid division by zero
        if self.char_width == 0:
            self.char_width = 8
        if self.char_height == 0:
            self.char_height = 16
            
        border_width = self.width // self.char_width
        border_height = (self.height - self.char_height * 3) // self.char_height
        corruption = self.corruption_level
        frame = int(time.time() * 10)
        main_border_lines = self.border_manager.generate_border(
            border_width, border_height, BorderRegion.MAIN_OUTPUT, corruption, frame
        )

        self.logger.debug(f"border_width={border_width}, border_height={border_height}")

        # Render main output border (top)
        for y, border_row in enumerate(main_border_lines):
            self._render_text(surface, border_row, 0, y * self.char_height, TerminalStyle(dim=True))

        # Calculate input line position
        input_y = self.height - self.char_height

        # Render buffer content (inside main border)
        visible_lines = min(len(self.buffer), border_height - 2)
        start_idx = max(0, len(self.buffer) - visible_lines - self.scroll_offset)

        for i in range(visible_lines):
            if start_idx + i < len(self.buffer):
                line = self.buffer[start_idx + i]
                text = line.text
                style = line.style

                # Apply effects if effect_manager is provided
                if effect_manager:
                    text = effect_manager.apply_effects(text, start_idx + i)

                # Render the text inside the border
                y_pos = (i + 1) * self.char_height
                self._render_text(surface, f"{main_border_lines[i+1][0]}{text}{main_border_lines[i+1][-1]}", 0, y_pos, style)

        # --- Procedural Borders: Command Bar ---
        cmd_bar_border_lines = self.border_manager.generate_border(
            border_width, 3, BorderRegion.COMMAND_BAR, corruption, frame
        )
        # Render command bar border (bottom)
        for y, border_row in enumerate(cmd_bar_border_lines):
            y_pos = input_y + (y - 1) * self.char_height
            self._render_text(surface, border_row, 0, y_pos, TerminalStyle(dim=True))

        # Render prompt and current input (inside command bar border)
        prompt = self.prompt_override or "> "
        input_text = prompt + self.current_input

        # Apply corruption effects to input if corrupted
        if self._is_corrupted and effect_manager:
            input_text = effect_manager.apply_effects(input_text, -1)

        # Render input line inside border, with safety checks
        if (
            isinstance(cmd_bar_border_lines, list)
            and len(cmd_bar_border_lines) > 1
            and len(cmd_bar_border_lines[1]) >= 2
        ):
            left = cmd_bar_border_lines[1][0]
            right = cmd_bar_border_lines[1][-1]
        else:
            left = "|"
            right = "|"
        self._render_text(surface, f"{left}{input_text}{right}", 0, input_y, TerminalStyle())

        # Update cursor position based on rendered input
        self.cursor_x = len(input_text) * self.char_width
        self.cursor_y = input_y

        # Render cursor if visible
        if self.cursor_visible and time.time() - self.last_cursor_toggle < self.cursor_blink_time:
            cursor_color = (200, 200, 200) if not self._is_corrupted else (255, 0, 0)
            pygame.draw.rect(surface, cursor_color, 
                           (self.cursor_x, self.cursor_y, 2, self.char_height))

        # --- Procedural Borders: Rusty Panel (bottom left 1/6th) ---
        rusty_width = max(10, border_width // 6)
        rusty_height = max(5, border_height // 3)
        rusty_x = 0
        rusty_y = self.height - rusty_height * self.char_height - self.char_height * 3
        rusty_border_lines = self.border_manager.generate_border(
            rusty_width, rusty_height, BorderRegion.RUSTY_PANEL, corruption, frame
        )
        for y, border_row in enumerate(rusty_border_lines):
            self._render_text(surface, border_row, rusty_x, rusty_y + y * self.char_height, TerminalStyle(dim=True))

        # Render completion suggestions if any (unchanged)
        if self.completion_suggestions:
            # Calculate suggestion box position
            box_x = self.cursor_x
            box_y = input_y - (len(self.completion_suggestions) + 1) * self.char_height

            # Draw suggestion box background
            box_width = max(len(s) for s in self.completion_suggestions) * self.char_width + 10
            box_height = len(self.completion_suggestions) * self.char_height + 4

            # Apply corruption effects to suggestion box
            if self._is_corrupted:
                # Dynamic corruption effects
                corruption_level = getattr(self, 'corruption_level', 0.0)
                box_color = (
                    int(40 + corruption_level * 100),  # R
                    int(corruption_level * 20),        # G
                    int(corruption_level * 20)         # B
                )
                border_color = (
                    int(255 - corruption_level * 100), # R
                    int(corruption_level * 50),        # G
                    int(corruption_level * 50)         # B
                )

                # Add corruption overlay
                if corruption_level > 0.3:
                    overlay = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
                    for _ in range(int(corruption_level * 20)):
                        x = random.randint(0, box_width)
                        y = random.randint(0, box_height)
                        pygame.draw.line(overlay, (255, 0, 0, int(corruption_level * 100)),
                                       (x, y), (x + random.randint(-5, 5), y + random.randint(-5, 5)))
                    surface.blit(overlay, (box_x, box_y))
            else:
                box_color = (20, 20, 20)  # Dark gray for normal state
                border_color = (100, 100, 100)  # Light gray border

            pygame.draw.rect(surface, box_color, (box_x, box_y, box_width, box_height))
            pygame.draw.rect(surface, border_color, (box_x, box_y, box_width, box_height), 1)

            # Render suggestions
            for i, suggestion in enumerate(self.completion_suggestions):
                y_pos = box_y + i * self.char_height + 2

                # Highlight selected suggestion
                if i == self.completion_index:
                    if self._is_corrupted:
                        highlight_color = (
                            int(80 + corruption_level * 100),  # R
                            int(corruption_level * 20),        # G
                            int(corruption_level * 20)         # B
                        )
                    else:
                        highlight_color = (60, 60, 60)
                    pygame.draw.rect(surface, highlight_color, 
                                   (box_x + 2, y_pos, box_width - 4, self.char_height))

                # Apply corruption effects to suggestions
                if self._is_corrupted and effect_manager:
                    # Progressive corruption based on suggestion index
                    corruption_factor = 1.0 + (i * 0.1)  # More corruption for later suggestions
                    suggestion = effect_manager.apply_effects(suggestion, -2 - i, corruption_factor)

                self._render_text(surface, suggestion, box_x + 5, y_pos, TerminalStyle())

        # --- Documentation ---
        # The procedural border system is now integrated for all major UI regions:
        # - Main output (top/side borders)
        # - Command bar (bottom border)
        # - Rusty assistant panel (bottom left)
        # Borders are animated, escalate with corruption, and are modular for future effect layering.

    def add_to_buffer(self, text: str, style: Optional[TerminalStyle] = None):
        """Add text to the buffer with optional styling."""
        if style is None:
            style = TerminalStyle()
        
        # Apply character effects if available
        processed_text = self.apply_character_effects(text)
        
        self.buffer.append(TextLine(processed_text, style))
        if len(self.buffer) > self.max_history:
            self.buffer.pop(0)

    def clear_buffer(self):
        """Clear the terminal buffer."""
        self.logger.debug("clear_buffer called!")
        self.buffer = []

    def set_cursor(self, x: int, y: int):
        """Set cursor position."""
        self.cursor_x = max(0, min(x, self.width - 1))
        self.cursor_y = max(0, min(y, self.height - 1))

    def get_cursor(self) -> Tuple[int, int]:
        """Get current cursor position."""
        return (self.cursor_x, self.cursor_y)
        
    def set_dimensions(self, width: int, height: int):
        """Set the dimensions of the terminal renderer."""
        self.logger.debug(f"Setting terminal dimensions: width={width}, height={height}")
        self.width = max(1, width)  # Ensure width is at least 1
        self.height = max(1, height)  # Ensure height is at least 1

    def set_corruption(self, level: float):
        """Set corruption level."""
        self.corruption_level = max(0.0, min(1.0, level))
        self._is_corrupted = level > 0.0

    def get_corruption(self) -> float:
        """Get current corruption level."""
        return self.corruption_level

    def is_corrupted(self) -> bool:
        """Check if terminal is corrupted."""
        return self._is_corrupted

    def apply_character_effects(self, text: str) -> str:
        """Apply active character-level effects to text."""
        if not self.effect_manager:
            return text
            
        # Apply all active character effects
        processed_text = text
        for effect_name, effect in self.effect_manager.current_effects.items():
            if hasattr(effect, 'apply') and effect.is_active:
                processed_text = effect.apply(processed_text)
                
        return processed_text

    def set_prompt_override(self, prompt: str):
        """Set a custom prompt."""
        self.prompt_override = prompt

    def clear_prompt_override(self):
        """Clear the custom prompt."""
        self.prompt_override = None

    def set_completion_handler(self, handler):
        """Set the completion handler."""
        self.completion_handler = handler

    def set_theme_manager(self, theme_manager):
        """Set the theme manager."""
        self.theme_manager = theme_manager

    def _render_text(self, surface: pygame.Surface, text: str, x: int, y: int, style: TerminalStyle):
        """Render text to the given surface with the specified style."""
        font = self.bold_font if style.bold else self.font
        text_surface = font.render(text, True, style.fg_color)
        surface.blit(text_surface, (x, y))

@dataclass
class TextLine:
    """Represents a line of text in the buffer."""
    text: str
    style: TerminalStyle