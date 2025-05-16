import pygame
from effects import get_theme_color, get_current_theme, set_theme as set_global_theme, TextOverlayEffect, TextJiggleEffect, COLOR_WHITE # Import effect classes
from file_system_handler import FileSystemHandler # Import the new handler

# --- Constants ---
DEFAULT_FONT_SIZE = 18
LINE_SPACING = 0 
MARGIN_X = 10
MARGIN_Y = 10

# Use a sentinel for "not provided" to distinguish from explicitly passing None
_NOT_PROVIDED = object()

# --- Text Rendering Function ---
def render_text_line(surface, text, position, fg_color, font, bg_color=None, bold=False, antialias=True):
    current_font = font
    original_bold_state = current_font.get_bold()
    if bold:
        current_font.set_bold(True)
    
    try:
        text_surface = current_font.render(text, antialias, fg_color, bg_color)
        surface.blit(text_surface, position)
    except Exception as e:
        print(f"Error rendering text '{text}' with fg={fg_color}, bg={bg_color}, bold={bold}: {e}")
        try:
            error_font = pygame.font.Font(None, DEFAULT_FONT_SIZE) 
            error_surface = error_font.render(f"[Render Error]", True, (255,0,0), (100,0,0))
            surface.blit(error_surface, position)
        except Exception as fallback_e:
            print(f"Fallback render error: {fallback_e}")
    finally:
        if bold and current_font.get_bold() != original_bold_state:
             current_font.set_bold(original_bold_state)

