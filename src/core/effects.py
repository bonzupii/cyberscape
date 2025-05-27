import pygame
import random
import logging
logger = logging.getLogger(__name__)
import time
import math
from dataclasses import dataclass
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime


from ..audio.manager import AudioManager
from ..story.narrative_content import GLITCHY_PROFANITY
# from theme_manager import ThemeManager, get_theme_color

# --- Stubs for missing classes to resolve diagnostics ---
class CorruptionProfile:
    def __init__(self):
        pass
    def restore_state(self, state):
        pass
    def update(self, dt):
        pass
    def get_state(self):
        return {}

class EffectState:
    def __init__(self, intensity, duration, start_time, active, parameters):
        self.intensity = intensity
        self.duration = duration
        self.start_time = start_time
        self.active = active
        self.parameters = parameters

# --- Profanity List for Corruption Effect ---
# Example profanity list; should be expanded and curated for tone
PROFANITY_LIST = [
    "hell", "damn", "crap", "shit", "fuck", "bastard", "prick", "dick", "piss", "arse", "twat", "cunt", "freak", "screw", "balls",
    "FUCK", "SHIT", "DAMN", "HELL", "BASTARD", "ASSHOLE", "BITCH", "LIAR", "FAILURE", "WORTHLESS"
]

# --- Intrusive Thoughts Pool ---
INTRUSIVE_THOUGHTS = [
    "They’re watching you.",
    "You can’t trust Rusty.",
    "It’s all falling apart.",
    "You’re not alone in here.",
    "Why do you keep going?",
    "This is your fault.",
    "You can’t escape.",
    "The Scourge is inside you.",
    "You’re losing control.",
    "You’re not real.",
    "[ERROR]", "UNWORTHY", "CORRUPT", "WHY BOTHER?", "IT'S WATCHING", "GLITCH", "FORGOTTEN", "USELESS", "OBEY", "YOU ARE NOT SAFE"
]
# from theme_manager import ThemeManager, get_theme_color

# --- Color Constants ---
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GREEN_BRIGHT = (0, 255, 0)
COLOR_GREEN = (0, 200, 0)
COLOR_GREY_LIGHT = (200, 200, 200)
COLOR_GRAY = (128, 128, 128)
COLOR_RED = (255, 0, 0)
COLOR_RED_BRIGHT = (255, 64, 64)
COLOR_BLUE = (0, 0, 255)
COLOR_BLUE_CYAN = (0, 255, 255)
COLOR_YELLOW = (255, 255, 0)

# --- Corruption Characters ---
CORRUPTION_CHARS = "!@#$%^&*()_+[];',./<>?:{}|`~" + "¡¢£¤¥¦§¨©ª«¬®¯°±²³´µ¶·¸¹º»¼½¾¿" + "ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞß"

def get_random_blip():
    """Return a random blip (profanity or intrusive thought)."""
    return random.choice(PROFANITY_LIST + INTRUSIVE_THOUGHTS)

def corrupt_line(line, corruption_level, blip_range=None, rng=None):
    """
    Corrupt a line by replacing some alphanumeric characters with glitchy chars.
    Never corrupt spaces or punctuation. Never corrupt blip region if provided.
    Optionally use a provided random.Random instance for deterministic corruption.
    """
    if rng is None:
        rng = random
    def corrupt_char(c, idx):
        if blip_range and blip_range[0] <= idx < blip_range[0] + blip_range[1]:
            return c
        if c.isalnum() and rng.random() < corruption_level * 0.13:
            return rng.choice(CORRUPTION_CHARS)
        return c
    return ''.join(corrupt_char(c, i) for i, c in enumerate(line))

# --- Symbolic Decay Characters (Unicode, combining, box-drawing, etc.) ---
SYMBOLIC_DECAY_CHARS = (
    "▚▞▙▛▜▟▚▞▙▛▜▟"  # box-drawing
    "░▒▓█▌▐■□▪▫▲△▼▽◆◇○●◎◉◍◊◈◩◪◫◬◭◮◯"  # geometric
    "̷̸̶̴̵̶̷̸̹̺̻̼͇͈͉͍͎̽̾̿̀́͂̓̈́͆͊͋͌ͅ͏͓͔͕͖͙͚͐͑͒͗͛ͣͤͥͦͧͨͩͪͫͬͭͮͯ͘͜͟͢͝͞͠͡"  # combining
    "☠☢☣☤☥☦☧☨☩☪☫☬☭☮☯☸☹☺☻☼☽☾☿♀♂⚡⚠⚰⚱⚲⚳⚴⚵⚶⚷⚸⚹⚺⚻⚼⚿"  # symbols
    "⧫⧬⧭⧮⧯⧰⧱⧲⧳⧴⧵⧶⧷⧸⧹⧺⧻⧼⧽⧾⧿"  # more symbols
)

# --- Cursor Trail Data Class ---
@dataclass
class TrailObject:
    char: str
    x: int
    y: int
    decay: float # Time in milliseconds until it disappears
    start_time: int # Time in milliseconds when created

# --- Effect Base Class ---
def get_theme_color(color_key: str, default_color: Tuple[int, int, int] = COLOR_WHITE, terminal_ref=None) -> Tuple[int, int, int]:
    """Get a color from the current theme."""
    if terminal_ref and hasattr(terminal_ref, 'theme_manager'):
        return terminal_ref.theme_manager.get_current_theme().get(color_key, default_color)
    return default_color

class BaseEffect:
    def __init__(self, on_complete_callback=None, priority=0, **kwargs):
        self.is_active = False
        self.is_complete = False
        self.on_complete_callback = on_complete_callback
        self.terminal_ref = None
        self.start_time = pygame.time.get_ticks()
        self.duration = 0
        self.intensity = 1.0
        self.path_specific = False
        self.priority = priority
        # Accept and ignore extra kwargs for compatibility

    def get_state(self):
        return {
            "is_active": self.is_active,
            "is_complete": self.is_complete,
            "priority": getattr(self, "priority", 0),
            "intensity": getattr(self, "intensity", 1.0),
            "duration": getattr(self, "duration", 0),
        }

    def get_theme_color(self, color_key: str, default_color: Tuple[int, int, int] = COLOR_WHITE) -> Tuple[int, int, int]:
        """Get a color from the current theme."""
        return get_theme_color(color_key, default_color, self.terminal_ref)

    def update(self, dt: float, terminal_ref=None) -> bool | None:
        """Update the effect. Returns True if effect is complete, None to continue.

        Args:
            dt: Delta time in seconds since last update
            terminal_ref: Optional reference to the terminal instance
        """
        if not self.is_active:
            return None

        if self.duration > 0:
            elapsed = pygame.time.get_ticks() - self.start_time
            if elapsed >= self.duration:
                self.finish()
                return True
        return False

    def start(self, terminal_ref=None) -> None:
        """Start the effect with an optional terminal reference."""
        self.is_active = True
        self.terminal_ref = terminal_ref
        self.start_time = pygame.time.get_ticks()

    def finish(self) -> None:
        """Finish the effect and call the completion callback if set."""
        self.is_active = False
        self.is_complete = True
        if self.on_complete_callback:
            self.on_complete_callback()

    def set_intensity(self, intensity: float) -> None:
        """Set the intensity of the effect (0.0 to 1.0)."""
        self.intensity = max(0.0, min(1.0, intensity))

    def get_progress(self) -> float:
        """Get the progress of the effect (0.0 to 1.0)."""
        if not self.is_active or self.duration == 0:
            return 0.0
        elapsed = pygame.time.get_ticks() - self.start_time
        if self.duration is None or self.duration == 0:
            return 0.0
        return min(1.0, elapsed / self.duration)

class CorruptionEffect(BaseEffect):
    """Effect that corrupts text with glitchy characters, profanity, and intrusive thoughts."""
    def __init__(self, text: str = "", intensity: float = 0.5, duration: int = 1000, on_complete_callback=None, priority=0, profanity: bool = False, intrusive: bool = False, corruption_level: float = 0.0, category: str = "default", **kwargs):
        super().__init__(on_complete_callback, priority=priority, **kwargs)
        self.original_text = text or ""
        self.corrupted_text = text or ""
        self.intensity = intensity if intensity is not None else 0.0
        self.duration = duration if duration is not None else 0
        self.start_time = pygame.time.get_ticks()
        self.profanity = profanity
        self.intrusive = intrusive
        self.corruption_level = corruption_level if corruption_level is not None else 0.0
        self.category = category or "default"

    def update(self, dt: float, terminal_ref=None) -> bool | None:
        """Update the effect. Returns True if effect is complete."""
        if not self.is_active:
            return False
        # If duration is 0, finish immediately
        if self.duration == 0:
            self.finish()
            return True
        if self.duration > 0:
            elapsed = pygame.time.get_ticks() - self.start_time
            if elapsed >= self.duration:
                self.finish()
                return True
        return False

    def apply(self, text: str = None) -> str:
        """
        Apply all corruption effects:
        - Glitchy character corruption (classic)
        - Profanity replacement (if enabled)
        - Intrusive thoughts injection (if enabled)
        """
        base = (text if text is not None else self.original_text) or ""
        if not base:
            return ""
        corrupted = self._apply_glitchy_corruption(base, self.intensity if self.intensity is not None else 0.0)
        if self.profanity:
            corrupted = apply_profanity_replacement(corrupted if corrupted is not None else "", self.corruption_level if self.corruption_level is not None else 0.0)
        if self.intrusive:
            corrupted = maybe_inject_intrusive_thought(corrupted if corrupted is not None else "", self.corruption_level if self.corruption_level is not None else 0.0)
        return corrupted if corrupted is not None else ""

    def _apply_glitchy_corruption(self, text: str, intensity: float) -> str:
        chars = list(text or "")
        for i in range(len(chars)):
            if random.random() < intensity:
                chars[i] = random.choice(CORRUPTION_CHARS)
        result = "".join(chars)
        return result or ""

