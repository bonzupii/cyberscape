import pygame
import random

# --- Color Definitions (can be expanded) ---
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GREY_LIGHT = (200, 200, 200)
COLOR_GREY_DARK = (50, 50, 50)
COLOR_RED_BRIGHT = (255, 0, 0)
COLOR_RED_DARK = (150, 0, 0)
COLOR_GREEN_BRIGHT = (0, 255, 0)
COLOR_GREEN_DARK = (0, 150, 0)
COLOR_BLUE_BRIGHT = (0, 0, 255)
COLOR_BLUE_CYAN = (0, 255, 255)
COLOR_YELLOW_BRIGHT = (255, 255, 0)
COLOR_MAGENTA_BRIGHT = (255, 0, 255)

# --- Theme Definitions ---
# Each theme is a dictionary defining key colors for the terminal.
# 'default_fg': Default foreground text color
# 'default_bg': Default background color for the terminal
# 'prompt': Color for the input prompt (e.g., "> ")
# 'error': Color for error messages
# 'success': Color for success messages
# 'highlight': A general highlight color

THEMES = {
    "default": {
        "default_fg": COLOR_GREY_LIGHT,
        "default_bg": COLOR_BLACK,
        "prompt": COLOR_GREEN_BRIGHT,
        "error": COLOR_RED_BRIGHT,
        "success": COLOR_GREEN_BRIGHT,
        "highlight": COLOR_BLUE_CYAN,
        "name": "Default Terminal"
    },
    "corrupted_kali": {
        "default_fg": (180, 220, 180), # Muted green
        "default_bg": (10, 20, 10),   # Very dark green/black
        "prompt": (100, 255, 100),    # Brighter green for prompt
        "error": (255, 80, 80),       # Glitchy red
        "success": (80, 220, 80),     # Muted success green
        "highlight": (220, 80, 220),  # Corrupted magenta
        "name": "Corrupted Kali"
    },
    "digital_nightmare": {
        "default_fg": (150, 0, 0),       # Dark blood red
        "default_bg": (10, 0, 0),       # Near black with red tint
        "prompt": (200, 50, 50),      # Menacing red prompt
        "error": (255, 150, 0),     # Unsettling orange/yellow for errors
        "success": (100, 0, 0),     # Barely visible success
        "highlight": (255, 0, 255),   # Harsh magenta
        "name": "Digital Nightmare"
    },
    "classic_dos": {
        "default_fg": COLOR_GREY_LIGHT,
        "default_bg": (0, 0, 128), # Dark Blue
        "prompt": COLOR_WHITE,
        "error": COLOR_YELLOW_BRIGHT,
        "success": COLOR_GREEN_BRIGHT,
        "highlight": COLOR_WHITE,
        "name": "Classic DOS"
    }
}

# --- Global Theme Management (Simple version) ---
# For a more complex game, this might be part of a settings class or game state.
current_theme_name = "default"

def get_current_theme():
    """Returns the dictionary for the currently active theme."""
    return THEMES.get(current_theme_name, THEMES["default"])

def set_theme(theme_name):
    """Sets the active theme by name."""
    global current_theme_name
    if theme_name in THEMES:
        current_theme_name = theme_name
        # print(f"Theme changed to: {THEMES[current_theme_name]['name']}") # Keep for debug
        return True
    else:
        # print(f"Warning: Theme '{theme_name}' not found.") # Keep for debug
        return False
 
def get_theme_color(color_key, theme=None):
    """
    Safely gets a color from the current (or specified) theme.
    Falls back to white if the key or theme is not found.
    """
    active_theme = theme if theme else get_current_theme()
    return active_theme.get(color_key, COLOR_WHITE)

# --- Text Effects ---

class BaseEffect:
    def __init__(self, on_complete_callback=None):
        self.is_active = True
        self.is_complete = False
        self.on_complete_callback = on_complete_callback

    def update(self, dt_ms, terminal_ref):
        """Returns True if the effect did something that might require a screen update, False otherwise."""
        raise NotImplementedError("Effect subclass must implement update()")

    def start(self, terminal_ref):
        """Called when the effect becomes the current one in the queue."""
        pass # Optional for effects to implement

    def finish(self):
        self.is_complete = True
        self.is_active = False
        if self.on_complete_callback:
            self.on_complete_callback()