class Terminal:
    MARGIN_X = 5  # Default horizontal margin
    MARGIN_Y = 5  # Default vertical margin
    LINE_SPACING = 0 # font.get_linesize() should include appropriate spacing
 
    def __init__(self, width, height, font_name_prefs=None, completion_handler=None): # Add completion_handler
        self.width = width
        self.height = height
        self.new_font_path = "OpenDyslexicMono-Regular.otf"
        self.completion_handler = completion_handler # Store the handler

        try:
            self.font = pygame.font.Font(self.new_font_path, DEFAULT_FONT_SIZE)
            # print(f"Terminal loaded font: {self.new_font_path}") # Keep for potential future debug, but quiet for now
        except pygame.error as e_new_font:
            # print(f"Error loading font '{self.new_font_path}': {e_new_font}. Trying fallback system fonts.") # Keep for debug
            if font_name_prefs is None:
                font_name_prefs = ['consolas', 'couriernew', 'monospace']
            font_match_str = ','.join(font_name_prefs)
            try:
                FONT_NAME_FALLBACK = pygame.font.match_font(font_match_str)
                if FONT_NAME_FALLBACK is None:
                    # print(f"Could not match preferred system fonts. Using Pygame default font.") # Keep for debug
                    FONT_NAME_FALLBACK = pygame.font.get_default_font()
                self.font = pygame.font.Font(FONT_NAME_FALLBACK, DEFAULT_FONT_SIZE)
                # print(f"Terminal loaded fallback font: {FONT_NAME_FALLBACK}") # Keep for debug
            except pygame.error as e_fallback_system:
                # print(f"Error loading fallback system font '{FONT_NAME_FALLBACK if 'FONT_NAME_FALLBACK' in locals() else font_match_str}': {e_fallback_system}. Using Pygame default system font.") # Keep for debug
                try:
                    self.font = pygame.font.Font(None, DEFAULT_FONT_SIZE + 4) # Default Pygame font
                except pygame.error as e_absolute_fallback:
                    # print(f"Critical error: Could not load any font: {e_absolute_fallback}") # Keep for debug
                    pygame.quit()
                    raise RuntimeError("Failed to initialize any font for the terminal.") from e_absolute_fallback

        if self.font:
            original_linesize = self.font.get_linesize() # This is the value we should use
            font_character_height = self.font.get_height() # For reference
            self.line_height = original_linesize # Use font's natural line size
            if self.line_height < 1: self.line_height = 1 # Should not happen with valid font
            # print(f"Terminal Font: self.line_height set to font.get_linesize(): {self.line_height}. (Character height was: {font_character_height})") # Keep for debug
        else:
            self.line_height = DEFAULT_FONT_SIZE

        self.username = "hacker"
        self.hostname = "kali"
        self.fs_handler = FileSystemHandler(initial_username=self.username)
        self.font_color = COLOR_WHITE 
        self.buffer = []
        self.scroll_offset = 0
        self.input_string = ""
        self.cursor_char_pos = 0
        self.cursor_visible = True
        self.cursor_blink_timer = 0
        self.cursor_blink_interval = 500
        self.command_history = []
        self.history_index = -1
        self.current_input_temp = ""
        # Remove old completion state variables
        # self.last_completion_prefix = None
        # self.completion_options = []
        # self.completion_index = 0
        self.prompt_override = None

        self.apply_theme_colors()
        
        self.output_area_height = self.height - (2 * MARGIN_Y)
        if self.output_area_height < 0: self.output_area_height = 0
        self.input_line_height = self.line_height + LINE_SPACING
        self.max_lines_visible = (self.output_area_height - self.input_line_height) // (self.line_height + LINE_SPACING)
        if self.max_lines_visible < 0: self.max_lines_visible = 0
        # Remove old known_commands list, completion handler will get commands from config
        # self.known_commands = [...]

    # Add method to set completion handler after init
    def set_completion_handler(self, handler):
        self.completion_handler = handler

    def _update_prompt_string(self):
        path_for_prompt = self.fs_handler.get_current_path_str()
        if self.prompt_override is not None:
            self.prompt = self.prompt_override
        else:
            self.prompt = f"{self.username}@{self.hostname}:{path_for_prompt}$ "

    def set_prompt_override(self, prompt_str):
        self.prompt_override = prompt_str
        self._update_prompt_string()

    def clear_prompt_override(self):
        self.prompt_override = None
        self._update_prompt_string()

    def set_username(self, new_username):
        self.username = new_username
        self._update_prompt_string()

    def set_hostname(self, new_hostname):
        self.hostname = new_hostname
        self._update_prompt_string()

    def resize(self, new_width, new_height):
        self.width = new_width
        self.height = new_height
        if self.font:
            original_linesize = self.font.get_linesize()
            font_character_height = self.font.get_height() # For reference
            self.line_height = original_linesize # Use font's natural line size
            if self.line_height < 1: self.line_height = 1
        else:
            self.line_height = DEFAULT_FONT_SIZE
            # print("Warning: Terminal resize called but font not available. Using default line height.") # Keep for debug
        self.output_area_height = self.height - (2 * MARGIN_Y)
        if self.output_area_height < 0: self.output_area_height = 0
        self.max_lines_visible = (self.output_area_height - (self.line_height + LINE_SPACING)) // (self.line_height + LINE_SPACING)
        if self.max_lines_visible < 0: self.max_lines_visible = 0
        self.input_line_height = self.line_height + LINE_SPACING
        self.scroll_to_bottom()

    def _wrap_text(self, text, font, max_width):
        lines = []
        words = text.split(' ')
        current_line = ""
        for word_idx, word in enumerate(words):
            if "\n" in word:
                sub_words = word.split("\n")
                for i, sub_word in enumerate(sub_words):
                    test_line = sub_word if not current_line else current_line + " " + sub_word
                    if font.size(test_line)[0] <= max_width:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line.rstrip() if current_line else current_line)
                        if font.size(sub_word)[0] > max_width:
                            temp_word_line = ""
                            for char_val_idx, char_val in enumerate(sub_word):
                                if font.size(temp_word_line + char_val)[0] <= max_width:
                                    temp_word_line += char_val
                                else:
                                    lines.append(temp_word_line)
                                    temp_word_line = char_val
                                if char_val_idx == len(sub_word) -1 and temp_word_line:
                                     lines.append(temp_word_line)
                            current_line = "" 
                        else: 
                            current_line = sub_word
                    if i < len(sub_words) - 1:
                        if current_line: lines.append(current_line.rstrip() if current_line else current_line)
                        current_line = ""
                continue
            test_line = word if not current_line else current_line + " " + word
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line.rstrip() if current_line else current_line)
                if font.size(word)[0] > max_width:
                    temp_word_line = ""
                    for char_val_idx, char_val in enumerate(word):
                        if font.size(temp_word_line + char_val)[0] <= max_width:
                            temp_word_line += char_val
                        else:
                            lines.append(temp_word_line)
                            temp_word_line = char_val
                        if char_val_idx == len(word) -1 and temp_word_line: 
                            lines.append(temp_word_line)
                    current_line = "" 
                else: 
                    current_line = word
        if current_line:
            lines.append(current_line.rstrip() if current_line else current_line)
        if text.endswith('\n'):
            if not lines or lines[-1]:
                lines.append("")
        return lines if lines else [""]

    def add_line(self, text_content, fg_color=None, bg_color=None, bold=False, style_key=None):
        final_fg_color = fg_color
        if style_key:
            final_fg_color = get_theme_color(style_key)
        elif fg_color is None:
            final_fg_color = self.font_color
        available_width = self.width - (2 * MARGIN_X)
        if available_width <= 0: available_width = 1
        wrapped_lines = self._wrap_text(text_content, self.font, available_width)
        first_new_line_index = -1
        for i, line_segment in enumerate(wrapped_lines):
            line_data = (line_segment, final_fg_color, bg_color, bold)
            self.buffer.append(line_data)
            if i == 0:
                first_new_line_index = len(self.buffer) - 1
        if len(self.buffer) > self.max_lines_visible and \
           self.scroll_offset >= max(0, len(self.buffer) - self.max_lines_visible -1) :
             self.scroll_to_bottom()
        return first_new_line_index if wrapped_lines else len(self.buffer) -1

    def update_buffer_line(self, line_index, new_text, fg_color=_NOT_PROVIDED, bg_color=_NOT_PROVIDED, bold=_NOT_PROVIDED):
        if 0 <= line_index < len(self.buffer):
            old_text, old_fg, old_bg, old_bold = self.buffer[line_index]
            final_text = new_text 
            final_fg = fg_color if fg_color is not _NOT_PROVIDED else old_fg
            final_bg = bg_color if bg_color is not _NOT_PROVIDED else old_bg
            final_bold = bold if bold is not _NOT_PROVIDED else old_bold
            self.buffer[line_index] = (final_text, final_fg, final_bg, final_bold)
            return True
        return False

    def get_buffer_line_details(self, line_index):
        if 0 <= line_index < len(self.buffer):
            return self.buffer[line_index]
        return None

    def scroll_up(self, amount=None):
        scroll_amount = amount
        if scroll_amount is None: 
            scroll_amount = self.max_lines_visible // 3 if self.max_lines_visible > 0 else 1
        if scroll_amount == 0: scroll_amount = 1
        self.scroll_offset = max(0, self.scroll_offset - scroll_amount)

    def scroll_down(self, amount=None):
        scroll_amount = amount
        if scroll_amount is None: 
            scroll_amount = self.max_lines_visible // 3 if self.max_lines_visible > 0 else 1
        if scroll_amount == 0: scroll_amount = 1
        max_scroll = max(0, len(self.buffer) - self.max_lines_visible)
        self.scroll_offset = min(max_scroll, self.scroll_offset + scroll_amount)
        
    def scroll_to_bottom(self):
        self.scroll_offset = max(0, len(self.buffer) - self.max_lines_visible)

    def clear_buffer(self):
        self.buffer = []
        self.scroll_offset = 0

    def render(self, surface, effect_manager=None):
        surface.fill(self.bg_color)
        start_index = self.scroll_offset
        end_index = min(len(self.buffer), self.scroll_offset + self.max_lines_visible)
        current_y = self.MARGIN_Y
        active_jiggle_effect = None
        if effect_manager and effect_manager.effect_queue and isinstance(effect_manager.effect_queue[0], TextJiggleEffect):
            active_jiggle_effect = effect_manager.effect_queue[0]

        for i in range(start_index, end_index):
            text, fg_color_stored, bg_color, is_bold = self.buffer[i]
            if active_jiggle_effect and active_jiggle_effect.line_index == i:
                original_details_jiggle, char_offsets_jiggle = active_jiggle_effect.get_jiggle_data()
                if original_details_jiggle and len(char_offsets_jiggle) == len(original_details_jiggle[0]):
                    current_x_char_jiggle = self.MARGIN_X
                    jiggle_text, jiggle_fg, jiggle_bg, jiggle_bold = original_details_jiggle
                    for char_idx, char_visual in enumerate(jiggle_text):
                        dx, dy = char_offsets_jiggle[char_idx]
                        char_pos = (current_x_char_jiggle + dx, current_y + dy)
                        render_text_line(surface, char_visual, char_pos,
                                         jiggle_fg, self.font, bg_color=jiggle_bg, bold=jiggle_bold)
                        current_x_char_jiggle += self.font.size(char_visual)[0]
                else: 
                    render_text_line(surface, text, (self.MARGIN_X, current_y),
                                     fg_color_stored, self.font, bg_color=bg_color, bold=is_bold)
            else: 
                if text.startswith(self.prompt) and fg_color_stored == self.font_color:
                    prompt_part = self.prompt
                    command_part = text[len(self.prompt):]
                    prompt_render_pos = (self.MARGIN_X, current_y)
                    render_text_line(surface, prompt_part, prompt_render_pos,
                                     self.prompt_color, self.font, bg_color=bg_color, bold=is_bold)
                    prompt_width = self.font.size(prompt_part)[0]
                    command_render_pos = (self.MARGIN_X + prompt_width, current_y)
                    render_text_line(surface, command_part, command_render_pos,
                                     self.font_color, self.font,
                                     bg_color=bg_color, bold=is_bold)
                else: 
                    render_text_line(surface, text, (self.MARGIN_X, current_y),
                                     fg_color_stored, self.font, bg_color=bg_color, bold=is_bold)
            current_y += self.line_height + self.LINE_SPACING
        
        num_rendered_lines = end_index - start_index
        # Use current_y which is the position after the last rendered buffer line
        input_line_y_pos = current_y
        max_input_y = self.height - MARGIN_Y - self.input_line_height
        if input_line_y_pos > max_input_y:
            input_line_y_pos = max_input_y
            if input_line_y_pos < self.MARGIN_Y : input_line_y_pos = self.MARGIN_Y

        input_text_render_pos = (self.MARGIN_X, input_line_y_pos)
        prompt_width = 0
        if self.prompt:
            render_text_line(surface, self.prompt, input_text_render_pos,
                             self.prompt_color, self.font)
            prompt_width = self.font.size(self.prompt)[0]
        render_text_line(surface, self.input_string,
                         (input_text_render_pos[0] + prompt_width, input_text_render_pos[1]),
                         self.font_color, self.font)

        if self.cursor_visible:
            text_before_cursor = self.input_string[:self.cursor_char_pos]
            cursor_offset_x = self.font.size(text_before_cursor)[0]
            cursor_x = self.MARGIN_X + prompt_width + cursor_offset_x
            cursor_y = input_text_render_pos[1]
            cursor_char_to_render = " "
            if self.cursor_char_pos < len(self.input_string):
                cursor_char_to_render = self.input_string[self.cursor_char_pos]
            char_width, _ = self.font.size(cursor_char_to_render)
            if char_width == 0: char_width = self.font.size(" ")[0]
            y_offset_for_block = 0
            if self.font.get_height() > self.line_height:
                y_offset_for_block = (self.font.get_height() - self.line_height) // 2
            cursor_block_actual_y = cursor_y + y_offset_for_block
            cursor_rect = pygame.Rect(cursor_x, cursor_block_actual_y, char_width, self.line_height)

            if self.cursor_visible: 
                current_theme = get_current_theme()
                cursor_block_bg_color = get_theme_color('cursor_bg', current_theme)
                if cursor_block_bg_color == COLOR_WHITE: 
                    cursor_block_bg_color = self.font_color
                char_on_cursor_fg_color = get_theme_color('cursor_fg', current_theme)
                if char_on_cursor_fg_color == COLOR_WHITE:
                     char_on_cursor_fg_color = self.bg_color
                pygame.draw.rect(surface, cursor_block_bg_color, cursor_rect)
                if self.cursor_char_pos < len(self.input_string): 
                    render_text_line(surface, cursor_char_to_render, (cursor_x, cursor_y),
                                     char_on_cursor_fg_color, self.font, bold=False) # bold is already a kwarg here

        if effect_manager:
            if effect_manager.effect_queue and isinstance(effect_manager.effect_queue[0], TextOverlayEffect):
                active_overlay_effect = effect_manager.effect_queue[0]
                overlay_elements = active_overlay_effect.get_overlay_elements()
                for char, x, y, color in overlay_elements:
                    render_text_line(surface, char, (x,y), fg_color=color, font=self.font)

    def apply_theme_colors(self):
        old_default_fg = self.font_color if hasattr(self, 'font_color') else None
        new_theme = get_current_theme()
        new_default_fg = get_theme_color('default_fg', new_theme)
        new_bg_color = get_theme_color('default_bg', new_theme)
        new_prompt_color = get_theme_color('prompt', new_theme)
        self.font_color = new_default_fg
        self.bg_color = new_bg_color
        self.prompt_color = new_prompt_color
        if old_default_fg is not None:
            for i, (text, fg, bg, bold) in enumerate(self.buffer):
                if fg == old_default_fg:
                    self.buffer[i] = (text, new_default_fg, bg, bold)
        self._update_prompt_string()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.cursor_char_pos = max(0, self.cursor_char_pos - 1)
                self.cursor_visible = True 
                self.cursor_blink_timer = 0
            elif event.key == pygame.K_RIGHT:
                self.cursor_char_pos = min(len(self.input_string), self.cursor_char_pos + 1)
                self.cursor_visible = True
                self.cursor_blink_timer = 0
            elif event.key == pygame.K_BACKSPACE:
                if self.cursor_char_pos > 0:
                    self.input_string = self.input_string[:self.cursor_char_pos-1] + self.input_string[self.cursor_char_pos:]
                    self.cursor_char_pos -= 1
                self.history_index = -1
                # Reset completion state with new handler if backspace is pressed
                if self.completion_handler:
                    self.completion_handler._last_input_line = ""
                    self.completion_handler._last_suggestions = []
                    self.completion_handler._suggestion_index = -1
                self.last_completion_prefix = None
                self.completion_options = []
                self.completion_index = 0
            elif event.key == pygame.K_DELETE:
                if self.cursor_char_pos < len(self.input_string):
                    self.input_string = self.input_string[:self.cursor_char_pos] + self.input_string[self.cursor_char_pos+1:]
                # Reset completion state with new handler if delete is pressed
                if self.completion_handler:
                    self.completion_handler._last_input_line = ""
                    self.completion_handler._last_suggestions = []
                    self.completion_handler._suggestion_index = -1
                self.last_completion_prefix = None
                self.completion_options = []
                self.completion_index = 0
            elif event.key == pygame.K_RETURN:
                entered_command = self.input_string.strip()
                if entered_command: 
                    self.add_line(self.prompt + entered_command, fg_color=self.font_color)
                    if not self.command_history or self.command_history[-1] != entered_command:
                        self.command_history.append(entered_command)
                    self.input_string = ""
                    self.cursor_char_pos = 0 
                    self.history_index = -1
                    return entered_command
            elif event.key == pygame.K_UP:
                if self.command_history:
                    if self.history_index == -1: 
                        self.current_input_temp = self.input_string 
                        self.history_index = len(self.command_history) - 1
                    elif self.history_index > 0:
                        self.history_index -= 1
                    self.input_string = self.command_history[self.history_index]
                    self.cursor_char_pos = len(self.input_string) 
            elif event.key == pygame.K_DOWN:
                if self.command_history:
                    if self.history_index != -1 and self.history_index < len(self.command_history) - 1:
                        self.history_index += 1
                        self.input_string = self.command_history[self.history_index]
                        self.cursor_char_pos = len(self.input_string)
                    elif self.history_index == len(self.command_history) - 1:
                        self.history_index = -1
                        self.input_string = self.current_input_temp
                        self.cursor_char_pos = len(self.input_string)
            elif event.key == pygame.K_TAB:
                if self.completion_handler:
                    # Get suggestions from the handler
                    suggestions, common_prefix = self.completion_handler.get_suggestions(
                        self.input_string, self.cursor_char_pos
                    )

                    if len(suggestions) == 1:
                        # Unique completion
                        completed_text = suggestions[0]
                        # Insert the completion
                        # Find the start of the word/path being completed
                        last_space = self.input_string.rfind(" ", 0, self.cursor_char_pos)
                        last_slash = self.input_string.rfind("/", 0, self.cursor_char_pos)
                        start_pos = max(last_space, last_slash) + 1
                        self.input_string = self.input_string[:start_pos] + completed_text + self.input_string[self.cursor_char_pos:]
                        self.cursor_char_pos = start_pos + len(completed_text)

                        # Add space or '/' based on completion type (e.g., directory)
                        # The completion handler adds '/' for directories already.
                        # Add space for commands unless it's a directory.
                        if not completed_text.endswith('/'):
                             # Check if it's a command that shouldn't auto-add space (customize as needed)
                             no_space_commands = {"clear", "pwd", "quit", "exit", "fullscreen", "windowed"}
                             # Basic check: if it contains '/', assume it's a path/module, don't add space
                             if '/' not in completed_text and completed_text not in no_space_commands:
                                  self.input_string += " "
                                  self.cursor_char_pos += 1

                    elif len(suggestions) > 1:
                        # Multiple suggestions
                        # Find the start of the word/path being completed
                        last_space = self.input_string.rfind(" ", 0, self.cursor_char_pos)
                        last_slash = self.input_string.rfind("/", 0, self.cursor_char_pos)
                        start_pos = max(last_space, last_slash) + 1

                        if common_prefix and len(common_prefix) > (self.cursor_char_pos - start_pos):
                            # Insert common prefix if it's longer than what's typed
                            prefix_to_insert = common_prefix
                            self.input_string = self.input_string[:start_pos] + prefix_to_insert + self.input_string[self.cursor_char_pos:]
                            self.cursor_char_pos = start_pos + len(prefix_to_insert)
                        else:
                            # Cycle through suggestions on subsequent tabs
                            cycled_suggestion = self.completion_handler.cycle_suggestion()
                            if cycled_suggestion:
                                # The end of the segment to replace is the current cursor position
                                end_pos = self.cursor_char_pos

                                # Replace the current word/path with the cycled suggestion
                                self.input_string = self.input_string[:start_pos] + cycled_suggestion + self.input_string[end_pos:]
                                self.cursor_char_pos = start_pos + len(cycled_suggestion)

                                # Add space or '/' based on completion type (e.g., directory)
                                # The completion handler adds '/' for directories already.
                                # Add space for commands unless it's a directory.
                                if not cycled_suggestion.endswith('/'):
                                     # Check if it's a command that shouldn't auto-add space (customize as needed)
                                     no_space_commands = {"clear", "pwd", "quit", "exit", "fullscreen", "windowed"}
                                     # Basic check: if it contains '/', assume it's a path/module, don't add space
                                     if '/' not in cycled_suggestion and cycled_suggestion not in no_space_commands:
                                          self.input_string += " "
                                          self.cursor_char_pos += 1
                            # Optionally display all suggestions if no common prefix and not cycling
                            # else:
                            #     self.add_line(" ".join(suggestions)) # Display options

                # Reset history index if tab is pressed
                self.history_index = -1
            elif event.unicode:
                # This check ensures that pressing Tab doesn't also insert a tab character if event.unicode happens to be '\t'
                if event.unicode and event.key != pygame.K_TAB:
                    self.input_string = self.input_string[:self.cursor_char_pos] + event.unicode + self.input_string[self.cursor_char_pos:]
                    self.cursor_char_pos += len(event.unicode)
                    self.history_index = -1
                    # Reset completion state on any other key press
                    if self.completion_handler:
                         self.completion_handler._last_input_line = "" # Reset handler's internal state too
                         self.completion_handler._last_suggestions = []
                         self.completion_handler._suggestion_index = -1
                    self.last_completion_prefix = None
                    self.completion_options = []
                    self.completion_index = 0
        return None

    # Remove old _get_common_prefix method
    # def _get_common_prefix(self, strings): ...

    def update_cursor(self, dt):
        self.cursor_blink_timer += dt
        while self.cursor_blink_timer >= self.cursor_blink_interval:
            self.cursor_blink_timer -= self.cursor_blink_interval # Subtract one interval
            self.cursor_visible = not self.cursor_visible
        # Stray theme lines removed.
        # Duplicated handle_input and update_cursor methods removed.