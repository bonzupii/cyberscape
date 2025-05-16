import pygame
import random
from game_state import game_state_manager, STATE_DISCLAIMER, STATE_MAIN_TERMINAL, STATE_MINIGAME, STATE_MSFCONSOLE, STATE_ROLE_SELECTION, STATE_PUZZLE_ACTIVE
from commands_config import COMMAND_ACCESS, ROLE_WHITE_HAT, ROLE_GREY_HAT, ROLE_BLACK_HAT # Import from new config
from terminal_renderer import Terminal, render_text_line as render_text # render_text used for disclaimer
from effects import set_theme, get_current_theme, THEMES, EffectManager # For theme command and effects
# Import command processing functions and handler dictionaries
from command_handler import (
    process_main_terminal_command,
    process_msfconsole_command,
    MAIN_COMMAND_HANDLERS, # Import the handler dict
    MSF_COMMAND_HANDLERS   # Import the handler dict
)
# Remove old MSF tab completion import: handle_msfconsole_tab_completion
from puzzle_manager import PuzzleManager # Import PuzzleManager
from completion_handler import CompletionHandler # Import the new handler
# game_state constants like STATE_MAIN_TERMINAL, STATE_MSFCONSOLE are already imported from game_state


# --- Constants ---
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Cyberscape: Digital Dread"
FPS = 60

# --- Colors ---
BLACK = (0, 0, 0)
# WHITE = (255, 255, 255) # Retained for reference if needed later
 
# --- Pygame Initialization ---
pygame.init()
pygame.mixer.init() # Initialize the mixer
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption(WINDOW_TITLE)
pygame.key.set_repeat(500, 50) # Enable key repeat: 500ms delay, 50ms interval
clock = pygame.time.Clock()

# --- Sound Effects ---
keypress_sound = None
try:
    keypress_sound = pygame.mixer.Sound("sounds/keypress.wav")
    # print("Successfully loaded sounds/keypress.wav") # Keep for debug
except pygame.error as e:
    # print(f"Warning: Could not load sounds/keypress.wav - {e}") # Keep for debug
    # print("Game will continue without keypress sound effect.") # Keep for debug
    pass # Silently continue if sound fails to load

# --- Disclaimer Screen Fonts ---
NEW_FONT_NAME = "OpenDyslexicMono-Regular.otf" # Added by user
# MONO_FONT_PREFS = ['Consolas', 'DejaVu Sans Mono', 'Liberation Mono', 'Courier New', 'monospace'] # Retained for fallback reference
DISCLAIMER_FONT_SIZE_LARGE = 26 # Adjusted from 32
DISCLAIMER_FONT_SIZE_MEDIUM = 13 # Adjusted from 20 (approx 35% reduction for skull)
DISCLAIMER_FONT_SIZE_SMALL = 16 # Adjusted from 20

def load_monospace_font(size):
    font_to_load = None
    try:
        # Attempt to load the new font directly
        font_to_load = pygame.font.Font(NEW_FONT_NAME, size)
        # print(f"Disclaimer: Successfully loaded font '{NEW_FONT_NAME}' with size {size}.") # Keep for debug
        return font_to_load
    except pygame.error as e:
        # print(f"Disclaimer: Warning - Could not load '{NEW_FONT_NAME}' with size {size} ({e}).") # Keep for debug
        # Fallback to Pygame's default font if the new one fails
        try:
            font_to_load = pygame.font.Font(None, size)
            # print(f"Disclaimer: Successfully loaded Pygame default font with size {size} as fallback.") # Keep for debug
            return font_to_load
        except pygame.error as e_fallback:
            # print(f"Disclaimer: Critical error - Could not load Pygame default font with size {size} ({e_fallback}).") # Keep for debug
            # This is a critical failure; the game might not be able to render text.
            # Consider raising an exception or handling it more gracefully if this occurs.
            pygame.quit() # Quit pygame if no font can be loaded at all
            raise RuntimeError(f"Failed to initialize any font for disclaimer (size {size}).") from e_fallback