class TypingEffect(BaseEffect):
    def __init__(self, text_to_type, char_delay_ms, fg_color, bg_color=None, bold=False, on_complete_callback=None):
        super().__init__(on_complete_callback)
        self.full_text = text_to_type
        self.char_delay = char_delay_ms
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.bold = bold

        self.current_display_text = ""
        self.current_char_index = 0
        self.timer = 0
        self.line_index_in_terminal = -1

    def start(self, terminal_ref):
        if not self.full_text:  # Case 1: Empty text
            self.current_display_text = ""
            self.current_char_index = 0
            self.line_index_in_terminal = terminal_ref.add_line(
                self.current_display_text, self.fg_color, self.bg_color, self.bold
            )
            if self.line_index_in_terminal is None:
                # print("Error: TypingEffect (empty text) failed to add initial line to terminal.") # Keep for debug
                self.finish() # Must finish if add_line failed
            elif self.char_delay == 0: # Only finish if instant and add_line succeeded
                self.finish()
            # If char_delay > 0 and add_line succeeded for empty text, it's NOT complete yet.
            return

        # Case 2: Non-empty text
        if self.char_delay == 0:  # Instant display
            self.current_display_text = self.full_text
            self.current_char_index = len(self.full_text)
            self.line_index_in_terminal = terminal_ref.add_line(
                self.current_display_text, self.fg_color, self.bg_color, self.bold
            )
            if self.line_index_in_terminal is None:
                # print(f"Error: TypingEffect (instant, non-empty) failed to add line for '{self.full_text}'.") # Keep for debug
                pass # Explicitly do nothing if the line index is None
            # Instant display always finishes in start, regardless of add_line success,
            # as there's no further typing process.
            self.finish()
        else:  # Delayed typing for non-empty text
            self.current_display_text = self.full_text[0]
            self.current_char_index = 1
            self.line_index_in_terminal = terminal_ref.add_line(
                self.current_display_text, self.fg_color, self.bg_color, self.bold
            )
            if self.line_index_in_terminal is None:
                # print(f"Error: TypingEffect (delayed, non-empty) failed to add initial line for '{self.full_text}'.") # Keep for debug
                self.finish() # If initial add_line fails, cannot proceed with typing.
 
    def update(self, dt_ms, terminal_ref):
        if not self.is_active:
            return False
        
        if self.is_complete: # If already complete, no update (should have returned True on the frame it completed)
            return False

        # Handle empty text case (should be completed in start, but as a safeguard)
        if not self.full_text:
            if not self.is_complete:
                self.finish()
                return True # Became complete this frame
            return False

        # Handle instant display (char_delay == 0)
        # This should also be completed in start, but as a safeguard.
        if self.char_delay == 0:
            if not self.is_complete:
                self.finish()
                return True # Became complete this frame
            return False

        # Regular typing effect logic
        self.timer += dt_ms
        made_change_this_update = False

        while self.timer >= self.char_delay:
            if self.current_char_index < len(self.full_text):
                self.current_char_index += 1
                self.current_display_text = self.full_text[:self.current_char_index]
                self.timer -= self.char_delay
                if self.line_index_in_terminal is not None and self.line_index_in_terminal != -1 : # Check for valid index
                    terminal_ref.update_buffer_line(
                        self.line_index_in_terminal, self.current_display_text,
                        self.fg_color, self.bg_color, self.bold
                    )
                made_change_this_update = True
            else: # All characters have been typed
                if not self.is_complete:
                    self.finish()
                    return True # Text completed this frame
                return False # Already completed in a previous sub-loop of this update
        
        # Check for completion if all characters are displayed and not already completed
        if not self.is_complete and self.current_char_index == len(self.full_text):
            self.finish()
            return True # Became complete this frame
        
        return made_change_this_update

class TimedDelayEffect(BaseEffect):
    def __init__(self, duration_ms, on_complete_callback=None):
        super().__init__(on_complete_callback)
        self.duration = duration_ms
        self.timer = 0

    def update(self, dt_ms, terminal_ref):
        if not self.is_active or self.is_complete:
            return False
        
        self.timer += dt_ms
        if self.timer >= self.duration:
            self.finish()
            return False # Delay itself doesn't update display, but its completion allows next effect
        return False # No visual change during delay