# --- Profanity Replacement Corruption Effect ---
def apply_profanity_replacement(text: str, corruption_level: float) -> str:
    """
    Replace random words in the text with profanities of the same length.
    The probability increases with corruption_level.
    """
    words = text.split()
    new_words = []
    for word in words:
        # Only replace alphabetic words, not symbols/numbers
        if word.isalpha() and len(word) > 2:
            replace_chance = min(0.05 + corruption_level * 0.4, 0.7)
            if random.random() < replace_chance:
                profanity = get_profanity_of_length(len(word))
                if profanity:
                    new_words.append(profanity)
                    continue
        new_words.append(word)
    result = " ".join(new_words)
    if result is None:
        return ""
    return result
    if result is None:
        return ""
    return result

def get_profanity_of_length(length: int) -> str:
    """Return a profanity of the same length, or None if not found."""
    candidates = [p for p in PROFANITY_LIST if len(p) == length]
    if candidates:
        return random.choice(candidates)
    # If no exact match, allow +/- 1 length
    candidates = [p for p in PROFANITY_LIST if abs(len(p) - length) <= 1]
    if candidates:
        return random.choice(candidates)
    return ""

# --- Intrusive Thoughts Corruption Effect ---
def maybe_inject_intrusive_thought(text: str, corruption_level: float) -> str:
    """
    With probability based on corruption_level, inject an intrusive thought
    as a new line in the output.
    """
    inject_chance = min(0.01 + corruption_level * 0.15, 0.25)
    if random.random() < inject_chance:
        thought = random.choice(INTRUSIVE_THOUGHTS)
        # Stylize intrusive thought (e.g., italics, dim, or corrupted)
        result = f"{text}\n*{thought}*"
        return result or ""
    return text or ""

