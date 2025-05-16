import random
import shlex
from game_state import STATE_MSFCONSOLE, ROLE_WHITE_HAT, ROLE_GREY_HAT, ROLE_BLACK_HAT, STATE_PUZZLE_ACTIVE, STATE_MAIN_TERMINAL
from effects import THEMES, set_theme as set_global_theme, get_current_theme
from commands_config import COMMAND_ACCESS
# Import puzzle_manager from main.py - acknowledge potential circular dependency for now.
# This is done to access the single instance of PuzzleManager created in main.
try:
    from main import puzzle_manager as global_puzzle_manager
except ImportError:
    # This might happen during linting or if main hasn't fully initialized puzzle_manager yet.
    # For runtime, main.py should ensure puzzle_manager is available before command processing.
    global_puzzle_manager = None

# Note: terminal, game_state_manager, effect_manager, puzzle_manager are passed as arguments to handlers.
 
# --- Individual Command Handlers for Main Terminal ---

def _handle_clear(args, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    terminal.clear_buffer()
    terminal.add_line("Screen cleared.", style_key='success')
    return True, None

def _handle_help(args, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    terminal.add_line("Available commands:", style_key='highlight')
    
    current_state = game_state_manager.get_state()
    allowed_key = "allowed_main"
    help_text_key = "help_text_main"

    if current_state == STATE_PUZZLE_ACTIVE:
        allowed_key = "allowed_puzzle"
        help_text_key = "help_text_puzzle"
        terminal.add_line("--- Puzzle Mode Commands ---", style_key='comment')
    
    # Default to Grey Hat's command set if role is not explicitly found or if specific state commands are missing.
    role_config = COMMAND_ACCESS.get(player_role, COMMAND_ACCESS[ROLE_GREY_HAT])
    
    allowed_commands_for_role_state = role_config.get(allowed_key, [])
    help_texts_for_role_state = role_config.get(help_text_key, {})

    # If in a specific state and no commands are defined for it, fall back to main commands for that role.
    if not allowed_commands_for_role_state and current_state != STATE_MAIN_TERMINAL:
        allowed_commands_for_role_state = role_config.get("allowed_main", [])
        help_texts_for_role_state = role_config.get("help_text_main", {})
        if current_state == STATE_PUZZLE_ACTIVE: # Add a note if falling back for puzzle mode
             terminal.add_line("(No puzzle-specific commands defined for this role, showing general commands)", style_key='comment')

    for cmd_name_key in sorted(allowed_commands_for_role_state): # Sort for consistent help output.
        if cmd_name_key in help_texts_for_role_state:
            terminal.add_line(help_texts_for_role_state[cmd_name_key])
    
    # Ensure quit/exit are shown if they are universally available.
    if "quit" not in allowed_commands_for_role_state and "quit" in COMMAND_ACCESS[ROLE_GREY_HAT].get("help_text_main", {}):
        terminal.add_line(COMMAND_ACCESS[ROLE_GREY_HAT]["help_text_main"]["quit"])
    if current_state == STATE_PUZZLE_ACTIVE and "exit_puzzle" not in allowed_commands_for_role_state and "exit_puzzle" in COMMAND_ACCESS[ROLE_GREY_HAT].get("help_text_puzzle", {}):
         terminal.add_line(COMMAND_ACCESS[ROLE_GREY_HAT]["help_text_puzzle"]["exit_puzzle"]) # Ensure exit_puzzle is shown in puzzle mode help
    return True, None

def _handle_msfconsole(args, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    game_state_manager.change_state(STATE_MSFCONSOLE)
    terminal.clear_buffer()
    terminal.set_prompt_override("msf6 > ")
    terminal.add_line("Starting Metasploit Framework console...", style_key='highlight')
    terminal.add_line("       =[ metasploit v6.0.50-dev                          ]", fg_color=(200,200,0))
    terminal.add_line("+ -- --=[ 2100 exploits - 1100 auxiliary - 360 post       ]", fg_color=(200,200,0))
    terminal.add_line("+ -- --=[ 590 payloads - 45 encoders - 10 nops            ]", fg_color=(200,200,0))
    terminal.add_line("       =[ 1000 evasion                                     ]", fg_color=(200,200,0))
    terminal.add_line("")
    return True, None

def _handle_echo(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    terminal.add_line(" ".join(args_list))
    return True, None

def _handle_whoami(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    username_output = terminal.username
    line_idx = terminal.add_line(username_output)
    if terminal.fs_handler.is_item_corrupted("/"): # Assuming root corruption affects this
        if line_idx != -1:
            effect_manager.start_character_corruption_effect(
                line_idx, duration_ms=350, intensity=0.2, rate_ms=60
            )
    return True, None

def _handle_hostname(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    hostname_output = terminal.hostname
    line_idx = terminal.add_line(hostname_output)
    if terminal.fs_handler.is_item_corrupted("/"): # Assuming root corruption affects this
        if line_idx != -1:
            effect_manager.start_text_flicker_effect(
                line_idx, duration_ms=350, flicker_rate_ms=70, flicker_color_key='error'
            )
    return True, None

def _handle_uname(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    output_line_str = ""
    if args_list and args_list[0] == "-a":
        output_line_str = "Linux kali 6.1.0-kali5-amd64 #1 SMP PREEMPT_DYNAMIC Debian 6.1.12-1kali2 (2023-02-23) x86_64 GNU/Linux"
    else:
        output_line_str = "Linux"
    
    line_idx = terminal.add_line(output_line_str)
    if terminal.fs_handler.is_item_corrupted("/"): # Assuming root corruption affects this
        if line_idx != -1:
            effect_manager.start_character_corruption_effect(
                line_idx, duration_ms=400, intensity=0.25, rate_ms=50
            )
    return True, None
 
def _handle_head_tail(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role, command_name):
    num_lines = 10
    file_path_str = None
    
    opt_idx = 0
    # Check for -n option
    if len(args_list) > opt_idx and args_list[opt_idx] == "-n":
        opt_idx += 1 # Move past '-n'
        if len(args_list) > opt_idx: # Check if there's a value after -n
            try:
                num_lines = int(args_list[opt_idx])
                opt_idx += 1 # Move past the number
            except ValueError:
                terminal.add_line(f"{command_name}: invalid number of lines: '{args_list[opt_idx]}'", style_key='error')
                return True, None
        else: # -n was the last argument
            terminal.add_line(f"{command_name}: option requires an argument -- 'n'", style_key='error')
            return True, None
    
    # The next argument should be the file path
    if len(args_list) > opt_idx:
        file_path_str = args_list[opt_idx]
    else:
        terminal.add_line(f"{command_name}: missing file operand", style_key='error')
        return True, None

    if file_path_str:
        file_content = terminal.fs_handler.get_item_content(file_path_str)
        if file_content is None:
            resolved_path = terminal.fs_handler._resolve_path_str_to_list(file_path_str)
            node = terminal.fs_handler._get_node_at_path(resolved_path)
            if isinstance(node, dict): # Target is a directory
                terminal.add_line(f"{command_name}: {file_path_str}: Is a directory", style_key='error')
            else: # Target does not exist
                terminal.add_line(f"{command_name}: {file_path_str}: No such file or directory", style_key='error')
        elif isinstance(file_content, str): # Target is a file with content
            content_lines = file_content.splitlines()
            if command_name == "head":
                lines_to_show = content_lines[:num_lines]
            else: # tail
                lines_to_show = content_lines[-num_lines:]
            for line_content in lines_to_show:
                terminal.add_line(line_content)
        # No explicit else needed if get_item_content returns something other than str or None.
    return True, None
 
def _handle_head(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    return _handle_head_tail(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role, "head")

def _handle_tail(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    return _handle_head_tail(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role, "tail")

def _handle_rm(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    if player_role == ROLE_WHITE_HAT:
        terminal.add_line("rm: Operation not permitted for White Hat alignment.", style_key='error')
        return True, None

    if not args_list:
        terminal.add_line("rm: missing operand", style_key='error')
        return True, None

    recursive_remove = False
    path_args = []
    unknown_options = []

    for arg in args_list:
        if arg == "-r" or arg == "-rf":
            recursive_remove = True
        elif arg.startswith("-") and len(arg) > 1: # Check for other options
            unknown_options.append(arg)
        else:
            path_args.append(arg)

    if unknown_options:
        for opt in unknown_options:
            terminal.add_line(f"rm: invalid option -- '{opt[1:]}'", style_key='error')
        terminal.add_line("Usage: rm [-r | -rf] <file_or_directory>", style_key='error') # Basic usage
        return True, None

    if not path_args:
        terminal.add_line("rm: missing operand", style_key='error')
        return True, None

    if len(path_args) > 1:
        terminal.add_line("rm: currently supports removing one item at a time", style_key='error')
        # Alternatively, could iterate and try to remove each:
        # for p_arg in path_args:
        #     success, message = terminal.fs_handler.remove_item(p_arg, recursive=recursive_remove)
        #     if not success:
        #         terminal.add_line(message, style_key='error')
        return True, None

    target_to_remove_str = path_args[0]
    success, message = terminal.fs_handler.remove_item(target_to_remove_str, recursive=recursive_remove)
    if not success:
        terminal.add_line(message, style_key='error')
    return True, None

def _handle_mv(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    if player_role == ROLE_WHITE_HAT:
        terminal.add_line("mv: Operation not permitted for White Hat alignment.", style_key='error')
    else:
        if len(args_list) == 2:
            src_str = args_list[0]
            dest_str = args_list[1]
            success, message = terminal.fs_handler.move_item(src_str, dest_str)
            if not success:
                terminal.add_line(message, style_key='error')
        else:
            terminal.add_line("mv: missing file operand(s) or too many arguments", style_key='error')
            terminal.add_line("Usage: mv <source> <destination>", style_key='error')
    return True, None

def _handle_theme(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    if args_list:
        theme_name_input = args_list[0].lower()
        if len(args_list) > 1:
            terminal.add_line("theme: too many arguments", style_key='error')
            terminal.add_line("Usage: theme <theme_name>", style_key='error')
            return True, None
        # Alias handling
        if theme_name_input == "kali": theme_name_input = "corrupted_kali"
        if theme_name_input == "nightmare": theme_name_input = "digital_nightmare"
        if theme_name_input == "dos": theme_name_input = "classic_dos"
        
        if set_global_theme(theme_name_input):
            terminal.apply_theme_colors()
            terminal.add_line(f"Theme set to: {get_current_theme()['name']}", style_key='success')
        else:
            terminal.add_line(f"Theme '{theme_name_input}' not found. Available: {', '.join(THEMES.keys())}", style_key='error')
    else:
        terminal.add_line("Usage: theme <theme_name>", style_key='error')
        terminal.add_line(f"Sets the terminal color scheme. Available themes: {', '.join(THEMES.keys())}", style_key='error')
    return True, None

def _handle_type_effect(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    if args_list:
        text_to_type = " ".join(args_list)
        effect_manager.start_typing_effect(text_to_type, char_delay_ms=30, style_key='highlight')
    else:
        terminal.add_line("Usage: type <text>", style_key='error')
        terminal.add_line("Simulates typing out the provided text.", style_key='error')
    return True, None

def _handle_burst_effect(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    if args_list:
        text_to_burst = " ".join(args_list)
        effect_manager.start_typing_effect(text_to_burst, char_delay_ms=0, style_key='highlight')
    else:
        terminal.add_line("Usage: burst <text>", style_key='error')
        terminal.add_line("Instantly displays the provided text.", style_key='error')
    return True, None

def _handle_sequence_effect(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    terminal.add_line("Starting effect sequence...", style_key='highlight')
    effect_manager.start_typing_effect("First message...", char_delay_ms=50)
    effect_manager.start_timed_delay(1000)
    effect_manager.start_typing_effect("Second message, after a delay.", char_delay_ms=40, style_key='success')
    effect_manager.start_timed_delay(500)
    effect_manager.start_typing_effect("Third and final message.", char_delay_ms=60, style_key='error', bold=True, on_complete_callback=lambda: terminal.add_line("Sequence complete!", style_key='success'))
    return True, None

def _handle_corrupt_effect(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    try:
        if not args_list:
            raise IndexError # Trigger usage message if no args

        line_offset = int(args_list[0])
        duration = int(args_list[1]) if len(args_list) > 1 else 1000
        intensity_percent = int(args_list[2]) if len(args_list) > 2 else 30
        rate = int(args_list[3]) if len(args_list) > 3 else 75
        
        intensity_float = intensity_percent / 100.0
        
        actual_index = line_offset
        if line_offset < 0 :
            actual_index = len(terminal.buffer) + line_offset
        
        if not (0 <= actual_index < len(terminal.buffer)):
            terminal.add_line(f"Error: Line offset {line_offset} (index {actual_index}) out of bounds.", style_key='error')
        else:
            terminal.add_line(f"Corrupting line {line_offset} (index {actual_index}) for {duration}ms, intensity {intensity_percent}%, rate {rate}ms.", style_key='highlight')
            effect_manager.start_character_corruption_effect(
                actual_index, duration, intensity_float, rate
            )
    except (IndexError, ValueError):
        terminal.add_line("Usage: corrupt <line_offset> [duration_ms] [intensity_percent] [rate_ms]", style_key='error')
        terminal.add_line("Corrupts characters on a specified line. Example: corrupt -1 2000 50 50", style_key='error')
    return True, None

def _handle_flicker_effect(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    try:
        if not args_list:
            raise IndexError # Trigger usage message

        line_offset = int(args_list[0])
        duration = int(args_list[1]) if len(args_list) > 1 else 1000
        rate = int(args_list[2]) if len(args_list) > 2 else 100
        color_key = args_list[3] if len(args_list) > 3 else 'error'

        actual_index = line_offset
        if line_offset < 0:
            actual_index = len(terminal.buffer) + line_offset
        
        if not (0 <= actual_index < len(terminal.buffer)):
            terminal.add_line(f"Error: Line offset {line_offset} (index {actual_index}) for flicker out of bounds.", style_key='error')
        elif color_key not in get_current_theme():
            terminal.add_line(f"Error: Flicker color key '{color_key}' not in current theme. Valid keys: {', '.join(get_current_theme().keys())}", style_key='error')
        else:
            terminal.add_line(f"Flickering line {line_offset} (index {actual_index}) for {duration}ms, rate {rate}ms, color '{color_key}'.", style_key='highlight')
            effect_manager.start_text_flicker_effect(
                actual_index, duration, rate, color_key
            )
    except (IndexError, ValueError):
        terminal.add_line("Usage: flicker <line_offset> [duration_ms] [rate_ms] [color_key]", style_key='error')
        terminal.add_line("Flickers a specified line with a chosen color. Example: flicker -1 1500 80 error", style_key='error')
    return True, None

def _handle_colorchange_effect(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    try:
        if not args_list:
            raise IndexError # Trigger usage message

        line_offset = int(args_list[0])
        duration = int(args_list[1]) if len(args_list) > 1 else 1000
        fg_color_key = args_list[2].lower() if len(args_list) > 2 and args_list[2].lower() != "none" else None
        bg_color_key = args_list[3].lower() if len(args_list) > 3 and args_list[3].lower() != "none" else None

        actual_index = line_offset
        if line_offset < 0:
            actual_index = len(terminal.buffer) + line_offset
        
        if not (0 <= actual_index < len(terminal.buffer)):
            terminal.add_line(f"Error: Line offset {line_offset} (index {actual_index}) for colorchange out of bounds.", style_key='error')
        elif not fg_color_key and not bg_color_key:
            terminal.add_line("Error: colorchange requires at least a fg_color_key or bg_color_key.", style_key='error')
        elif fg_color_key and fg_color_key not in get_current_theme():
            terminal.add_line(f"Error: fg_color_key '{fg_color_key}' not in theme.", style_key='error')
        elif bg_color_key and bg_color_key not in get_current_theme():
            terminal.add_line(f"Error: bg_color_key '{bg_color_key}' not in theme.", style_key='error')
        else:
            terminal.add_line(f"Changing line {line_offset} (idx {actual_index}) for {duration}ms. FG: {fg_color_key}, BG: {bg_color_key}", style_key='highlight')
            effect_manager.start_temp_color_change_effect(
                actual_index, duration, fg_color_key, bg_color_key
            )
    except (IndexError, ValueError):
        terminal.add_line("Usage: colorchange <offset> <duration> [fg_key|none] [bg_key|none]", style_key='error')
        terminal.add_line("Temporarily changes color of a line. Example: colorchange -1 1000 error highlight", style_key='error')
    return True, None

def _handle_overlay_effect(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    try:
        # Provide defaults if arguments are missing or empty
        duration_str = args_list[0].strip() if len(args_list) > 0 and args_list[0].strip() else "1500"
        num_chars_str = args_list[1].strip() if len(args_list) > 1 and args_list[1].strip() else "50"
        color_key = args_list[2].strip() if len(args_list) > 2 and args_list[2].strip() else 'error'
        rate_str = args_list[3].strip() if len(args_list) > 3 and args_list[3].strip() else "100"

        duration = int(duration_str)
        num_chars = int(num_chars_str)
        rate = int(rate_str)

        if color_key not in get_current_theme():
            terminal.add_line(f"Error: Overlay color key '{color_key}' not in current theme. Valid keys: {', '.join(get_current_theme().keys())}", style_key='error')
        else:
            terminal.add_line(f"Starting text overlay: {duration}ms, {num_chars} chars, color '{color_key}', rate {rate}ms.", style_key='highlight')
            effect_manager.start_text_overlay_effect(
                duration, num_chars, None, color_key, rate
            )
    except ValueError:
        terminal.add_line("Error: Invalid numeric value for overlay parameters.", style_key='error')
        terminal.add_line("Usage: overlay [duration_ms] [num_chars] [color_key] [rate_ms]", style_key='error')
    # IndexError might still occur if args_list is shorter than expected,
    # but the logic for defaults handles cases where elements are empty strings.
    # The original IndexError catch was for cmd_args, which is now args_list.
    # If args_list is too short, it will be caught by Python's IndexError.
    return True, None

def _handle_jiggle_effect(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    try:
        if not args_list:
            raise IndexError # Trigger usage message

        line_offset = int(args_list[0])
        duration = int(args_list[1]) if len(args_list) > 1 else 1000
        intensity = int(args_list[2]) if len(args_list) > 2 else 1
        rate = int(args_list[3]) if len(args_list) > 3 else 50

        actual_index = line_offset
        if line_offset < 0:
            actual_index = len(terminal.buffer) + line_offset
        
        if not (0 <= actual_index < len(terminal.buffer)):
            terminal.add_line(f"Error: Line offset {line_offset} (index {actual_index}) for jiggle out of bounds.", style_key='error')
        else:
            terminal.add_line(f"Jiggling line {line_offset} (index {actual_index}) for {duration}ms, intensity {intensity}, rate {rate}ms.", style_key='highlight')
            effect_manager.start_text_jiggle_effect(
                actual_index, duration, intensity, rate
            )
    except (IndexError, ValueError):
        terminal.add_line("Usage: jiggle <line_offset> [duration_ms] [intensity] [rate_ms]", style_key='error')
        terminal.add_line("Jiggles characters on a specified line. Example: jiggle -1 1000 2 50", style_key='error')
    return True, None

def _handle_screenres(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    if args_list:
        if len(args_list) > 1:
            terminal.add_line("Error: Too many arguments for screenres. Use WxH.", style_key='error')
            return True, None
        res_parts = args_list[0].lower().split('x')
        if len(res_parts) == 2:
            try:
                new_w = int(res_parts[0])
                new_h = int(res_parts[1])
                if new_w > 0 and new_h > 0:
                    return True, {'action': 'screen_change', 'type': 'set_resolution', 'width': new_w, 'height': new_h}
                else:
                    terminal.add_line("Error: Width and height must be positive.", style_key='error')
            except ValueError:
                terminal.add_line("Error: Invalid resolution format. Use WxH (e.g., 800x600).", style_key='error')
        else:
            terminal.add_line("Error: Invalid resolution format. Use WxH (e.g., 800x600).", style_key='error')
    else:
        terminal.add_line("Usage: screenres <Width>x<Height>", style_key='error')
        terminal.add_line("Changes the screen resolution. Example: screenres 800x600", style_key='error')
    return True, None # No screen change if error

def _handle_fullscreen(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    return True, {'action': 'screen_change', 'type': 'fullscreen'}

def _handle_windowed(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    return True, {'action': 'screen_change', 'type': 'windowed'}

def _handle_pwd(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    current_path_str = terminal.fs_handler.get_current_path_str()
    line_idx = terminal.add_line(current_path_str)
    
    if terminal.fs_handler.is_item_corrupted(current_path_str): # Check corruption of current path
        if line_idx != -1:
            effect_manager.start_character_corruption_effect(
                line_idx,
                duration_ms=random.randint(300, 500),
                intensity=random.uniform(0.15, 0.3),
                rate_ms=random.randint(50, 80)
            )
            effect_manager.start_timed_delay(random.randint(40, 90)) # Short delay after effect
    return True, None

def _handle_ls(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    target_ls_path_str = "."
    if args_list:
        if len(args_list) > 1:
            terminal.add_line("ls: too many arguments", style_key='error')
            # Consider showing usage or just erroring out. For now, error out.
            return True, None
        target_ls_path_str = args_list[0]
    resolved_path_list = terminal.fs_handler._resolve_path_str_to_list(target_ls_path_str)
    node = terminal.fs_handler._get_node_at_path(resolved_path_list)

    if isinstance(node, str): # It's a file
        terminal.add_line(target_ls_path_str) # Just print the filename if ls is on a file
    elif isinstance(node, dict): # It's a directory
        items = terminal.fs_handler.list_items(target_ls_path_str)
        if items:
            corrupted_files_in_dir = terminal.fs_handler.get_corrupted_file_count_in_dir(target_ls_path_str)
            apply_glitch_to_listing = corrupted_files_in_dir > 1
            
            for item_name in sorted(items): # Sort for consistent output
                line_idx = terminal.add_line(item_name)
                
                if apply_glitch_to_listing and line_idx != -1:
                    if random.random() < 0.25:
                        effect_type = random.choice(["corrupt", "flicker"])
                        if effect_type == "corrupt":
                            effect_manager.start_character_corruption_effect(
                                line_idx,
                                duration_ms=random.randint(250, 400),
                                intensity=random.uniform(0.1, 0.25),
                                rate_ms=random.randint(40, 70)
                            )
                        else: # flicker
                            effect_manager.start_text_flicker_effect(
                                line_idx,
                                duration_ms=random.randint(250, 400),
                                flicker_rate_ms=random.randint(60, 90),
                                flicker_color_key=random.choice(['error', 'highlight'])
                            )
                        effect_manager.start_timed_delay(random.randint(30, 80))
        # If items is empty, ls on an empty directory produces no output, which is standard.
    elif node is None:
        terminal.add_line(f"ls: cannot access '{target_ls_path_str}': No such file or directory", style_key='error')
    else: # Should not happen with current fs_handler structure (only dict, str, None)
        terminal.add_line(f"ls: cannot access '{target_ls_path_str}': Not a file or directory", style_key='error')
    return True, None

def _handle_cd(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    target_dir_name = "~" # Default to home
    if args_list:
        if len(args_list) > 1:
            terminal.add_line("cd: too many arguments", style_key='error')
            return True, None
        target_dir_name = args_list[0]
    success, message = terminal.fs_handler.execute_cd(target_dir_name)
    if not success:
        terminal.add_line(message, style_key='error')
    else:
        terminal._update_prompt_string() # Update prompt after successful cd
    return True, None

def _handle_cat(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    if not args_list:
        terminal.add_line("cat: missing file operand", style_key='error')
        return True, None
    if len(args_list) > 1:
        terminal.add_line("cat: too many arguments", style_key='error')
        # For now, only process the first one, or could error out.
        # Standard cat concatenates, but our fs_handler.get_item_content takes one path.
        # Let's stick to one for now.
        terminal.add_line("Usage: cat <file>", style_key='error')
        return True, None
        
    file_path_str = args_list[0]
    # The rest of the original logic for checking content and corruption remains
    # but the initial `if args.strip():` and its `else` for missing operand are handled above.
    # Need to ensure the original `else` (line 510 in original, now ~545) is removed or adapted.
    # The original `else` was:
    # else:
    #     terminal.add_line("cat: missing file operand", style_key='error')
    # This is now covered by `if not args_list:`.
    # The existing logic from line 523 (original) continues from here:
    content = terminal.fs_handler.get_item_content(file_path_str)
    if content is not None: # Content exists (it's a file)
        is_corrupted = terminal.fs_handler.is_item_corrupted(file_path_str)
        if is_corrupted:
            terminal.add_line(f"[{file_path_str} - CORRUPTED DATA STREAM]", style_key='error', bold=True)
            effect_manager.start_timed_delay(250)
            for line_content in content.splitlines():
                line_idx = terminal.add_line(line_content, style_key='error') # Show corrupted content with error style
                if line_idx != -1:
                    effect_manager.start_character_corruption_effect(
                        line_idx,
                        duration_ms=1500,
                        intensity=0.3,
                        rate_ms=60
                    )
                    effect_manager.start_timed_delay(50) # Small delay between corrupted lines
            effect_manager.start_timed_delay(1500) # Delay after all corrupted content
            terminal.add_line(f"[END OF CORRUPTED STREAM - {file_path_str}]", style_key='error', bold=True)
        else:
            for line_content in content.splitlines():
                terminal.add_line(line_content)
    else: # Path does not exist or is a directory
        resolved_path = terminal.fs_handler._resolve_path_str_to_list(file_path_str)
        node = terminal.fs_handler._get_node_at_path(resolved_path)
        if isinstance(node, dict): # It's a directory
            terminal.add_line(f"cat: {file_path_str}: Is a directory", style_key='error')
        else: # Does not exist
            terminal.add_line(f"cat: {file_path_str}: No such file or directory", style_key='error')
    # The old else block for missing operand in _handle_cat was here.
    # It's now handled by the `if not args_list:` check at the beginning of _handle_cat.
    return True, None

def _handle_mkdir(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    if not args_list:
        terminal.add_line("mkdir: missing operand", style_key='error')
        terminal.add_line("Usage: mkdir <directory_name>", style_key='error')
        return True, None
    if len(args_list) > 1:
        terminal.add_line("mkdir: too many arguments", style_key='error')
        # Consider creating multiple if desired, but for now, one at a time.
        terminal.add_line("Usage: mkdir <directory_name>", style_key='error')
        return True, None
        
    dir_name = args_list[0]
    success, message = terminal.fs_handler.execute_mkdir(dir_name)
    if not success:
        terminal.add_line(message, style_key='error')
    return True, None

def _handle_touch(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    if not args_list:
        terminal.add_line("touch: missing file operand", style_key='error')
        terminal.add_line("Usage: touch <filename>", style_key='error')
        return True, None
    if len(args_list) > 1:
        terminal.add_line("touch: too many arguments", style_key='error')
        terminal.add_line("Usage: touch <filename>", style_key='error')
        return True, None
        
    file_name = args_list[0]
    success, message = terminal.fs_handler.execute_touch(file_name)
    if not success:
        terminal.add_line(message, style_key='error')
    return True, None

def _handle_grep(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    if len(args_list) != 2:
        terminal.add_line("Usage: grep <pattern> <file>", style_key='error')
        return True, None

    pattern_str = args_list[0]
    file_path_str = args_list[1]

    file_content = terminal.fs_handler.get_item_content(file_path_str)

    if file_content is None:
        resolved_path = terminal.fs_handler._resolve_path_str_to_list(file_path_str)
        node = terminal.fs_handler._get_node_at_path(resolved_path)
        if isinstance(node, dict): # Target is a directory
            terminal.add_line(f"grep: {file_path_str}: Is a directory", style_key='error')
        else: # Target does not exist
            terminal.add_line(f"grep: {file_path_str}: No such file or directory", style_key='error')
        return True, None
    elif not isinstance(file_content, str): # Should be string content
        terminal.add_line(f"grep: {file_path_str}: Not a regular file or cannot read content", style_key='error')
        return True, None

    found_match = False
    is_corrupted = terminal.fs_handler.is_item_corrupted(file_path_str)

    for line_num, line_content in enumerate(file_content.splitlines()):
        if pattern_str in line_content: # Case-sensitive search
            found_match = True
            display_line = f"{line_num + 1}:{line_content}"
            line_idx = terminal.add_line(display_line)

            if is_corrupted and line_idx != -1 and random.random() < 0.15: # 15% chance to glitch
                effect_type = random.choice(["corrupt_char_brief", "flicker_brief"])
                if effect_type == "corrupt_char_brief":
                    effect_manager.start_character_corruption_effect(
                        line_idx, duration_ms=random.randint(200, 350),
                        intensity=random.uniform(0.05, 0.15),
                        rate_ms=random.randint(40, 70)
                    )
                else: # flicker_brief
                    effect_manager.start_text_flicker_effect(
                        line_idx, duration_ms=random.randint(200, 350),
                        flicker_rate_ms=random.randint(50, 80),
                        flicker_color_key=random.choice(['error', 'warning'])
                    )
                effect_manager.start_timed_delay(random.randint(20, 50))
    return True, None
def _handle_integrity_check(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    if player_role == ROLE_WHITE_HAT:
        terminal.add_line("Performing system integrity scan...", style_key='highlight')
        effect_manager.start_timed_delay(500)
        terminal.add_line("Scanning critical system files...", style_key='default_fg')
        effect_manager.start_timed_delay(1000)
        terminal.add_line("Verifying kernel modules...", style_key='default_fg')
        effect_manager.start_timed_delay(700)
        terminal.add_line("Checking for unauthorized processes...", style_key='default_fg')
        effect_manager.start_timed_delay(800)
        terminal.add_line("Integrity Scan: All systems nominal. No anomalies detected.", style_key='success')
    else:
        # This case should ideally not be reached if command access is correctly enforced
        terminal.add_line("Error: integrity_check is a White Hat aligned command.", style_key='error')
    return True, None

def _handle_observe_traffic(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    if player_role == ROLE_GREY_HAT:
        terminal.add_line("Initializing network traffic monitor...", style_key='highlight')
        effect_manager.start_timed_delay(600)
        terminal.add_line("Monitoring packet flow on eth0...", style_key='default_fg')
        effect_manager.start_timed_delay(1200)
        terminal.add_line("Analyzing data streams for unusual patterns...", style_key='default_fg')
        effect_manager.start_timed_delay(900)
        terminal.add_line("Traffic Observation: Minor encrypted traffic spikes detected from unknown origin. Further analysis required.", style_key='warning')
    else:
        terminal.add_line("Error: observe_traffic is a Grey Hat aligned command.", style_key='error')
    return True, None

def _handle_find_exploit(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    if player_role == ROLE_BLACK_HAT:
        terminal.add_line("Scanning for known vulnerabilities...", style_key='highlight')
        effect_manager.start_timed_delay(700)
        terminal.add_line("Cross-referencing local system services with exploit database...", style_key='default_fg')
        effect_manager.start_timed_delay(1500)
        terminal.add_line("Checking for outdated software versions...", style_key='default_fg')
        effect_manager.start_timed_delay(1000)
        terminal.add_line("Vulnerability Scan: Potential buffer overflow in 'aether_daemon_v1.2'. Exploit 'CVE-2024-AETHER01' may apply.", style_key='error')
    else:
        terminal.add_line("Error: find_exploit is a Black Hat aligned command.", style_key='error')
    return True, None

def _handle_scan(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    if not args_list:
        terminal.add_line("scan: missing file operand", style_key='error')
        terminal.add_line("Usage: scan <filename>", style_key='error')
        terminal.add_line("Analyzes a file for corruption and integrity.", style_key='error')
        return True, None
    if len(args_list) > 1:
        terminal.add_line("scan: too many arguments", style_key='error')
        terminal.add_line("Usage: scan <filename>", style_key='error')
        return True, None
        
    file_path_str = args_list[0]
    
    # Check if the target is a file and not a directory
    # We can infer this by trying to get its content; directories won't have string content.
    # Or, more directly, check its type if fs_handler supports it.
    # For now, let's use a combination of content check and path check.
    
    resolved_path_list = terminal.fs_handler._resolve_path_str_to_list(file_path_str)
    node = terminal.fs_handler._get_node_at_path(resolved_path_list)

    if node is None:
        terminal.add_line(f"scan: {file_path_str}: No such file or directory", style_key='error')
        return True, None
    if isinstance(node, dict): # It's a directory
        terminal.add_line(f"scan: {file_path_str}: Is a directory. Cannot scan directories.", style_key='error')
        return True, None
    
    # If it's not None and not a dict, it should be a file (string content)
    # Proceed with scanning simulation

    terminal.add_line(f"Initiating integrity scan for: {file_path_str}...", style_key='highlight')
    effect_manager.start_timed_delay(300)
    
    line_idx_scan_progress = terminal.add_line("Scanning sectors... [  0%]", style_key='default_fg')
    effect_manager.start_timed_delay(400)
    if line_idx_scan_progress != -1:
        terminal.update_line_text(line_idx_scan_progress, "Scanning sectors... [ 25%]")
    effect_manager.start_timed_delay(400)
    if line_idx_scan_progress != -1:
        terminal.update_line_text(line_idx_scan_progress, "Scanning sectors... [ 50%]")
        effect_manager.start_text_jiggle_effect(line_idx_scan_progress, 300, 1, 60)
    effect_manager.start_timed_delay(500)
    if line_idx_scan_progress != -1:
        terminal.update_line_text(line_idx_scan_progress, "Scanning sectors... [ 75%]")
    effect_manager.start_timed_delay(400)
    if line_idx_scan_progress != -1:
        terminal.update_line_text(line_idx_scan_progress, "Scanning sectors... [100%]")
    effect_manager.start_timed_delay(200)
    terminal.add_line("Analyzing data structure...", style_key='default_fg')
    effect_manager.start_timed_delay(600)

    is_corrupted = terminal.fs_handler.is_item_corrupted(file_path_str)

    if is_corrupted:
        corruption_level = random.randint(15, 75) # Simulated corruption percentage
        line_idx_status = terminal.add_line(f"Scan Complete: {file_path_str}", style_key='warning')
        effect_manager.start_timed_delay(100)
        line_idx_detail = terminal.add_line(f"Status: CORRUPTION DETECTED. Integrity: {100-corruption_level}%", style_key='error', bold=True)
        if line_idx_detail != -1:
            effect_manager.start_character_corruption_effect(line_idx_detail, 1200, 0.2, 50)
        
        effect_manager.start_timed_delay(200)
        terminal.add_line(f"Estimated data loss: {corruption_level}%.", style_key='error')
        terminal.add_line("Anomaly signatures found: UNSTABLE_READ_SECTOR, DATA_FRAGMENTATION_HIGH", style_key='error')
        effect_manager.start_timed_delay(150)
        terminal.add_line("Recommendation: Use 'parse' to attempt data extraction or 'restore' to attempt repair.", style_key='highlight')
    else:
        terminal.add_line(f"Scan Complete: {file_path_str}", style_key='success')
        effect_manager.start_timed_delay(100)
        terminal.add_line("Status: STABLE. No corruption detected.", style_key='success')
        terminal.add_line("File integrity verified.", style_key='success')

    return True, None

def _handle_parse(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    if not args_list:
        terminal.add_line("parse: missing file operand", style_key='error')
        terminal.add_line("Usage: parse <filename>", style_key='error')
        terminal.add_line("Attempts to extract readable data from a file, especially if corrupted.", style_key='error')
        return True, None
    if len(args_list) > 1:
        terminal.add_line("parse: too many arguments", style_key='error')
        terminal.add_line("Usage: parse <filename>", style_key='error')
        return True, None
        
    file_path_str = args_list[0]
    resolved_path_list = terminal.fs_handler._resolve_path_str_to_list(file_path_str)
    node = terminal.fs_handler._get_node_at_path(resolved_path_list)

    if node is None:
        terminal.add_line(f"parse: {file_path_str}: No such file or directory", style_key='error')
        return True, None
    if isinstance(node, dict): # It's a directory
        terminal.add_line(f"parse: {file_path_str}: Is a directory. Cannot parse directories.", style_key='error')
        return True, None

    # Assuming 'node' is file content (string) at this point
    file_content_str = terminal.fs_handler.get_item_content(file_path_str) # Re-fetch to be sure
    if file_content_str is None: # Should not happen if node was found, but as a safeguard
        terminal.add_line(f"parse: Error accessing content for {file_path_str}", style_key='error')
        return True, None

    terminal.add_line(f"Parsing data stream from: {file_path_str}...", style_key='highlight')
    effect_manager.start_timed_delay(300)
    
    line_idx_parse_progress = terminal.add_line("Analyzing headers... [  0%]", style_key='default_fg')
    effect_manager.start_timed_delay(350)
    if line_idx_parse_progress != -1:
        terminal.update_line_text(line_idx_parse_progress, "Analyzing headers... [ 33%]")
    effect_manager.start_timed_delay(350)
    if line_idx_parse_progress != -1:
        terminal.update_line_text(line_idx_parse_progress, "Identifying data blocks... [ 66%]")
        effect_manager.start_text_flicker_effect(line_idx_parse_progress, 400, 80, 'highlight')
    effect_manager.start_timed_delay(450)
    if line_idx_parse_progress != -1:
        terminal.update_line_text(line_idx_parse_progress, "Reconstructing readable segments... [100%]")
    effect_manager.start_timed_delay(200)

    is_corrupted = terminal.fs_handler.is_item_corrupted(file_path_str)
    
    extracted_fragments = []
    original_lines = file_content_str.splitlines()
    
    if is_corrupted:
        terminal.add_line("Corruption detected. Attempting partial data extraction.", style_key='warning')
        effect_manager.start_timed_delay(250)
        for line in original_lines:
            if random.random() > 0.4: # Simulate some lines being recoverable
                # Simulate partial recovery with some visual noise
                if random.random() < 0.3: # 30% chance of a line being heavily garbled
                    garbled_line = "".join(random.choice("!@#$%^&*();':[],./<>?") if random.random() < 0.7 else char for char in line)
                    extracted_fragments.append(garbled_line)
                else:
                    extracted_fragments.append(line)
            else:
                extracted_fragments.append("... [UNRECOVERABLE SEGMENT] ...")
        
        if not extracted_fragments and original_lines: # If all lines were "unrecoverable"
             extracted_fragments.append("... [NO READABLE DATA FOUND DUE TO SEVERE CORRUPTION] ...")

    else: # Not corrupted, parse should just show content, perhaps with a note
        terminal.add_line("File appears stable. Extracting all content.", style_key='success')
        effect_manager.start_timed_delay(150)
        extracted_fragments = original_lines

    if extracted_fragments:
        terminal.add_line("--- BEGIN PARSED DATA ---", style_key='highlight')
        for i, fragment in enumerate(extracted_fragments):
            line_idx = terminal.add_line(fragment)
            if is_corrupted and line_idx != -1:
                if "... [UNRECOVERABLE SEGMENT] ..." in fragment:
                    effect_manager.start_temp_color_change_effect(line_idx, 99999, 'error', None) # Make it permanently red
                elif random.random() < 0.15: # Lightly corrupt some of the recovered lines
                     effect_manager.start_character_corruption_effect(line_idx, 800, 0.1, 70)
            effect_manager.start_timed_delay(30) # Small delay between lines
        terminal.add_line("--- END PARSED DATA ---", style_key='highlight')
    else:
        terminal.add_line("No data could be extracted.", style_key='warning')
        
    return True, None

def _handle_restore(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    if not args_list:
        terminal.add_line("restore: missing file operand", style_key='error')
        terminal.add_line("Usage: restore <filename>", style_key='error')
        terminal.add_line("Attempts to repair a corrupted file.", style_key='error')
        return True, None
    if len(args_list) > 1:
        terminal.add_line("restore: too many arguments", style_key='error')
        terminal.add_line("Usage: restore <filename>", style_key='error')
        return True, None
        
    file_path_str = args_list[0]
    resolved_path_list = terminal.fs_handler._resolve_path_str_to_list(file_path_str)
    node = terminal.fs_handler._get_node_at_path(resolved_path_list)

    if node is None:
        terminal.add_line(f"restore: {file_path_str}: No such file or directory", style_key='error')
        return True, None
    if isinstance(node, dict): # It's a directory
        terminal.add_line(f"restore: {file_path_str}: Is a directory. Cannot restore directories.", style_key='error')
        return True, None

    if not terminal.fs_handler.is_item_corrupted(file_path_str):
        terminal.add_line(f"restore: {file_path_str}: File is not corrupted. No action taken.", style_key='success')
        return True, None

    terminal.add_line(f"Attempting to restore integrity of: {file_path_str}...", style_key='highlight')
    effect_manager.start_timed_delay(300)
    
    line_idx_restore_progress = terminal.add_line("Analyzing corruption patterns... [  0%]", style_key='default_fg')
    effect_manager.start_timed_delay(450)
    if line_idx_restore_progress != -1:
        terminal.update_line_text(line_idx_restore_progress, "Analyzing corruption patterns... [ 20%]")
        effect_manager.start_text_jiggle_effect(line_idx_restore_progress, 500, 1, 70)
    effect_manager.start_timed_delay(550)
    if line_idx_restore_progress != -1:
        terminal.update_line_text(line_idx_restore_progress, "Rebuilding data sectors... [ 40%]")
    effect_manager.start_timed_delay(600)
    if line_idx_restore_progress != -1:
        terminal.update_line_text(line_idx_restore_progress, "Verifying checksums... [ 60%]")
        effect_manager.start_character_corruption_effect(line_idx_restore_progress, 700, 0.05, 80) # Subtle effect
    effect_manager.start_timed_delay(700)
    if line_idx_restore_progress != -1:
        terminal.update_line_text(line_idx_restore_progress, "Finalizing file structure... [ 80%]")
    effect_manager.start_timed_delay(500)
    if line_idx_restore_progress != -1:
        terminal.update_line_text(line_idx_restore_progress, "Finalizing file structure... [100%]")
    effect_manager.start_timed_delay(200)

    # Simulate restoration success/failure
    # For now, let's say White Hat has a higher chance of full success.
    # Grey Hat might partially succeed. Black Hat might "restore" it in a way that benefits them (not implemented yet).
    
    restoration_chance = 0.6 # Base chance
    if player_role == ROLE_WHITE_HAT:
        restoration_chance = 0.85
    elif player_role == ROLE_GREY_HAT:
        restoration_chance = 0.55
    elif player_role == ROLE_BLACK_HAT:
        restoration_chance = 0.3 # Lower chance of true restoration, maybe it gets "differently" corrupted.

    if random.random() < restoration_chance:
        success, msg = terminal.fs_handler.mark_item_corrupted(file_path_str, corrupted_status=False)
        if success:
            terminal.add_line(f"Restore successful: {file_path_str} integrity has been restored.", style_key='success')
            terminal.add_line("File is now stable.", style_key='success')
        else: # Should not happen if file exists
            terminal.add_line(f"Restore error: Could not update corruption status for {file_path_str}. {msg}", style_key='error')
    else:
        # Simulate partial or failed restoration
        remaining_corruption_level = random.randint(5, 30) # How much corruption "remains"
        terminal.add_line(f"Restore partially successful: {file_path_str}", style_key='warning')
        terminal.add_line(f"Significant data recovered, but some corruption remains (approx. {remaining_corruption_level}%).", style_key='warning')
        # We don't change the corrupted status in fs_handler, it's still considered corrupted.
        # Future: Could modify the file content to reflect partial restoration.
        line_idx_warn = terminal.add_line("Further 'parse' or 'restore' attempts may be needed, or data loss may be permanent.", style_key='error')
        if line_idx_warn != -1:
            effect_manager.start_text_flicker_effect(line_idx_warn, 1500, 100, 'error')

    return True, None

# --- Puzzle Command Handlers ---
def _handle_start_puzzle(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    if not puzzle_manager_instance:
        terminal.add_line("Puzzle system not initialized.", style_key='error')
        return True, None
    
    if not args_list:
        terminal.add_line("start_puzzle: missing puzzle_id operand", style_key='error')
        terminal.add_line("Usage: start_puzzle <puzzle_id>", style_key='error')
        available_puzzles = list(puzzle_manager_instance.puzzles.keys())
        if available_puzzles:
            terminal.add_line(f"Available puzzles: {', '.join(available_puzzles)}", style_key='comment')
        else:
            terminal.add_line("No puzzles currently available.", style_key='comment')
        return True, None

    if len(args_list) > 1:
        terminal.add_line("start_puzzle: too many arguments", style_key='error')
        terminal.add_line("Usage: start_puzzle <puzzle_id>", style_key='error')
        return True, None
        
    puzzle_id = args_list[0]
    # Original 'if not puzzle_id:' is now covered by 'if not args_list:'
    # The rest of the logic continues

    puzzle_display_text = puzzle_manager_instance.start_puzzle(puzzle_id)
    if puzzle_display_text.startswith("Error:"):
        terminal.add_line(puzzle_display_text, style_key='error')
    else:
        game_state_manager.change_state(STATE_PUZZLE_ACTIVE)
        terminal.clear_buffer()
        terminal.add_line(f"--- Puzzle Activated: {puzzle_manager_instance.active_puzzle.name} ---", style_key='highlight')
        for line in puzzle_display_text.split('\n'):
            terminal.add_line(line)
        terminal.add_line("---", style_key='highlight')
        terminal.add_line("Use 'solve <your_answer>' to attempt.", style_key='comment')
        terminal.add_line("Use 'hint' for a clue, or 'exit_puzzle' to leave.", style_key='comment')
        terminal.set_prompt_override(f"puzzle ({puzzle_id}) > ")
    return True, None

def _handle_solve_puzzle(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    if not puzzle_manager_instance:
        terminal.add_line("Puzzle system not initialized.", style_key='error')
        return True, None
    if game_state_manager.get_state() != STATE_PUZZLE_ACTIVE:
        terminal.add_line("No puzzle is currently active. Use 'start_puzzle <id>'.", style_key='error')
        return True, None
    if not puzzle_manager_instance.active_puzzle:
        terminal.add_line("Error: Puzzle active state mismatch. Returning to main terminal.", style_key='error')
        game_state_manager.change_state(STATE_MAIN_TERMINAL)
        terminal.clear_prompt_override()
        return True, None

    if not args_list:
        terminal.add_line("Usage: solve <your_answer>", style_key='error')
        return True, None
    
    player_attempt = " ".join(args_list)
    solved, feedback = puzzle_manager_instance.attempt_active_puzzle(player_attempt)
    terminal.add_line(feedback, style_key='success' if solved else 'error')

    if solved:
        game_state_manager.change_state(STATE_MAIN_TERMINAL)
        terminal.clear_prompt_override()
        terminal.add_line("Returning to main terminal.", style_key='highlight')
    return True, None

def _handle_puzzle_hint(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    if not puzzle_manager_instance:
        terminal.add_line("Puzzle system not initialized.", style_key='error')
        return True, None
    if game_state_manager.get_state() != STATE_PUZZLE_ACTIVE:
        terminal.add_line("No puzzle is currently active to get a hint for.", style_key='error')
        return True, None
    
    hint_text = puzzle_manager_instance.get_active_puzzle_hint()
    terminal.add_line(hint_text, style_key='comment')
    return True, None

def _handle_exit_puzzle(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    if game_state_manager.get_state() == STATE_PUZZLE_ACTIVE:
        game_state_manager.change_state(STATE_MAIN_TERMINAL)
        terminal.clear_prompt_override()
        if puzzle_manager_instance and puzzle_manager_instance.active_puzzle:
            terminal.add_line(f"Exited puzzle: {puzzle_manager_instance.active_puzzle.name}", style_key='warning')
            puzzle_manager_instance.active_puzzle = None
        else:
            terminal.add_line("Exited puzzle mode.", style_key='warning')
        terminal.add_line("Returning to main terminal.", style_key='highlight')
    else:
        terminal.add_line("Not currently in a puzzle.", style_key='error')
    return True, None

# --- Main Command Map ---
# --- System Management Command Handlers ---

def _handle_status(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    """Handles the 'status' command."""
    terminal.add_line("System Status: Nominal", style_key='success')
    terminal.add_line("Aether Network Connection: Stable", style_key='success')
    terminal.add_line("Corruption Level: Minimal", style_key='warning') # Example
    # TODO: Add more dynamic status info based on game_state
    return True, None

def _handle_processes(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    """Handles the 'processes' command."""
    terminal.add_line("PID   USER      COMMAND", style_key='highlight')
    terminal.add_line("1     root      /sbin/init", style_key='default_fg')
    terminal.add_line("45    system    aether_core_monitor", style_key='default_fg')
    terminal.add_line("101   player    /bin/bash", style_key='default_fg') # Example player process
    terminal.add_line("105   player    python main.py", style_key='default_fg') # The game itself?
    terminal.add_line("666   unknown   ???", style_key='error') # Example suspicious process
    # TODO: Add dynamic process list based on game_state, maybe corrupted entries
    return True, None

def _handle_kill(args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role):
    """Handles the 'kill' command."""
    if not args_list:
        terminal.add_line("kill: missing operand", style_key='error')
        terminal.add_line("Usage: kill <pid>", style_key='error')
        return True, None
    if len(args_list) > 1:
        terminal.add_line("kill: too many arguments", style_key='error')
        terminal.add_line("Usage: kill <pid>", style_key='error')
        return True, None

    try:
        pid_to_kill = int(args_list[0])
        # TODO: Add logic to check if PID exists and handle killing it
        # For now, just simulate based on PID
        if pid_to_kill == 666:
            terminal.add_line(f"Attempting to terminate process {pid_to_kill}...", style_key='warning')
            effect_manager.start_timed_delay(500)
            line_idx = terminal.add_line(f"kill: ({pid_to_kill}) - Operation failed. Access denied or process unstable.", style_key='error')
            if line_idx != -1:
                 effect_manager.start_character_corruption_effect(line_idx, 1000, 0.2, 60)
        elif pid_to_kill in [1, 45]:
             terminal.add_line(f"kill: ({pid_to_kill}) - Operation not permitted.", style_key='error')
        elif pid_to_kill in [101, 105]:
             terminal.add_line(f"Process {pid_to_kill} terminated.", style_key='success')
        else:
             terminal.add_line(f"kill: ({pid_to_kill}) - No such process.", style_key='error')

    except ValueError:
        terminal.add_line(f"kill: '{args_list[0]}' is not a valid PID.", style_key='error')

    return True, None
MAIN_COMMAND_HANDLERS = {
    "clear": _handle_clear,
    "help": _handle_help,
    "msfconsole": _handle_msfconsole,
    "echo": _handle_echo,
    "whoami": _handle_whoami,
    "hostname": _handle_hostname,
    "uname": _handle_uname,
    "head": _handle_head,
    "tail": _handle_tail,
    "rm": _handle_rm,
    "mv": _handle_mv,
    "theme": _handle_theme,
    "type": _handle_type_effect,
    "burst": _handle_burst_effect,
    "sequence": _handle_sequence_effect,
    "corrupt": _handle_corrupt_effect,
    "flicker": _handle_flicker_effect,
    "colorchange": _handle_colorchange_effect,
    "overlay": _handle_overlay_effect,
    "jiggle": _handle_jiggle_effect,
    "screenres": _handle_screenres,
    "fullscreen": _handle_fullscreen,
    "windowed": _handle_windowed,
    "pwd": _handle_pwd,
    "ls": _handle_ls,
    "cd": _handle_cd,
    "cat": _handle_cat,
    "mkdir": _handle_mkdir,
    "touch": _handle_touch,
    "scan": _handle_scan,
    "parse": _handle_parse,
    "restore": _handle_restore,
    "status": _handle_status,
    "processes": _handle_processes,
    "kill": _handle_kill,
    "integrity_check": _handle_integrity_check,
    "observe_traffic": _handle_observe_traffic,
    "find_exploit": _handle_find_exploit,
    "grep": _handle_grep,
    "start_puzzle": _handle_start_puzzle,
    "solve": _handle_solve_puzzle,
    "hint": _handle_puzzle_hint,
    "exit_puzzle": _handle_exit_puzzle,
}

def process_main_terminal_command(command_entered, terminal, game_state_manager, effect_manager, puzzle_manager_instance):
    """
    Processes commands entered in the main terminal.
    Returns a tuple: (bool: continue_running, dict: screen_action_details or None)
    screen_action_details can be:
    {'action': 'screen_change', 'type': 'set_resolution', 'width': W, 'height': H}
    {'action': 'screen_change', 'type': 'fullscreen'}
    {'action': 'screen_change', 'type': 'windowed'}
    """
    player_role = game_state_manager.get_player_role()
    try:
        parts = shlex.split(command_entered)
    except ValueError: # Handles unclosed quotes
        terminal.add_line("Error: Unmatched quote in command.", style_key='error')
        return True, None

    if not parts: # Empty command
        return True, None

    command_base = parts[0].lower()
    command_args_list = parts[1:] if len(parts) > 1 else []

    # Universal quit/exit commands
    if command_base in ["quit", "exit"]:
        if game_state_manager.is_state(STATE_PUZZLE_ACTIVE):
            # _handle_exit_puzzle now correctly accepts args_list
            _handle_exit_puzzle(command_args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role)
            return True, None # Stay in game, just exited puzzle
        return False, None # Signal to quit the game from other states

    current_state = game_state_manager.get_state()
    allowed_key = "allowed_main"
    if current_state == STATE_PUZZLE_ACTIVE:
        allowed_key = "allowed_puzzle"
    
    role_command_config = COMMAND_ACCESS.get(player_role, COMMAND_ACCESS[ROLE_GREY_HAT])
    
    if command_base not in role_command_config.get(allowed_key, []):
        if current_state == STATE_PUZZLE_ACTIVE and command_base in role_command_config.get("allowed_main", []):
            pass
        else:
            terminal.add_line(f"Error: Command '{command_base}' not recognized or not available for your alignment/state.", style_key='error')
            return True, None

    if command_base in MAIN_COMMAND_HANDLERS:
        handler = MAIN_COMMAND_HANDLERS[command_base]
        return handler(command_args_list, terminal, game_state_manager, effect_manager, puzzle_manager_instance, player_role)
    
    # Fallback for unknown commands if not caught by access check (should be rare)
    if command_entered:
        terminal.add_line(f"Unknown command: '{command_base}'", style_key='error')
    
    return True, None

# --- Individual Command Handlers for MSFConsole ---

def _handle_msf_clear(args, terminal, game_state_manager, effect_manager, player_role_msf): # Renamed args to match others, though not used
    terminal.clear_buffer()
    terminal.add_line("Screen cleared.", style_key='success')
    # MSF commands don't return screen_action, and continue_running is implicit.

def _handle_msf_exit_back(args, terminal, game_state_manager, effect_manager, player_role_msf):
    terminal.clear_prompt_override()
    game_state_manager.change_state("MAIN_TERMINAL")
    terminal.clear_buffer()
    terminal.add_line("Exited msfconsole.", style_key="highlight")
    terminal.add_line("Type 'help' for a list of commands.")
    # MSF commands don't directly control the main game loop's running status.
 
def _handle_msf_help(args, terminal, game_state_manager, effect_manager, player_role_msf):
    terminal.add_line("Core Commands:", style_key='highlight')
    allowed_msf_cmds_for_role = COMMAND_ACCESS.get(player_role_msf, {}).get("allowed_msf", list(COMMAND_ACCESS[ROLE_GREY_HAT]["help_text_msf"].keys()))
    help_texts_msf_role = COMMAND_ACCESS.get(player_role_msf, {}).get("help_text_msf", COMMAND_ACCESS[ROLE_GREY_HAT]["help_text_msf"])
    
    for cmd_key in sorted(allowed_msf_cmds_for_role):
        if cmd_key in help_texts_msf_role:
            terminal.add_line(help_texts_msf_role[cmd_key])
    
    # Ensure back/exit are shown if universally available but not in role's list
    if "back" not in allowed_msf_cmds_for_role and "back" in COMMAND_ACCESS[ROLE_GREY_HAT]["help_text_msf"]:
            terminal.add_line(COMMAND_ACCESS[ROLE_GREY_HAT]["help_text_msf"]["back"])
    if "exit" not in allowed_msf_cmds_for_role and "exit" in COMMAND_ACCESS[ROLE_GREY_HAT]["help_text_msf"]:
            terminal.add_line(COMMAND_ACCESS[ROLE_GREY_HAT]["help_text_msf"]["exit"])

def _get_current_msf_module(terminal):
    if terminal.prompt_override and terminal.prompt_override.startswith("msf6 exploit("):
        try:
            return terminal.prompt_override.split("(",1)[1].split(")",1)[0]
        except IndexError:
            return None
    return None

def _handle_msf_search(args, terminal, game_state_manager, effect_manager, player_role_msf):
    keyword = args.lower().strip() # _handle_msf_search still uses 'args' string, not args_list yet.
    if keyword:
        terminal.add_line(f"Matching Modules ({keyword}):", style_key="highlight")
        terminal.add_line("========================")
        terminal.add_line("")
        terminal.add_line("  #  Name                                     Disclosure Date  Rank    Check  Description")
        terminal.add_line("  -  ----                                     ---------------  ----    -----  -----------")
        found_count = 0
        # MSF_SIMULATED_MODULES should be defined globally or passed
        for i, mod_name in enumerate(MSF_SIMULATED_MODULES):
            if keyword in mod_name:
                found_count +=1
                rank = "excellent" if "exploit" in mod_name else "normal"
                desc = "Exploit module." if "exploit" in mod_name else "Auxiliary module."
                if mod_name == "exploit/windows/smb/ms08_067_netapi":
                    desc = "Microsoft Server Service Relative Path Stack Corruption"
                elif mod_name == "exploit/windows/smb/ms17_010_eternalblue":
                    desc = "MS17-010 EternalBlue SMB Remote Windows Kernel Pool Corruption"
                terminal.add_line(f"  {found_count-1:<2} {mod_name:<40} 2008-10-28       {rank:<7} No     {desc}")
        if found_count == 0:
            terminal.add_line(f"No modules found matching '{keyword}'.")
        terminal.scroll_to_bottom() # Scroll to bottom after adding all lines
    else:
        terminal.add_line("Usage: search <keyword>", style_key='error')

def _handle_msf_use(args, terminal, game_state_manager, effect_manager, player_role_msf):
    module_name = args.strip()
    if module_name and module_name in MSF_SIMULATED_MODULES: # MSF_SIMULATED_MODULES global or passed
        terminal.set_prompt_override(f"msf6 exploit({module_name}) > ")
    elif module_name:
        terminal.add_line(f"Failed to load module: {module_name}", style_key='error')
    else:
        terminal.add_line("Usage: use <module_path>", style_key='error')

def _handle_msf_info(args, terminal, game_state_manager, effect_manager, player_role_msf):
    module_to_info = args.strip()
    if not module_to_info: # If no arg, use current module
        module_to_info = _get_current_msf_module(terminal)
    
    if module_to_info and module_to_info in MSF_SIMULATED_MODULES: # MSF_SIMULATED_MODULES global or passed
        terminal.add_line(f"\nName: {module_to_info}", style_key="highlight")
        terminal.add_line(f"     Module: {module_to_info}")
        terminal.add_line( "     Platform: Windows" if "windows" in module_to_info else "     Platform: Multi")
        terminal.add_line( "     Arch: x86, x64")
        terminal.add_line( "     Privileged: Yes" if "exploit" in module_to_info else "     Privileged: No")
        terminal.add_line( "     Rank: Excellent" if "exploit" in module_to_info else "     Rank: Normal")
        terminal.add_line( "\nProvided by:")
        terminal.add_line( "  Hacker <hacker@example.com>")
        terminal.add_line( "\nAvailable targets:")
        terminal.add_line( "  Id  Name")
        terminal.add_line( "  --  ----")
        terminal.add_line( "  0   Automatic Targeting")
        terminal.add_line( "\nBasic options:") # Example options
        if module_to_info == "exploit/windows/smb/ms08_067_netapi":
                terminal.add_line("  RHOSTS  <blank>  yes  The target address range or CIDR identifier")
                terminal.add_line("  RPORT   445      yes  The target port (TCP)")
        elif module_to_info == "exploit/multi/handler":
                terminal.add_line("  PAYLOAD <blank>  yes  Payload to use.")
                terminal.add_line("  LHOST   <blank>  yes  The listen address (an interface may be specified)")
                terminal.add_line("  LPORT   4444     yes  The listen port")
        else:
            terminal.add_line("  RHOSTS  <blank>  yes  The target address")
            terminal.add_line("  LHOST   <blank>  no   The local host to listen on")
        terminal.add_line("\nDescription:")
        terminal.add_line(f"  Simulated description for {module_to_info}.")
        terminal.add_line("\nReferences:") # Example references
        terminal.add_line( "  https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2008-4250")
        terminal.add_line( "  https://www.exploit-db.com/exploits/12345")
        terminal.add_line("")
    elif module_to_info: # Arg was provided but not found
        terminal.add_line(f"Module not found: {module_to_info}", style_key='error')
    else: # No arg and no current module
        terminal.add_line("No module selected. Use 'info <module>' or 'use <module>' first.", style_key='error')

def _handle_msf_show_options(args, terminal, game_state_manager, effect_manager, player_role_msf):
    current_module_sim = _get_current_msf_module(terminal)
    if current_module_sim:
        terminal.add_line(f"\nModule options ({current_module_sim}):", style_key='highlight')
        terminal.add_line("\n   Name     Current Setting  Required  Description")
        terminal.add_line("   ----     ---------------  --------  -----------")
        if current_module_sim == "exploit/windows/smb/ms08_067_netapi":
            terminal.add_line("   RHOSTS                    yes       The target address range or CIDR identifier")
            terminal.add_line("   RPORT    445              yes       The target port (TCP)")
            terminal.add_line("   SMBPIPE  BROWSER          yes       The named pipe to use (BROWSER, SRVSVC)")
        elif current_module_sim == "exploit/multi/handler":
            terminal.add_line("   PAYLOAD                   yes       Payload to use.")
            terminal.add_line("   LHOST                     yes       The listen address")
            terminal.add_line("   LPORT    4444             yes       The listen port")
        elif current_module_sim == "exploit/windows/smb/ms17_010_eternalblue":
            terminal.add_line("   RHOSTS                    yes       The target host(s), range CIDR identifier, or hosts file with syntax 'file:<path>'")
            terminal.add_line("   RPORT    445              yes       The target port (TCP)")
        else:
            # Generic options for other modules if any
            terminal.add_line("   RHOSTS                    yes       The target address")
            terminal.add_line("   LHOST                     no        The local host to listen on (for reverse payloads)")
        terminal.add_line("\nExploit target:", style_key='highlight')
        terminal.add_line("\n   Id  Name")
        terminal.add_line("   --  ----")
        terminal.add_line("   0   Automatic Targeting\n")
    else:
        terminal.add_line("No module selected. Use 'use <module>' first.", style_key='error')

def _handle_msf_set(args, terminal, game_state_manager, effect_manager, player_role_msf):
    parts = args.split(" ", 1) # Split only once to get OPTION and VALUE
    if len(parts) == 2:
        opt, val = parts[0], parts[1]
        # Placeholder: In a real scenario, these would be stored (e.g., in game_state_manager or a context dict).
        terminal.add_line(f"{opt} => {val}")
    else:
        terminal.add_line("Usage: set <option> <value>", style_key='error')

def _handle_msf_run_exploit(args, terminal, game_state_manager, effect_manager, player_role_msf):
    current_module_sim = _get_current_msf_module(terminal)
    if player_role_msf == ROLE_WHITE_HAT:
        terminal.add_line("msf6> Command 'run'/'exploit' not permitted for White Hat alignment.", style_key='error')
    elif current_module_sim:
        terminal.add_line(f"[*] Started reverse TCP handler on 10.0.2.15:4444", style_key='highlight') # Example IP
        terminal.add_line(f"[*] {current_module_sim}: Running against RHOSTS=192.168.1.100 RPORT=445", style_key='highlight') # Example params
        terminal.add_line(f"[*] 192.168.1.100:445 - Automatically detecting the target...", style_key='highlight')
        effect_manager.start_timed_delay(500) # Simulate detection time
        terminal.add_line(f"[*] 192.168.1.100:445 - Fingerprint: Windows XP - Service Pack 3 - lang:English", style_key='success')
        terminal.add_line(f"[*] 192.168.1.100:445 - Selected Target: Windows XP SP3 English (AlwaysOn NX)", style_key='success')
        effect_manager.start_timed_delay(300)
        terminal.add_line(f"[*] 192.168.1.100:445 - Attempting to trigger the vulnerability...", style_key='highlight')
        effect_manager.start_timed_delay(1000) # Simulate exploitation attempt.
        # Simulate success with Meterpreter session.
        effect_manager.start_typing_effect(
            "[+] Meterpreter session 1 opened (10.0.2.15:4444 -> 192.168.1.100:1028) at 2024-05-10 06:30:00 -0500", # Example details.
            char_delay_ms=20,
            style_key='success',
            on_complete_callback=lambda: terminal.add_line("meterpreter > ", fg_color=get_current_theme().get('prompt'))
        )
        # TODO: Potentially change game state here to a METERPRETER_SESSION state if more interaction is planned.
    else:
        terminal.add_line("No module selected or exploit context not set.", style_key='error')

def _handle_msf_sessions(args, terminal, game_state_manager, effect_manager, player_role_msf):
    # This is a simplified check. A real version would check game_state for active sessions.
    session_opened_line_present = False
    for buf_line_data in terminal.buffer: # Check terminal history for a session line
        if "Meterpreter session 1 opened" in buf_line_data[0]:
            session_opened_line_present = True
            break
            
    if args.strip() == "-l" or not args.strip(): # Handles "sessions" and "sessions -l"
        if session_opened_line_present:
                terminal.add_line("\nActive sessions", style_key="highlight")
                terminal.add_line("===============\n")
                terminal.add_line("  Id  Type         Information                       Connection")
                terminal.add_line("  --  ----         -----------                       ----------")
                terminal.add_line("  1   meterpreter  NT AUTHORITY\\SYSTEM @ VICTIMPC  10.0.2.15:4444 -> 192.168.1.100:1028 (192.168.1.100)")
        else:
            terminal.add_line("No active sessions.")
    elif args.strip().startswith("-i "): # Placeholder for interacting with a session
        terminal.add_line("Session interaction not fully implemented. Example: sessions -i 1", style_key="highlight")
    else:
        terminal.add_line("Usage: sessions [-l | -i <id>]", style_key="error")

# --- MSF Command Map ---
MSF_COMMAND_HANDLERS = {
    "exit": _handle_msf_exit_back,
    "back": _handle_msf_exit_back,
    "clear": _handle_msf_clear, # Add clear command
    "help": _handle_msf_help,
    "search": _handle_msf_search,
    "use": _handle_msf_use,
    "info": _handle_msf_info,
    "show": _handle_msf_show_options,
    "set": _handle_msf_set,
    "run": _handle_msf_run_exploit,
    "exploit": _handle_msf_run_exploit, # Alias for run
    "sessions": _handle_msf_sessions,
}

MSF_KNOWN_COMMANDS = ["help", "use", "show", "set", "run", "exploit", "back", "exit", "search", "info", "sessions", "clear"]
MSF_SIMULATED_MODULES = [
    "exploit/windows/smb/ms08_067_netapi", "exploit/windows/smb/ms17_010_eternalblue",
    "exploit/multi/handler", "auxiliary/scanner/portscan/tcp", "auxiliary/scanner/http/title",
    "post/windows/gather/checkvm"
]
MSF_SIMULATED_OPTIONS = ["RHOSTS", "RPORT", "LHOST", "LPORT", "PAYLOAD", "TARGETURI", "THREADS"]

# --- MSF Command Processing --- (Old handle_msfconsole_tab_completion function removed)
def process_msfconsole_command(msf_command_entered, terminal, game_state_manager, effect_manager):
    """
    Processes commands entered in the MSFConsole.
    (Currently does not return a running status, assumes msfconsole itself doesn't quit the game directly)
    """
    current_module_sim = None
    if terminal.prompt_override and terminal.prompt_override.startswith("msf6 exploit("):
        current_module_sim = terminal.prompt_override.split("(",1)[1].split(")",1)[0]

    player_role_msf = game_state_manager.get_player_role()
    parts = msf_command_entered.split(" ", 1)
    msf_cmd_base = parts[0].lower()
    msf_cmd_args = parts[1] if len(parts) > 1 else ""

    allowed_msf_cmds_for_role = COMMAND_ACCESS.get(player_role_msf, {}).get("allowed_msf", list(COMMAND_ACCESS[ROLE_GREY_HAT]["help_text_msf"].keys()))

    if msf_cmd_base in MSF_COMMAND_HANDLERS:
        # exit/back are special, always allowed. Help should also generally be available.
        if msf_cmd_base not in allowed_msf_cmds_for_role and msf_cmd_base not in ["exit", "back", "help"]:
            terminal.add_line(f"msf6> Command '{msf_cmd_base}' not available for your current operational alignment.", style_key='error')
        else:
            handler = MSF_COMMAND_HANDLERS[msf_cmd_base]
            handler(msf_cmd_args, terminal, game_state_manager, effect_manager, player_role_msf)
    # Fallback for unknown MSFConsole commands.
    elif msf_command_entered: # Ensure there was some input.
        terminal.add_line(f"msf6> Unknown command: {msf_command_entered}", style_key='error')