# Characters to use for corruption. Can be expanded.
CORRUPTION_CHARS = "!@#$%^&*()_+[];',./<>?:{}|`~" + "¡¢£¤¥¦§¨©ª«¬®¯°±²³´µ¶·¸¹º»¼½¾¿" + "ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞß"

class CharacterCorruptionEffect(BaseEffect):
    def __init__(self, line_index, duration_ms, corruption_intensity=0.2, corruption_rate_ms=175, on_complete_callback=None):
        super().__init__(on_complete_callback)
        self.line_index = line_index # Index of the line in terminal buffer to corrupt
        self.duration = duration_ms
        self.corruption_intensity = corruption_intensity # 0.0 to 1.0, fraction of chars to corrupt
        self.corruption_rate = corruption_rate_ms # How often to change the corruption pattern

        self.total_timer = 0 # For total duration
        self.corruption_timer = 0 # For changing corruption pattern
        
        self.original_text = ""
        self.original_fg = None
        self.original_bg = None
        self.original_bold = False

    def start(self, terminal_ref):
        line_details = terminal_ref.get_buffer_line_details(self.line_index)
        if line_details:
            self.original_text, self.original_fg, self.original_bg, self.original_bold = line_details
            if not self.original_text: # Don't corrupt empty lines
                self.finish()
                return
            self._apply_corruption(terminal_ref) # Apply initial corruption
        else:
            # print(f"Error: CharacterCorruptionEffect could not find line {self.line_index}") # Keep for debug
            self.finish() # Cannot proceed
 
    def _corrupt_text(self, text):
        if not text: return ""
        text_list = list(text)
        num_to_corrupt = int(len(text_list) * self.corruption_intensity)
        indices_to_corrupt = random.sample(range(len(text_list)), k=min(num_to_corrupt, len(text_list)))
        
        for i in indices_to_corrupt:
            if text_list[i] != ' ': # Don't corrupt spaces usually
                text_list[i] = random.choice(CORRUPTION_CHARS)
        return "".join(text_list)

    def _apply_corruption(self, terminal_ref):
        corrupted_text = self._corrupt_text(self.original_text)
        terminal_ref.update_buffer_line(
            self.line_index, corrupted_text,
            self.original_fg, self.original_bg, self.original_bold
        )

    def update(self, dt_ms, terminal_ref):
        if not self.is_active or self.is_complete:
            return False

        self.total_timer += dt_ms
        self.corruption_timer += dt_ms

        if self.total_timer >= self.duration:
            # Restore original text and finish
            if self.line_index != -1 and self.original_text is not None:
                 terminal_ref.update_buffer_line(
                    self.line_index, self.original_text,
                    self.original_fg, self.original_bg, self.original_bold
                )
            self.finish()
            return True # Restored text, needs update

        if self.corruption_timer >= self.corruption_rate:
            self.corruption_timer %= self.corruption_rate
            if self.line_index != -1 and self.original_text is not None:
                self._apply_corruption(terminal_ref)
                return True # Corruption changed, needs update
        
        return False