disclaimer_mono_font_large = load_monospace_font(DISCLAIMER_FONT_SIZE_LARGE)
disclaimer_mono_font_medium = load_monospace_font(DISCLAIMER_FONT_SIZE_MEDIUM)
disclaimer_mono_font_small = load_monospace_font(DISCLAIMER_FONT_SIZE_SMALL)


# --- Game State ---
# GameStateManager is initialized in game_state.py
# Initial state is STATE_DISCLAIMER
 
# --- Terminal Instance ---
terminal = Terminal(WINDOW_WIDTH, WINDOW_HEIGHT) # Instantiate Terminal first

# --- File System Handler (accessed via terminal) ---
# fs_handler is initialized within Terminal, so we access it via terminal.fs_handler

# --- Command Configurations (for CompletionHandler) ---
# Combine command handlers for the completion handler
command_configs_for_completion = {
    'main': MAIN_COMMAND_HANDLERS,
    'msf': MSF_COMMAND_HANDLERS
    # Add puzzle context commands if they have a separate handler dict later
}

# --- Completion Handler ---
completion_handler = CompletionHandler(
    game_state_manager=game_state_manager,
    file_system_handler=terminal.fs_handler, # Pass the handler from the terminal instance
    command_configs=command_configs_for_completion
)

# --- Pass Completion Handler to Terminal ---
terminal.set_completion_handler(completion_handler) # Add this method to Terminal class

# --- Initial boot messages ---
terminal.add_line("Cyberscape: Digital Dread - Booting...", style_key='highlight')
terminal.add_line("System Initialized.", style_key='success')
terminal.add_line("Waiting for user acknowledgement of disclaimer...")

# --- Effect Manager ---
effect_manager = EffectManager(terminal) # Pass the terminal instance

# --- Puzzle Manager ---
puzzle_manager = PuzzleManager() # Instantiate PuzzleManager

# --- ASCII Skull Art for Disclaimer ---
# Note: Leading spaces for the first line of the skull art use an invisible character
# "‎" to ensure correct rendering alignment.
SKULL_DETAILED_FRAME_CLOSED = r"""
‎ ‎ ‎ ‎ ‎ .----.
  .-"      "-.
 /            \
|              |
|,  .-.  .-.  ,|
| )(__/  \__)( |
|/     /\     \|
(_     ^^     _)
 \__|IIIIII|__/
  | \IIIIII/ |
  \          /
   `--------`
                      
"""
SKULL_DETAILED_FRAME_OPEN = r"""
‎ ‎ ‎ ‎ ‎ .----.
  .-"      "-.
 /            \
|              |
|,  .-.  .-.  ,|
| )(__/  \__)( |
|/     /\     \|
(_     ^^     _)
 \__|IIIIII|__/
  | |      | |
  | \IIIIII/ |
  \          /
   `--------`
"""
# Process skull frames carefully to ensure consistent line counts and preserve alignment
skull_frame_lines_closed_raw = SKULL_DETAILED_FRAME_CLOSED.strip().split('\n')
skull_frame_lines_open_raw = SKULL_DETAILED_FRAME_OPEN.strip().split('\n')

skull_frame_lines_closed = [line.rstrip() for line in skull_frame_lines_closed_raw]
skull_frame_lines_open = [line.rstrip() for line in skull_frame_lines_open_raw]

# Pad the shorter frame to match the length of the longer one
max_lines = max(len(skull_frame_lines_closed), len(skull_frame_lines_open))

while len(skull_frame_lines_closed) < max_lines:
    skull_frame_lines_closed.append("")
while len(skull_frame_lines_open) < max_lines:
    skull_frame_lines_open.append("")
 
skull_frames = [skull_frame_lines_closed, skull_frame_lines_open]
current_skull_frame_index = 0 # Initialize skull animation index
skull_animation_timer = 0
SKULL_ANIMATION_INTERVAL = 350 # milliseconds
GLITCH_CHARS = ['*', '#', '$', '%', '&', '?', '§', '!', '~', '@', '^']
CHARACTER_CORRUPTION_CHANCE = 0.03 # 3% chance per character