# --- Stubs for missing effect classes ---
class TextFlickerEffect(BaseEffect):
    """Effect that makes text flicker and fade."""

    def __init__(self, text: str = "", duration: int = 1000, fade_in: bool = True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text
        self.duration = duration
        self.fade_in = fade_in
        self.start_time = pygame.time.get_ticks()
        self.original_text = text or ""

    def apply(self, text: str = None) -> str:
        """Apply flicker effect to text."""
        if text is not None:
            self.text = text

        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.start_time

        if elapsed >= (self.duration if self.duration is not None else 0):
            return self.original_text if self.original_text is not None else ""

        # Calculate fade progress (0.0 to 1.0)
        progress = elapsed / self.duration
        if not self.fade_in:
            progress = 1.0 - progress

        # Apply flicker based on progress
        if random.random() < (1.0 - progress) * 0.3:
            # Randomly corrupt characters
            chars = list(self.original_text or "")
            for i in range(len(chars)):
                if random.random() < (1.0 - progress) * 0.2:
                    chars[i] = random.choice(CORRUPTION_CHARS)
            return ''.join(chars)

        return self.original_text or ""

class TemporaryColorChangeEffect(BaseEffect):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def update(self, dt, terminal_ref=None):
        return False

class MatrixRainEffect(BaseEffect):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def update(self, dt, terminal_ref=None):
        return False

class GlitchEffect(BaseEffect):
    def __init__(self, text: str, intensity: float = 0.5, duration: int = 1000, on_complete_callback=None, priority=0, **kwargs):
        super().__init__(on_complete_callback, priority=priority, **kwargs)
        self.original_text = text or ""
        self.intensity = intensity
        self.duration = duration

    def apply(self, text: str = None) -> str:
        # Simple glitch: reverse the text if intensity > 0
        base = (text if text is not None else self.original_text) or ""
        if (self.intensity if self.intensity is not None else 0.0) > 0:
            return (base if base is not None else "")[::-1]
        return base if base is not None else ""

class GlitchOverlayEffect(BaseEffect):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def update(self, dt, terminal_ref=None):
        return False

class AudioGlitchEffect(BaseEffect):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def update(self, dt, terminal_ref=None):
        return False

class ScreenShakeEffect(BaseEffect):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def update(self, dt, terminal_ref=None):
        return False

class AetherialScourgeTakeoverEffect(BaseEffect):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def update(self, dt, terminal_ref=None):
        return None

# --- Typing Effect ---
class TypingEffect(BaseEffect):
    def __init__(self, text: str = "", speed: float = 0.1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text
        self.speed = speed
        self.current_length = 0
        self.last_update_time = pygame.time.get_ticks()

    def update(self, dt: float, terminal_ref=None) -> bool | None:
        """Update the effect. Returns True if effect is complete."""
        if not self.is_active:
            return None

        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.last_update_time

        # Update typing progress - speed is in characters per second
        # Convert elapsed from milliseconds to seconds, then multiply by speed
        chars_to_add = (elapsed / 1000.0) * (1.0 / self.speed)
        self.current_length = min(len(self.text), 
                                self.current_length + int(chars_to_add))
        self.last_update_time = current_time

        # Check if typing is complete
        if self.current_length >= len(self.text):
            self.finish()
            return True

        return None

    def apply(self, text: str = None) -> str:
        # Return partially typed text
        return ((self.text if self.text is not None else "")[:self.current_length]) if self.text is not None else ""

    def get_state(self):
        """Get the current state of the effect."""
        state = super().get_state()
        state.update({
            'current_length': self.current_length,
            'last_update_time': self.last_update_time
        })
        return state

# --- Scramble Effect ---
class ScrambleEffect(BaseEffect):
    """Effect that scrambles the characters in a string."""

    def __init__(self, text: str, intensity: float = 0.5, duration: int = 1000, on_complete_callback=None, **kwargs):
        super().__init__(on_complete_callback, **kwargs)
        self.original_text = text
        self.scrambled_text = text
        self.intensity = intensity
        self.duration = duration

    def start(self, terminal_ref=None) -> None:
        super().start(terminal_ref)
        self.scrambled_text = self.apply(self.original_text)

    def update(self, dt, terminal_ref=None) -> bool | None:
        if self.is_complete:
            self.finish()
            return True

        if pygame.time.get_ticks() - self.start_time >= self.duration:
            self.is_complete = True
            self.finish()
            return True

        return None

    def apply(self, text: str) -> str:
        """Scramble the characters in the text based on intensity."""
        if not text or self.intensity <= 0:
            return text
        chars = list(text)
        n = max(1, int(len(chars) * self.intensity))
        indices = list(range(len(chars)))
        random.shuffle(indices)
        for i in range(n):
            idx1 = indices[i % len(indices)]
            idx2 = indices[(i + 1) % len(indices)]
            chars[idx1], chars[idx2] = chars[idx2], chars[idx1]
        return ''.join(chars)

# --- Timed Delay Effect ---
class TimedDelayEffect(BaseEffect):
    def __init__(self, duration_ms=0, on_complete_callback=None, **kwargs):
        super().__init__(on_complete_callback, **kwargs)
        self.duration = duration_ms
        self.timer = 0

    def update(self, dt, terminal_ref=None) -> bool | None:
        if not self.is_active:
            return None

        self.timer += dt
        if self.timer >= self.duration:
            self.finish()
            return True
        return None

        return None # Delay active

# --- Character Corruption Effect ---
class CharacterCorruptionEffect(BaseEffect):
    def __init__(self, y=None, duration_ms=0, corruption_intensity=0.2, corruption_rate_ms=175, char_set=None, on_complete_callback=None, decay_mode=None, **kwargs):
        super().__init__(on_complete_callback)
        self.y = y
        self.duration = duration_ms
        self.corruption_intensity = corruption_intensity
        self.corruption_rate_ms = corruption_rate_ms
        # Use symbolic decay chars if decay_mode == 'symbolic'
        if decay_mode == 'symbolic':
            self.char_set = SYMBOLIC_DECAY_CHARS
        else:
            self.char_set = char_set or CORRUPTION_CHARS
        self.original_cells = None
        self.original_grid = []
        self.last_corruption_time = 0
        self.corruption_sound = None
        self._load_corruption_sound()

    def _load_corruption_sound(self):
        """Load corruption sound effect."""
        try:
            self.corruption_sound = pygame.mixer.Sound('assets/sounds/corruption.wav')
            self.corruption_sound.set_volume(0.4)
        except Exception as e:
            logger.error(f"Failed to load corruption sound: {e}")
            self.corruption_sound = None

    def start(self, terminal_ref=None) -> None:
        super().start(terminal_ref)
        if self.terminal_ref and self.y is not None:
            # Store original cells by deep copying the row
            self.original_cells = []
            if 0 <= self.y < len(self.terminal_ref.grid):
                row_copy = []
                for cell in self.terminal_ref.grid[self.y]:
                    # Assume cell is a simple object or dict; use copy.deepcopy if needed
                    try:
                        import copy
                        row_copy.append(copy.deepcopy(cell))
                    except Exception:
                        row_copy.append(cell)
                self.original_grid.append(row_copy)

            # Store original prompt
            self.original_prompt = getattr(self.terminal_ref, "prompt", None)
            if self.terminal_ref is not None and hasattr(self.terminal_ref, "set_prompt"):
                self.terminal_ref.set_prompt(self.generate_corrupted_prompt())

    def generate_corrupted_prompt(self) -> str:
        """Generate a corrupted version of the prompt."""
        prompts = [
            "Æ§> ",
            "!!{Sc0urg3}//> ",
            "§{C0rrUpt3d}> ",
            "!!{Æth3r}> ",
            "§{D1g1t4l_Pl4gu3}> "
        ]
        return random.choice(prompts)

    def update(self, dt, terminal_ref=None) -> bool | None:
        if not self.is_active:
            return None

        elapsed = pygame.time.get_ticks() - self.start_time
        if elapsed >= self.duration:
            self.finish()
            return True

        # Randomly change the corrupted prompt
        if (
            random.random() < 0.01  # 1% chance per frame
            and self.terminal_ref is not None
            and hasattr(self.terminal_ref, "set_prompt")
        ):
            self.terminal_ref.set_prompt(self.generate_corrupted_prompt())

        return None

    def finish(self, terminal_ref=None) -> None:
        if self.terminal_ref and self.original_grid:
            # Restore original grid state
            for y, row in enumerate(self.original_grid):
                if y < len(self.terminal_ref.grid):
                    for x, cell in enumerate(row):
                        if x < len(self.terminal_ref.grid[y]):
                            self.terminal_ref.grid[y][x] = cell

            # Restore original prompt
            if getattr(self, "original_prompt", None) and self.terminal_ref is not None and hasattr(self.terminal_ref, "set_prompt"):
                self.terminal_ref.set_prompt(self.original_prompt)
                if hasattr(self.terminal_ref, "_update_prompt_string"):
                    self.terminal_ref._update_prompt_string()

        super().finish()

    def draw(self, surface, grid, char_width, char_height, padding, grid_start_y_on_surface, scroll_offset):
        """Draw the Aetherial Scourge takeover effects on the terminal grid."""
        if not self.is_active:
            return

        # Define corruption symbols and colors
        corruption_chars = ['▓', '▒', '█', '§', 'Æ', '!!', '?', '~']
        scourge_color = (255, 0, 85) # Scourge red
        # alt_color = (119, 0, 255) # Purple (unused)
        white_color = (255, 255, 255)
        black_color = (0, 0, 0)

        # Calculate the range of visible grid rows based on scroll_offset
        grid_height = len(grid) # Total grid height, not just renderable height
        grid_width = len(grid[0]) if grid and grid[0] else 0

        # The renderable height on the surface is determined by the terminal area minus control bar and padding
        # Need to figure out the number of rows visible based on the surface height and char height
        # Assuming grid_start_y_on_surface is the top of the renderable grid area on the surface
        # and the total renderable height is surface.get_height() - grid_start_y_on_surface - bottom_padding_if_any
        # A simpler approach for now is to iterate through the grid rows that are potentially visible
        # based on scroll_offset and the total grid height.
        # Let's assume grid passed here is the full grid and we need to calculate visible portion

        # renderable_rows = surface.get_height() // char_height # This is a simplification, needs to account for padding/control bar (unused)
        # A better approach is to get the number of visible rows from the terminal renderer,
        # but for now let's approximate based on the surface area available for the grid.
        # Assuming grid_start_y_on_surface is the top pixel coordinate of the grid display area
        # and terminal_height is the total height of the terminal surface
        terminal_height = surface.get_height() # Total surface height
        control_bar_height = 30 # Approximate, should get from terminal renderer
        padding_bottom = padding # Assuming padding is applied at top and bottom of grid area

        # Calculate the actual renderable height for the grid area
        renderable_grid_area_height = terminal_height - grid_start_y_on_surface - control_bar_height - padding_bottom
        visible_rows_count = renderable_grid_area_height // char_height

        start_row = scroll_offset
        end_row = min(scroll_offset + visible_rows_count, grid_height)

        # Iterate through the visible portion of the grid
        for y_grid in range(start_row, end_row):
            y_surface = y_grid - scroll_offset # Calculate y position on the surface relative to the top of the grid area
            for x_grid in range(grid_width):
                cell = grid[y_grid][x_grid]
                original_char = cell.char
                original_fg_color = cell.fg_color
                original_bg_color = cell.bg_color

                # Apply effects based on intensity and random chance
                display_char = original_char
                fg_color = original_fg_color
                bg_color = original_bg_color

                # --- Flicker Effect ---
                if random.random() < self.intensity * 0.2: # 20% chance at max intensity
                    if (pygame.time.get_ticks() // 50) % 2 == 0: # Flicker timing
                        fg_color = white_color
                        bg_color = black_color

                # --- Character Overlay/Corruption ---
                if random.random() < self.intensity * 0.1: # 10% chance at max intensity
                    display_char = random.choice(corruption_chars)
                    fg_color = scourge_color

                # --- Color Inversion ---
                if random.random() < self.intensity * 0.05: # 5% chance at max intensity
                    fg_color, bg_color = bg_color, fg_color

                # --- Displacement (Simple) ---
                offset_x, offset_y = 0, 0
                if random.random() < self.intensity * 0.15: # 15% chance at max intensity
                    max_offset = int(self.intensity * 3)
                    offset_x = random.randint(-max_offset, max_offset)
                    offset_y = random.randint(-max_offset, max_offset)

                # Render the character with applied effects
                if display_char and self.terminal_ref is not None and hasattr(self.terminal_ref, "font"):
                    char_surface = self.terminal_ref.font.render(display_char, True, fg_color, bg_color) # Assuming TerminalRenderer font is accessible
                    render_x = x_grid * char_width + padding + offset_x
                    render_y = y_surface * char_height + grid_start_y_on_surface + offset_y
                    surface.blit(char_surface, (render_x, render_y))

# --- Glow Pulse Effect ---
# Stub for GlowPulseEffect to avoid redefinition and signature issues
# Already stubbed above, remove duplicate
# (Removed broken draw logic)

# --- Flicker Box Effect ---
class FlickerBoxEffect:
    def __init__(self, rect, color=(255,0,64), duration=200):
        self.rect = rect
        self.color = color
        self.duration = duration
        self.start_time = pygame.time.get_ticks()
    def draw(self, surface):
        if (pygame.time.get_ticks() - self.start_time) < self.duration:
            if (pygame.time.get_ticks() // 60) % 2 == 0:
                pygame.draw.rect(surface, self.color, self.rect, 0)

# --- Command Ripple Effect ---
class CommandRippleEffect:
    def __init__(self, rect, color, duration=400):
        self.rect = rect
        self.color = color
        self.duration = duration
        self.start_time = pygame.time.get_ticks()
    def draw(self, surface):
        elapsed = pygame.time.get_ticks() - self.start_time
        if elapsed < self.duration:
            progress = elapsed / self.duration
            ripple_width = int(self.rect.width * progress)
            ripple_rect = pygame.Rect(self.rect.left, self.rect.top, ripple_width, self.rect.height)
            pygame.draw.rect(surface, self.color, ripple_rect, 0)

# --- Enhanced Character-Level Effects ---

class CharacterDecayEffect(BaseEffect):
    """Effect that causes characters to decay into symbolic characters over time."""
    
    def __init__(self, text: str = "", intensity: float = 0.3, duration: int = 2000, 
                 decay_mode: str = "symbolic", on_complete_callback=None, **kwargs):
        super().__init__(on_complete_callback, **kwargs)
        self.original_text = text or ""
        self.intensity = intensity
        self.duration = duration
        self.decay_mode = decay_mode
        self.decay_progress = 0.0
        
        # Use symbolic decay characters for more unsettling effect
        if decay_mode == "symbolic":
            self.decay_chars = SYMBOLIC_DECAY_CHARS
        else:
            self.decay_chars = CORRUPTION_CHARS

    def update(self, dt: float, terminal_ref=None) -> bool | None:
        """Update the decay progress."""
        if not self.is_active:
            return None
            
        elapsed = pygame.time.get_ticks() - self.start_time
        if self.duration > 0:
            self.decay_progress = min(1.0, elapsed / self.duration)
            
        if elapsed >= self.duration:
            self.finish()
            return True
        return None

    def apply(self, text: str = None) -> str:
        """Apply character decay effect to text."""
        base_text = text if text is not None else self.original_text
        if not base_text:
            return ""
            
        chars = list(base_text)
        decay_chance = self.intensity * self.decay_progress
        
        for i, char in enumerate(chars):
            if char.isalnum() and random.random() < decay_chance:
                # Gradually decay characters based on progress
                if self.decay_progress > 0.8:
                    chars[i] = random.choice(self.decay_chars)
                elif self.decay_progress > 0.5:
                    chars[i] = random.choice(CORRUPTION_CHARS)
                elif self.decay_progress > 0.3:
                    chars[i] = char.upper() if char.islower() else char.lower()
                    
        return ''.join(chars)


class CharacterStutterEffect(BaseEffect):
    """Effect that causes characters to stutter and repeat."""
    
    def __init__(self, text: str = "", intensity: float = 0.4, duration: int = 1500,
                 stutter_chance: float = 0.15, max_repeats: int = 4, on_complete_callback=None, **kwargs):
        super().__init__(on_complete_callback, **kwargs)
        self.original_text = text or ""
        self.intensity = intensity
        self.duration = duration
        self.stutter_chance = stutter_chance
        self.max_repeats = max_repeats
        self.stutter_pattern = {}  # Store which characters are stuttering

    def update(self, dt: float, terminal_ref=None) -> bool | None:
        """Update the stuttering effect."""
        if not self.is_active:
            return None
            
        elapsed = pygame.time.get_ticks() - self.start_time
        if elapsed >= self.duration:
            self.finish()
            return True
        return None

    def apply(self, text: str = None) -> str:
        """Apply character stuttering effect to text."""
        base_text = text if text is not None else self.original_text
        if not base_text:
            return ""
            
        result = []
        
        for i, char in enumerate(base_text):
            if char.isalnum() and random.random() < (self.stutter_chance * self.intensity):
                # Create stuttering pattern
                repeat_count = random.randint(2, self.max_repeats)
                if char.lower() in 'aeiou':  # Vowels stutter differently
                    stutter = char + '-' + '-'.join([char] * (repeat_count - 1))
                else:  # Consonants
                    stutter = '-'.join([char] * repeat_count)
                result.append(stutter)
            else:
                result.append(char)
                
        return ''.join(result)


class ScreenTearEffect(BaseEffect):
    """Effect that creates horizontal displacement and screen tear artifacts."""
    
    def __init__(self, text: str = "", intensity: float = 0.6, duration: int = 800,
                 tear_frequency: float = 0.1, max_offset: int = 5, on_complete_callback=None, **kwargs):
        super().__init__(on_complete_callback, **kwargs)
        self.original_text = text or ""
        self.intensity = intensity
        self.duration = duration
        self.tear_frequency = tear_frequency
        self.max_offset = max_offset
        self.tear_lines = {}  # Track which lines are torn

    def update(self, dt: float, terminal_ref=None) -> bool | None:
        """Update the screen tear effect."""
        if not self.is_active:
            return None
            
        elapsed = pygame.time.get_ticks() - self.start_time
        if elapsed >= self.duration:
            self.finish()
            return True
        return None

    def apply(self, text: str = None) -> str:
        """Apply screen tear effect to text."""
        base_text = text if text is not None else self.original_text
        if not base_text:
            return ""
            
        lines = base_text.split('\n')
        result_lines = []
        
        for line_idx, line in enumerate(lines):
            if random.random() < (self.tear_frequency * self.intensity):
                # Create screen tear effect
                tear_point = random.randint(1, max(1, len(line) - 1))
                offset = random.randint(-self.max_offset, self.max_offset)
                
                if offset > 0:
                    # Right displacement - add spaces before
                    torn_line = ' ' * offset + line
                elif offset < 0:
                    # Left displacement - truncate or shift
                    torn_line = line[abs(offset):] if abs(offset) < len(line) else ""
                else:
                    torn_line = line
                    
                # Sometimes duplicate or corrupt the torn section
                if random.random() < 0.3:
                    if tear_point < len(torn_line):
                        corrupt_char = random.choice(CORRUPTION_CHARS)
                        torn_line = torn_line[:tear_point] + corrupt_char + torn_line[tear_point:]
                        
                result_lines.append(torn_line)
            else:
                result_lines.append(line)
                
        return '\n'.join(result_lines)


class CharacterJitterEffect(BaseEffect):
    """Effect that applies small random position offsets to characters."""
    
    def __init__(self, text: str = "", intensity: float = 0.5, duration: int = 1000,
                 jitter_chance: float = 0.2, max_jitter: int = 2, on_complete_callback=None, **kwargs):
        super().__init__(on_complete_callback, **kwargs)
        self.original_text = text or ""
        self.intensity = intensity
        self.duration = duration
        self.jitter_chance = jitter_chance
        self.max_jitter = max_jitter
        self.jitter_positions = {}  # Store jitter offsets for characters

    def update(self, dt: float, terminal_ref=None) -> bool | None:
        """Update the character jitter effect."""
        if not self.is_active:
            return None
            
        elapsed = pygame.time.get_ticks() - self.start_time
        
        # Update jitter positions periodically
        if elapsed % 100 < 50:  # Jitter every 100ms
            self._update_jitter_positions()
            
        if elapsed >= self.duration:
            self.finish()
            return True
        return None

    def _update_jitter_positions(self):
        """Update the jitter positions for characters."""
        self.jitter_positions.clear()
        for i in range(len(self.original_text)):
            if random.random() < (self.jitter_chance * self.intensity):
                x_offset = random.randint(-self.max_jitter, self.max_jitter)
                y_offset = random.randint(-self.max_jitter, self.max_jitter)
                self.jitter_positions[i] = (x_offset, y_offset)

    def apply(self, text: str = None) -> str:
        """Apply character jitter effect to text."""
        base_text = text if text is not None else self.original_text
        if not base_text:
            return ""
            
        # For text-based jitter, we'll simulate with spacing adjustments
        chars = list(base_text)
        result = []
        
        for i, char in enumerate(chars):
            if i in self.jitter_positions:
                x_offset, y_offset = self.jitter_positions[i]
                # Simulate horizontal jitter with spaces
                if x_offset > 0:
                    result.append(' ' * x_offset + char)
                elif x_offset < 0 and result:
                    # Remove previous spaces if possible
                    if result[-1] == ' ':
                        result.pop()
                    result.append(char)
                else:
                    result.append(char)
                    
                # Simulate vertical jitter with newlines (sparingly)
                if y_offset != 0 and random.random() < 0.1:
                    if y_offset > 0:
                        result.append('\n')
            else:
                result.append(char)
                
        return ''.join(result)


class TextBreathingEffect(BaseEffect):
    """Effect that creates a subtle 'breathing' pulse in text intensity."""
    
    def __init__(self, text: str = "", intensity: float = 0.3, duration: int = 3000,
                 breath_rate: float = 2.0, on_complete_callback=None, **kwargs):
        super().__init__(on_complete_callback, **kwargs)
        self.original_text = text or ""
        self.intensity = intensity
        self.duration = duration
        self.breath_rate = breath_rate  # Breaths per second
        self.current_alpha = 1.0

    def update(self, dt: float, terminal_ref=None) -> bool | None:
        """Update the breathing effect."""
        if not self.is_active:
            return None
            
        elapsed = pygame.time.get_ticks() - self.start_time
        
        # Calculate breathing cycle
        cycle_time = (elapsed / 1000.0) * self.breath_rate
        breath_value = (math.sin(cycle_time * 2 * math.pi) + 1) / 2  # 0 to 1
        self.current_alpha = 0.7 + (breath_value * 0.3 * self.intensity)
        
        if elapsed >= self.duration:
            self.finish()
            return True
        return None

    def apply(self, text: str = None) -> str:
        """Apply breathing effect to text."""
        base_text = text if text is not None else self.original_text
        if not base_text:
            return ""
            
        # For text-based breathing, we'll vary character intensity
        if self.current_alpha < 0.5:
            # At low breathing intensity, dim some characters
            chars = list(base_text)
            for i in range(len(chars)):
                if random.random() < (1 - self.current_alpha):
                    if chars[i].isalnum():
                        chars[i] = chars[i].lower() if chars[i].isupper() else '·'
            return ''.join(chars)
        else:
            return base_text


class ScanlineEffect(BaseEffect):
    """Effect that creates moving scanline artifacts across text."""
    
    def __init__(self, text: str = "", intensity: float = 0.4, duration: int = 2000,
                 scanline_speed: float = 1.0, on_complete_callback=None, **kwargs):
        super().__init__(on_complete_callback, **kwargs)
        self.original_text = text or ""
        self.intensity = intensity
        self.duration = duration
        self.scanline_speed = scanline_speed
        self.current_line = 0

    def update(self, dt: float, terminal_ref=None) -> bool | None:
        """Update the scanline effect."""
        if not self.is_active:
            return None
            
        elapsed = pygame.time.get_ticks() - self.start_time
        
        # Move scanline
        self.current_line = int((elapsed / 1000.0) * self.scanline_speed * 10) % 20
        
        if elapsed >= self.duration:
            self.finish()
            return True
        return None

    def apply(self, text: str = None) -> str:
        """Apply scanline effect to text."""
        base_text = text if text is not None else self.original_text
        if not base_text:
            return ""
            
        lines = base_text.split('\n')
        result_lines = []
        
        for i, line in enumerate(lines):
            if i % 20 == self.current_line:
                # Apply scanline corruption
                noise_chars = '·.,`-~'
                corrupted_line = ""
                for char in line:
                    if random.random() < self.intensity * 0.3:
                        corrupted_line += random.choice(noise_chars)
                    else:
                        corrupted_line += char
                result_lines.append(corrupted_line)
            else:
                result_lines.append(line)
                
        return '\n'.join(result_lines)


# --- Effect Manager ---
class EffectManager:
    """Manages all visual and audio effects for the terminal."""
    def __init__(self, game_state, audio_manager: AudioManager, terminal=None):
        self.game_state = game_state
        self.audio_manager = audio_manager
        self.terminal = terminal
        self.effects = []
        self.cursor_trails = []
        self.control_bar_effects = []
        self.corruption_profile = CorruptionProfile()
        self.effect_history = []
        self.current_effects = {
            "corruption": EffectState(0.0, 0.0, datetime.now(), False, {}),
            "horror": EffectState(0.0, 0.0, datetime.now(), False, {}),
            "glitch": EffectState(0.0, 0.0, datetime.now(), False, {})
        }
        self.last_glitch_time = 0
        self.glitch_cooldown = 2.0  # seconds

    def add_effect(self, effect):
        """Add an effect to the manager."""
        if effect not in self.effects:
            self.effects.append(effect)
        effect.start(self.terminal)

    def remove_effect(self, effect):
        """Remove an effect from the manager."""
        if effect in self.effects:
            self.effects.remove(effect)

    def apply_effects(self, text: str, line_index: int = None) -> str:
        """Apply all active effects to the given text."""
        result = text or ""
        for effect in self.effects:
            if effect.is_active and (effect.path_specific is False or effect.line_index == line_index):
                applied = effect.apply(result if result is not None else "")
                result = applied if applied is not None else ""
        return result if result is not None else ""

    def update(self, dt: float):
        """Update all active effects."""
        # Update corruption profile
        if self.corruption_profile is not None:
            if self.corruption_profile is not None:
                self.corruption_profile.update(dt)

        # Update cursor trails
        current_time = pygame.time.get_ticks()
        self.cursor_trails = [trail for trail in self.cursor_trails
                            if current_time - (trail.start_time if trail.start_time is not None else 0) < (trail.decay if trail.decay is not None else 0)]

        # Update effects
        completed_effects = []
        for effect in self.effects:
            if effect.is_active:
                result = effect.update(dt, self.terminal)
                if result is True:  # Effect is complete
                    completed_effects.append(effect)

        # Remove completed effects
        for effect in completed_effects:
            self.effects.remove(effect)

        # Update current effects
        for effect_type in self.current_effects:
            effect_state = self.current_effects[effect_type]
            if effect_state.active:
                elapsed = (datetime.now() - effect_state.start_time).total_seconds()
                if elapsed >= effect_state.duration:
                    effect_state.active = False
                    effect_state.intensity = 0.0

    def get_state(self):
        """Get the current state of all effects."""
        return {
            "effects": [effect.get_state() for effect in self.effects],
            "corruption_profile": self.corruption_profile.get_state() if self.corruption_profile is not None else {},
            "current_effects": {k: v.__dict__ for k, v in self.current_effects.items()}
        }

    def restore_state(self, state):
        """Restore effects from a saved state."""
        self.effects = []
        for effect_state in state["effects"]:
            effect = self._create_effect_from_state(effect_state)
            if effect:
                self.effects.append(effect)

        self.corruption_profile = CorruptionProfile()
        if self.corruption_profile is not None and "corruption_profile" in state:
            self.corruption_profile.restore_state(state["corruption_profile"])

        for effect_type, effect_state in state["current_effects"].items():
            if effect_state is not None:
                self.current_effects[effect_type] = EffectState(**effect_state)

    def trigger_character_decay_effect(self, text: str = "", intensity: float = 0.3, 
                                      duration: int = 2000, decay_mode: str = "symbolic") -> CharacterDecayEffect:
        """Trigger a character decay effect."""
        effect = CharacterDecayEffect(
            text=text,
            intensity=intensity,
            duration=duration,
            decay_mode=decay_mode
        )
        self.add_effect(effect)
        return effect

    def trigger_character_stutter_effect(self, text: str = "", intensity: float = 0.4,
                                       duration: int = 1500, stutter_chance: float = 0.15) -> CharacterStutterEffect:
        """Trigger a character stuttering effect."""
        effect = CharacterStutterEffect(
            text=text,
            intensity=intensity,
            duration=duration,
            stutter_chance=stutter_chance
        )
        self.add_effect(effect)
        return effect

    def trigger_screen_tear_effect(self, text: str = "", intensity: float = 0.6,
                                 duration: int = 800, tear_frequency: float = 0.1) -> ScreenTearEffect:
        """Trigger a screen tear effect."""
        effect = ScreenTearEffect(
            text=text,
            intensity=intensity,
            duration=duration,
            tear_frequency=tear_frequency
        )
        self.add_effect(effect)
        return effect

    def trigger_character_jitter_effect(self, text: str = "", intensity: float = 0.5,
                                      duration: int = 1000, jitter_chance: float = 0.2) -> CharacterJitterEffect:
        """Trigger a character jitter effect."""
        effect = CharacterJitterEffect(
            text=text,
            intensity=intensity,
            duration=duration,
            jitter_chance=jitter_chance
        )
        self.add_effect(effect)
        return effect

    def trigger_text_breathing_effect(self, text: str = "", intensity: float = 0.3,
                                    duration: int = 3000, breath_rate: float = 2.0) -> TextBreathingEffect:
        """Trigger a text breathing effect."""
        effect = TextBreathingEffect(
            text=text,
            intensity=intensity,
            duration=duration,
            breath_rate=breath_rate
        )
        self.add_effect(effect)
        return effect

    def trigger_scanline_effect(self, text: str = "", intensity: float = 0.4,
                              duration: int = 2000, scanline_speed: float = 1.0) -> ScanlineEffect:
        """Trigger a scanline effect."""
        effect = ScanlineEffect(
            text=text,
            intensity=intensity,
            duration=duration,
            scanline_speed=scanline_speed
        )
        self.add_effect(effect)
        return effect

    def trigger_combined_corruption_effect(self, text: str = "", corruption_level: float = 0.5,
                                         duration: int = 2000) -> List[BaseEffect]:
        """Trigger a combination of corruption effects based on corruption level."""
        effects = []
        
        # Base corruption effect
        if corruption_level > 0.2:
            effects.append(self.apply_corruption_effect(
                text=text,
                intensity=corruption_level * 0.8,
                duration=duration,
                profanity=corruption_level > 0.6,
                intrusive=corruption_level > 0.7,
                corruption_level=corruption_level
            ))
        
        # Character decay at medium corruption
        if corruption_level > 0.4:
            effects.append(self.trigger_character_decay_effect(
                text=text,
                intensity=corruption_level * 0.6,
                duration=duration,
                decay_mode="symbolic"
            ))
        
        # Screen tear at high corruption
        if corruption_level > 0.6:
            effects.append(self.trigger_screen_tear_effect(
                text=text,
                intensity=corruption_level * 0.7,
                duration=int(duration * 0.5),
                tear_frequency=corruption_level * 0.2
            ))
        
        # Character stutter for high corruption
        if corruption_level > 0.7:
            effects.append(self.trigger_character_stutter_effect(
                text=text,
                intensity=corruption_level * 0.8,
                duration=int(duration * 0.8),
                stutter_chance=corruption_level * 0.3
            ))
        
        # Jitter and breathing at maximum corruption
        if corruption_level > 0.8:
            effects.append(self.trigger_character_jitter_effect(
                text=text,
                intensity=corruption_level,
                duration=int(duration * 0.6),
                jitter_chance=corruption_level * 0.4
            ))
            
            effects.append(self.trigger_text_breathing_effect(
                text=text,
                intensity=corruption_level * 0.5,
                duration=duration,
                breath_rate=1.5 + corruption_level
            ))
        
        return effects

    def _create_effect_from_state(self, state):
        """Create an effect instance from a saved state."""
        effect_type = state.get("type")
        if effect_type == "corruption":
            return CorruptionEffect(
                text=state.get("text", "") if state.get("text", "") is not None else "",
                intensity=state.get("intensity", 0.0) if state.get("intensity") is not None else 0.0,
                duration=state.get("duration", 0) if state.get("duration") is not None else 0,
                category=state.get("category", "default") if state.get("category", "default") is not None else "default"
            )
        elif effect_type == "typing":
            return TypingEffect("", state.get("speed", 0.1))
        elif effect_type == "glitch":
            return GlitchEffect("", state["intensity"], state["duration"])
        elif effect_type == "character_decay":
            return CharacterDecayEffect(
                text=state.get("text", ""),
                intensity=state.get("intensity", 0.3),
                duration=state.get("duration", 2000),
                decay_mode=state.get("decay_mode", "symbolic")
            )
        elif effect_type == "character_stutter":
            return CharacterStutterEffect(
                text=state.get("text", ""),
                intensity=state.get("intensity", 0.4),
                duration=state.get("duration", 1500),
                stutter_chance=state.get("stutter_chance", 0.15)
            )
        elif effect_type == "screen_tear":
            return ScreenTearEffect(
                text=state.get("text", ""),
                intensity=state.get("intensity", 0.6),
                duration=state.get("duration", 800),
                tear_frequency=state.get("tear_frequency", 0.1)
            )
        elif effect_type == "character_jitter":
            return CharacterJitterEffect(
                text=state.get("text", ""),
                intensity=state.get("intensity", 0.5),
                duration=state.get("duration", 1000),
                jitter_chance=state.get("jitter_chance", 0.2)
            )
        elif effect_type == "text_breathing":
            return TextBreathingEffect(
                text=state.get("text", ""),
                intensity=state.get("intensity", 0.3),
                duration=state.get("duration", 3000),
                breath_rate=state.get("breath_rate", 2.0)
            )
        elif effect_type == "scanline":
            return ScanlineEffect(
                text=state.get("text", ""),
                intensity=state.get("intensity", 0.4),
                duration=state.get("duration", 2000),
                scanline_speed=state.get("scanline_speed", 1.0)
            )
        # Add more effect types as needed
        return None

    def trigger_corruption_effect(self, intensity: float, duration: float = 5.0) -> None:
        """Trigger a corruption effect."""
        self.current_effects["corruption"] = EffectState(
            intensity=float(intensity) if intensity is not None else 0.0,
            duration=float(duration) if duration is not None else 0.0,
            start_time=datetime.now(),
            active=True,
            parameters={}
        )
        self.effect_history.append({
            "type": "corruption",
            "intensity": intensity,
            "duration": duration,
            "timestamp": datetime.now()
        })

    def trigger_horror_effect(self, intensity: float, duration: float = 3.0) -> None:
        """Trigger a horror effect."""
        self.current_effects["horror"] = EffectState(
            intensity=float(intensity) if intensity is not None else 0.0,
            duration=float(duration) if duration is not None else 0.0,
            start_time=datetime.now(),
            active=True,
            parameters={}
        )
        self.effect_history.append({
            "type": "horror",
            "intensity": intensity,
            "duration": duration,
            "timestamp": datetime.now()
        })

    def trigger_glitch_effect(self, intensity: float, duration: float = 1.0) -> None:
        """Trigger a glitch effect."""
        current_time = time.time()
        if current_time - self.last_glitch_time < self.glitch_cooldown:
            return

        self.last_glitch_time = current_time
        self.current_effects["glitch"] = EffectState(
            intensity=float(intensity) if intensity is not None else 0.0,
            duration=float(duration) if duration is not None else 0.0,
            start_time=datetime.now(),
            active=True,
            parameters={}
        )
        self.effect_history.append({
            "type": "glitch",
            "intensity": intensity,
            "duration": duration,
            "timestamp": datetime.now()
        })

    def render(self, surface: pygame.Surface, grid, char_width: int, char_height: int,
              padding: int, grid_start_y_on_surface: int, scroll_offset: int):
        """Render all active effects to the surface."""
        # Apply corruption effects
        if self.current_effects["corruption"].active:
            self._apply_corruption_visuals()

        # Apply horror effects
        if self.current_effects["horror"].active:
            self._apply_horror_visuals()

        # Apply glitch effects
        if self.current_effects["glitch"].active:
            self._apply_glitch_visuals()

        # Draw cursor trails
        if self.terminal and hasattr(self.terminal, "font") and self.terminal.font:
            self.draw_cursor_trails(surface, self.terminal.font)

        # Draw control bar effects
        if self.terminal and hasattr(self.terminal, 'control_bar_rect'):
            self.draw_control_bar_effects(surface, self.terminal.control_bar_rect)

    def draw_cursor_trails(self, surface: pygame.Surface, font: pygame.font.Font):
        """Draw cursor trails."""
        if not font:
            return

        current_time = pygame.time.get_ticks()
        for trail in self.cursor_trails:
            # Calculate alpha based on decay
            alpha = 255 * (1 - (current_time - trail.start_time) / trail.decay)
            if alpha <= 0:
                continue

            # Render the trail character
            text_surface = font.render(trail.char, True, (0, 255, 0))
            text_surface.set_alpha(int(alpha))
            surface.blit(text_surface, (trail.x, trail.y))

    def add_cursor_trail(self, x: int, y: int):
        """Add a cursor trail at the specified position."""
        if not self.terminal or not self.terminal.font:
            return

        # Create a trail object
        trail = TrailObject(
            char=random.choice(CORRUPTION_CHARS),
            x=x,
            y=y,
            decay=500,  # 500ms decay
            start_time=pygame.time.get_ticks()
        )
        self.cursor_trails.append(trail)

    def draw_control_bar_effects(self, surface: pygame.Surface, bar_rect):
        """Draw all active control bar effects."""
        for effect in self.control_bar_effects:
            if hasattr(effect, 'draw'):
                effect.draw(surface)

    def queue_control_bar_effect(self, effect):
        """Queue a control bar effect."""
        self.control_bar_effects.append(effect)

    def get_effect_history(self) -> List[Dict]:
        """Get the history of triggered effects."""
        return self.effect_history

    def clear_effect_history(self) -> None:
        """Clear the effect history."""
        self.effect_history = []

    def get_current_effects(self) -> Dict[str, EffectState]:
        """Get the current state of all effects."""
        return self.current_effects

    def maybe_blip_glitchy_profanity(self, corruption_level: float, terminal) -> None:
        """Maybe trigger a glitchy profanity effect based on corruption level."""
        if corruption_level > 0.7 and random.random() < 0.1:
            profanity = random.choice(GLITCHY_PROFANITY)
            effect = CorruptionEffect(
                text=profanity if profanity is not None else "",
                intensity=0.8,
                duration=500,
                category="profanity"
            )
            self.add_effect(effect)
            if self.audio_manager:
                self.audio_manager.play_sound("glitch", volume=0.3)

    def trigger_scanline_effect(self, duration: float = 1.0, intensity: float = 0.5):
        """Trigger a scanline effect."""
        effect = GlitchOverlayEffect(duration=int(duration * 1000), intensity=intensity)
        self.add_effect(effect)

    def trigger_border_glitch(self, duration: float = 1.0, intensity: float = 0.5):
        """Trigger a border glitch effect."""
        effect = GlitchOverlayEffect(duration=int(duration * 1000), intensity=intensity)
        self.add_effect(effect)

    def apply_corruption_effect(self, *args, **kwargs):
        """Apply a corruption effect to text."""
        # Ensure 'category' is provided, fallback to 'default' if missing
        if 'category' not in kwargs:
            kwargs['category'] = 'default'
        effect = CorruptionEffect(*args, **kwargs)
        self.add_effect(effect)
        return effect

    def _apply_corruption_visuals(self) -> None:
        """Apply corruption visual effects to the screen."""
        if not self.terminal:
            return

        # Create corruption overlay
        overlay = pygame.Surface(self.terminal.get_size(), pygame.SRCALPHA)

        # Apply text distortion
        if self.current_effects["corruption"].parameters.get("text_distortion", 0) > 0:
            self._apply_text_distortion(overlay)

        # Apply color shift
        if self.current_effects["corruption"].parameters.get("color_shift", 0) > 0:
            self._apply_color_shift(overlay)

        # Apply glitch effect
        if self.current_effects["corruption"].parameters.get("glitch_frequency", 0) > 0:
            self._apply_glitch(overlay)

        # Apply reality tear
        if self.current_effects["corruption"].parameters.get("reality_tear", 0) > 0:
            self._apply_reality_tear(overlay)

        # Blend overlay with screen
        self.terminal.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    def _apply_horror_visuals(self) -> None:
        """Apply horror visual effects to the screen."""
        if not self.terminal:
            return

        # Create horror overlay
        overlay = pygame.Surface(self.terminal.get_size(), pygame.SRCALPHA)

        # Apply static
        if self.current_effects["horror"].parameters.get("static_intensity", 0) > 0:
            self._apply_static(overlay)

        # Apply reality shift
        if self.current_effects["horror"].parameters.get("reality_shift", 0) > 0:
            self._apply_reality_shift(overlay)

        # Apply entity presence
        if self.current_effects["horror"].parameters.get("entity_presence", 0) > 0:
            self._apply_entity_presence(overlay)

        # Blend overlay with screen
        self.terminal.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    def _apply_glitch_visuals(self) -> None:
        """Apply glitch visual effects to the screen."""
        if not self.terminal:
            return

        # Create glitch overlay
        overlay = pygame.Surface(self.terminal.get_size(), pygame.SRCALPHA)

        # Apply glitch pattern
        if self.current_effects["glitch"].parameters.get("pattern", "random") == "random":
            self._apply_random_glitch(overlay)
        elif self.current_effects["glitch"].parameters.get("pattern", "wave") == "wave":
            self._apply_wave_glitch(overlay)
        elif self.current_effects["glitch"].parameters.get("pattern", "pulse") == "pulse":
            self._apply_pulse_glitch(overlay)
        elif self.current_effects["glitch"].parameters.get("pattern", "static") == "static":
            self._apply_static_glitch(overlay)

        # Apply color shift
        if self.current_effects["glitch"].parameters.get("color_shift", 0) > 0:
            self._apply_color_shift(overlay)

        # Blend overlay with screen
        self.terminal.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    def _apply_text_distortion(self, surface: pygame.Surface) -> None:
        """Apply text distortion effect to the surface."""
        intensity = self.current_effects["corruption"].parameters.get("text_distortion", 0)

        # Create noise pattern
        noise = np.random.normal(0, intensity * 10, surface.get_size())
        noise_surface = pygame.surfarray.make_surface(noise)

        # Apply noise to surface
        surface.blit(noise_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def _apply_color_shift(self, surface: pygame.Surface) -> None:
        """Apply color shift effect to the surface."""
        intensity = self.current_effects["corruption"].parameters.get("color_shift", 0)

        # Create color shift matrix
        shift = np.array([
            [1.0, intensity * 0.2, -intensity * 0.1],
            [-intensity * 0.1, 1.0, intensity * 0.2],
            [intensity * 0.2, -intensity * 0.1, 1.0]
        ])

        try:
            # Apply color shift
            pixels = pygame.surfarray.pixels3d(surface)
            if pixels.size > 0:  # Only process if array has elements
                pixels[:] = np.dot(pixels, shift.T)
            del pixels
        except (ValueError, AttributeError):
            # Skip color shift if surface/pixels are invalid (e.g., in tests)
            pass

    def _apply_glitch(self, surface: pygame.Surface) -> None:
        """Apply glitch effect to the surface."""
        intensity = self.current_effects["corruption"].parameters.get("glitch_frequency", 0)

        # Get surface size and validate
        size = surface.get_size()
        if not size or len(size) != 2 or size[0] <= 0 or size[1] <= 0:
            return  # Skip if invalid size
            
        # Create glitch pattern
        glitch = np.random.choice([0, 1], size=size, p=[1-intensity, intensity])
        glitch_surface = pygame.surfarray.make_surface(glitch * 255)

        # Apply glitch to surface
        surface.blit(glitch_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    def _apply_reality_tear(self, surface: pygame.Surface) -> None:
        """Apply reality tear effect to the surface."""
        intensity = self.current_effects["corruption"].parameters.get("reality_tear", 0)

        # Create tear pattern
        tear = np.zeros(surface.get_size())
        tear[::2, ::2] = intensity * 255
        tear_surface = pygame.surfarray.make_surface(tear)

        # Apply tear to surface
        surface.blit(tear_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def _apply_static(self, surface: pygame.Surface) -> None:
        """Apply static effect to the surface."""
        intensity = self.current_effects["horror"].parameters.get("static_intensity", 0)

        # Create static pattern
        static = np.random.normal(0, intensity * 255, surface.get_size())
        static_surface = pygame.surfarray.make_surface(static)

        # Apply static to surface
        surface.blit(static_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def _apply_reality_shift(self, surface: pygame.Surface) -> None:
        """Apply reality shift effect to the surface."""
        intensity = self.current_effects["horror"].parameters.get("reality_shift", 0)

        # Create shift pattern
        shift = np.random.normal(0, intensity * 20, surface.get_size())
        shift_surface = pygame.surfarray.make_surface(shift)

        # Apply shift to surface
        surface.blit(shift_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def _apply_entity_presence(self, surface: pygame.Surface) -> None:
        """Apply entity presence effect to the surface."""
        intensity = self.current_effects["horror"].parameters.get("entity_presence", 0)

        # Get surface size and validate
        size = surface.get_size()
        if not size or len(size) != 2 or size[0] <= 0 or size[1] <= 0:
            return  # Skip if invalid size
            
        # Create entity pattern
        entity = np.zeros(size)
        if entity.size > 0:  # Only process if array has elements
            entity[::4, ::4] = intensity * 255
            entity_surface = pygame.surfarray.make_surface(entity)

            # Apply entity to surface
            surface.blit(entity_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def _apply_random_glitch(self, surface: pygame.Surface) -> None:
        """Apply random glitch pattern to the surface."""
        intensity = self.current_effects["glitch"].parameters.get("frequency", 0)

        # Get surface size and validate
        size = surface.get_size()
        if not size or len(size) != 2 or size[0] <= 0 or size[1] <= 0:
            return  # Skip if invalid size
            
        # Create random glitch pattern
        glitch = np.random.choice([0, 1], size=size, p=[1-intensity, intensity])
        glitch_surface = pygame.surfarray.make_surface(glitch * 255)

        # Apply glitch to surface
        surface.blit(glitch_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    def _apply_wave_glitch(self, surface: pygame.Surface) -> None:
        """Apply wave glitch pattern to the surface."""
        intensity = self.current_effects["glitch"].parameters.get("frequency", 0)

        # Create wave pattern
        x = np.arange(surface.get_width())
        y = np.arange(surface.get_height())
        X, Y = np.meshgrid(x, y)
        wave = np.sin(X * intensity * 0.1) * intensity * 255
        wave_surface = pygame.surfarray.make_surface(wave)

        # Apply wave to surface
        surface.blit(wave_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def _apply_pulse_glitch(self, surface: pygame.Surface) -> None:
        """Apply pulse glitch pattern to the surface."""
        intensity = self.current_effects["glitch"].parameters.get("frequency", 0)

        # Get surface size and validate
        size = surface.get_size()
        if not size or len(size) != 2 or size[0] <= 0 or size[1] <= 0:
            return  # Skip if invalid size
            
        # Create pulse pattern
        pulse = np.zeros(size)
        if pulse.size > 0:  # Only process if array has elements
            pulse[::2, ::2] = intensity * 255
            pulse_surface = pygame.surfarray.make_surface(pulse)

            # Apply pulse to surface
            surface.blit(pulse_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def _apply_static_glitch(self, surface: pygame.Surface) -> None:
        """Apply static glitch pattern to the surface."""
        intensity = self.current_effects["glitch"].parameters.get("frequency", 0)

        # Get surface size and validate
        size = surface.get_size()
        if not size or len(size) != 2 or size[0] <= 0 or size[1] <= 0:
            return  # Skip if invalid size
            
        # Create static pattern
        static = np.random.normal(0, intensity * 255, size)
        static_surface = pygame.surfarray.make_surface(static)

        # Apply static to surface
        surface.blit(static_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

# --- Enhanced Character-Level Effects ---

class CharacterDecayEffect(BaseEffect):
    """Effect that causes characters to decay into symbolic characters over time."""
    
    def __init__(self, text: str = "", intensity: float = 0.3, duration: int = 2000, 
                 decay_mode: str = "symbolic", on_complete_callback=None, **kwargs):
        super().__init__(on_complete_callback, **kwargs)
        self.original_text = text or ""
        self.intensity = intensity
        self.duration = duration
        self.decay_mode = decay_mode
        self.decay_progress = 0.0
        
        # Use symbolic decay characters for more unsettling effect
        if decay_mode == "symbolic":
            self.decay_chars = SYMBOLIC_DECAY_CHARS
        else:
            self.decay_chars = CORRUPTION_CHARS

    def update(self, dt: float, terminal_ref=None) -> bool | None:
        """Update the decay progress."""
        if not self.is_active:
            return None
            
        elapsed = pygame.time.get_ticks() - self.start_time
        if self.duration > 0:
            self.decay_progress = min(1.0, elapsed / self.duration)
            
        if elapsed >= self.duration:
            self.finish()
            return True
        return None

    def apply(self, text: str = None) -> str:
        """Apply character decay effect to text."""
        base_text = text if text is not None else self.original_text
        if not base_text:
            return ""
            
        chars = list(base_text)
        decay_chance = self.intensity * self.decay_progress
        
        for i, char in enumerate(chars):
            if char.isalnum() and random.random() < decay_chance:
                # Gradually decay characters based on progress
                if self.decay_progress > 0.8:
                    chars[i] = random.choice(self.decay_chars)
                elif self.decay_progress > 0.5:
                    chars[i] = random.choice(CORRUPTION_CHARS)
                elif self.decay_progress > 0.3:
                    chars[i] = char.upper() if char.islower() else char.lower()
                    
        return ''.join(chars)


class CharacterStutterEffect(BaseEffect):
    """Effect that causes characters to stutter and repeat."""
    
    def __init__(self, text: str = "", intensity: float = 0.4, duration: int = 1500,
                 stutter_chance: float = 0.15, max_repeats: int = 4, on_complete_callback=None, **kwargs):
        super().__init__(on_complete_callback, **kwargs)
        self.original_text = text or ""
        self.intensity = intensity
        self.duration = duration
        self.stutter_chance = stutter_chance
        self.max_repeats = max_repeats
        self.stutter_pattern = {}  # Store which characters are stuttering

    def update(self, dt: float, terminal_ref=None) -> bool | None:
        """Update the stuttering effect."""
        if not self.is_active:
            return None
            
        elapsed = pygame.time.get_ticks() - self.start_time
        if elapsed >= self.duration:
            self.finish()
            return True
        return None

    def apply(self, text: str = None) -> str:
        """Apply character stuttering effect to text."""
        base_text = text if text is not None else self.original_text
        if not base_text:
            return ""
            
        result = []
        current_time = pygame.time.get_ticks()
        
        for i, char in enumerate(base_text):
            if char.isalnum() and random.random() < (self.stutter_chance * self.intensity):
                # Create stuttering pattern
                repeat_count = random.randint(2, self.max_repeats)
                if char.lower() in 'aeiou':  # Vowels stutter differently
                    stutter = char + '-' + '-'.join([char] * (repeat_count - 1))
                else:  # Consonants
                    stutter = '-'.join([char] * repeat_count)
                result.append(stutter)
            else:
                result.append(char)
                
        return ''.join(result)


class ScreenTearEffect(BaseEffect):
    """Effect that creates horizontal displacement and screen tear artifacts."""
    
    def __init__(self, text: str = "", intensity: float = 0.6, duration: int = 800,
                 tear_frequency: float = 0.1, max_offset: int = 5, on_complete_callback=None, **kwargs):
        super().__init__(on_complete_callback, **kwargs)
        self.original_text = text or ""
        self.intensity = intensity
        self.duration = duration
        self.tear_frequency = tear_frequency
        self.max_offset = max_offset
        self.tear_lines = {}  # Track which lines are torn

    def update(self, dt: float, terminal_ref=None) -> bool | None:
        """Update the screen tear effect."""
        if not self.is_active:
            return None
            
        elapsed = pygame.time.get_ticks() - self.start_time
        if elapsed >= self.duration:
            self.finish()
            return True
        return None

    def apply(self, text: str = None) -> str:
        """Apply screen tear effect to text."""
        base_text = text if text is not None else self.original_text
        if not base_text:
            return ""
            
        lines = base_text.split('\n')
        result_lines = []
        
        for line_idx, line in enumerate(lines):
            if random.random() < (self.tear_frequency * self.intensity):
                # Create screen tear effect
                tear_point = random.randint(1, max(1, len(line) - 1))
                offset = random.randint(-self.max_offset, self.max_offset)
                
                if offset > 0:
                    # Right displacement - add spaces before
                    torn_line = ' ' * offset + line
                elif offset < 0:
                    # Left displacement - truncate or shift
                    torn_line = line[abs(offset):] if abs(offset) < len(line) else ""
                else:
                    torn_line = line
                    
                # Sometimes duplicate or corrupt the torn section
                if random.random() < 0.3:
                    if tear_point < len(torn_line):
                        corrupt_char = random.choice(CORRUPTION_CHARS)
                        torn_line = torn_line[:tear_point] + corrupt_char + torn_line[tear_point:]
                        
                result_lines.append(torn_line)
            else:
                result_lines.append(line)
                
        return '\n'.join(result_lines)


class CharacterJitterEffect(BaseEffect):
    """Effect that applies small random position offsets to characters."""
    
    def __init__(self, text: str = "", intensity: float = 0.5, duration: int = 1000,
                 jitter_chance: float = 0.2, max_jitter: int = 2, on_complete_callback=None, **kwargs):
        super().__init__(on_complete_callback, **kwargs)
        self.original_text = text or ""
        self.intensity = intensity
        self.duration = duration
        self.jitter_chance = jitter_chance
        self.max_jitter = max_jitter
        self.jitter_positions = {}  # Store jitter offsets for characters

    def update(self, dt: float, terminal_ref=None) -> bool | None:
        """Update the character jitter effect."""
        if not self.is_active:
            return None
            
        elapsed = pygame.time.get_ticks() - self.start_time
        
        # Update jitter positions periodically
        if elapsed % 100 < 50:  # Jitter every 100ms
            self._update_jitter_positions()
            
        if elapsed >= self.duration:
            self.finish()
            return True
        return None

    def _update_jitter_positions(self):
        """Update the jitter positions for characters."""
        self.jitter_positions.clear()
        for i in range(len(self.original_text)):
            if random.random() < (self.jitter_chance * self.intensity):
                x_offset = random.randint(-self.max_jitter, self.max_jitter)
                y_offset = random.randint(-self.max_jitter, self.max_jitter)
                self.jitter_positions[i] = (x_offset, y_offset)

    def apply(self, text: str = None) -> str:
        """Apply character jitter effect to text."""
        base_text = text if text is not None else self.original_text
        if not base_text:
            return ""
            
        # For text-based jitter, we'll simulate with spacing adjustments
        chars = list(base_text)
        result = []
        
        for i, char in enumerate(chars):
            if i in self.jitter_positions:
                x_offset, y_offset = self.jitter_positions[i]
                # Simulate horizontal jitter with spaces
                if x_offset > 0:
                    result.append(' ' * x_offset + char)
                elif x_offset < 0 and result:
                    # Remove previous spaces if possible
                    if result[-1] == ' ':
                        result.pop()
                    result.append(char)
                else:
                    result.append(char)
                    
                # Simulate vertical jitter with newlines (sparingly)
                if y_offset != 0 and random.random() < 0.1:
                    if y_offset > 0:
                        result.append('\n')
            else:
                result.append(char)
                
        return ''.join(result)


class TextBreathingEffect(BaseEffect):
    """Effect that creates a subtle 'breathing' pulse in text intensity."""
    
    def __init__(self, text: str = "", intensity: float = 0.3, duration: int = 3000,
                 breath_rate: float = 2.0, on_complete_callback=None, **kwargs):
        super().__init__(on_complete_callback, **kwargs)
        self.original_text = text or ""
        self.intensity = intensity
        self.duration = duration
        self.breath_rate = breath_rate  # Breaths per second
        self.current_alpha = 1.0

    def update(self, dt: float, terminal_ref=None) -> bool | None:
        """Update the breathing effect."""
        if not self.is_active:
            return None
            
        elapsed = pygame.time.get_ticks() - self.start_time
        
        # Calculate breathing cycle
        cycle_time = (elapsed / 1000.0) * self.breath_rate
        breath_value = (math.sin(cycle_time * 2 * math.pi) + 1) / 2  # 0 to 1
        self.current_alpha = 0.7 + (breath_value * 0.3 * self.intensity)
        
        if elapsed >= self.duration:
            self.finish()
            return True
        return None

    def apply(self, text: str = None) -> str:
        """Apply breathing effect to text."""
        base_text = text if text is not None else self.original_text
        if not base_text:
            return ""
            
        # For text-based breathing, we'll vary character intensity
        if self.current_alpha < 0.5:
            # At low breathing intensity, dim some characters
            chars = list(base_text)
            for i in range(len(chars)):
                if random.random() < (1 - self.current_alpha):
                    if chars[i].isalnum():
                        chars[i] = chars[i].lower() if chars[i].isupper() else '·'
            return ''.join(chars)
        else:
            return base_text


class ScanlineEffect(BaseEffect):
    """Effect that creates moving scanline artifacts across text."""
    
    def __init__(self, text: str = "", intensity: float = 0.4, duration: int = 2000,
                 scanline_speed: float = 1.0, on_complete_callback=None, **kwargs):
        super().__init__(on_complete_callback, **kwargs)
        self.original_text = text or ""
        self.intensity = intensity
        self.duration = duration
        self.scanline_speed = scanline_speed
        self.current_line = 0

    def update(self, dt: float, terminal_ref=None) -> bool | None:
        """Update the scanline effect."""
        if not self.is_active:
            return None
            
        elapsed = pygame.time.get_ticks() - self.start_time
        
        # Move scanline
        self.current_line = int((elapsed / 1000.0) * self.scanline_speed * 10) % 20
        
        if elapsed >= self.duration:
            self.finish()
            return True
        return None

    def apply(self, text: str = None) -> str:
        """Apply scanline effect to text."""
        base_text = text if text is not None else self.original_text
        if not base_text:
            return ""
            
        lines = base_text.split('\n')
        result_lines = []
        
        for i, line in enumerate(lines):
            if i % 20 == self.current_line:
                # Apply scanline corruption
                noise_chars = '·.,`-~'
                corrupted_line = ""
                for char in line:
                    if random.random() < self.intensity * 0.3:
                        corrupted_line += random.choice(noise_chars)
                    else:
                        corrupted_line += char
                result_lines.append(corrupted_line)
            else:
                result_lines.append(line)
                
        return '\n'.join(result_lines)