class TextFlickerEffect(BaseEffect):
    def __init__(self, line_index, duration_ms, flicker_rate_ms=100, flicker_color_key='error', on_complete_callback=None):
        super().__init__(on_complete_callback)
        self.line_index = line_index
        self.duration = duration_ms
        self.flicker_rate = flicker_rate_ms
        self.flicker_color_key = flicker_color_key # Key from theme, e.g., 'error' or 'highlight'

        self.total_timer = 0
        self.flicker_timer = 0
        self.is_flickered_state = False # True if currently showing flicker color

        self.original_text = ""
        self.original_fg = None
        self.original_bg = None
        self.original_bold = False
        self.flicker_fg_color = None


    def start(self, terminal_ref):
        line_details = terminal_ref.get_buffer_line_details(self.line_index)
        if line_details:
            self.original_text, self.original_fg, self.original_bg, self.original_bold = line_details
            if not self.original_text: # Don't flicker empty lines
                self.finish()
                return
            self.flicker_fg_color = get_theme_color(self.flicker_color_key)
            if self.flicker_fg_color == self.original_fg: # If same, use background to "hide"
                self.flicker_fg_color = get_theme_color('default_bg')
            self._apply_flicker_state(terminal_ref, True) # Start in flickered state
        else:
            # print(f"Error: TextFlickerEffect could not find line {self.line_index}") # Keep for debug
            self.finish()
 
    def _apply_flicker_state(self, terminal_ref, show_flicker):
        target_fg = self.flicker_fg_color if show_flicker else self.original_fg
        terminal_ref.update_buffer_line(
            self.line_index, self.original_text, # Text itself doesn't change
            target_fg, self.original_bg, self.original_bold
        )
        self.is_flickered_state = show_flicker

    def update(self, dt_ms, terminal_ref):
        if not self.is_active or self.is_complete:
            return False

        self.total_timer += dt_ms
        self.flicker_timer += dt_ms

        if self.total_timer >= self.duration:
            # Restore original color and finish
            if self.line_index != -1 and self.original_text is not None:
                 self._apply_flicker_state(terminal_ref, False) # Restore original
            self.finish()
            return True # Restored color

        if self.flicker_timer >= self.flicker_rate:
            self.flicker_timer %= self.flicker_rate
            if self.line_index != -1 and self.original_text is not None:
                self._apply_flicker_state(terminal_ref, not self.is_flickered_state) # Toggle
                return True # Flicker state changed
        
        return False

class TemporaryColorChangeEffect(BaseEffect):
    def __init__(self, line_index, duration_ms, new_fg_color_key=None, new_bg_color_key=None, on_complete_callback=None):
        super().__init__(on_complete_callback)
        self.line_index = line_index
        self.duration = duration_ms
        self.new_fg_color_key = new_fg_color_key # Theme key for new FG color
        self.new_bg_color_key = new_bg_color_key # Theme key for new BG color

        self.total_timer = 0
        
        self.original_text = ""
        self.original_fg = None
        self.original_bg = None
        self.original_bold = False
        
        self.temp_fg = None
        self.temp_bg = None

    def start(self, terminal_ref):
        line_details = terminal_ref.get_buffer_line_details(self.line_index)
        if line_details:
            self.original_text, self.original_fg, self.original_bg, self.original_bold = line_details
            if not self.original_text: # Don't affect empty lines
                self.finish()
                return

            self.temp_fg = get_theme_color(self.new_fg_color_key) if self.new_fg_color_key else self.original_fg
            self.temp_bg = get_theme_color(self.new_bg_color_key) if self.new_bg_color_key else self.original_bg
            
            if self.temp_fg == self.original_fg and self.temp_bg == self.original_bg:
                # No actual change, so just finish
                self.finish()
                return

            terminal_ref.update_buffer_line(
                self.line_index, self.original_text,
                self.temp_fg, self.temp_bg, self.original_bold
            )
        else:
            # print(f"Error: TemporaryColorChangeEffect could not find line {self.line_index}") # Keep for debug
            self.finish()
 
    def update(self, dt_ms, terminal_ref):
        if not self.is_active or self.is_complete:
            return False

        self.total_timer += dt_ms
        if self.total_timer >= self.duration:
            # Restore original colors and finish
            if self.line_index != -1 and self.original_text is not None:
                 terminal_ref.update_buffer_line(
                    self.line_index, self.original_text,
                    self.original_fg, self.original_bg, self.original_bold
                )
            self.finish()
            return True # Restored color
        return False # No change until duration is up