# --- Main Game Loop ---
running = True
while running:
    dt = clock.tick(FPS) # Delta time in milliseconds

    # --- Skull Animation Update (only for disclaimer state) ---
    if game_state_manager.is_state(STATE_DISCLAIMER):
        skull_animation_timer += dt
        if skull_animation_timer >= SKULL_ANIMATION_INTERVAL:
            skull_animation_timer %= SKULL_ANIMATION_INTERVAL
            current_skull_frame_index = (current_skull_frame_index + 1) % len(skull_frames)

    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            WINDOW_WIDTH = event.w
            WINDOW_HEIGHT = event.h
            screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
            terminal.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # Play keypress sound for any keydown event, if sound is loaded
        if event.type == pygame.KEYDOWN and keypress_sound:
            keypress_sound.play()

        if game_state_manager.is_state(STATE_DISCLAIMER):
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Reset skull animation for next time disclaimer is shown (if ever)
                    current_skull_frame_index = 0
                    skull_animation_timer = 0
                    game_state_manager.change_state(STATE_ROLE_SELECTION)
                    terminal.clear_buffer() # Clear boot messages
                    terminal.add_line("Ethical Protocols Acknowledged. System Integrity Nominal.", style_key='success')
                    terminal.add_line("Initializing User Profile Interface...", style_key='highlight')
                    terminal.add_line(" ")
                    terminal.add_line("Choose Your Path:", style_key='highlight')
                    terminal.add_line("-------------------", style_key='highlight')
                    terminal.add_line("1. White Hat - The Defender. Uphold the light, protect the innocent.", style_key='success')
                    terminal.add_line("                 (Access to defensive tools, system analysis, integrity checks)", style_key='comment')
                    terminal.add_line("2. Grey Hat  - The Balance. Walk the line, for the greater good... or profit.", style_key='default_fg')
                    terminal.add_line("                 (Versatile toolkit, access to restricted systems, information brokering)", style_key='comment')
                    terminal.add_line("3. Black Hat - The Shadow. Embrace the chaos, exploit the vulnerabilities.", style_key='error')
                    terminal.add_line("                 (Offensive tools, stealth mechanics, network exploitation)", style_key='comment')
                    terminal.add_line("-------------------")
                    terminal.add_line("Enter number (1-3) to select your operational alignment:")
                elif event.key == pygame.K_ESCAPE: # Allow exit from disclaimer
                    running = False
        elif game_state_manager.is_state(STATE_ROLE_SELECTION):
            if event.type == pygame.KEYDOWN:
                role_chosen = None
                role_name_str = ""
                if event.key == pygame.K_1 or event.key == pygame.K_KP_1:
                    role_chosen = ROLE_WHITE_HAT
                    role_name_str = "White Hat"
                elif event.key == pygame.K_2 or event.key == pygame.K_KP_2:
                    role_chosen = ROLE_GREY_HAT
                    role_name_str = "Grey Hat"
                elif event.key == pygame.K_3 or event.key == pygame.K_KP_3:
                    role_chosen = ROLE_BLACK_HAT
                    role_name_str = "Black Hat"
                elif event.key == pygame.K_ESCAPE:
                    running = False

                if role_chosen:
                    game_state_manager.set_player_role(role_chosen)
                    terminal.clear_buffer()
                    terminal.add_line(f"Operational Alignment: {role_name_str} confirmed.", style_key='success')

                    if role_chosen == ROLE_WHITE_HAT:
                        terminal.set_username("guardian")
                        terminal.set_hostname("aegis-01")
                        terminal.add_line("System protocols updated. Defensive measures online.", style_key='success')
                        terminal.add_line("Your mission: Protect the innocent. Uphold the light.", style_key='highlight')
                    elif role_chosen == ROLE_GREY_HAT:
                        terminal.set_username("shadow_walker")
                        terminal.set_hostname("nexus-7")
                        terminal.add_line("Network access rerouted. Anonymity cloak engaged.", style_key='highlight')
                        terminal.add_line("The lines blur. Your path is your own to forge.", style_key='default_fg')
                    elif role_chosen == ROLE_BLACK_HAT:
                        terminal.set_username("void_reaver")
                        terminal.set_hostname("hades-net")
                        terminal.add_line("Firewalls bypassed. Root access granted. The system is yours.", style_key='error')
                        terminal.add_line("Embrace the chaos. Exploit the vulnerabilities.", style_key='error')
                    
                    # Display background info
                    background = game_state_manager.get_player_attribute('background')
                    motivation = game_state_manager.get_player_attribute('motivation')
                    if background:
                        terminal.add_line(f"Background: {background}", style_key='comment')
                    if motivation:
                        terminal.add_line(f"Motivation: {motivation}", style_key='comment')

                    terminal.add_line(" ")
                    terminal.add_line("Welcome to the Cyberscape.", style_key='highlight')
                    terminal.add_line("Type 'help' for a list of commands.")
                    game_state_manager.change_state(STATE_MAIN_TERMINAL)
        elif game_state_manager.is_state(STATE_MAIN_TERMINAL):
            # If an effect is active, it might consume some input or prevent normal terminal input
            if effect_manager.is_effect_active():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: # Allow skipping current effect with ESC
                        effect_manager.skip_current_effect()
                    # Other input generally ignored during an effect sequence
            else: # No effect active, normal terminal input
                command_entered = None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False # Exit game
                    elif event.key == pygame.K_PAGEUP:
                        terminal.scroll_up()
                    elif event.key == pygame.K_PAGEDOWN:
                        terminal.scroll_down()
                    elif event.key == pygame.K_HOME:
                        terminal.scroll_offset = 0
                    elif event.key == pygame.K_END:
                        terminal.scroll_to_bottom()
                    else:
                        # This is where text input and tab/enter/backspace are handled
                        command_entered = terminal.handle_input(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4: # Scroll up
                        terminal.scroll_up(amount=3)
                    elif event.button == 5: # Scroll down
                        terminal.scroll_down(amount=3)

                if command_entered is not None:
                    # Call the extracted command processor, now passing puzzle_manager
                    should_continue, screen_action = process_main_terminal_command(command_entered, terminal, game_state_manager, effect_manager, puzzle_manager)
                    if not should_continue:
                        running = False # Command handler signaled to quit
                    
                    if screen_action:
                        action_type = screen_action.get('type')
                        if action_type == 'set_resolution':
                            new_w = screen_action.get('width')
                            new_h = screen_action.get('height')
                            if new_w and new_h:
                                WINDOW_WIDTH = new_w
                                WINDOW_HEIGHT = new_h
                                screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
                                terminal.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
                                terminal.add_line(f"Screen resolution set to {WINDOW_WIDTH}x{WINDOW_HEIGHT}.", style_key='success')
                        elif action_type == 'fullscreen':
                            try:
                                display_info = pygame.display.Info()
                                WINDOW_WIDTH = display_info.current_w
                                WINDOW_HEIGHT = display_info.current_h
                                screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN | pygame.RESIZABLE)
                                terminal.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
                                terminal.add_line(f"Switched to fullscreen mode ({WINDOW_WIDTH}x{WINDOW_HEIGHT}).", style_key='success')
                            except pygame.error as e:
                                terminal.add_line(f"Error switching to fullscreen: {e}", style_key='error')
                                WINDOW_WIDTH = 1280 # Fallback
                                WINDOW_HEIGHT = 720
                                screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
                                terminal.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
                        elif action_type == 'windowed':
                            current_w, current_h = screen.get_size()
                            if current_w > 1920 or current_h > 1080: # Sensible default if coming from large fullscreen
                                WINDOW_WIDTH = 1280
                                WINDOW_HEIGHT = 720
                            # Else, WINDOW_WIDTH and WINDOW_HEIGHT should be the last user-set windowed size or default
                            try:
                                screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
                                terminal.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
                                terminal.add_line(f"Switched to windowed mode ({WINDOW_WIDTH}x{WINDOW_HEIGHT}).", style_key='success')
                            except pygame.error as e:
                                terminal.add_line(f"Error switching to windowed mode: {e}", style_key='error')
 
                # pygame.TEXTINPUT event is handled by terminal.handle_input via event.unicode
        elif game_state_manager.is_state(STATE_PUZZLE_ACTIVE):
            command_entered = None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Allow exiting puzzle with ESCAPE, then process as 'exit_puzzle' command
                    command_entered = "exit_puzzle"
                elif event.key == pygame.K_PAGEUP:
                    terminal.scroll_up()
                elif event.key == pygame.K_PAGEDOWN:
                    terminal.scroll_down()
                elif event.key == pygame.K_HOME:
                    terminal.scroll_offset = 0
                elif event.key == pygame.K_END:
                    terminal.scroll_to_bottom()
                else:
                    command_entered = terminal.handle_input(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4: # Scroll up
                    terminal.scroll_up(amount=3)
                elif event.button == 5: # Scroll down
                    terminal.scroll_down(amount=3)
            
            if command_entered is not None:
                # Process puzzle-related commands (solve, hint, exit_puzzle)
                should_continue, screen_action = process_main_terminal_command(command_entered, terminal, game_state_manager, effect_manager, puzzle_manager)
                if not should_continue:
                    running = False
                # Screen actions are unlikely from puzzle commands but handle if necessary
                if screen_action:
                    # (Handle screen actions similarly to STATE_MAIN_TERMINAL if any are defined for puzzle commands)
                    pass # Placeholder for now

        elif game_state_manager.is_state(STATE_MSFCONSOLE):
            # MSFCONSOLE Event Handling
            msf_command_entered = None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    terminal.clear_prompt_override()
                    game_state_manager.change_state(STATE_MAIN_TERMINAL)
                    terminal.clear_buffer()
                    terminal.add_line("Exited msfconsole.", style_key="highlight")
                    terminal.add_line("Type 'help' for a list of commands.")
                elif event.key == pygame.K_PAGEUP:
                    terminal.scroll_up()
                elif event.key == pygame.K_PAGEDOWN:
                    terminal.scroll_down()
                elif event.key == pygame.K_HOME:
                    terminal.scroll_offset = 0
                elif event.key == pygame.K_END:
                    terminal.scroll_to_bottom()
                # Tab completion is now handled within terminal.handle_input
                # elif event.key == pygame.K_TAB:
                #     # Old MSF handler removed
                #     pass
                else:
                    msf_command_entered = terminal.handle_input(event)
            elif event.type == pygame.MOUSEBUTTONDOWN: # Add this block for MSFCONSOLE
                if event.button == 4: # Scroll up
                    terminal.scroll_up(amount=3)
                elif event.button == 5: # Scroll down
                    terminal.scroll_down(amount=3)
            
            if msf_command_entered is not None:
                process_msfconsole_command(msf_command_entered, terminal, game_state_manager, effect_manager)
    # --- Game Logic Updates ---
    # Update cursor only for states that use it for input
    if game_state_manager.is_state(STATE_MAIN_TERMINAL) or \
       game_state_manager.is_state(STATE_MSFCONSOLE) or \
       game_state_manager.is_state(STATE_PUZZLE_ACTIVE):
        # For puzzle state, cursor should be active unless an effect is running (e.g. typing out feedback)
        if not effect_manager.is_effect_active() or \
           game_state_manager.is_state(STATE_MSFCONSOLE) or \
           (game_state_manager.is_state(STATE_PUZZLE_ACTIVE) and not effect_manager.is_effect_active()):
            terminal.update_cursor(dt)
    
    # Update effects regardless of state, if they are active (unless a state specifically disallows it)
    effect_manager.update(dt)


    # --- Rendering ---
    screen.fill(BLACK) # Clear screen with black (can be redundant if terminal fills)

    if game_state_manager.is_state(STATE_DISCLAIMER):
        # Fonts are now pre-loaded: disclaimer_mono_font_large, disclaimer_mono_font_medium, disclaimer_mono_font_small

        # --- Render Skull ---
        skull_y_start = 30
        skull_color = (0, 200, 50) # Glitchy green
        current_skull_art_lines = skull_frames[current_skull_frame_index]
        
        # Calculate max width of skull lines for centering
        max_skull_line_width = 0
        if current_skull_art_lines:
             max_skull_line_width = max(disclaimer_mono_font_medium.size(line)[0] for line in current_skull_art_lines)
        
        skull_x_start = WINDOW_WIDTH // 2 - max_skull_line_width // 2
        
        for i, line in enumerate(current_skull_art_lines):
            line_y_pos = skull_y_start + i * disclaimer_mono_font_medium.get_linesize()
            if i == 0: # Special handling for the first line
                content_part = line.lstrip()
                # Get the original leading whitespace string
                num_leading_spaces = len(line) - len(content_part)
                leading_spaces_original_str = line[:num_leading_spaces]
                
                # Calculate the visual width of these leading spaces
                leading_spaces_width = 0
                if leading_spaces_original_str: # Ensure there are spaces to measure
                    leading_spaces_width = disclaimer_mono_font_medium.size(leading_spaces_original_str)[0]
                
                # Render the content part, visually offset by its original leading spaces, from skull_x_start
                render_x_position = skull_x_start + leading_spaces_width
                render_text(screen, content_part, (render_x_position, line_y_pos), fg_color=skull_color, font=disclaimer_mono_font_medium)
            else:
                # Render other lines normally, their leading spaces are respected
                render_text(screen, line, (skull_x_start, line_y_pos), fg_color=skull_color, font=disclaimer_mono_font_medium)
        
        y_offset = skull_y_start + len(current_skull_art_lines) * disclaimer_mono_font_medium.get_linesize() + 5 # Further reduced from 10


        # --- Render Distorted Title ---
        title_text = "WARNING: Mature Audiences Only"
        original_title_color = (255, 100, 100)
        title_base_y = y_offset
        
        # Calculate total width of title for centering
        total_title_width = disclaimer_mono_font_large.size(title_text)[0]
        current_char_x = WINDOW_WIDTH // 2 - total_title_width // 2

        for char_idx, char_visual in enumerate(title_text):
            dx = random.randint(-1, 1)
            dy = random.randint(-1, 1)
            # Slightly vary color, keeping red prominent
            char_color_r = original_title_color[0]
            char_color_g = max(0, min(255, original_title_color[1] + random.randint(-20, 20)))
            char_color_b = max(0, min(255, original_title_color[2] + random.randint(-20, 20)))
            distorted_char_color = (char_color_r, char_color_g, char_color_b)
            
            char_pos = (current_char_x + dx, title_base_y + dy)
            render_text(screen, char_visual, char_pos, fg_color=distorted_char_color, font=disclaimer_mono_font_large)
            current_char_x += disclaimer_mono_font_large.size(char_visual)[0]
        
        y_offset += disclaimer_mono_font_large.get_linesize() + 5 # Further reduced from 10


        # --- Render Disclaimer Messages with Character Corruption ---
        messages = [
            "This game is a work of fiction and intended for mature audiences.",
            "It explores themes of horror and hacking.",
            " ",
            "The activities depicted, if performed in real life, can have serious",
            "legal, ethical, and personal consequences.",
            " ",
            "This simulation does not endorse or encourage any illegal or unethical behavior.",
            "Always act responsibly and ethically online and offline.",
            " ",
            "Player discretion is strongly advised."
        ]
        original_message_color = (200, 200, 200)
        for msg_line in messages:
            msg_total_width = disclaimer_mono_font_small.size(msg_line)[0]
            current_msg_char_x = WINDOW_WIDTH // 2 - msg_total_width // 2
            
            for char_visual in msg_line:
                display_char = char_visual
                char_fg_color = original_message_color
                if char_visual != ' ' and random.random() < CHARACTER_CORRUPTION_CHANCE: # Only corrupt non-space chars
                    display_char = random.choice(GLITCH_CHARS)
                    # Optional: slightly alter color for glitched char
                    # char_fg_color = (random.randint(150,250), random.randint(50,150), random.randint(50,150))

                char_pos = (current_msg_char_x, y_offset)
                render_text(screen, display_char, char_pos, fg_color=char_fg_color, font=disclaimer_mono_font_small)
                current_msg_char_x += disclaimer_mono_font_small.size(display_char)[0]
            y_offset += disclaimer_mono_font_small.get_linesize()
        
        y_offset += 10 # Further reduced from 15, extra space before continue prompt
        
        # --- Render Jittery "Press SPACE" Text ---
        continue_text = "Press SPACE to acknowledge and continue."
        original_continue_color = (255, 255, 0)
        continue_base_y = y_offset
        
        # Use disclaimer_mono_font_large for "Press SPACE" text
        total_continue_width = disclaimer_mono_font_large.size(continue_text)[0]
        current_continue_char_x = WINDOW_WIDTH // 2 - total_continue_width // 2

        for char_visual in continue_text:
            dx = random.randint(-1, 1)
            dy = random.randint(-1, 1)
            
            char_color_r = max(0, min(255, original_continue_color[0] + random.randint(-20, 20)))
            char_color_g = max(0, min(255, original_continue_color[1] + random.randint(-20, 20)))
            char_color_b = original_continue_color[2] # Keep blue component stable for yellow
            distorted_char_color = (char_color_r, char_color_g, char_color_b)
            
            char_pos = (current_continue_char_x + dx, continue_base_y + dy)
            # Use disclaimer_mono_font_large here
            render_text(screen, char_visual, char_pos, fg_color=distorted_char_color, font=disclaimer_mono_font_large)
            current_continue_char_x += disclaimer_mono_font_large.size(char_visual)[0]
        
        # Use disclaimer_mono_font_large for y_offset increment
        y_offset += disclaimer_mono_font_large.get_linesize() + 10 # Reduced spacing, using large font metric
 
        # --- Second Skull Rendering Removed (comment kept for history) ---
 
    elif game_state_manager.is_state(STATE_ROLE_SELECTION):
        terminal.render(screen, effect_manager) # Uses terminal to display role choices
    elif game_state_manager.is_state(STATE_MAIN_TERMINAL):
        terminal.render(screen, effect_manager) # Pass effect_manager for overlay rendering
    elif game_state_manager.is_state(STATE_MSFCONSOLE):
        # MSFConsole uses the main terminal instance for display.
        # The prompt is set when switching to this state.
        terminal.render(screen, effect_manager)
    elif game_state_manager.is_state(STATE_MINIGAME):
        # Placeholder for minigame rendering
        render_text(screen, "MINIGAME ACTIVE", (10,10), fg_color=(0,255,255), font=pygame.font.Font(None, 28))
    elif game_state_manager.is_state(STATE_PUZZLE_ACTIVE):
        # Puzzle content is displayed via the terminal buffer
        terminal.render(screen, effect_manager)
        
    # Optional debug display for current game state:
    # state_debug_text = f"State: {game_state_manager.get_state()} Role: {game_state_manager.get_player_role()}"
    # debug_font = pygame.font.Font(None, 18)
    # render_text(screen, state_debug_text, (10, WINDOW_HEIGHT - 20), fg_color=(128,128,128), font=debug_font)
 
    pygame.display.flip() # Update the full display
 
# --- Quit Pygame ---
pygame.quit()