class TextOverlayEffect(BaseEffect):
    def __init__(self, duration_ms, num_chars=50, char_set=None, color_key='error', update_rate_ms=100, on_complete_callback=None):
        super().__init__(on_complete_callback)
        self.duration = duration_ms
        self.num_chars = num_chars
        self.char_set = char_set if char_set else CORRUPTION_CHARS # Reuse corruption chars or define a new set
        self.color_key = color_key
        self.update_rate = update_rate_ms

        self.total_timer = 0
        self.overlay_update_timer = 0
        
        self.overlay_elements = [] # List of (char, x, y, color)
        self.overlay_color = None

    def start(self, terminal_ref):
        self.overlay_color = get_theme_color(self.color_key)
        self._generate_overlay_elements(terminal_ref) # Initial generation

    def _generate_overlay_elements(self, terminal_ref):
        self.overlay_elements = []
        # Ensure font is available for size calculation
        char_width = 8  # Default fallback
        char_height = 16 # Default fallback
        if terminal_ref.font:
            try:
                # Attempt to get size of a common character, fallback if font not fully ready
                char_size_test = terminal_ref.font.size("X")
                char_width = char_size_test[0]
                char_height = terminal_ref.font.get_linesize()
            except pygame.error:
                pass # Use default if font.size fails

        for _ in range(self.num_chars):
            char = random.choice(self.char_set)
            # Position in pixels, ensuring char fits within bounds
            max_x = terminal_ref.width - char_width
            max_y = terminal_ref.height - char_height
            x = random.randint(0, max_x if max_x > 0 else 0)
            y = random.randint(0, max_y if max_y > 0 else 0)
            self.overlay_elements.append((char, x, y, self.overlay_color))

    def update(self, dt_ms, terminal_ref):
        if not self.is_active or self.is_complete:
            self.overlay_elements = [] # Clear elements when not active
            return False

        self.total_timer += dt_ms
        self.overlay_update_timer += dt_ms

        if self.total_timer >= self.duration:
            self.overlay_elements = []
            self.finish()
            return True # Effect ended, clear overlay

        if self.overlay_update_timer >= self.update_rate:
            self.overlay_update_timer %= self.update_rate
            self._generate_overlay_elements(terminal_ref)
            return True # Overlay elements regenerated
            
        return False # No change to overlay elements this frame, but still active

    def get_overlay_elements(self):
        if self.is_active and not self.is_complete:
            return self.overlay_elements
        return []

class TextJiggleEffect(BaseEffect):
    def __init__(self, line_index, duration_ms, jiggle_intensity=1, update_rate_ms=50, on_complete_callback=None):
        super().__init__(on_complete_callback)
        self.line_index = line_index
        self.duration = duration_ms
        self.jiggle_intensity = jiggle_intensity # Max pixel offset
        self.update_rate = update_rate_ms

        self.total_timer = 0
        self.jiggle_timer = 0
        
        self.original_line_details = None # To store (text, fg, bg, bold)
        self.char_offsets = [] # List of (dx, dy) for each char

        # This effect needs special handling in Terminal's render method
        # to draw characters with individual offsets.
        # It won't directly call update_buffer_line in the same way other effects do.
        # Instead, it provides data for the renderer.

    def start(self, terminal_ref):
        self.original_line_details = terminal_ref.get_buffer_line_details(self.line_index)
        if not self.original_line_details or not self.original_line_details[0]: # No text or line not found
            self.finish()
            return
        self._generate_char_offsets()

    def _generate_char_offsets(self):
        self.char_offsets = []
        if self.original_line_details:
            text = self.original_line_details[0]
            for _ in text:
                dx = random.randint(-self.jiggle_intensity, self.jiggle_intensity)
                dy = random.randint(-self.jiggle_intensity, self.jiggle_intensity)
                self.char_offsets.append((dx, dy))

    def update(self, dt_ms, terminal_ref):
        if not self.is_active or self.is_complete:
            return False

        self.total_timer += dt_ms
        self.jiggle_timer += dt_ms

        if self.total_timer >= self.duration:
            self.char_offsets = [] # Clear offsets
            self.finish()
            # The terminal renderer will need to know to stop jiggling this line.
            # This might involve the terminal checking active effects or this effect explicitly telling it.
            return True # Effect ended, needs redraw to restore normal rendering

        if self.jiggle_timer >= self.update_rate:
            self.jiggle_timer %= self.update_rate
            self._generate_char_offsets()
            return True # Offsets regenerated, needs redraw
            
        return False # Still active, but offsets haven't changed this frame

    def get_jiggle_data(self):
        """Provides the original line data and character offsets for rendering."""
        if self.is_active and not self.is_complete and self.original_line_details:
            return self.original_line_details, self.char_offsets
        return None, []


class EffectManager:
    def __init__(self, terminal_ref):
        self.effect_queue = [] # Stores instances of BaseEffect subclasses
        self.terminal = terminal_ref
        # Store references to actual effect types to avoid issues with patching in tests
        self._typing_effect_type = TypingEffect
        self._character_corruption_effect_type = CharacterCorruptionEffect
        self._text_flicker_effect_type = TextFlickerEffect
        self._temporary_color_change_effect_type = TemporaryColorChangeEffect
        self._text_overlay_effect_type = TextOverlayEffect
        self._text_jiggle_effect_type = TextJiggleEffect
        self._timed_delay_effect_type = TimedDelayEffect

    def _add_effect_to_queue(self, effect_instance):
        self.effect_queue.append(effect_instance)
        if len(self.effect_queue) == 1: # If queue was empty, start this new effect
            self.effect_queue[0].start(self.terminal)


    def start_typing_effect(self, text, char_delay_ms=50, fg_color=None, bg_color=None, bold=False, style_key=None, on_complete_callback=None):
        final_fg_color = fg_color
        if style_key:
            final_fg_color = get_theme_color(style_key)
        elif fg_color is None:
            final_fg_color = get_theme_color('default_fg')
        
        effect = TypingEffect(text, char_delay_ms, final_fg_color, bg_color, bold, on_complete_callback)
        self._add_effect_to_queue(effect)

    def start_timed_delay(self, duration_ms, on_complete_callback=None):
        if duration_ms <= 0:
            if on_complete_callback: on_complete_callback()
            return # No delay needed
        effect = TimedDelayEffect(duration_ms, on_complete_callback)
        self._add_effect_to_queue(effect)

    def start_character_corruption_effect(self, line_index, duration_ms=1000, intensity=0.2, rate_ms=75, on_complete_callback=None):
        """
        Applies a character corruption effect to an existing line in the terminal.
        line_index: The index of the line in the terminal's buffer.
                      Can be a positive index from start, or negative from end (e.g., -1 for last line).
        duration_ms: Total time the effect lasts.
        intensity: Fraction of characters to corrupt (0.0 to 1.0).
        rate_ms: How often the corruption pattern changes.
        """
        # Adjust negative line_index to be positive relative to current buffer size
        actual_line_index = line_index
        if line_index < 0:
            actual_line_index = len(self.terminal.buffer) + line_index
            
        if not (0 <= actual_line_index < len(self.terminal.buffer)):
            # print(f"Error: Invalid line_index {line_index} (resolved to {actual_line_index}) for corruption effect. Buffer size: {len(self.terminal.buffer)}") # Keep for debug
            if on_complete_callback: on_complete_callback()
            return
 
        effect = CharacterCorruptionEffect(actual_line_index, duration_ms, intensity, rate_ms, on_complete_callback)
        self._add_effect_to_queue(effect)

    def start_text_flicker_effect(self, line_index, duration_ms=1000, flicker_rate_ms=100, flicker_color_key='error', on_complete_callback=None):
        actual_line_index = line_index
        if line_index < 0:
            actual_line_index = len(self.terminal.buffer) + line_index
        
        if not (0 <= actual_line_index < len(self.terminal.buffer)):
            # print(f"Error: Invalid line_index {line_index} (resolved to {actual_line_index}) for flicker effect. Buffer size: {len(self.terminal.buffer)}") # Keep for debug
            if on_complete_callback: on_complete_callback()
            return
            
        effect = TextFlickerEffect(actual_line_index, duration_ms, flicker_rate_ms, flicker_color_key, on_complete_callback)
        self._add_effect_to_queue(effect)

    def start_temp_color_change_effect(self, line_index, duration_ms=1000, new_fg_color_key=None, new_bg_color_key=None, on_complete_callback=None):
        actual_line_index = line_index
        if line_index < 0:
            actual_line_index = len(self.terminal.buffer) + line_index
        
        if not (0 <= actual_line_index < len(self.terminal.buffer)):
            # print(f"Error: Invalid line_index {line_index} (resolved to {actual_line_index}) for color change effect. Buffer size: {len(self.terminal.buffer)}") # Keep for debug
            if on_complete_callback: on_complete_callback()
            return
        
        if not new_fg_color_key and not new_bg_color_key:
            # print("Error: TemporaryColorChangeEffect requires at least one new color key (fg or bg).") # Keep for debug
            if on_complete_callback: on_complete_callback()
            return
 
        effect = TemporaryColorChangeEffect(actual_line_index, duration_ms, new_fg_color_key, new_bg_color_key, on_complete_callback)
        self._add_effect_to_queue(effect)

    def start_text_overlay_effect(self, duration_ms=2000, num_chars=30, char_set=None, color_key='error', update_rate_ms=100, on_complete_callback=None):
        effect = TextOverlayEffect(duration_ms, num_chars, char_set, color_key, update_rate_ms, on_complete_callback)
        self._add_effect_to_queue(effect)
        # Note: This effect type might need special handling in the renderer
        # if it's meant to overlay *everything* rather than just being a step in a sequence.
        # For now, it's a queued effect. If it's active, Terminal.render will ask for its elements.

    def start_text_jiggle_effect(self, line_index, duration_ms=1000, jiggle_intensity=1, update_rate_ms=50, on_complete_callback=None):
        actual_line_index = line_index
        if line_index < 0:
            actual_line_index = len(self.terminal.buffer) + line_index
        
        if not (0 <= actual_line_index < len(self.terminal.buffer)):
            # print(f"Error: Invalid line_index {line_index} (resolved to {actual_line_index}) for jiggle effect. Buffer size: {len(self.terminal.buffer)}") # Keep for debug
            if on_complete_callback: on_complete_callback()
            return
            
        effect = TextJiggleEffect(actual_line_index, duration_ms, jiggle_intensity, update_rate_ms, on_complete_callback)
        self._add_effect_to_queue(effect)
    def update(self, dt_ms):
        if not self.effect_queue:
            return

        current_effect = self.effect_queue[0]
        if current_effect.is_active:
            current_effect.update(dt_ms, self.terminal)

        if current_effect.is_complete:
            self.effect_queue.pop(0) # Remove completed effect
            if self.effect_queue: # If there's a next effect, start it
                self.effect_queue[0].start(self.terminal)
    
    def is_effect_active(self):
        return bool(self.effect_queue) # True if there's anything in the queue

    def skip_current_effect(self):
        if not self.effect_queue:
            return

        current_effect = self.effect_queue[0]
        
        # Specific skip logic for different effect types
        if isinstance(current_effect, self._typing_effect_type):
            if current_effect.line_index_in_terminal != -1: # Ensure line was created
                current_effect.current_display_text = current_effect.full_text # Show full text
                current_effect.current_char_index = len(current_effect.full_text)
                self.terminal.update_buffer_line(
                    current_effect.line_index_in_terminal, current_effect.current_display_text,
                    current_effect.fg_color, current_effect.bg_color, current_effect.bold
                )
        elif isinstance(current_effect, self._character_corruption_effect_type):
            if current_effect.line_index != -1 and current_effect.original_text is not None: # Check if start was successful
                self.terminal.update_buffer_line(
                    current_effect.line_index, current_effect.original_text,
                    current_effect.original_fg, current_effect.original_bg, current_effect.original_bold
                )
        elif isinstance(current_effect, self._text_flicker_effect_type):
            if current_effect.line_index != -1 and current_effect.original_text is not None:
                self.terminal.update_buffer_line(
                    current_effect.line_index, current_effect.original_text,
                    current_effect.original_fg, current_effect.original_bg, current_effect.original_bold
                )
        elif isinstance(current_effect, self._temporary_color_change_effect_type):
            if current_effect.line_index != -1 and current_effect.original_text is not None:
                 self.terminal.update_buffer_line(
                    current_effect.line_index, current_effect.original_text,
                    current_effect.original_fg, current_effect.original_bg, current_effect.original_bold
                )
        elif isinstance(current_effect, self._text_overlay_effect_type):
            current_effect.overlay_elements = []
        elif isinstance(current_effect, self._text_jiggle_effect_type):
            current_effect.char_offsets = [] # Clear jiggle when skipping

        # For TimedDelayEffect, skipping just means finishing it.
        
        current_effect.finish() # Generic finish call for all effects
        
        # The main update loop will then pop it and start the next one.