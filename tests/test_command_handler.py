import pytest
from unittest.mock import MagicMock, patch, call
from command_handler import (
    process_main_terminal_command,
    process_msfconsole_command, # Will test later
    _handle_clear,
    _handle_help,
    _handle_echo,
    _handle_whoami,
    _handle_hostname,
    _handle_uname,
    _handle_head,
    _handle_tail,
    _handle_pwd,
    _handle_cd,
    _handle_mkdir,
    _handle_touch,
    _handle_cat,
    _handle_ls,
    _handle_rm,
    _handle_mv,
    _handle_theme,
    _handle_type_effect,
    _handle_burst_effect,
    _handle_sequence_effect,
    _handle_corrupt_effect,
    _handle_flicker_effect,
    _handle_colorchange_effect,
    _handle_overlay_effect,
    _handle_jiggle_effect,
    _handle_screenres,
    _handle_msf_exit_back,
    _handle_msf_help,
    _handle_msf_search,
    _handle_msf_use,
    _handle_msf_info,
    _handle_msf_show_options,
    _handle_msf_set,
    _handle_msf_run_exploit,
    _handle_msf_sessions,
    _handle_integrity_check, # Added for new command
    _handle_observe_traffic, # Added for new command
    _handle_find_exploit,    # Added for new command
    _handle_scan,
    _handle_parse,
    _handle_restore,
    _handle_grep, # Added for new command
    _handle_status,
    _handle_processes,
    _handle_kill,
    _handle_msfconsole, # Added for new test
    _handle_start_puzzle, # Added for new test
    _handle_solve_puzzle, # Added for new test
    # Import other handlers as they are tested
    _handle_puzzle_hint, # Added for new test
    _handle_exit_puzzle, # Added for new test
    MAIN_COMMAND_HANDLERS,
    MSF_COMMAND_HANDLERS,
    _handle_msf_clear, # Ensure this is imported
    _get_current_msf_module # Import the helper function
)
from game_state import GameStateManager, STATE_MAIN_TERMINAL, STATE_MSFCONSOLE, STATE_PUZZLE_ACTIVE, ROLE_WHITE_HAT, ROLE_GREY_HAT, ROLE_BLACK_HAT
from effects import EffectManager # For type hinting if needed, will be mocked
from terminal_renderer import Terminal # For type hinting, will be mocked
from commands_config import COMMAND_ACCESS # For checking allowed commands

# --- Mocks and Fixtures ---

@pytest.fixture
def mock_terminal():
    term = MagicMock(spec=Terminal)
    term.buffer = []
    term.username = "testuser"
    term.hostname = "testhost"
    term.fs_handler = MagicMock() # Mock the fs_handler attribute of terminal
    term.prompt_override = None # Initialize prompt_override for MSF console state
    term.fs_handler.get_current_path_str.return_value = "~" # Default mock path
    term.fs_handler.is_item_corrupted.return_value = False # Default not corrupted
    term.apply_theme_colors = MagicMock() # Mock this method
    term._update_prompt_string = MagicMock() # Mock this method
    term.clear_prompt_override = MagicMock()
    term.set_prompt_override = MagicMock()
    term.add_line = MagicMock(return_value=0) # return a dummy line index
    term.clear_buffer = MagicMock()
    term.update_line_text = MagicMock() # Add mock for update_line_text
    return term

@pytest.fixture
def mock_game_state_manager():
    gsm = MagicMock(spec=GameStateManager)
    gsm.get_player_role.return_value = ROLE_GREY_HAT # Default to a permissive role
    gsm.change_state = MagicMock()
    return gsm

@pytest.fixture
def mock_effect_manager():
    em = MagicMock(spec=EffectManager)
    return em

# --- Tests for Individual Main Command Handlers ---

def test_handle_clear(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_clear([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.clear_buffer.assert_called_once()
    mock_terminal.add_line.assert_called_with("Screen cleared.", style_key='success')

def test_handle_echo(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = ["Hello,", "world!"]
    # Assuming _handle_echo is called by process_main_terminal_command,
    # it would receive args_list.
    # The puzzle_manager_instance is often passed but not always used by simple handlers.
    # For _handle_echo, it's not used, so passing None or a MagicMock is fine.
    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_echo(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_with("Hello, world!")

def test_handle_echo_empty_list(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = []
    mock_puzzle_manager = MagicMock()
    _handle_echo(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_called_with("")

def test_handle_echo_single_word(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = ["Test"]
    mock_puzzle_manager = MagicMock()
    _handle_echo(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_called_with("Test")

def test_handle_whoami(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_terminal.username = "player_one"
    mock_terminal.fs_handler.is_item_corrupted.return_value = False # Not corrupted
    
    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_whoami([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_with("player_one")
    mock_effect_manager.start_character_corruption_effect.assert_not_called()

def test_handle_whoami_corrupted(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_terminal.username = "glitched_user"
    mock_terminal.fs_handler.is_item_corrupted.return_value = True # Root is corrupted
    mock_terminal.add_line.return_value = 5 # Simulate a valid line index

    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_whoami([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_with("glitched_user")
    mock_effect_manager.start_character_corruption_effect.assert_called_once_with(
        5, duration_ms=350, intensity=0.2, rate_ms=60
    )

def test_handle_hostname(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_terminal.hostname = "cyberdeck"
    mock_terminal.fs_handler.is_item_corrupted.return_value = False

    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_hostname([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_with("cyberdeck")
    mock_effect_manager.start_text_flicker_effect.assert_not_called()

def test_handle_hostname_corrupted(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_terminal.hostname = "unstable_host"
    mock_terminal.fs_handler.is_item_corrupted.return_value = True
    mock_terminal.add_line.return_value = 3

    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_hostname([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_with("unstable_host")
    mock_effect_manager.start_text_flicker_effect.assert_called_once_with(
        3, duration_ms=350, flicker_rate_ms=70, flicker_color_key='error'
    )

def test_handle_uname_default(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_terminal.fs_handler.is_item_corrupted.return_value = False
    mock_terminal.add_line.return_value = 0 # Dummy line index

    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_uname([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_with("Linux")
    mock_effect_manager.start_character_corruption_effect.assert_not_called()

def test_handle_uname_default_corrupted(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_terminal.fs_handler.is_item_corrupted.return_value = True # Root is corrupted
    mock_terminal.add_line.return_value = 1 # Simulate a valid line index

    mock_puzzle_manager = MagicMock()
    # Note: "some_other_arg" will be the first element in args_list.
    # _handle_uname checks `args_list[0] == "-a"`. So this will take the non "-a" path.
    continue_running, action = _handle_uname(["some_other_arg"], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_with("Linux")
    mock_effect_manager.start_character_corruption_effect.assert_called_once_with(
        1, duration_ms=400, intensity=0.25, rate_ms=50
    )

def test_handle_uname_all_arg(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_terminal.fs_handler.is_item_corrupted.return_value = False
    mock_terminal.add_line.return_value = 2

    expected_output = "Linux kali 6.1.0-kali5-amd64 #1 SMP PREEMPT_DYNAMIC Debian 6.1.12-1kali2 (2023-02-23) x86_64 GNU/Linux"
    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_uname(["-a"], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_with(expected_output)
    mock_effect_manager.start_character_corruption_effect.assert_not_called()

def test_handle_uname_all_arg_corrupted(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_terminal.fs_handler.is_item_corrupted.return_value = True
    mock_terminal.add_line.return_value = 3 # Dummy line index
    mock_puzzle_manager = MagicMock()
    expected_output = "Linux kali 6.1.0-kali5-amd64 #1 SMP PREEMPT_DYNAMIC Debian 6.1.12-1kali2 (2023-02-23) x86_64 GNU/Linux"
    
    continue_running, action = _handle_uname(["-a"], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_with(expected_output)
    mock_effect_manager.start_character_corruption_effect.assert_called_once_with(
        3, duration_ms=400, intensity=0.25, rate_ms=50
    )
    mock_terminal.add_line.assert_called_with(expected_output)
    mock_effect_manager.start_character_corruption_effect.assert_called_once()

# --- Test for shlex parsing in process_main_terminal_command ---
def test_process_main_terminal_command_shlex_parsing(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_puzzle_manager = MagicMock()
    # Mock a handler for 'echo' to check the args_list it receives
    mock_echo_handler = MagicMock(return_value=(True, None))
    
    with patch.dict(MAIN_COMMAND_HANDLERS, {'echo': mock_echo_handler}):
        # Test with a command that requires shlex splitting (quoted argument)
        command_input = 'echo "hello world" this is a test'
        process_main_terminal_command(command_input, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager)
        
        # Assert that the mock_echo_handler was called with the correctly parsed list
        expected_args_list = ['hello world', 'this', 'is', 'a', 'test']
        mock_echo_handler.assert_called_once()
        # The actual call object is mock_echo_handler.call_args.
        # It's a tuple (args, kwargs). args is also a tuple.
        # The first element of the inner args tuple is our args_list.
        called_args_list = mock_echo_handler.call_args[0][0]
        assert called_args_list == expected_args_list

    # Test with unclosed quote
    mock_terminal.reset_mock() # Reset add_line calls
    command_input_unclosed_quote = 'echo "hello world'
    process_main_terminal_command(command_input_unclosed_quote, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager)
    mock_terminal.add_line.assert_called_with("Error: Unmatched quote in command.", style_key='error')


# --- Tests for _handle_msfconsole ---

def test_handle_msfconsole(mock_terminal, mock_game_state_manager, mock_effect_manager):
    """Test the logic for entering MSF mode."""
    mock_puzzle_manager = MagicMock()
    args = [] # _handle_msfconsole doesn't use args

    continue_running, action = _handle_msfconsole(
        args,
        mock_terminal,
        mock_game_state_manager,
        mock_effect_manager,
        mock_puzzle_manager,
        ROLE_GREY_HAT # Role doesn't affect this function's core logic
    )

    assert continue_running is True
    assert action is None

    # Assert state change
    mock_game_state_manager.change_state.assert_called_once_with(STATE_MSFCONSOLE)

    # Assert terminal changes
    mock_terminal.clear_buffer.assert_called_once()
    mock_terminal.set_prompt_override.assert_called_once_with("msf6 > ")

    # Assert output lines are added
    expected_calls = [
        call("Starting Metasploit Framework console...", style_key='highlight'),
        call("       =[ metasploit v6.0.50-dev                          ]", fg_color=(200,200,0)),
        call("+ -- --=[ 2100 exploits - 1100 auxiliary - 360 post       ]", fg_color=(200,200,0)),
        call("+ -- --=[ 590 payloads - 45 encoders - 10 nops            ]", fg_color=(200,200,0)),
        call("       =[ 1000 evasion                                     ]", fg_color=(200,200,0)),
        call("")
    ]
    mock_terminal.add_line.assert_has_calls(expected_calls, any_order=False)
    assert mock_terminal.add_line.call_count == len(expected_calls)
# --- Tests for MSFConsole Command Handlers ---
def test_handle_msf_clear(mock_terminal, mock_game_state_manager, mock_effect_manager):
    # player_role_msf is passed but not used by _handle_msf_clear
    _handle_msf_clear(None, mock_terminal, mock_game_state_manager, mock_effect_manager, ROLE_GREY_HAT)
    mock_terminal.clear_buffer.assert_called_once()
    mock_terminal.add_line.assert_called_with("Screen cleared.", style_key='success')

# --- Tests for _get_current_msf_module ---

def test_get_current_msf_module_when_set(mock_terminal):
    """Test _get_current_msf_module when a module is set."""
    mock_terminal.prompt_override = "msf6 exploit(multi/handler) > "
    module_name = _get_current_msf_module(mock_terminal)
    assert module_name == "multi/handler"

def test_get_current_msf_module_when_not_set(mock_terminal):
    """Test _get_current_msf_module when no module is set."""
    mock_terminal.prompt_override = "msf6 > "
    module_name = _get_current_msf_module(mock_terminal)
    assert module_name is None

def test_get_current_msf_module_none_prompt_override(mock_terminal):
    """Test _get_current_msf_module when prompt_override is None."""
    mock_terminal.prompt_override = None
    module_name = _get_current_msf_module(mock_terminal)
    assert module_name is None

# --- Tests for Puzzle Command Handlers ---

def test_handle_start_puzzle_no_puzzle_manager(mock_terminal, mock_game_state_manager, mock_effect_manager):
    """Test _handle_start_puzzle when puzzle manager is not initialized."""
    args = ["puzzle123"]
    continue_running, action = _handle_start_puzzle(
        args, mock_terminal, mock_game_state_manager, mock_effect_manager, None, ROLE_GREY_HAT
    )
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with("Puzzle system not initialized.", style_key='error')

def test_handle_start_puzzle_missing_operand(mock_terminal, mock_game_state_manager, mock_effect_manager):
    """Test _handle_start_puzzle with no arguments."""
    mock_puzzle_manager = MagicMock()
    mock_puzzle_manager.puzzles = {"puzzle1": {}, "puzzle2": {}} # Simulate available puzzles
    args = []
    continue_running, action = _handle_start_puzzle(
        args, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT
    )
    assert continue_running is True
    assert action is None
    expected_calls = [
        call("start_puzzle: missing puzzle_id operand", style_key='error'),
        call("Usage: start_puzzle <puzzle_id>", style_key='error'),
        call("Available puzzles: puzzle1, puzzle2", style_key='comment')
    ]
    mock_terminal.add_line.assert_has_calls(expected_calls, any_order=False)
    assert mock_terminal.add_line.call_count == len(expected_calls)

def test_handle_start_puzzle_missing_operand_no_available_puzzles(mock_terminal, mock_game_state_manager, mock_effect_manager):
    """Test _handle_start_puzzle with no arguments and no available puzzles."""
    mock_puzzle_manager = MagicMock()
    mock_puzzle_manager.puzzles = {} # Simulate no available puzzles
    args = []
    continue_running, action = _handle_start_puzzle(
        args, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT
    )
    assert continue_running is True
    assert action is None
    expected_calls = [
        call("start_puzzle: missing puzzle_id operand", style_key='error'),
        call("Usage: start_puzzle <puzzle_id>", style_key='error'),
        call("No puzzles currently available.", style_key='comment')
    ]
    mock_terminal.add_line.assert_has_calls(expected_calls, any_order=False)
    assert mock_terminal.add_line.call_count == len(expected_calls)


def test_handle_start_puzzle_too_many_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    """Test _handle_start_puzzle with too many arguments."""
    mock_puzzle_manager = MagicMock()
    args = ["puzzle123", "extra_arg"]
    continue_running, action = _handle_start_puzzle(
        args, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT
    )
    assert continue_running is True
    assert action is None
    expected_calls = [
        call("start_puzzle: too many arguments", style_key='error'),
        call("Usage: start_puzzle <puzzle_id>", style_key='error')
    ]
    mock_terminal.add_line.assert_has_calls(expected_calls, any_order=False)
    assert mock_terminal.add_line.call_count == len(expected_calls)

def test_handle_start_puzzle_not_found(mock_terminal, mock_game_state_manager, mock_effect_manager):
    """Test _handle_start_puzzle when the specified puzzle ID is not found."""
    mock_puzzle_manager = MagicMock()
    puzzle_id = "nonexistent_puzzle"
    mock_puzzle_manager.start_puzzle.return_value = f"Error: Puzzle '{puzzle_id}' not found."
    args = [puzzle_id]
    continue_running, action = _handle_start_puzzle(
        args, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT
    )
    assert continue_running is True
    assert action is None
    mock_puzzle_manager.start_puzzle.assert_called_once_with(puzzle_id)
    mock_terminal.add_line.assert_called_once_with(f"Error: Puzzle '{puzzle_id}' not found.", style_key='error')
    mock_game_state_manager.change_state.assert_not_called() # State should not change on error
    mock_terminal.clear_buffer.assert_not_called()
    mock_terminal.set_prompt_override.assert_not_called()

def test_handle_start_puzzle_success(mock_terminal, mock_game_state_manager, mock_effect_manager):
    """Test _handle_start_puzzle with a valid puzzle ID."""
    mock_puzzle_manager = MagicMock()
    puzzle_id = "valid_puzzle"
    puzzle_name = "Valid Puzzle Name"
    puzzle_display_text = "This is the puzzle text.\nAnother line."
    
    # Mock the active_puzzle attribute that is set by start_puzzle
    mock_puzzle_manager.active_puzzle = MagicMock()
    mock_puzzle_manager.active_puzzle.name = puzzle_name
    
    mock_puzzle_manager.start_puzzle.return_value = puzzle_display_text
    args = [puzzle_id]
    
    # Ensure initial state is not puzzle active
    mock_game_state_manager.current_state = STATE_MAIN_TERMINAL

    continue_running, action = _handle_start_puzzle(
        args, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT
    )
    assert continue_running is True
    assert action is None
    mock_puzzle_manager.start_puzzle.assert_called_once_with(puzzle_id)
    mock_game_state_manager.change_state.assert_called_once_with(STATE_PUZZLE_ACTIVE)
    mock_terminal.clear_buffer.assert_called_once()
    
    # Check prompt override is set correctly for puzzle state
    mock_terminal.set_prompt_override.assert_called_once_with(f"puzzle ({puzzle_id}) > ")

    expected_calls = [
        call(f"--- Puzzle Activated: {puzzle_name} ---", style_key='highlight'),
        call("This is the puzzle text."),
        call("Another line."),
        call("---", style_key='highlight'),
        call("Use 'solve <your_answer>' to attempt.", style_key='comment'),
        call("Use 'hint' for a clue, or 'exit_puzzle' to leave.", style_key='comment')
    ]
    mock_terminal.add_line.assert_has_calls(expected_calls, any_order=False)
    assert mock_terminal.add_line.call_count == len(expected_calls)

# --- Tests for _handle_solve_puzzle ---

def test_handle_solve_puzzle_no_active_puzzle(mock_terminal, mock_game_state_manager, mock_effect_manager):
    """Test _handle_solve_puzzle when there is no active puzzle."""
    mock_puzzle_manager = MagicMock()
    mock_puzzle_manager.active_puzzle = None # Simulate no active puzzle
    mock_game_state_manager.get_state.return_value = STATE_PUZZLE_ACTIVE # Set the state for the test
    args = ["some_answer"]

    continue_running, action = _handle_solve_puzzle(
        args, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT
    )

    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with("Error: Puzzle active state mismatch. Returning to main terminal.", style_key='error')
    mock_game_state_manager.change_state.assert_called_once_with(STATE_MAIN_TERMINAL)
    mock_terminal.clear_prompt_override.assert_called_once()
    mock_puzzle_manager.submit_solution.assert_not_called() # Ensure submit_solution is not called

def test_handle_solve_puzzle_no_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    """Test _handle_solve_puzzle with no arguments."""
    mock_puzzle_manager = MagicMock()
    mock_puzzle_manager.active_puzzle = MagicMock() # Simulate an active puzzle
    mock_game_state_manager.get_state.return_value = STATE_PUZZLE_ACTIVE # Set the state for the test
    args = []

    continue_running, action = _handle_solve_puzzle(
        args, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT
    )

    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with("Usage: solve <your_answer>", style_key='error')
    mock_puzzle_manager.attempt_active_puzzle.assert_not_called()

def test_handle_solve_puzzle_too_many_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    """Test _handle_solve_puzzle with too many arguments."""
    mock_puzzle_manager = MagicMock()
    mock_puzzle_manager.active_puzzle = MagicMock() # Simulate an active puzzle
    # Mock the return value of attempt_active_puzzle to avoid subsequent assertions failing
    mock_puzzle_manager.attempt_active_puzzle.return_value = (False, "Incorrect. Try again.")
    mock_game_state_manager.get_state.return_value = STATE_PUZZLE_ACTIVE # Set the state for the test
    args = ["solution_part_1", "solution_part_2"]

    continue_running, action = _handle_solve_puzzle(
        args, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT
    )

    assert continue_running is True
    assert action is None
    # The function should join the arguments and pass them to attempt_active_puzzle
    mock_puzzle_manager.attempt_active_puzzle.assert_called_once_with("solution_part_1 solution_part_2")
    # It should also add the feedback line from attempt_active_puzzle
    mock_terminal.add_line.assert_called_once_with("Incorrect. Try again.", style_key='error')

def test_handle_solve_puzzle_correct_solution(mock_terminal, mock_game_state_manager, mock_effect_manager):
    """Test _handle_solve_puzzle with a correct solution."""
    mock_puzzle_manager = MagicMock()
    mock_puzzle_manager.active_puzzle = MagicMock() # Simulate an active puzzle
    mock_puzzle_manager.attempt_active_puzzle.return_value = (True, "Correct! Puzzle solved.") # Simulate correct solution
    mock_game_state_manager.get_state.return_value = STATE_PUZZLE_ACTIVE # Set the state for the test
    args = ["correct_answer"]

    continue_running, action = _handle_solve_puzzle(
        args, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT
    )

    assert continue_running is True
    assert action is None
    mock_puzzle_manager.attempt_active_puzzle.assert_called_once_with("correct_answer")
    # The function calls add_line twice on success
    expected_calls = [
        call("Correct! Puzzle solved.", style_key='success'),
        call("Returning to main terminal.", style_key='highlight')
    ]
    mock_terminal.add_line.assert_has_calls(expected_calls, any_order=False)
    assert mock_terminal.add_line.call_count == len(expected_calls)
    mock_game_state_manager.change_state.assert_called_once_with(STATE_MAIN_TERMINAL) # Should return to main state
    mock_terminal.clear_prompt_override.assert_called_once() # Should clear puzzle prompt

def test_handle_solve_puzzle_incorrect_solution(mock_terminal, mock_game_state_manager, mock_effect_manager):
    """Test _handle_solve_puzzle with an incorrect solution."""
    mock_puzzle_manager = MagicMock()
    mock_puzzle_manager.active_puzzle = MagicMock() # Simulate an active puzzle
    # The function calls attempt_active_puzzle, not submit_solution
    mock_puzzle_manager.attempt_active_puzzle.return_value = (False, "Incorrect. Try again.") # Simulate incorrect solution
    mock_game_state_manager.get_state.return_value = STATE_PUZZLE_ACTIVE # Set the state for the test
    args = ["wrong_answer"]

    continue_running, action = _handle_solve_puzzle(
        args, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT
    )

    assert continue_running is True
    assert action is None
    # Assert that attempt_active_puzzle was called with the correct argument
    mock_puzzle_manager.attempt_active_puzzle.assert_called_once_with("wrong_answer")
    # Assert that the feedback line was added
    mock_terminal.add_line.assert_called_once_with("Incorrect. Try again.", style_key='error')
    # Assert that the state did NOT change and prompt override was NOT cleared
    mock_game_state_manager.change_state.assert_not_called()
    mock_terminal.clear_prompt_override.assert_not_called()
    mock_terminal.add_line.assert_called_once_with("Incorrect. Try again.", style_key='error')
    mock_game_state_manager.change_state.assert_not_called() # Should remain in puzzle state
    mock_terminal.clear_prompt_override.assert_not_called()

# --- Tests for _handle_puzzle_hint ---

def test_handle_puzzle_hint_no_puzzle_manager(mock_terminal, mock_game_state_manager, mock_effect_manager):
    """Test _handle_puzzle_hint when puzzle manager is not initialized."""
    args = [] # _handle_puzzle_hint doesn't use args
    continue_running, action = _handle_puzzle_hint(
        args, mock_terminal, mock_game_state_manager, mock_effect_manager, None, ROLE_GREY_HAT
    )
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with("Puzzle system not initialized.", style_key='error')

def test_handle_puzzle_hint_no_active_puzzle(mock_terminal, mock_game_state_manager, mock_effect_manager):
    """Test _handle_puzzle_hint when no puzzle is active."""
    mock_puzzle_manager = MagicMock()
    mock_puzzle_manager.active_puzzle = None # Simulate no active puzzle
    mock_game_state_manager.get_state.return_value = STATE_MAIN_TERMINAL # Simulate not in puzzle state
    args = []
    continue_running, action = _handle_puzzle_hint(
        args, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT
    )
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with("No puzzle is currently active to get a hint for.", style_key='error')
    mock_puzzle_manager.get_active_puzzle_hint.assert_not_called() # Ensure hint is not requested

def test_handle_puzzle_hint_success(mock_terminal, mock_game_state_manager, mock_effect_manager):
    """Test _handle_puzzle_hint when a puzzle is active and hint is retrieved."""
    mock_puzzle_manager = MagicMock()
    mock_puzzle_manager.active_puzzle = MagicMock() # Simulate an active puzzle
    mock_game_state_manager.get_state.return_value = STATE_PUZZLE_ACTIVE # Simulate in puzzle state
    hint_text = "This is a helpful hint."
    mock_puzzle_manager.get_active_puzzle_hint.return_value = hint_text
    args = []
    continue_running, action = _handle_puzzle_hint(
        args, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT
    )
    assert continue_running is True
    assert action is None
    mock_puzzle_manager.get_active_puzzle_hint.assert_called_once()
    mock_terminal.add_line.assert_called_once_with(hint_text, style_key='comment')

# --- Tests for _handle_exit_puzzle ---

def test_handle_exit_puzzle_success(mock_terminal, mock_game_state_manager, mock_effect_manager):
    """Test _handle_exit_puzzle when a puzzle is active."""
    mock_puzzle_manager = MagicMock()
    mock_puzzle_manager.active_puzzle = MagicMock() # Simulate an active puzzle
    mock_puzzle_manager.active_puzzle.name = "Test Puzzle"
    mock_game_state_manager.get_state.return_value = STATE_PUZZLE_ACTIVE # Set the state for the test

    args = [] # _handle_exit_puzzle doesn't use args

    continue_running, action = _handle_exit_puzzle(
        args, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT
    )

    assert continue_running is True
    assert action is None

    # Assert state change
    mock_game_state_manager.change_state.assert_called_once_with(STATE_MAIN_TERMINAL)

    # Assert terminal changes
    mock_terminal.clear_prompt_override.assert_called_once()
    assert mock_puzzle_manager.active_puzzle is None # Should set active_puzzle to None

    # Assert output lines are added
    expected_calls = [
        call("Exited puzzle: Test Puzzle", style_key='warning'),
        call("Returning to main terminal.", style_key='highlight')
    ]
    mock_terminal.add_line.assert_has_calls(expected_calls, any_order=False)
    assert mock_terminal.add_line.call_count == len(expected_calls)

def test_handle_exit_puzzle_not_in_puzzle_state(mock_terminal, mock_game_state_manager, mock_effect_manager):
    """Test _handle_exit_puzzle when not in puzzle active state."""
    mock_puzzle_manager = MagicMock()
    mock_puzzle_manager.active_puzzle = None # No active puzzle
    mock_game_state_manager.get_state.return_value = STATE_MAIN_TERMINAL # Simulate not in puzzle state

    args = []

    continue_running, action = _handle_exit_puzzle(
        args, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT
    )

    assert continue_running is True
    assert action is None

    # Assert state change does not happen
    mock_game_state_manager.change_state.assert_not_called()

    # Assert terminal changes do not happen
    mock_terminal.clear_prompt_override.assert_not_called()
    assert mock_puzzle_manager.active_puzzle is None # Should remain None

    # Assert error line is added
    mock_terminal.add_line.assert_called_once_with("Not currently in a puzzle.", style_key='error')

def test_handle_exit_puzzle_active_state_no_active_puzzle(mock_terminal, mock_game_state_manager, mock_effect_manager):
    """Test _handle_exit_puzzle when in puzzle active state but active_puzzle is None."""
    mock_puzzle_manager = MagicMock()
    mock_puzzle_manager.active_puzzle = None # Simulate no active puzzle despite state
    mock_game_state_manager.get_state.return_value = STATE_PUZZLE_ACTIVE # Simulate in puzzle state

    args = []

    continue_running, action = _handle_exit_puzzle(
        args, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT
    )

    assert continue_running is True
    assert action is None

    # Assert state change
    mock_game_state_manager.change_state.assert_called_once_with(STATE_MAIN_TERMINAL)

    # Assert terminal changes
    mock_terminal.clear_prompt_override.assert_called_once()
    assert mock_puzzle_manager.active_puzzle is None # Should remain None

    # Assert output lines are added (the 'Exited puzzle mode.' branch)
    expected_calls = [
        call("Exited puzzle mode.", style_key='warning'),
        call("Returning to main terminal.", style_key='highlight')
    ]
    mock_terminal.add_line.assert_has_calls(expected_calls, any_order=False)
    assert mock_terminal.add_line.call_count == len(expected_calls)


# In test_handle_msf_search_with_keyword, add scroll_to_bottom assertion
# (This test already exists, we are modifying it)
# Find the existing test_handle_msf_search_with_keyword and add the assertion.
# For brevity, I'll assume it's found and show the modification.
# If it's not found, a new test would be structured similarly.

# Placeholder for where test_handle_msf_search_with_keyword would be:
# def test_handle_msf_search_with_keyword(...):
#    ... (existing assertions) ...
#    mock_terminal.scroll_to_bottom.assert_called_once() # Add this line

# Let's find the actual test_handle_msf_search_with_keyword and modify it.
# It's around line 1855 in the provided file listing.
# The following diff will target that existing test.

# --- Tests for _handle_head_tail (via _handle_head and _handle_tail) ---

def _test_head_tail_logic(command_fn, command_name, mock_terminal, mock_game_state_manager, mock_effect_manager):
    file_path = "test.txt"
    full_content = "\n".join([f"Line {i+1}" for i in range(20)]) # 20 lines of content
    mock_puzzle_manager = MagicMock() # Add mock puzzle manager

    # Test 1: Default lines (10)
    mock_terminal.reset_mock()
    mock_terminal.fs_handler.get_item_content.return_value = full_content
    command_fn([file_path], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.fs_handler.get_item_content.assert_called_with(file_path)
    if command_name == "head":
        expected_lines = full_content.splitlines()[:10]
    else: # tail
        expected_lines = full_content.splitlines()[-10:]
    assert mock_terminal.add_line.call_count == 10
    for i, line_content in enumerate(expected_lines):
        assert mock_terminal.add_line.call_args_list[i] == call(line_content)

    # Test 2: Custom lines with -n
    mock_terminal.reset_mock()
    mock_terminal.fs_handler.get_item_content.return_value = full_content
    command_fn(["-n", "5", file_path], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    if command_name == "head":
        expected_lines_n5 = full_content.splitlines()[:5]
    else: # tail
        expected_lines_n5 = full_content.splitlines()[-5:]
    assert mock_terminal.add_line.call_count == 5
    for i, line_content in enumerate(expected_lines_n5):
        assert mock_terminal.add_line.call_args_list[i] == call(line_content)

    # Test 3: File not found
    mock_terminal.reset_mock()
    mock_terminal.fs_handler.get_item_content.return_value = None
    mock_terminal.fs_handler._resolve_path_str_to_list.return_value = ["path", "to", file_path]
    mock_terminal.fs_handler._get_node_at_path.return_value = None # Simulate not found
    command_fn([file_path], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_called_with(f"{command_name}: {file_path}: No such file or directory", style_key='error')

    # Test 4: Target is a directory
    mock_terminal.reset_mock()
    mock_terminal.fs_handler.get_item_content.return_value = None
    mock_terminal.fs_handler._resolve_path_str_to_list.return_value = ["path", "to", file_path]
    mock_terminal.fs_handler._get_node_at_path.return_value = {} # Simulate directory
    command_fn([file_path], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_called_with(f"{command_name}: {file_path}: Is a directory", style_key='error')

    # Test 5: Missing file operand
    mock_terminal.reset_mock()
    command_fn([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_called_with(f"{command_name}: missing file operand", style_key='error')

    mock_terminal.reset_mock()
    command_fn(["-n", "5"], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT) # Only -n arg
    mock_terminal.add_line.assert_called_with(f"{command_name}: missing file operand", style_key='error')


    # Test 6: Invalid number for -n
    mock_terminal.reset_mock()
    command_fn(["-n", "abc", file_path], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_called_with(f"{command_name}: invalid number of lines: 'abc'", style_key='error')

    # Test 7: -n option without a number
    mock_terminal.reset_mock()
    command_fn(["-n", file_path], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    # This case, depending on implementation, might be caught as "missing file operand" if file_path is taken as the number,
    # or "invalid number" if it tries to parse file_path. The current code treats file_path as the number for -n.
    # Let's adjust based on current _handle_head_tail logic: it will try to parse file_path as num_lines.
    # If file_path is not a number, it's an invalid number. If it IS a number, then it's missing file operand.
    # For this test, assume file_path "test.txt" is not a number.
    mock_terminal.add_line.assert_called_with(f"{command_name}: invalid number of lines: '{file_path}'", style_key='error')

    mock_terminal.reset_mock()
    command_fn(["-n"], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT) # Just -n
    mock_terminal.add_line.assert_called_with(f"{command_name}: option requires an argument -- 'n'", style_key='error')


def test_handle_head(mock_terminal, mock_game_state_manager, mock_effect_manager):
    _test_head_tail_logic(_handle_head, "head", mock_terminal, mock_game_state_manager, mock_effect_manager)

def test_handle_tail(mock_terminal, mock_game_state_manager, mock_effect_manager):
    _test_head_tail_logic(_handle_tail, "tail", mock_terminal, mock_game_state_manager, mock_effect_manager)

# --- Tests for _handle_grep ---

def test_handle_grep_success_found_matches(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = ["pattern", "file.txt"]
    file_content = "line one has pattern\nline two no match\nanother pattern line"
    mock_terminal.fs_handler.get_item_content.return_value = file_content
    mock_terminal.fs_handler.is_item_corrupted.return_value = False
    mock_puzzle_manager = MagicMock()

    _handle_grep(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)

    expected_calls = [
        call("1:line one has pattern"),
        call("3:another pattern line")
    ]
    mock_terminal.add_line.assert_has_calls(expected_calls)
    assert mock_terminal.add_line.call_count == 2
    mock_effect_manager.start_character_corruption_effect.assert_not_called()
    mock_effect_manager.start_text_flicker_effect.assert_not_called()

def test_handle_grep_success_no_matches(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = ["nonexistent", "file.txt"]
    file_content = "line one\nline two"
    mock_terminal.fs_handler.get_item_content.return_value = file_content
    mock_terminal.fs_handler.is_item_corrupted.return_value = False
    mock_puzzle_manager = MagicMock()

    _handle_grep(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_not_called() # Grep outputs nothing if no match

def test_handle_grep_file_not_found(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = ["pattern", "nonexistent.txt"]
    mock_terminal.fs_handler.get_item_content.return_value = None
    mock_terminal.fs_handler._resolve_path_str_to_list.return_value = ["nonexistent.txt"]
    mock_terminal.fs_handler._get_node_at_path.return_value = None # Simulate not found
    mock_puzzle_manager = MagicMock()

    _handle_grep(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_called_once_with("grep: nonexistent.txt: No such file or directory", style_key='error')

def test_handle_grep_target_is_directory(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = ["pattern", "mydir"]
    mock_terminal.fs_handler.get_item_content.return_value = None # Directories don't have string content this way
    mock_terminal.fs_handler._resolve_path_str_to_list.return_value = ["mydir"]
    mock_terminal.fs_handler._get_node_at_path.return_value = {} # Simulate directory
    mock_puzzle_manager = MagicMock()

    _handle_grep(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_called_once_with("grep: mydir: Is a directory", style_key='error')

def test_handle_grep_incorrect_arg_count(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_puzzle_manager = MagicMock()
    _handle_grep(["pattern_only"], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_called_once_with("Usage: grep <pattern> <file>", style_key='error')

    mock_terminal.reset_mock()
    _handle_grep([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_called_once_with("Usage: grep <pattern> <file>", style_key='error')

    mock_terminal.reset_mock()
    _handle_grep(["p", "f", "extra"], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_called_once_with("Usage: grep <pattern> <file>", style_key='error')

def test_handle_grep_corrupted_file_with_match_and_glitch(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = ["error", "corrupt.log"]
    file_content = "normal line\nline with error\nsystem error critical"
    mock_terminal.fs_handler.get_item_content.return_value = file_content
    mock_terminal.fs_handler.is_item_corrupted.return_value = True # File is corrupted
    mock_terminal.add_line.side_effect = [1, 2] # Return different line indices for the two matches
    mock_puzzle_manager = MagicMock()

    with patch('random.random', side_effect=[0.1, 0.8]): # First match glitches, second doesn't
        _handle_grep(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)

    expected_add_line_calls = [
        call("2:line with error"),
        call("3:system error critical")
    ]
    mock_terminal.add_line.assert_has_calls(expected_add_line_calls)
    
    # Check that an effect was called for the first match (line_idx 1)
    # The exact effect type is random, so we check if either was called with the correct line_idx
    corruption_call_args = mock_effect_manager.start_character_corruption_effect.call_args
    flicker_call_args = mock_effect_manager.start_text_flicker_effect.call_args

    glitch_on_first_match = False
    if corruption_call_args and corruption_call_args[0][0] == 1: # Check line_idx
        glitch_on_first_match = True
    if flicker_call_args and flicker_call_args[0][0] == 1: # Check line_idx
        glitch_on_first_match = True
    
    assert glitch_on_first_match, "Expected a glitch effect on the first matching line from corrupted file"
    
    # Ensure no glitch on the second match (line_idx 2) due to random.random() returning 0.8
    for call_args in mock_effect_manager.start_character_corruption_effect.call_args_list:
        assert call_args[0][0] != 2, "Corruption effect should not have occurred on the second match"
    for call_args in mock_effect_manager.start_text_flicker_effect.call_args_list:
        assert call_args[0][0] != 2, "Flicker effect should not have occurred on the second match"

def test_handle_grep_empty_file(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = ["pattern", "empty.txt"]
    mock_terminal.fs_handler.get_item_content.return_value = ""
    mock_terminal.fs_handler.is_item_corrupted.return_value = False
    mock_puzzle_manager = MagicMock()

    _handle_grep(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_not_called()

# --- Tests for Effect Command Handlers ---

def test_handle_type_effect_with_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = ["Hello,", "this", "is", "a", "test."] # Will be joined to "Hello, this is a test."
    text_to_type = " ".join(args_list)
    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_type_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_effect_manager.start_typing_effect.assert_called_once_with(text_to_type, char_delay_ms=30, style_key='highlight')
    mock_terminal.add_line.assert_not_called()

def test_handle_type_effect_no_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_type_effect([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_effect_manager.start_typing_effect.assert_not_called()
    mock_terminal.add_line.assert_any_call("Usage: type <text>", style_key='error')
    mock_terminal.add_line.assert_any_call("Simulates typing out the provided text.", style_key='error')

def test_handle_type_effect_whitespace_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    # The handler joins args_list, so [" ", " ", " "] would become "   "
    # If the intent is to test what happens if the *original* input was "   ",
    # shlex.split("   ") would be [], so it's covered by _no_args.
    # If the input was `type "   "`, then args_list would be ["   "].
    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_type_effect(["   "], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    # Assert that start_typing_effect was called with "   "
    mock_effect_manager.start_typing_effect.assert_called_once_with("   ", char_delay_ms=30, style_key='highlight')

def test_handle_burst_effect_with_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = ["Instant", "text!"] # Will be joined
    text_to_burst = " ".join(args_list)
    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_burst_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    # Note: _handle_burst_effect calls start_typing_effect with char_delay_ms=0
    mock_effect_manager.start_typing_effect.assert_called_once_with(text_to_burst, char_delay_ms=0, style_key='highlight')
    mock_terminal.add_line.assert_not_called()

def test_handle_burst_effect_no_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_burst_effect([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_effect_manager.start_typing_effect.assert_not_called()
    mock_terminal.add_line.assert_any_call("Usage: burst <text>", style_key='error')
    mock_terminal.add_line.assert_any_call("Instantly displays the provided text.", style_key='error')

def test_handle_burst_effect_whitespace_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_puzzle_manager = MagicMock()
    # Similar to type_effect, if original input was "   ", shlex.split results in [].
    # If input was `burst "   "`, args_list is ["   "]
    continue_running, action = _handle_burst_effect(["   "], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_effect_manager.start_typing_effect.assert_called_once_with("   ", char_delay_ms=0, style_key='highlight')
    # mock_terminal.add_line.assert_any_call("Usage: burst <text>", style_key='error') # This should not be called if arg is provided
    # mock_terminal.add_line.assert_any_call("Instantly displays the provided text.", style_key='error') # This should not be called

def test_handle_sequence_effect(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_sequence_effect([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None

    mock_terminal.add_line.assert_any_call("Starting effect sequence...", style_key='highlight')

    expected_typing_calls = [
        call("First message...", char_delay_ms=50),
        call("Second message, after a delay.", char_delay_ms=40, style_key='success'),
        call("Third and final message.", char_delay_ms=60, style_key='error', bold=True, on_complete_callback=mock_effect_manager.start_typing_effect.call_args_list[2][1]['on_complete_callback']) # Check callback presence
    ]
    # Check the calls to start_typing_effect, ignoring the on_complete_callback object itself for the third call initially
    assert mock_effect_manager.start_typing_effect.call_count == 3
    for i in range(2): # First two calls
        assert mock_effect_manager.start_typing_effect.call_args_list[i] == expected_typing_calls[i]
    
    # For the third call, check text, char_delay_ms, style_key, and bold. Callback is checked separately.
    third_call_args, third_call_kwargs = mock_effect_manager.start_typing_effect.call_args_list[2]
    assert third_call_args == ("Third and final message.",)
    assert third_call_kwargs['char_delay_ms'] == 60
    assert third_call_kwargs['style_key'] == 'error'
    assert third_call_kwargs['bold'] is True
    assert 'on_complete_callback' in third_call_kwargs and callable(third_call_kwargs['on_complete_callback'])

    # Simulate the on_complete_callback
    third_call_kwargs['on_complete_callback']()
    mock_terminal.add_line.assert_any_call("Sequence complete!", style_key='success')
    
    expected_delay_calls = [
        call(1000),
        call(500)
    ]
    mock_effect_manager.start_timed_delay.assert_has_calls(expected_delay_calls)
    assert mock_effect_manager.start_timed_delay.call_count == 2
    assert action is None
def test_handle_corrupt_effect_valid_args_positive_offset(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_terminal.buffer = ["line 0", "line 1", "line 2"] # Need some buffer content
    args_list = ["1", "1500", "50", "60"] # line_offset, duration, intensity, rate
    line_offset, duration, intensity_percent, rate = 1, 1500, 50, 60
    expected_actual_index = 1
    expected_intensity_float = 0.5
    mock_puzzle_manager = MagicMock()

    continue_running, action = _handle_corrupt_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with(
        f"Corrupting line {line_offset} (index {expected_actual_index}) for {duration}ms, intensity {intensity_percent}%, rate {rate}ms.",
        style_key='highlight'
    )
    mock_effect_manager.start_character_corruption_effect.assert_called_once_with(
        expected_actual_index, duration, expected_intensity_float, rate
    )

def test_handle_corrupt_effect_valid_args_negative_offset_defaults(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_terminal.buffer = ["line 0", "line 1", "line 2", "line 3"]
    args_list = ["-2"] # line_offset, defaults for others
    line_offset = -2
    expected_actual_index = 2 # len(buffer) + line_offset = 4 + (-2) = 2
    # Default values from function: duration=1000, intensity_percent=30, rate=75
    expected_duration, expected_intensity_percent, expected_rate = 1000, 30, 75
    expected_intensity_float = 0.3
    mock_puzzle_manager = MagicMock()

    continue_running, action = _handle_corrupt_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with(
        f"Corrupting line {line_offset} (index {expected_actual_index}) for {expected_duration}ms, intensity {expected_intensity_percent}%, rate {expected_rate}ms.",
        style_key='highlight'
    )
    mock_effect_manager.start_character_corruption_effect.assert_called_once_with(
        expected_actual_index, expected_duration, expected_intensity_float, expected_rate
    )

def test_handle_corrupt_effect_offset_out_of_bounds_positive(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_terminal.buffer = ["line 0"]
    args_list = ["5"] # line_offset 5, but buffer only has 1 line (index 0)
    line_offset = 5
    expected_actual_index = 5
    mock_puzzle_manager = MagicMock()

    continue_running, action = _handle_corrupt_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with(
        f"Error: Line offset {line_offset} (index {expected_actual_index}) out of bounds.", style_key='error'
    )
    mock_effect_manager.start_character_corruption_effect.assert_not_called()

def test_handle_corrupt_effect_offset_out_of_bounds_negative(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_terminal.buffer = ["line 0", "line 1"]
    args_list = ["-5"] # line_offset -5, len(buffer) + (-5) = 2 - 5 = -3
    line_offset = -5
    expected_actual_index = -3
    mock_puzzle_manager = MagicMock()

    continue_running, action = _handle_corrupt_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with(
        f"Error: Line offset {line_offset} (index {expected_actual_index}) out of bounds.", style_key='error'
    )
    mock_effect_manager.start_character_corruption_effect.assert_not_called()

def test_handle_corrupt_effect_missing_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = [] # Empty list for missing args
    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_corrupt_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_any_call("Usage: corrupt <line_offset> [duration_ms] [intensity_percent] [rate_ms]", style_key='error')
    mock_terminal.add_line.assert_any_call("Corrupts characters on a specified line. Example: corrupt -1 2000 50 50", style_key='error')
    mock_effect_manager.start_character_corruption_effect.assert_not_called()

def test_handle_corrupt_effect_invalid_line_offset_type(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = ["abc"] # Invalid type for line_offset
    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_corrupt_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
@patch('command_handler.get_current_theme')
def test_handle_flicker_effect_valid_args_positive_offset(mock_get_theme, mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_get_theme.return_value = {'text': (255,255,255), 'error': (255,0,0), 'highlight': (0,255,0)}
    mock_terminal.buffer = ["line 0", "line 1", "line 2"]
    args_list = ["1", "1200", "80", "highlight"] # line_offset, duration, rate, color_key
    line_offset, duration, rate, color_key = 1, 1200, 80, 'highlight'
    expected_actual_index = 1
    mock_puzzle_manager = MagicMock()

    continue_running, action = _handle_flicker_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with(
        f"Flickering line {line_offset} (index {expected_actual_index}) for {duration}ms, rate {rate}ms, color '{color_key}'.",
        style_key='highlight'
    )
    mock_effect_manager.start_text_flicker_effect.assert_called_once_with(
        expected_actual_index, duration, rate, color_key
    )

@patch('command_handler.get_current_theme')
def test_handle_flicker_effect_valid_args_negative_offset_defaults(mock_get_theme, mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_get_theme.return_value = {'text': (255,255,255), 'error': (255,0,0)} # 'error' is default
    mock_terminal.buffer = ["line 0", "line 1", "line 2", "line 3"]
    args_list = ["-1"] # line_offset, defaults for others
    line_offset = -1
    expected_actual_index = 3 # len(buffer) + line_offset = 4 + (-1) = 3
    # Default values: duration=1000, rate=100, color_key='error'
    expected_duration, expected_rate, expected_color_key = 1000, 100, 'error'
    mock_puzzle_manager = MagicMock()

    continue_running, action = _handle_flicker_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with(
        f"Flickering line {line_offset} (index {expected_actual_index}) for {expected_duration}ms, rate {expected_rate}ms, color '{expected_color_key}'.",
        style_key='highlight'
    )
    mock_effect_manager.start_text_flicker_effect.assert_called_once_with(
        expected_actual_index, expected_duration, expected_rate, expected_color_key
    )

@patch('command_handler.get_current_theme')
def test_handle_flicker_effect_offset_out_of_bounds_positive(mock_get_theme, mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_get_theme.return_value = {'error': (255,0,0)}
    mock_terminal.buffer = ["line 0"]
    args_list = ["3"]
    line_offset = 3
    expected_actual_index = 3
    mock_puzzle_manager = MagicMock()

    continue_running, action = _handle_flicker_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with(
        f"Error: Line offset {line_offset} (index {expected_actual_index}) for flicker out of bounds.", style_key='error'
    )
    mock_effect_manager.start_text_flicker_effect.assert_not_called()

@patch('command_handler.get_current_theme')
def test_handle_flicker_effect_offset_out_of_bounds_negative(mock_get_theme, mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_get_theme.return_value = {'error': (255,0,0)}
    mock_terminal.buffer = ["line 0", "line 1"]
    args_list = ["-7"]
    line_offset = -7
    expected_actual_index = -5 # 2 + (-7)
    mock_puzzle_manager = MagicMock()

    continue_running, action = _handle_flicker_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with(
        f"Error: Line offset {line_offset} (index {expected_actual_index}) for flicker out of bounds.", style_key='error'
    )
    mock_effect_manager.start_text_flicker_effect.assert_not_called()

@patch('command_handler.get_current_theme')
def test_handle_flicker_effect_invalid_color_key(mock_get_theme, mock_terminal, mock_game_state_manager, mock_effect_manager):
    valid_theme = {'text': (1,1,1), 'success': (2,2,2)}
    mock_get_theme.return_value = valid_theme
    mock_terminal.buffer = ["line 0"]
    args_list = ["0", "1000", "100", "non_existent_color"]
    invalid_color_key = "non_existent_color"
    mock_puzzle_manager = MagicMock()

    continue_running, action = _handle_flicker_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with(
       f"Error: Flicker color key '{invalid_color_key}' not in current theme. Valid keys: {', '.join(valid_theme.keys())}", style_key='error'
    )
    mock_effect_manager.start_text_flicker_effect.assert_not_called()

def test_handle_flicker_effect_missing_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = []
    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_flicker_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_any_call("Usage: flicker <line_offset> [duration_ms] [rate_ms] [color_key]", style_key='error')
    mock_terminal.add_line.assert_any_call("Flickers a specified line with a chosen color. Example: flicker -1 1500 80 error", style_key='error')
    mock_effect_manager.start_text_flicker_effect.assert_not_called()

def test_handle_flicker_effect_invalid_arg_type(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = ["zero"] # Invalid type for line_offset
    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_flicker_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_any_call("Usage: flicker <line_offset> [duration_ms] [rate_ms] [color_key]", style_key='error')
    mock_terminal.add_line.assert_any_call("Flickers a specified line with a chosen color. Example: flicker -1 1500 80 error", style_key='error')
    mock_effect_manager.start_text_flicker_effect.assert_not_called()
@patch('command_handler.get_current_theme')
def test_handle_colorchange_effect_valid_args_all_params(mock_get_theme, mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_get_theme.return_value = {'text': (0,0,0), 'error': (255,0,0), 'success': (0,255,0)}
    mock_terminal.buffer = ["line 0", "line 1", "line 2"]
    args_list = ["1", "1500", "error", "success"] # offset, duration, fg_key, bg_key
    line_offset, duration, fg_key, bg_key = 1, 1500, 'error', 'success'
    expected_actual_index = 1
    mock_puzzle_manager = MagicMock()

    continue_running, action = _handle_colorchange_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with(
        f"Changing line {line_offset} (idx {expected_actual_index}) for {duration}ms. FG: {fg_key}, BG: {bg_key}",
        style_key='highlight'
    )
    mock_effect_manager.start_temp_color_change_effect.assert_called_once_with(
        expected_actual_index, duration, fg_key, bg_key
    )

@patch('command_handler.get_current_theme')
def test_handle_colorchange_effect_valid_fg_only_negative_offset(mock_get_theme, mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_get_theme.return_value = {'text': (0,0,0), 'warning': (255,255,0)}
    mock_terminal.buffer = ["line 0", "line 1", "line 2", "line 3"]
    args_list = ["-2", "500", "warning"] # offset, duration, fg_key (bg_key defaults to None)
    line_offset, duration, fg_key = -2, 500, 'warning'
    expected_actual_index = 2 # 4 + (-2)
    bg_key = None # Expected default
    mock_puzzle_manager = MagicMock()

    continue_running, action = _handle_colorchange_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with(
        f"Changing line {line_offset} (idx {expected_actual_index}) for {duration}ms. FG: {fg_key}, BG: {bg_key}",
        style_key='highlight'
    )
    mock_effect_manager.start_temp_color_change_effect.assert_called_once_with(
        expected_actual_index, duration, fg_key, bg_key
    )

@patch('command_handler.get_current_theme')
def test_handle_colorchange_effect_valid_bg_only_fg_none(mock_get_theme, mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_get_theme.return_value = {'text': (0,0,0), 'info_bg': (100,100,255)}
    mock_terminal.buffer = ["line 0"]
    args_list = ["0", "800", "none", "info_bg"] # offset, duration, 'none' for fg_key, bg_key
    line_offset, duration, bg_key = 0, 800, 'info_bg'
    expected_actual_index = 0
    fg_key = None # Expected
    mock_puzzle_manager = MagicMock()

    continue_running, action = _handle_colorchange_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with(
        f"Changing line {line_offset} (idx {expected_actual_index}) for {duration}ms. FG: {fg_key}, BG: {bg_key}",
        style_key='highlight'
    )
    mock_effect_manager.start_temp_color_change_effect.assert_called_once_with(
        expected_actual_index, duration, fg_key, bg_key
    )

@patch('command_handler.get_current_theme')
def test_handle_colorchange_effect_offset_out_of_bounds(mock_get_theme, mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_get_theme.return_value = {'text': (0,0,0)}
    mock_terminal.buffer = ["line 0"]
    args_list = ["10", "1000", "text"]
    line_offset = 10
    expected_actual_index = 10
    mock_puzzle_manager = MagicMock()

    continue_running, action = _handle_colorchange_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with(
        f"Error: Line offset {line_offset} (index {expected_actual_index}) for colorchange out of bounds.", style_key='error'
    )
    mock_effect_manager.start_temp_color_change_effect.assert_not_called()

@patch('command_handler.get_current_theme')
def test_handle_colorchange_effect_no_fg_or_bg_key(mock_get_theme, mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_get_theme.return_value = {'text': (0,0,0)}
    mock_terminal.buffer = ["line 0"]
    args_list = ["0", "1000"] # Only offset and duration
    mock_puzzle_manager = MagicMock()

    continue_running, action = _handle_colorchange_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with("Error: colorchange requires at least a fg_color_key or bg_color_key.", style_key='error')
    mock_effect_manager.start_temp_color_change_effect.assert_not_called()

    mock_terminal.reset_mock()
    args_list_none = ["0", "1000", "none", "none"]
    # mock_puzzle_manager is already defined for this test function scope
    _handle_colorchange_effect(args_list_none, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_called_once_with("Error: colorchange requires at least a fg_color_key or bg_color_key.", style_key='error')


@patch('command_handler.get_current_theme')
def test_handle_colorchange_effect_invalid_fg_key(mock_get_theme, mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_get_theme.return_value = {'text': (0,0,0)}
    mock_terminal.buffer = ["line 0"]
    args_list = ["0", "1000", "bad_fg_key"]
    mock_puzzle_manager = MagicMock()
    
    continue_running, action = _handle_colorchange_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with("Error: fg_color_key 'bad_fg_key' not in theme.", style_key='error')
    mock_effect_manager.start_temp_color_change_effect.assert_not_called()

@patch('command_handler.get_current_theme')
def test_handle_colorchange_effect_invalid_bg_key(mock_get_theme, mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_get_theme.return_value = {'text': (0,0,0), 'good_fg': (1,1,1)}
    mock_terminal.buffer = ["line 0"]
    args_list = ["0", "1000", "good_fg", "bad_bg_key"]
    mock_puzzle_manager = MagicMock()

    continue_running, action = _handle_colorchange_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with("Error: bg_color_key 'bad_bg_key' not in theme.", style_key='error')
    mock_effect_manager.start_temp_color_change_effect.assert_not_called()
@patch('command_handler.get_current_theme')
def test_handle_overlay_effect_all_args_valid(mock_get_theme, mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_get_theme.return_value = {'text': (0,0,0), 'success': (0,255,0)}
    args_list = ["2000", "75", "success", "150"] # duration, num_chars, color_key, rate
    duration, num_chars, color_key, rate = 2000, 75, 'success', 150
    mock_puzzle_manager = MagicMock()

    continue_running, action = _handle_overlay_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with(
        f"Starting text overlay: {duration}ms, {num_chars} chars, color '{color_key}', rate {rate}ms.",
        style_key='highlight'
    )
    mock_effect_manager.start_text_overlay_effect.assert_called_once_with(
        duration, num_chars, None, color_key, rate
    )

@patch('command_handler.get_current_theme')
def test_handle_overlay_effect_default_args(mock_get_theme, mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_get_theme.return_value = {'text': (0,0,0), 'error': (255,0,0)} # 'error' is default color
    args_list = [] # All defaults
    # Default values: duration=1500, num_chars=50, color_key='error', rate=100
    expected_duration, expected_num_chars, expected_color_key, expected_rate = 1500, 50, 'error', 100
    mock_puzzle_manager = MagicMock()

    continue_running, action = _handle_overlay_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with(
        f"Starting text overlay: {expected_duration}ms, {expected_num_chars} chars, color '{expected_color_key}', rate {expected_rate}ms.",
        style_key='highlight'
    )
    mock_effect_manager.start_text_overlay_effect.assert_called_once_with(
        expected_duration, expected_num_chars, None, expected_color_key, expected_rate
    )

@patch('command_handler.get_current_theme')
def test_handle_overlay_effect_some_args_empty_strings_use_defaults(mock_get_theme, mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_get_theme.return_value = {'text': (0,0,0), 'error': (255,0,0), 'custom_color': (1,2,3)}
    # To achieve defaults for num_chars and rate, but specify duration and color_key,
    # the user would type something like: overlay 2500 "" custom_color ""
    # shlex.split('overlay 2500 "" custom_color ""') -> ['overlay', '2500', '', 'custom_color', '']
    args_list = ["2500", "", "custom_color", ""]
    expected_duration, expected_color_key = 2500, 'custom_color'
    # Defaults: num_chars=50, rate=100
    expected_num_chars, expected_rate = 50, 100
    mock_puzzle_manager = MagicMock()

    continue_running, action = _handle_overlay_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    # This should now succeed with the corrected args_list
    mock_terminal.add_line.assert_called_once_with(
        f"Starting text overlay: {expected_duration}ms, {expected_num_chars} chars, color '{expected_color_key}', rate {expected_rate}ms.",
        style_key='highlight'
    )
    mock_effect_manager.start_text_overlay_effect.assert_called_once_with(
        expected_duration, expected_num_chars, None, expected_color_key, expected_rate
    )


@patch('command_handler.get_current_theme')
def test_handle_overlay_effect_invalid_color_key(mock_get_theme, mock_terminal, mock_game_state_manager, mock_effect_manager):
    valid_theme = {'text': (1,1,1)}
    mock_get_theme.return_value = valid_theme
    args_list = ["1000", "50", "non_existent_color"]
    invalid_color_key = "non_existent_color"
    mock_puzzle_manager = MagicMock()

    continue_running, action = _handle_overlay_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with(
       f"Error: Overlay color key '{invalid_color_key}' not in current theme. Valid keys: {', '.join(valid_theme.keys())}", style_key='error'
    )
    mock_effect_manager.start_text_overlay_effect.assert_not_called()

def test_handle_overlay_effect_invalid_numeric_value(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = ["not_a_number", "50", "error", "100"]
    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_overlay_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_any_call("Error: Invalid numeric value for overlay parameters.", style_key='error')
    mock_terminal.add_line.assert_any_call("Usage: overlay [duration_ms] [num_chars] [color_key] [rate_ms]", style_key='error')
    mock_effect_manager.start_text_overlay_effect.assert_not_called()

    mock_terminal.reset_mock()
    mock_effect_manager.reset_mock()
    args_str_num_chars = "1000 bad_num error 100"
def test_handle_jiggle_effect_valid_args_positive_offset(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_terminal.buffer = ["line 0", "line 1", "line 2"]
    args_list = ["1", "1500", "2", "60"] # line_offset, duration, intensity, rate
    line_offset, duration, intensity, rate = 1, 1500, 2, 60
    expected_actual_index = 1
    mock_puzzle_manager = MagicMock()

    continue_running, action = _handle_jiggle_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with(
        f"Jiggling line {line_offset} (index {expected_actual_index}) for {duration}ms, intensity {intensity}, rate {rate}ms.",
        style_key='highlight'
    )
    mock_effect_manager.start_text_jiggle_effect.assert_called_once_with(
        expected_actual_index, duration, intensity, rate
    )

def test_handle_jiggle_effect_valid_args_negative_offset_defaults(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_terminal.buffer = ["line 0", "line 1", "line 2", "line 3"]
    args_list = ["-2"] # line_offset, defaults for others
    line_offset = -2
    expected_actual_index = 2 # len(buffer) + line_offset = 4 + (-2) = 2
    # Default values from function: duration=1000, intensity=1, rate=50
    expected_duration, expected_intensity, expected_rate = 1000, 1, 50
    mock_puzzle_manager = MagicMock()

    continue_running, action = _handle_jiggle_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with(
        f"Jiggling line {line_offset} (index {expected_actual_index}) for {expected_duration}ms, intensity {expected_intensity}, rate {expected_rate}ms.",
        style_key='highlight'
    )
    mock_effect_manager.start_text_jiggle_effect.assert_called_once_with(
        expected_actual_index, expected_duration, expected_intensity, expected_rate
    )

def test_handle_jiggle_effect_offset_out_of_bounds_positive(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_terminal.buffer = ["line 0"]
    args_list = ["5"] # line_offset 5, but buffer only has 1 line (index 0)
    line_offset = 5
    expected_actual_index = 5
    mock_puzzle_manager = MagicMock()

    continue_running, action = _handle_jiggle_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with(
        f"Error: Line offset {line_offset} (index {expected_actual_index}) for jiggle out of bounds.", style_key='error'
    )
    mock_effect_manager.start_text_jiggle_effect.assert_not_called()

def test_handle_jiggle_effect_offset_out_of_bounds_negative(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_terminal.buffer = ["line 0", "line 1"]
    args_list = ["-5"] # line_offset -5, len(buffer) + (-5) = 2 - 5 = -3
    line_offset = -5
    expected_actual_index = -3
    mock_puzzle_manager = MagicMock()

    continue_running, action = _handle_jiggle_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with(
        f"Error: Line offset {line_offset} (index {expected_actual_index}) for jiggle out of bounds.", style_key='error'
    )
    mock_effect_manager.start_text_jiggle_effect.assert_not_called()

def test_handle_jiggle_effect_missing_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = []
    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_jiggle_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_any_call("Usage: jiggle <line_offset> [duration_ms] [intensity] [rate_ms]", style_key='error')
    mock_terminal.add_line.assert_any_call("Jiggles characters on a specified line. Example: jiggle -1 1000 2 50", style_key='error')
    mock_effect_manager.start_text_jiggle_effect.assert_not_called()

def test_handle_jiggle_effect_invalid_line_offset_type(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = ["abc"] # Invalid type for line_offset
    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_jiggle_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_any_call("Usage: jiggle <line_offset> [duration_ms] [intensity] [rate_ms]", style_key='error')
    mock_effect_manager.start_text_jiggle_effect.assert_not_called()

def test_handle_jiggle_effect_invalid_duration_type(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = ["0", "xyz"] # Invalid type for duration
    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_jiggle_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_any_call("Usage: jiggle <line_offset> [duration_ms] [intensity] [rate_ms]", style_key='error')
    mock_terminal.add_line.assert_any_call("Jiggles characters on a specified line. Example: jiggle -1 1000 2 50", style_key='error')
    mock_effect_manager.start_text_jiggle_effect.assert_not_called()
def test_handle_screenres_valid_resolution(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = ["1024x768"]
    expected_width, expected_height = 1024, 768
    mock_puzzle_manager = MagicMock()

    continue_running, action_dict = _handle_screenres(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action_dict == {'action': 'screen_change', 'type': 'set_resolution', 'width': expected_width, 'height': expected_height}
    mock_terminal.add_line.assert_not_called()

def test_handle_screenres_invalid_format_no_x(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = ["800600"]
    mock_puzzle_manager = MagicMock()
    continue_running, action_dict = _handle_screenres(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action_dict is None
    mock_terminal.add_line.assert_called_once_with("Error: Invalid resolution format. Use WxH (e.g., 800x600).", style_key='error')

def test_handle_screenres_invalid_format_too_many_parts(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = ["800x600x100"]
    mock_puzzle_manager = MagicMock()
    continue_running, action_dict = _handle_screenres(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action_dict is None
    mock_terminal.add_line.assert_called_once_with("Error: Invalid resolution format. Use WxH (e.g., 800x600).", style_key='error')

def test_handle_screenres_non_integer_width(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = ["abcx600"]
    mock_puzzle_manager = MagicMock()
    continue_running, action_dict = _handle_screenres(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action_dict is None
    mock_terminal.add_line.assert_called_once_with("Error: Invalid resolution format. Use WxH (e.g., 800x600).", style_key='error')

def test_handle_screenres_non_integer_height(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = ["800xdef"]
    mock_puzzle_manager = MagicMock()
    continue_running, action_dict = _handle_screenres(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action_dict is None
    mock_terminal.add_line.assert_called_once_with("Error: Invalid resolution format. Use WxH (e.g., 800x600).", style_key='error')

def test_handle_screenres_zero_width(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = ["0x600"]
    mock_puzzle_manager = MagicMock()
    continue_running, action_dict = _handle_screenres(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action_dict is None
    mock_terminal.add_line.assert_called_once_with("Error: Width and height must be positive.", style_key='error')

def test_handle_screenres_negative_height(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = ["800x-600"]
    mock_puzzle_manager = MagicMock()
    continue_running, action_dict = _handle_screenres(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action_dict is None
    mock_terminal.add_line.assert_called_once_with("Error: Width and height must be positive.", style_key='error')

def test_handle_screenres_no_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = []
    mock_puzzle_manager = MagicMock()
    continue_running, action_dict = _handle_screenres(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action_dict is None
    mock_terminal.add_line.assert_any_call("Usage: screenres <Width>x<Height>", style_key='error')
    mock_terminal.add_line.assert_any_call("Changes the screen resolution. Example: screenres 800x600", style_key='error')

def test_handle_screenres_whitespace_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    # shlex.split("   ") results in an empty list
    args_list = []
    mock_puzzle_manager = MagicMock()
    continue_running, action_dict = _handle_screenres(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action_dict is None
    mock_terminal.add_line.assert_any_call("Usage: screenres <Width>x<Height>", style_key='error')
    mock_terminal.add_line.assert_any_call("Changes the screen resolution. Example: screenres 800x600", style_key='error')
    mock_effect_manager.start_text_overlay_effect.assert_not_called()

def test_handle_colorchange_effect_missing_args_usage(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = []
    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_colorchange_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_any_call("Usage: colorchange <offset> <duration> [fg_key|none] [bg_key|none]", style_key='error')
    mock_terminal.add_line.assert_any_call("Temporarily changes color of a line. Example: colorchange -1 1000 error highlight", style_key='error')
    mock_effect_manager.start_temp_color_change_effect.assert_not_called()

def test_handle_colorchange_effect_invalid_arg_type_usage(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = ["not_an_int"]
    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_colorchange_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_any_call("Usage: colorchange <offset> <duration> [fg_key|none] [bg_key|none]", style_key='error')
    mock_effect_manager.start_temp_color_change_effect.assert_not_called()

def test_handle_corrupt_effect_invalid_duration_type(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = ["0", "xyz"] # Invalid type for duration
    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_corrupt_effect(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_any_call("Usage: corrupt <line_offset> [duration_ms] [intensity_percent] [rate_ms]", style_key='error')
    mock_effect_manager.start_character_corruption_effect.assert_not_called()
def test_handle_help_grey_hat(mock_terminal, mock_game_state_manager, mock_effect_manager):
    player_role = ROLE_GREY_HAT
    mock_game_state_manager.get_player_role.return_value = player_role
    
    mock_puzzle_manager = MagicMock()
    _handle_help([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, player_role)
    
    mock_terminal.add_line.assert_any_call("Available commands:", style_key='highlight')
    # Check if a few key help texts for Grey Hat are called
    grey_hat_help_texts = COMMAND_ACCESS[ROLE_GREY_HAT]["help_text_main"]
    mock_terminal.add_line.assert_any_call(grey_hat_help_texts["ls"])
    mock_terminal.add_line.assert_any_call(grey_hat_help_texts["rm"]) # Grey hat has rm
    mock_terminal.add_line.assert_any_call(grey_hat_help_texts["msfconsole"])


def test_handle_help_white_hat(mock_terminal, mock_game_state_manager, mock_effect_manager):
    player_role = ROLE_WHITE_HAT
    mock_game_state_manager.get_player_role.return_value = player_role

    mock_puzzle_manager = MagicMock()
    _handle_help([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, player_role)

    mock_terminal.add_line.assert_any_call("Available commands:", style_key='highlight')
    white_hat_help_texts = COMMAND_ACCESS[ROLE_WHITE_HAT]["help_text_main"]
    white_hat_allowed = COMMAND_ACCESS[ROLE_WHITE_HAT]["allowed_main"]

    # Check a command white hat has
    assert "ls" in white_hat_allowed
    mock_terminal.add_line.assert_any_call(white_hat_help_texts["ls"])
    
    # Check a command white hat does NOT have (rm)
    assert "rm" not in white_hat_allowed
    # Ensure the help text for 'rm' was NOT called
    rm_help_text_from_grey = COMMAND_ACCESS[ROLE_GREY_HAT]["help_text_main"]["rm"]
    
    # Get all calls to add_line
    calls = mock_terminal.add_line.call_args_list
    # Check that rm_help_text_from_grey is not in any of the calls
    assert not any(call_args[0][0] == rm_help_text_from_grey for call_args in calls), \
        "Help text for 'rm' should not be shown for White Hat"

def test_handle_pwd(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_terminal.fs_handler.get_current_path_str.return_value = "/home/testuser/documents"
    mock_terminal.fs_handler.is_item_corrupted.return_value = False
    mock_terminal.add_line.return_value = 10 # Dummy line index

    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_pwd([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_with("/home/testuser/documents")
    mock_effect_manager.start_character_corruption_effect.assert_not_called()

def test_handle_pwd_corrupted(mock_terminal, mock_game_state_manager, mock_effect_manager):
    current_path = "/var/glitched_logs"
    mock_terminal.fs_handler.get_current_path_str.return_value = current_path
    mock_terminal.fs_handler.is_item_corrupted.return_value = True # Path is corrupted
    mock_terminal.add_line.return_value = 12 # Simulate a valid line index

    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_pwd([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_with(current_path)
    mock_effect_manager.start_character_corruption_effect.assert_called_once()
    # More specific assertion for call args if needed, like checking the line_idx
    args, kwargs = mock_effect_manager.start_character_corruption_effect.call_args
    assert args[0] == 12 # Check the line_idx passed to the effect

def test_handle_cd_success(mock_terminal, mock_game_state_manager, mock_effect_manager):
    target_dir = "new_dir"
    mock_terminal.fs_handler.execute_cd.return_value = (True, f"Successfully changed to {target_dir}")

    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_cd([target_dir], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)

    assert continue_running is True
    assert action is None
    mock_terminal.fs_handler.execute_cd.assert_called_once_with(target_dir)
    mock_terminal.add_line.assert_not_called() # No error message
    mock_terminal._update_prompt_string.assert_called_once()

def test_handle_cd_failure(mock_terminal, mock_game_state_manager, mock_effect_manager):
    target_dir = "non_existent_dir"
    error_message = f"cd: {target_dir}: No such file or directory"
    mock_terminal.fs_handler.execute_cd.return_value = (False, error_message)

    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_cd([target_dir], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)

    assert continue_running is True
    assert action is None
    mock_terminal.fs_handler.execute_cd.assert_called_once_with(target_dir)
    mock_terminal.add_line.assert_called_once_with(error_message, style_key='error')
    mock_terminal._update_prompt_string.assert_not_called()

def test_handle_cd_no_args_goes_to_home(mock_terminal, mock_game_state_manager, mock_effect_manager):
    # Simulates 'cd' or 'cd '
    mock_terminal.fs_handler.execute_cd.return_value = (True, "Successfully changed to ~")

    mock_puzzle_manager = MagicMock()
    _handle_cd([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.fs_handler.execute_cd.assert_called_once_with("~")
    mock_terminal._update_prompt_string.assert_called_once()

    mock_terminal.fs_handler.execute_cd.reset_mock()
    mock_terminal._update_prompt_string.reset_mock()

    # shlex.split("   ") results in [], so this is the same as the above case.
    _handle_cd([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT) # cd with spaces
    mock_terminal.fs_handler.execute_cd.assert_called_once_with("~")
    mock_terminal._update_prompt_string.assert_called_once()

def test_handle_mkdir_success(mock_terminal, mock_game_state_manager, mock_effect_manager):
    dir_name = "new_test_dir"
    mock_terminal.fs_handler.execute_mkdir.return_value = (True, f"Directory '{dir_name}' created.")

    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_mkdir([dir_name], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)

    assert continue_running is True
    assert action is None
    mock_terminal.fs_handler.execute_mkdir.assert_called_once_with(dir_name)
    mock_terminal.add_line.assert_not_called() # No error message

def test_handle_mkdir_failure(mock_terminal, mock_game_state_manager, mock_effect_manager):
    dir_name = "existing_dir"
    error_message = f"mkdir: cannot create directory ‘{dir_name}’: File exists"
    mock_terminal.fs_handler.execute_mkdir.return_value = (False, error_message)

    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_mkdir([dir_name], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)

    assert continue_running is True
    assert action is None
    mock_terminal.fs_handler.execute_mkdir.assert_called_once_with(dir_name)
    mock_terminal.add_line.assert_called_once_with(error_message, style_key='error')

def test_handle_mkdir_no_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_puzzle_manager = MagicMock()
    _handle_mkdir([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    # The handler now prints two lines: "mkdir: missing operand" and then the usage.
    mock_terminal.add_line.assert_any_call("mkdir: missing operand", style_key='error')
    mock_terminal.add_line.assert_any_call("Usage: mkdir <directory_name>", style_key='error')
    assert mock_terminal.add_line.call_count == 2
    mock_terminal.fs_handler.execute_mkdir.assert_not_called()

    # Remove redundant second call test as it's identical to the first with args_list=[]
    # mock_terminal.add_line.reset_mock()
    # # shlex.split("   ") results in [], so this is the same as the above case.
    # _handle_mkdir([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT) # Only spaces
    # mock_terminal.add_line.assert_any_call("Usage: mkdir <directory_name>", style_key='error')
    mock_terminal.fs_handler.execute_mkdir.assert_not_called()

def test_handle_touch_success(mock_terminal, mock_game_state_manager, mock_effect_manager):
    file_name = "new_test_file.txt"
    mock_terminal.fs_handler.execute_touch.return_value = (True, f"File '{file_name}' touched.")

    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_touch([file_name], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)

    assert continue_running is True
    assert action is None
    mock_terminal.fs_handler.execute_touch.assert_called_once_with(file_name)
    mock_terminal.add_line.assert_not_called() # No error message

def test_handle_touch_failure(mock_terminal, mock_game_state_manager, mock_effect_manager):
    file_name = "a_directory/" # Trying to touch a directory or invalid name
    error_message = f"touch: cannot touch ‘{file_name}’: Not a file"
    mock_terminal.fs_handler.execute_touch.return_value = (False, error_message)

    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_touch([file_name], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)

    assert continue_running is True
    assert action is None
    mock_terminal.fs_handler.execute_touch.assert_called_once_with(file_name)
    mock_terminal.add_line.assert_called_once_with(error_message, style_key='error')

def test_handle_touch_no_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_puzzle_manager = MagicMock()
    _handle_touch([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    # The handler now prints two lines: "touch: missing file operand" and then the usage.
    mock_terminal.add_line.assert_any_call("touch: missing file operand", style_key='error')
    mock_terminal.add_line.assert_any_call("Usage: touch <filename>", style_key='error')
    assert mock_terminal.add_line.call_count == 2
    mock_terminal.fs_handler.execute_touch.assert_not_called()

    # Remove redundant second call test
    # mock_terminal.add_line.reset_mock()
    # # shlex.split("   ") results in [], so this is the same as the above case.
    # _handle_touch([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT) # Only spaces
    # mock_terminal.add_line.assert_any_call("Usage: touch <filename>", style_key='error')
    mock_terminal.fs_handler.execute_touch.assert_not_called()

def test_handle_cat_success_not_corrupted(mock_terminal, mock_game_state_manager, mock_effect_manager):
    file_path = "test_file.txt"
    file_content = "Line 1\nLine 2\nAnother line"
    mock_terminal.fs_handler.get_item_content.return_value = file_content
    mock_terminal.fs_handler.is_item_corrupted.return_value = False

    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_cat([file_path], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)

    assert continue_running is True
    assert action is None
    mock_terminal.fs_handler.get_item_content.assert_called_once_with(file_path)
    mock_terminal.fs_handler.is_item_corrupted.assert_called_once_with(file_path)
    calls = [call("Line 1"), call("Line 2"), call("Another line")]
    mock_terminal.add_line.assert_has_calls(calls)
    mock_effect_manager.start_character_corruption_effect.assert_not_called()
    mock_effect_manager.start_timed_delay.assert_not_called()

def test_handle_cat_success_corrupted(mock_terminal, mock_game_state_manager, mock_effect_manager):
    file_path = "corrupted_file.log"
    file_content = "Error log entry 1\nCritical failure data"
    mock_terminal.fs_handler.get_item_content.return_value = file_content
    mock_terminal.fs_handler.is_item_corrupted.return_value = True
    # Simulate add_line returning different indices for effect targeting
    mock_terminal.add_line.side_effect = [0, 1, 2, 3] # Indices for header, line1, line2, footer

    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_cat([file_path], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)

    assert continue_running is True
    assert action is None
    mock_terminal.fs_handler.get_item_content.assert_called_once_with(file_path)
    mock_terminal.fs_handler.is_item_corrupted.assert_called_once_with(file_path)

    # Check header and footer messages
    mock_terminal.add_line.assert_any_call(f"[{file_path} - CORRUPTED DATA STREAM]", style_key='error', bold=True)
    mock_terminal.add_line.assert_any_call(f"[END OF CORRUPTED STREAM - {file_path}]", style_key='error', bold=True)

    # Check content lines were added (with error style)
    mock_terminal.add_line.assert_any_call("Error log entry 1", style_key='error')
    mock_terminal.add_line.assert_any_call("Critical failure data", style_key='error')

    # Check effects were called for content lines
    # Expected corruption calls for line indices 1 and 2 (0 is header, 3 is footer)
    corruption_calls = [
        call(1, duration_ms=1500, intensity=0.3, rate_ms=60),
        call(2, duration_ms=1500, intensity=0.3, rate_ms=60)
    ]
    mock_effect_manager.start_character_corruption_effect.assert_has_calls(corruption_calls)
    assert mock_effect_manager.start_character_corruption_effect.call_count == 2

    # Check timed delays
    # One before content, two small ones between lines, one after content
    assert mock_effect_manager.start_timed_delay.call_count == 4
    mock_effect_manager.start_timed_delay.assert_any_call(250)
    mock_effect_manager.start_timed_delay.assert_any_call(50) # Called twice
    mock_effect_manager.start_timed_delay.assert_any_call(1500)


def test_handle_cat_file_not_found(mock_terminal, mock_game_state_manager, mock_effect_manager):
    file_path = "ghost_file.dat"
    mock_terminal.fs_handler.get_item_content.return_value = None
    # Simulate _get_node_at_path returning None for a non-existent item
    mock_terminal.fs_handler._resolve_path_str_to_list.return_value = ["path", "to", "ghost_file.dat"]
    mock_terminal.fs_handler._get_node_at_path.return_value = None

    mock_puzzle_manager = MagicMock()
    _handle_cat([file_path], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    
    mock_terminal.add_line.assert_called_once_with(f"cat: {file_path}: No such file or directory", style_key='error')

def test_handle_cat_is_a_directory(mock_terminal, mock_game_state_manager, mock_effect_manager):
    dir_path = "my_documents/"
    mock_terminal.fs_handler.get_item_content.return_value = None
    # Simulate _get_node_at_path returning a dict for a directory
    mock_terminal.fs_handler._resolve_path_str_to_list.return_value = ["~", "my_documents"]
    mock_terminal.fs_handler._get_node_at_path.return_value = {} # Empty dict signifies a directory

    mock_puzzle_manager = MagicMock()
    _handle_cat([dir_path], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)

    mock_terminal.add_line.assert_called_once_with(f"cat: {dir_path}: Is a directory", style_key='error')

def test_handle_cat_no_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_puzzle_manager = MagicMock()
    _handle_cat([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_called_once_with("cat: missing file operand", style_key='error')
    mock_terminal.fs_handler.get_item_content.assert_not_called()
    
    # Remove redundant second call test
    # mock_terminal.add_line.reset_mock()
    # # shlex.split("   ") results in [], so this is the same as the above case.
    # _handle_cat([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT) # Only spaces
    # mock_terminal.add_line.assert_any_call("Usage: cat <filename>", style_key='error')

def test_handle_ls_on_file(mock_terminal, mock_game_state_manager, mock_effect_manager):
    file_path_arg = "my_script.py"
    # Simulate _get_node_at_path returning a string (file content) for a file path
    mock_terminal.fs_handler._resolve_path_str_to_list.return_value = ["~", "my_script.py"]
    mock_terminal.fs_handler._get_node_at_path.return_value = "file content string" # Indicates it's a file

    mock_puzzle_manager = MagicMock()
    _handle_ls([file_path_arg], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    
    mock_terminal.add_line.assert_called_once_with(file_path_arg)
    mock_terminal.fs_handler.list_items.assert_not_called()

def test_handle_ls_on_directory_no_corruption_effects(mock_terminal, mock_game_state_manager, mock_effect_manager):
    dir_path_arg = "projects"
    items_in_dir = ["project_a/", "script.sh", "README.md"]
    mock_terminal.fs_handler._resolve_path_str_to_list.return_value = ["~", "projects"]
    mock_terminal.fs_handler._get_node_at_path.return_value = {} # Indicates a directory
    mock_terminal.fs_handler.list_items.return_value = items_in_dir
    mock_terminal.fs_handler.get_corrupted_file_count_in_dir.return_value = 0 # No corrupted files

    mock_puzzle_manager = MagicMock()
    _handle_ls([dir_path_arg], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)

    mock_terminal.fs_handler.list_items.assert_called_once_with(dir_path_arg)
    mock_terminal.fs_handler.get_corrupted_file_count_in_dir.assert_called_once_with(dir_path_arg)
    
    # Check that each item was added to the terminal
    expected_calls = [call("README.md"), call("project_a/"), call("script.sh")] # Sorted order
    mock_terminal.add_line.assert_has_calls(expected_calls, any_order=False) # ls sorts output
    assert mock_terminal.add_line.call_count == len(items_in_dir)
    mock_effect_manager.start_character_corruption_effect.assert_not_called()
    mock_effect_manager.start_text_flicker_effect.assert_not_called()

def test_handle_ls_on_directory_with_corruption_effects(mock_terminal, mock_game_state_manager, mock_effect_manager):
    dir_path_arg = "logs/"
    items_in_dir = ["error.log", "access.log", "debug.info"]
    mock_terminal.fs_handler._resolve_path_str_to_list.return_value = ["var", "logs"]
    mock_terminal.fs_handler._get_node_at_path.return_value = {}
    mock_terminal.fs_handler.list_items.return_value = items_in_dir
    mock_terminal.fs_handler.get_corrupted_file_count_in_dir.return_value = 2 # > 1, so effects should trigger
    
    # Mock random to control effect application
    # random.random side_effect:
    #   0.1 -> item 1 gets effect
    #   0.8 -> item 2 no effect
    #   0.15 -> item 3 gets effect
    # random.choice side_effect:
    #   "corrupt" -> item 1 effect type
    #   "flicker" -> item 3 effect type
    #   "error"   -> item 3 flicker_color_key
    with patch('random.random', side_effect=[0.1, 0.8, 0.15]), \
         patch('random.choice', side_effect=["corrupt", "flicker", "error"]):

        mock_puzzle_manager = MagicMock()
        _handle_ls([dir_path_arg], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)

    mock_terminal.fs_handler.list_items.assert_called_once_with(dir_path_arg)
    mock_terminal.fs_handler.get_corrupted_file_count_in_dir.assert_called_once_with(dir_path_arg)
    
    # Check items added
    # Sorted: access.log, debug.info, error.log
    mock_terminal.add_line.assert_any_call("access.log")
    mock_terminal.add_line.assert_any_call("debug.info")
    mock_terminal.add_line.assert_any_call("error.log")
    assert mock_terminal.add_line.call_count == len(items_in_dir)

    # Check effects (2 items should have effects based on random.random side_effect)
    assert mock_effect_manager.start_character_corruption_effect.call_count == 1
    assert mock_effect_manager.start_text_flicker_effect.call_count == 1
    assert mock_effect_manager.start_timed_delay.call_count == 2 # One delay per effect

def test_handle_ls_empty_directory(mock_terminal, mock_game_state_manager, mock_effect_manager):
    dir_path_arg = "empty_folder"
    mock_terminal.fs_handler._resolve_path_str_to_list.return_value = ["~", "empty_folder"]
    mock_terminal.fs_handler._get_node_at_path.return_value = {}
    mock_terminal.fs_handler.list_items.return_value = [] # Empty list

    mock_puzzle_manager = MagicMock()
    _handle_ls([dir_path_arg], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    
    mock_terminal.fs_handler.list_items.assert_called_once_with(dir_path_arg)
    mock_terminal.add_line.assert_not_called() # ls on empty dir produces no output

def test_handle_ls_path_not_found(mock_terminal, mock_game_state_manager, mock_effect_manager):
    path_arg = "non_existent_path"
    mock_terminal.fs_handler._resolve_path_str_to_list.return_value = ["non_existent_path"]
    mock_terminal.fs_handler._get_node_at_path.return_value = None # Path does not exist

    mock_puzzle_manager = MagicMock()
    _handle_ls([path_arg], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    
    mock_terminal.add_line.assert_called_once_with(f"ls: cannot access '{path_arg}': No such file or directory", style_key='error')

def test_handle_ls_no_args_uses_current_dir(mock_terminal, mock_game_state_manager, mock_effect_manager):
    # This test assumes "." is passed to fs_handler.list_items when no args given to _handle_ls
    items_in_current_dir = ["file1", "dir1/"]
    mock_terminal.fs_handler._resolve_path_str_to_list.return_value = ["~"] # Current dir is ~
    mock_terminal.fs_handler._get_node_at_path.return_value = {} # Current dir is a directory
    mock_terminal.fs_handler.list_items.return_value = items_in_current_dir
    mock_terminal.fs_handler.get_corrupted_file_count_in_dir.return_value = 0

    mock_puzzle_manager = MagicMock()
    _handle_ls([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    
    mock_terminal.fs_handler.list_items.assert_called_once_with(".")
    mock_terminal.fs_handler.get_corrupted_file_count_in_dir.assert_called_once_with(".")
    mock_terminal.add_line.assert_any_call("dir1/")
    mock_terminal.add_line.assert_any_call("file1")

def test_handle_rm_success_file(mock_terminal, mock_game_state_manager, mock_effect_manager):
    target = "file_to_remove.txt"
    mock_terminal.fs_handler.remove_item.return_value = (True, f"Removed '{target}'")

    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_rm([target], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)

    assert continue_running is True
    assert action is None
    mock_terminal.fs_handler.remove_item.assert_called_once_with(target, recursive=False)
    mock_terminal.add_line.assert_not_called()

def test_handle_rm_success_recursive_dir(mock_terminal, mock_game_state_manager, mock_effect_manager):
    target_dir = "dir_to_nuke"
    args_list_r = ["-r", target_dir]
    mock_terminal.fs_handler.remove_item.return_value = (True, f"Removed '{target_dir}'")
    mock_puzzle_manager = MagicMock()

    _handle_rm(args_list_r, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.fs_handler.remove_item.assert_called_once_with(target_dir, recursive=True)

    mock_terminal.fs_handler.remove_item.reset_mock()
    args_list_rf = ["-rf", target_dir] # Test -rf alias
    _handle_rm(args_list_rf, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.fs_handler.remove_item.assert_called_once_with(target_dir, recursive=True)


def test_handle_rm_failure_not_found(mock_terminal, mock_game_state_manager, mock_effect_manager):
    target = "ghost.dat"
    error_msg = f"rm: cannot remove '{target}': No such file or directory"
    mock_terminal.fs_handler.remove_item.return_value = (False, error_msg)

    mock_puzzle_manager = MagicMock()
    _handle_rm([target], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_called_once_with(error_msg, style_key='error')

def test_handle_rm_failure_dir_not_empty_no_recursive(mock_terminal, mock_game_state_manager, mock_effect_manager):
    target = "my_folder/"
    error_msg = f"rm: cannot remove '{target}': Directory not empty"
    mock_terminal.fs_handler.remove_item.return_value = (False, error_msg) # recursive=False by default

    mock_puzzle_manager = MagicMock()
    _handle_rm([target], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.fs_handler.remove_item.assert_called_once_with(target, recursive=False)
    mock_terminal.add_line.assert_called_once_with(error_msg, style_key='error')

def test_handle_rm_white_hat_permission_denied(mock_terminal, mock_game_state_manager, mock_effect_manager):
    target = "secret_file.txt"
    mock_puzzle_manager = MagicMock()
    _handle_rm([target], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_WHITE_HAT)
    
    mock_terminal.add_line.assert_called_once_with("rm: Operation not permitted for White Hat alignment.", style_key='error')
    mock_terminal.fs_handler.remove_item.assert_not_called()

def test_handle_rm_no_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_puzzle_manager = MagicMock()
    _handle_rm([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_called_once_with("rm: missing operand", style_key='error')

def test_handle_rm_only_r_flag(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_puzzle_manager = MagicMock()
    _handle_rm(["-r"], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    # Refactored _handle_rm with args_list=["-r"] now prints "rm: missing operand"
    mock_terminal.add_line.assert_called_once_with("rm: missing operand", style_key='error')

    mock_terminal.add_line.reset_mock()
    # shlex.split("-rf ") is ['-rf'], so this is same as above.
    _handle_rm(["-rf"], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT) # with space
    mock_terminal.add_line.assert_called_once_with("rm: missing operand", style_key='error')

def test_handle_mv_success(mock_terminal, mock_game_state_manager, mock_effect_manager):
    src = "old_name.txt"
    dest = "new_name.txt"
    args_list = [src, dest]
    mock_terminal.fs_handler.move_item.return_value = (True, f"Moved '{src}' to '{dest}'")
    mock_puzzle_manager = MagicMock()

    continue_running, action = _handle_mv(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)

    assert continue_running is True
    assert action is None
    mock_terminal.fs_handler.move_item.assert_called_once_with(src, dest)
    mock_terminal.add_line.assert_not_called()

def test_handle_mv_failure(mock_terminal, mock_game_state_manager, mock_effect_manager):
    src = "source_file.txt"
    dest = "non_existent_dir/dest_file.txt"
    args_list = [src, dest]
    error_msg = f"mv: cannot move '{src}' to '{dest}': No such file or directory"
    mock_terminal.fs_handler.move_item.return_value = (False, error_msg)
    mock_puzzle_manager = MagicMock()

    _handle_mv(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_called_once_with(error_msg, style_key='error')

def test_handle_mv_white_hat_permission_denied(mock_terminal, mock_game_state_manager, mock_effect_manager):
    args_list = ["file1", "file2"]
    mock_puzzle_manager = MagicMock()
    _handle_mv(args_list, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_WHITE_HAT)
    
    mock_terminal.add_line.assert_called_once_with("mv: Operation not permitted for White Hat alignment.", style_key='error')
    mock_terminal.fs_handler.move_item.assert_not_called()

def test_handle_mv_incorrect_args_count(mock_terminal, mock_game_state_manager, mock_effect_manager):
    # No args
    mock_puzzle_manager = MagicMock()
    _handle_mv([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_any_call("mv: missing file operand(s) or too many arguments", style_key='error')
    mock_terminal.add_line.assert_any_call("Usage: mv <source> <destination>", style_key='error')
    
    mock_terminal.add_line.reset_mock()
    # One arg
    _handle_mv(["source_only"], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_any_call("mv: missing file operand(s) or too many arguments", style_key='error')

    mock_terminal.add_line.reset_mock()
    # Three args
    _handle_mv(["src", "dest", "extra"], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_any_call("mv: missing file operand(s) or too many arguments", style_key='error')

# Patching set_global_theme and get_current_theme from the effects module,
# as they are imported and used by command_handler's _handle_theme.
@patch('command_handler.set_global_theme')
@patch('command_handler.get_current_theme')
def test_handle_theme_success(mock_get_current_theme, mock_set_global_theme, mock_terminal, mock_game_state_manager, mock_effect_manager):
    theme_name_arg = "corrupted_kali"
    mock_set_global_theme.return_value = True # Simulate successful theme set
    mock_get_current_theme.return_value = {'name': "Corrupted Kali"} # Simulate getting the new theme name

    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_theme([theme_name_arg], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)

    assert continue_running is True
    assert action is None
    mock_set_global_theme.assert_called_once_with(theme_name_arg)
    mock_terminal.apply_theme_colors.assert_called_once()
    mock_terminal.add_line.assert_called_once_with("Theme set to: Corrupted Kali", style_key='success')

@patch('command_handler.set_global_theme')
def test_handle_theme_alias(mock_set_global_theme, mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_set_global_theme.return_value = True
    with patch('command_handler.get_current_theme', return_value={'name': "Digital Nightmare"}):
        mock_puzzle_manager = MagicMock()
        _handle_theme(["nightmare"], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
        mock_set_global_theme.assert_called_with("digital_nightmare") # Check alias resolution

    mock_set_global_theme.reset_mock() # Reset for the next alias check
    mock_terminal.apply_theme_colors.reset_mock()
    mock_terminal.add_line.reset_mock()
    with patch('command_handler.get_current_theme', return_value={'name': "Corrupted Kali"}):
        # mock_puzzle_manager already defined in this scope if we assume it's part of the same test function block
        # However, to be safe and explicit for each "act" part:
        mock_puzzle_manager = MagicMock()
        _handle_theme(["kali"], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
        mock_set_global_theme.assert_called_with("corrupted_kali")

    mock_set_global_theme.reset_mock()
    mock_terminal.apply_theme_colors.reset_mock()
    mock_terminal.add_line.reset_mock()
    with patch('command_handler.get_current_theme', return_value={'name': "Classic DOS"}):
        mock_puzzle_manager = MagicMock()
        _handle_theme(["dos"], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
        mock_set_global_theme.assert_called_with("classic_dos")


@patch('command_handler.THEMES', {"default": {}, "other": {}})  # This is the outer patch
@patch('command_handler.set_global_theme')      # Inner patch
# The decorator below was duplicated, ensuring only one remains.
# @patch('command_handler.THEMES', {"default": {}, "other": {}}) # This line was the duplicate and is effectively removed by the corrected search block.
def test_handle_theme_not_found(mock_set_global_theme, # From inner @patch('command_handler.set_global_theme')
                                 mock_terminal, mock_game_state_manager, mock_effect_manager):
    theme_name_arg = "non_existent_theme"
    mock_set_global_theme.return_value = False # Simulate theme not found

    # Import command_handler locally to access its THEMES which is patched
    import command_handler as ch_module_under_test

    mock_puzzle_manager = MagicMock()
    _handle_theme([theme_name_arg], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    
    mock_terminal.apply_theme_colors.assert_not_called()
    # Access the patched THEMES directly from the module for its keys
    available_themes_str = ", ".join(sorted(ch_module_under_test.THEMES.keys()))
    mock_terminal.add_line.assert_called_once_with(
        f"Theme '{theme_name_arg}' not found. Available: {available_themes_str}",
        style_key='error'
    )

@patch('command_handler.THEMES', {"default": {}, "hacker": {}})
def test_handle_theme_no_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    # Import command_handler locally to access its THEMES which is patched
    import command_handler as ch_module_under_test

    mock_puzzle_manager = MagicMock()
    _handle_theme([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_any_call("Usage: theme <theme_name>", style_key='error')
    # Access the patched THEMES directly from the module for its keys
    available_themes_str = ", ".join(sorted(ch_module_under_test.THEMES.keys()))
    mock_terminal.add_line.assert_any_call(
        f"Sets the terminal color scheme. Available themes: {available_themes_str}",
        style_key='error'
    )

# --- Tests for Role-Specific Commands ---

def test_handle_integrity_check_white_hat(mock_terminal, mock_game_state_manager, mock_effect_manager):
    player_role = ROLE_WHITE_HAT
    mock_game_state_manager.get_player_role.return_value = player_role
    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_integrity_check([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, player_role)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_any_call("Performing system integrity scan...", style_key='highlight')
    mock_terminal.add_line.assert_any_call("Integrity Scan: All systems nominal. No anomalies detected.", style_key='success')
    assert mock_effect_manager.start_timed_delay.call_count == 4 # Based on current implementation

def test_handle_integrity_check_other_roles_denied(mock_terminal, mock_game_state_manager, mock_effect_manager):
    for player_role in [ROLE_GREY_HAT, ROLE_BLACK_HAT]:
        mock_terminal.reset_mock()
        mock_effect_manager.reset_mock()
        mock_game_state_manager.get_player_role.return_value = player_role
        mock_puzzle_manager = MagicMock()
        continue_running, action = _handle_integrity_check([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, player_role)
        assert continue_running is True
        assert action is None
        mock_terminal.add_line.assert_called_with("Error: integrity_check is a White Hat aligned command.", style_key='error')
        mock_effect_manager.start_timed_delay.assert_not_called()

def test_handle_observe_traffic_grey_hat(mock_terminal, mock_game_state_manager, mock_effect_manager):
    player_role = ROLE_GREY_HAT
    mock_game_state_manager.get_player_role.return_value = player_role
    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_observe_traffic([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, player_role)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_any_call("Initializing network traffic monitor...", style_key='highlight')
    mock_terminal.add_line.assert_any_call("Traffic Observation: Minor encrypted traffic spikes detected from unknown origin. Further analysis required.", style_key='warning')
    assert mock_effect_manager.start_timed_delay.call_count == 3

def test_handle_observe_traffic_other_roles_denied(mock_terminal, mock_game_state_manager, mock_effect_manager):
    for player_role in [ROLE_WHITE_HAT, ROLE_BLACK_HAT]:
        mock_terminal.reset_mock()
        mock_effect_manager.reset_mock()
        mock_game_state_manager.get_player_role.return_value = player_role
        mock_puzzle_manager = MagicMock()
        continue_running, action = _handle_observe_traffic([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, player_role)
        assert continue_running is True
        assert action is None
        mock_terminal.add_line.assert_called_with("Error: observe_traffic is a Grey Hat aligned command.", style_key='error')
        mock_effect_manager.start_timed_delay.assert_not_called()

def test_handle_find_exploit_black_hat(mock_terminal, mock_game_state_manager, mock_effect_manager):
    player_role = ROLE_BLACK_HAT
    mock_game_state_manager.get_player_role.return_value = player_role
    mock_puzzle_manager = MagicMock()
    continue_running, action = _handle_find_exploit([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, player_role)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_any_call("Scanning for known vulnerabilities...", style_key='highlight')
    mock_terminal.add_line.assert_any_call("Vulnerability Scan: Potential buffer overflow in 'aether_daemon_v1.2'. Exploit 'CVE-2024-AETHER01' may apply.", style_key='error')
    assert mock_effect_manager.start_timed_delay.call_count == 3

def test_handle_find_exploit_other_roles_denied(mock_terminal, mock_game_state_manager, mock_effect_manager):
    for player_role in [ROLE_WHITE_HAT, ROLE_GREY_HAT]:
        mock_terminal.reset_mock()
        mock_effect_manager.reset_mock()
        mock_game_state_manager.get_player_role.return_value = player_role
        mock_puzzle_manager = MagicMock()
        continue_running, action = _handle_find_exploit([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, player_role)
        assert continue_running is True
# --- Tests for System Management Commands ---

def test_handle_status(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_puzzle_manager = MagicMock()
    player_role = ROLE_GREY_HAT # Role doesn't affect current placeholder output

    continue_running, action = _handle_status([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, player_role)

    assert continue_running is True
    assert action is None
    expected_calls = [
        call("System Status: Nominal", style_key='success'),
        call("Aether Network Connection: Stable", style_key='success'),
        call("Corruption Level: Minimal", style_key='warning')
    ]
    mock_terminal.add_line.assert_has_calls(expected_calls)
    assert mock_terminal.add_line.call_count == 3

def test_handle_processes(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_puzzle_manager = MagicMock()
    player_role = ROLE_GREY_HAT

    continue_running, action = _handle_processes([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, player_role)

    assert continue_running is True
    assert action is None
    expected_calls = [
        call("PID   USER      COMMAND", style_key='highlight'),
        call("1     root      /sbin/init", style_key='default_fg'),
        call("45    system    aether_core_monitor", style_key='default_fg'),
        call("101   player    /bin/bash", style_key='default_fg'),
        call("105   player    python main.py", style_key='default_fg'),
        call("666   unknown   ???", style_key='error')
    ]
    mock_terminal.add_line.assert_has_calls(expected_calls)
    assert mock_terminal.add_line.call_count == 6

def test_handle_kill_valid_pid_terminates(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_puzzle_manager = MagicMock()
    player_role = ROLE_GREY_HAT
    pid_to_kill = "101"

    continue_running, action = _handle_kill([pid_to_kill], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, player_role)

    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with(f"Process {pid_to_kill} terminated.", style_key='success')
    mock_effect_manager.start_character_corruption_effect.assert_not_called()

def test_handle_kill_protected_pid_access_denied(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_puzzle_manager = MagicMock()
    player_role = ROLE_GREY_HAT
    pid_to_kill = "1" # System process

    continue_running, action = _handle_kill([pid_to_kill], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, player_role)
    
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with(f"kill: ({pid_to_kill}) - Operation not permitted.", style_key='error')

def test_handle_kill_suspicious_pid_fails_with_effect(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_puzzle_manager = MagicMock()
    player_role = ROLE_GREY_HAT
    pid_to_kill = "666"
    mock_terminal.add_line.return_value = 5 # Simulate line index for effect

    continue_running, action = _handle_kill([pid_to_kill], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, player_role)

    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_any_call(f"Attempting to terminate process {pid_to_kill}...", style_key='warning')
    mock_terminal.add_line.assert_any_call(f"kill: ({pid_to_kill}) - Operation failed. Access denied or process unstable.", style_key='error')
    mock_effect_manager.start_character_corruption_effect.assert_called_once_with(5, 1000, 0.2, 60)

def test_handle_kill_non_existent_pid(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_puzzle_manager = MagicMock()
    player_role = ROLE_GREY_HAT
    pid_to_kill = "9999"

    continue_running, action = _handle_kill([pid_to_kill], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, player_role)

    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with(f"kill: ({pid_to_kill}) - No such process.", style_key='error')

def test_handle_kill_no_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_puzzle_manager = MagicMock()
    player_role = ROLE_GREY_HAT

    continue_running, action = _handle_kill([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, player_role)

    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_any_call("kill: missing operand", style_key='error')
    mock_terminal.add_line.assert_any_call("Usage: kill <pid>", style_key='error')
    assert mock_terminal.add_line.call_count == 2

def test_handle_kill_too_many_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_puzzle_manager = MagicMock()
    player_role = ROLE_GREY_HAT

    continue_running, action = _handle_kill(["123", "456"], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, player_role)

    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_any_call("kill: too many arguments", style_key='error')
    mock_terminal.add_line.assert_any_call("Usage: kill <pid>", style_key='error')
    assert mock_terminal.add_line.call_count == 2

def test_handle_kill_invalid_pid_format(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_puzzle_manager = MagicMock()
    player_role = ROLE_GREY_HAT
    invalid_pid = "abc"

    continue_running, action = _handle_kill([invalid_pid], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, player_role)

    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_once_with(f"kill: '{invalid_pid}' is not a valid PID.", style_key='error')
    mock_effect_manager.start_timed_delay.assert_not_called()

# --- Tests for _handle_scan ---

def test_handle_scan_file_exists_not_corrupted(mock_terminal, mock_game_state_manager, mock_effect_manager):
    file_path = "stable_file.txt"
    mock_terminal.fs_handler._resolve_path_str_to_list.return_value = ["~", file_path]
    mock_terminal.fs_handler._get_node_at_path.return_value = "file content" # Indicates it's a file
    mock_terminal.fs_handler.is_item_corrupted.return_value = False
    mock_terminal.add_line.return_value = 0 # Dummy line index for progress updates

    mock_puzzle_manager = MagicMock()
    _handle_scan([file_path], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)

    mock_terminal.add_line.assert_any_call(f"Initiating integrity scan for: {file_path}...", style_key='highlight')
    # Progress updates use update_line_text
    mock_terminal.update_line_text.assert_any_call(0, "Scanning sectors... [100%]")
    mock_terminal.add_line.assert_any_call("Analyzing data structure...", style_key='default_fg')
    mock_terminal.add_line.assert_any_call(f"Scan Complete: {file_path}", style_key='success')
    mock_terminal.add_line.assert_any_call("Status: STABLE. No corruption detected.", style_key='success')
    mock_terminal.fs_handler.is_item_corrupted.assert_called_once_with(file_path)
    assert mock_effect_manager.start_timed_delay.call_count >= 6 # Multiple delays for progress

def test_handle_scan_file_exists_corrupted(mock_terminal, mock_game_state_manager, mock_effect_manager):
    file_path = "corrupted_data.bin"
    mock_terminal.fs_handler._resolve_path_str_to_list.return_value = ["~", file_path]
    mock_terminal.fs_handler._get_node_at_path.return_value = "file content"
    mock_terminal.fs_handler.is_item_corrupted.return_value = True
    mock_terminal.add_line.return_value = 0 # Dummy line index

    with patch('random.randint', return_value=42): # Mock corruption level
        mock_puzzle_manager = MagicMock()
        _handle_scan([file_path], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)

    mock_terminal.add_line.assert_any_call(f"Scan Complete: {file_path}", style_key='warning')
    mock_terminal.add_line.assert_any_call(f"Status: CORRUPTION DETECTED. Integrity: {100-42}%", style_key='error', bold=True)
    mock_terminal.add_line.assert_any_call(f"Estimated data loss: {42}%.", style_key='error')
    mock_terminal.add_line.assert_any_call("Recommendation: Use 'parse' to attempt data extraction or 'restore' to attempt repair.", style_key='highlight')
    mock_effect_manager.start_character_corruption_effect.assert_called()

def test_handle_scan_file_not_found(mock_terminal, mock_game_state_manager, mock_effect_manager):
    file_path = "non_existent.dat"
    mock_terminal.fs_handler._resolve_path_str_to_list.return_value = ["~", file_path]
    mock_terminal.fs_handler._get_node_at_path.return_value = None # File not found

    mock_puzzle_manager = MagicMock()
    _handle_scan([file_path], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_called_once_with(f"scan: {file_path}: No such file or directory", style_key='error')

def test_handle_scan_is_directory(mock_terminal, mock_game_state_manager, mock_effect_manager):
    dir_path = "my_folder/"
    mock_terminal.fs_handler._resolve_path_str_to_list.return_value = ["~", "my_folder"]
    mock_terminal.fs_handler._get_node_at_path.return_value = {} # It's a directory

    mock_puzzle_manager = MagicMock()
    _handle_scan([dir_path], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_called_once_with(f"scan: {dir_path}: Is a directory. Cannot scan directories.", style_key='error')

def test_handle_scan_no_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_puzzle_manager = MagicMock()
    # shlex.split(" ") is [], or shlex.split("") is []
    _handle_scan([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_any_call("Usage: scan <filename>", style_key='error')
    mock_terminal.add_line.assert_any_call("Analyzes a file for corruption and integrity.", style_key='error')

# --- Tests for _handle_parse ---

def test_handle_parse_file_exists_not_corrupted(mock_terminal, mock_game_state_manager, mock_effect_manager):
    file_path = "readable_doc.txt"
    content = "This is line one.\nThis is line two."
    mock_terminal.fs_handler._resolve_path_str_to_list.return_value = ["~", file_path]
    mock_terminal.fs_handler._get_node_at_path.return_value = content
    mock_terminal.fs_handler.get_item_content.return_value = content
    mock_terminal.fs_handler.is_item_corrupted.return_value = False
    mock_terminal.add_line.return_value = 0

    mock_puzzle_manager = MagicMock()
    _handle_parse([file_path], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)

    mock_terminal.add_line.assert_any_call(f"Parsing data stream from: {file_path}...", style_key='highlight')
    mock_terminal.add_line.assert_any_call("File appears stable. Extracting all content.", style_key='success')
    mock_terminal.add_line.assert_any_call("--- BEGIN PARSED DATA ---", style_key='highlight')
    mock_terminal.add_line.assert_any_call("This is line one.")
    mock_terminal.add_line.assert_any_call("This is line two.")
    mock_terminal.add_line.assert_any_call("--- END PARSED DATA ---", style_key='highlight')
    mock_effect_manager.start_character_corruption_effect.assert_not_called()

@patch('random.random')
def test_handle_parse_file_exists_corrupted(mock_random_random, mock_terminal, mock_game_state_manager, mock_effect_manager):
    file_path = "damaged_archive.zip"
    content = "ValidHeader\nCorruptDataSegment\nAnotherValidPart"
    mock_terminal.fs_handler._resolve_path_str_to_list.return_value = ["~", file_path]
    mock_terminal.fs_handler._get_node_at_path.return_value = content
    mock_terminal.fs_handler.get_item_content.return_value = content
    mock_terminal.fs_handler.is_item_corrupted.return_value = True
    mock_terminal.add_line.return_value = 0

    # Control random outcomes: 1st line recoverable, 2nd not, 3rd recoverable but garbled
    mock_random_random.side_effect = [
        # Line 1 ("ValidHeader"): Recoverable, NOT heavily garbled
        0.6,  # Call 1: L1 > 0.4 -> True (recoverable)
        0.5,  # Call 2: L1 < 0.3 -> False (NOT heavily garbled)
        # Line 2 ("CorruptDataSegment"): Unrecoverable
        0.3,  # Call 3: L2 > 0.4 -> False (unrecoverable)
        # Line 3 ("AnotherValidPart"): Recoverable, HEAVILY garbled
        0.7,  # Call 4: L3 > 0.4 -> True (recoverable)
        0.2,  # Call 5: L3 < 0.3 -> True (HEAVILY garbled)
        # Calls 6-21 (16 calls) for garbling characters in "AnotherValidPart"
        # (all < 0.7 to ensure random.choice is used)
        0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
        0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
        # Post-loop light corruption checks for extracted_fragments
        0.2,  # Call 22: For fragment 1 ("ValidHeader") -> no light corruption
        0.1,  # Call 23: For fragment 3 (garbled "AnotherValidPart") -> light corruption
    ]
    mock_puzzle_manager = MagicMock()
    _handle_parse([file_path], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)

    mock_terminal.add_line.assert_any_call("Corruption detected. Attempting partial data extraction.", style_key='warning')
    mock_terminal.add_line.assert_any_call("--- BEGIN PARSED DATA ---", style_key='highlight')
    mock_terminal.add_line.assert_any_call("ValidHeader")
    mock_terminal.add_line.assert_any_call("... [UNRECOVERABLE SEGMENT] ...")
    # Check if the garbled line was added (content will be unpredictable due to random.choice)
    # We can check that a third content line was added.
    parsed_lines = [c[0][0] for c in mock_terminal.add_line.call_args_list if "---" not in c[0][0] and "Parsing data" not in c[0][0] and "Corruption detected" not in c[0][0]]
    assert len(parsed_lines) >= 3 # Header, Unrecoverable, Garbled
    assert "... [UNRECOVERABLE SEGMENT] ..." in parsed_lines
    assert "ValidHeader" in parsed_lines
    # Check that some effect was applied to the unrecoverable segment
    mock_effect_manager.start_temp_color_change_effect.assert_any_call(0, 99999, 'error', None)


def test_handle_parse_file_not_found(mock_terminal, mock_game_state_manager, mock_effect_manager):
    file_path = "missing_doc.txt"
    mock_terminal.fs_handler._resolve_path_str_to_list.return_value = ["~", file_path]
    mock_terminal.fs_handler._get_node_at_path.return_value = None

    mock_puzzle_manager = MagicMock()
    _handle_parse([file_path], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_called_once_with(f"parse: {file_path}: No such file or directory", style_key='error')

def test_handle_parse_is_directory(mock_terminal, mock_game_state_manager, mock_effect_manager):
    dir_path = "config_dir/"
    mock_terminal.fs_handler._resolve_path_str_to_list.return_value = ["~", "config_dir"]
    mock_terminal.fs_handler._get_node_at_path.return_value = {}

    mock_puzzle_manager = MagicMock()
    _handle_parse([dir_path], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_called_once_with(f"parse: {dir_path}: Is a directory. Cannot parse directories.", style_key='error')

def test_handle_parse_no_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_puzzle_manager = MagicMock()
    # shlex.split("  ") is []
    _handle_parse([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_any_call("Usage: parse <filename>", style_key='error')

# --- Tests for _handle_restore ---

def test_handle_restore_file_not_corrupted(mock_terminal, mock_game_state_manager, mock_effect_manager):
    file_path = "healthy_file.exe"
    mock_terminal.fs_handler._resolve_path_str_to_list.return_value = ["~", file_path]
    mock_terminal.fs_handler._get_node_at_path.return_value = "content"
    mock_terminal.fs_handler.is_item_corrupted.return_value = False

    mock_puzzle_manager = MagicMock()
    _handle_restore([file_path], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_called_with(f"restore: {file_path}: File is not corrupted. No action taken.", style_key='success')
    mock_terminal.fs_handler.mark_item_corrupted.assert_not_called()

@patch('random.random')
def test_handle_restore_successful_white_hat(mock_random_random, mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_random_random.return_value = 0.1 # Ensure success for White Hat (chance 0.85)
    file_path = "fixable.dll"
    mock_terminal.fs_handler._resolve_path_str_to_list.return_value = ["~", file_path]
    mock_terminal.fs_handler._get_node_at_path.return_value = "corrupted content"
    mock_terminal.fs_handler.is_item_corrupted.return_value = True
    mock_terminal.fs_handler.mark_item_corrupted.return_value = (True, "Status updated")
    mock_terminal.add_line.return_value = 0
    mock_game_state_manager.get_player_role.return_value = ROLE_WHITE_HAT # Set role for this test

    mock_puzzle_manager = MagicMock()
    _handle_restore([file_path], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_WHITE_HAT)

    mock_terminal.add_line.assert_any_call(f"Attempting to restore integrity of: {file_path}...", style_key='highlight')
    # Progress updates use update_line_text
    mock_terminal.update_line_text.assert_any_call(0, "Finalizing file structure... [100%]")
    mock_terminal.add_line.assert_any_call(f"Restore successful: {file_path} integrity has been restored.", style_key='success')
    mock_terminal.fs_handler.mark_item_corrupted.assert_called_once_with(file_path, corrupted_status=False)

@patch('random.random')
def test_handle_restore_partially_successful_grey_hat(mock_random_random, mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_random_random.return_value = 0.9 # Ensure failure for Grey Hat (chance 0.55) -> partial success
    file_path = "glitchy.sav"
    mock_terminal.fs_handler._resolve_path_str_to_list.return_value = ["~", file_path]
    mock_terminal.fs_handler._get_node_at_path.return_value = "very corrupted"
    mock_terminal.fs_handler.is_item_corrupted.return_value = True
    mock_terminal.add_line.return_value = 0
    mock_game_state_manager.get_player_role.return_value = ROLE_GREY_HAT

    with patch('random.randint', return_value=20): # Mock remaining corruption
        mock_puzzle_manager = MagicMock()
        _handle_restore([file_path], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)

    mock_terminal.add_line.assert_any_call(f"Restore partially successful: {file_path}", style_key='warning')
    mock_terminal.add_line.assert_any_call(f"Significant data recovered, but some corruption remains (approx. 20%).", style_key='warning')
    mock_terminal.fs_handler.mark_item_corrupted.assert_not_called() # Status isn't changed to False
    mock_effect_manager.start_text_flicker_effect.assert_called()

def test_handle_restore_file_not_found(mock_terminal, mock_game_state_manager, mock_effect_manager):
    file_path = "lost_file.tmp"
    mock_terminal.fs_handler._resolve_path_str_to_list.return_value = ["~", file_path]
    mock_terminal.fs_handler._get_node_at_path.return_value = None

    mock_puzzle_manager = MagicMock()
    _handle_restore([file_path], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_called_once_with(f"restore: {file_path}: No such file or directory", style_key='error')

def test_handle_restore_is_directory(mock_terminal, mock_game_state_manager, mock_effect_manager):
    dir_path = "backup_folder/"
    mock_terminal.fs_handler._resolve_path_str_to_list.return_value = ["~", "backup_folder"]
    mock_terminal.fs_handler._get_node_at_path.return_value = {}

    mock_puzzle_manager = MagicMock()
    _handle_restore([dir_path], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_called_once_with(f"restore: {dir_path}: Is a directory. Cannot restore directories.", style_key='error')

def test_handle_restore_no_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_puzzle_manager = MagicMock()
    # shlex.split("   ") is []
    _handle_restore([], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_GREY_HAT)
    mock_terminal.add_line.assert_any_call("Usage: restore <filename>", style_key='error')

# --- Tests for process_main_terminal_command ---
 
def test_process_main_terminal_command_quit(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_puzzle_manager = MagicMock()
    # For this test, ensure we are not in puzzle state for quit to exit game
    mock_game_state_manager.is_state.return_value = False
    continue_running, action = process_main_terminal_command("quit", mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager)
    assert continue_running is False
    assert action is None

    # mock_puzzle_manager already defined in this scope
    mock_game_state_manager.is_state.return_value = False # Ensure not in puzzle state
    continue_running, action = process_main_terminal_command("exit", mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager)
    assert continue_running is False
    assert action is None

def test_process_main_terminal_command_unknown(mock_terminal, mock_game_state_manager, mock_effect_manager):
    command = "unknown_command_test"
    mock_puzzle_manager = MagicMock()
    continue_running, action = process_main_terminal_command(command, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager)
    assert continue_running is True
    assert action is None
    mock_terminal.add_line.assert_called_with(f"Error: Command '{command}' not recognized or not available for your alignment/state.", style_key='error')

def test_process_main_terminal_command_dispatch_echo(mock_terminal, mock_game_state_manager, mock_effect_manager):
    # Instead of patching the function directly, patch its entry in the command map
    # This ensures that the process_main_terminal_command function uses our mock.
    mock_specific_handler = MagicMock(return_value=(True, None))
    
    with patch.dict(MAIN_COMMAND_HANDLERS, {'echo': mock_specific_handler}):
        command_input = "echo Hello Test"
        mock_puzzle_manager = MagicMock()
        process_main_terminal_command(command_input, mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager)
        
        expected_player_role = mock_game_state_manager.get_player_role()
        mock_specific_handler.assert_called_once_with(
            ['Hello', 'Test'], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, expected_player_role
        )

def test_process_main_terminal_command_role_permission_allowed(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_game_state_manager.get_player_role.return_value = ROLE_WHITE_HAT
    # 'ls' is allowed for White Hat. Need to ensure _handle_ls is in MAIN_COMMAND_HANDLERS
    # For this test, we assume it is and can be patched.

    mock_handle_ls_replacement = MagicMock(return_value=(True, None))

    # Patch the 'ls' entry in the MAIN_COMMAND_HANDLERS dictionary
    with patch.dict(MAIN_COMMAND_HANDLERS, {'ls': mock_handle_ls_replacement}):
        mock_puzzle_manager = MagicMock()
        process_main_terminal_command("ls -la", mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager)

        # Assert that our replacement mock was called
        mock_handle_ls_replacement.assert_called_once_with(
            ['-la'], mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager, ROLE_WHITE_HAT
        )

def test_process_main_terminal_command_role_permission_denied(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_game_state_manager.get_player_role.return_value = ROLE_WHITE_HAT
    # 'rm' is not allowed for White Hat
    
    mock_puzzle_manager = MagicMock()
    process_main_terminal_command("rm important_file", mock_terminal, mock_game_state_manager, mock_effect_manager, mock_puzzle_manager)
    
    mock_terminal.add_line.assert_called_with(
        "Error: Command 'rm' not recognized or not available for your alignment/state.",
        style_key='error'
    )

# --- Tests for MSFConsole Command Handlers ---

def test_handle_msf_exit_back(mock_terminal, mock_game_state_manager, mock_effect_manager):
    player_role = ROLE_GREY_HAT # Role doesn't affect this command's core logic

    _handle_msf_exit_back("", mock_terminal, mock_game_state_manager, mock_effect_manager, player_role)

    mock_terminal.clear_prompt_override.assert_called_once()
    mock_game_state_manager.change_state.assert_called_once_with("MAIN_TERMINAL")
    mock_terminal.clear_buffer.assert_called_once()
    mock_terminal.add_line.assert_any_call("Exited msfconsole.", style_key="highlight")
    mock_terminal.add_line.assert_any_call("Type 'help' for a list of commands.")
    assert mock_terminal.add_line.call_count == 2

def test_handle_msf_help_grey_hat(mock_terminal, mock_game_state_manager, mock_effect_manager):
    player_role = ROLE_GREY_HAT
    # Ensure COMMAND_ACCESS is available for the test
    from command_handler import COMMAND_ACCESS as CH_COMMAND_ACCESS

    _handle_msf_help("", mock_terminal, mock_game_state_manager, mock_effect_manager, player_role)

    mock_terminal.add_line.assert_any_call("Core Commands:", style_key='highlight')
    
    # Check if help texts for Grey Hat's allowed MSF commands are called
    grey_hat_msf_help_texts = CH_COMMAND_ACCESS[ROLE_GREY_HAT]["help_text_msf"]
    grey_hat_allowed_msf = CH_COMMAND_ACCESS[ROLE_GREY_HAT]["allowed_msf"]

    for cmd_key in sorted(grey_hat_allowed_msf):
        if cmd_key in grey_hat_msf_help_texts:
            mock_terminal.add_line.assert_any_call(grey_hat_msf_help_texts[cmd_key])
    
    # Verify that a known Grey Hat command's help is present
    assert "use" in grey_hat_allowed_msf
    mock_terminal.add_line.assert_any_call(grey_hat_msf_help_texts["use"])
    # Verify 'run' (exploit) is present for grey hat
    assert "run" in grey_hat_allowed_msf
    mock_terminal.add_line.assert_any_call(grey_hat_msf_help_texts["run"])


def test_handle_msf_help_white_hat(mock_terminal, mock_game_state_manager, mock_effect_manager):
    player_role = ROLE_WHITE_HAT
    from command_handler import COMMAND_ACCESS as CH_COMMAND_ACCESS

    _handle_msf_help("", mock_terminal, mock_game_state_manager, mock_effect_manager, player_role)

    mock_terminal.add_line.assert_any_call("Core Commands:", style_key='highlight')

    white_hat_msf_help_texts = CH_COMMAND_ACCESS[ROLE_WHITE_HAT]["help_text_msf"]
    white_hat_allowed_msf = CH_COMMAND_ACCESS[ROLE_WHITE_HAT]["allowed_msf"]
    
    # Check a command white hat has (e.g., 'search')
    assert "search" in white_hat_allowed_msf
    mock_terminal.add_line.assert_any_call(white_hat_msf_help_texts["search"])

    # Check a command white hat does NOT have (e.g., 'run' or 'exploit')
    assert "run" not in white_hat_allowed_msf
    assert "exploit" not in white_hat_allowed_msf
    
    run_help_text_from_grey = CH_COMMAND_ACCESS[ROLE_GREY_HAT]["help_text_msf"]["run"]
    
    calls = mock_terminal.add_line.call_args_list
    assert not any(call_args[0][0] == run_help_text_from_grey for call_args in calls), \
        "Help text for 'run'/'exploit' should not be shown for White Hat in MSF help"

def test_handle_msf_search_with_keyword(mock_terminal, mock_game_state_manager, mock_effect_manager):
    from command_handler import MSF_SIMULATED_MODULES # Keep this import local to the test
    keyword = "smb"
    player_role = ROLE_GREY_HAT

    _handle_msf_search(keyword, mock_terminal, mock_game_state_manager, mock_effect_manager, player_role)

    mock_terminal.add_line.assert_any_call(f"Matching Modules ({keyword}):", style_key="highlight")
    mock_terminal.add_line.assert_any_call("  #  Name                                     Disclosure Date  Rank    Check  Description")
    
    found_in_code = [mod for mod in MSF_SIMULATED_MODULES if keyword in mod]
    assert len(found_in_code) > 0, "Test keyword should find modules"
    
    # Check if at least one found module's line is added (simplified check)
    # A more robust check would verify all details for each found module.
    # For example, checking the first found module:
    first_found_mod = found_in_code[0]
    if first_found_mod == "exploit/windows/smb/ms08_067_netapi":
        desc = "Microsoft Server Service Relative Path Stack Corruption"
        mock_terminal.add_line.assert_any_call(f"  0  {first_found_mod:<40} 2008-10-28       excellent No     {desc}")
    elif first_found_mod == "exploit/windows/smb/ms17_010_eternalblue":
        desc = "MS17-010 EternalBlue SMB Remote Windows Kernel Pool Corruption"
        mock_terminal.add_line.assert_any_call(f"  0  {first_found_mod:<40} 2008-10-28       excellent No     {desc}")
    # Add other specific module checks here if necessary
    
    mock_terminal.scroll_to_bottom.assert_called_once()


def test_handle_msf_search_no_keyword(mock_terminal, mock_game_state_manager, mock_effect_manager):
    player_role = ROLE_GREY_HAT
    _handle_msf_search(" ", mock_terminal, mock_game_state_manager, mock_effect_manager, player_role)
    mock_terminal.add_line.assert_called_with("Usage: search <keyword>", style_key='error')

def test_handle_msf_search_keyword_not_found(mock_terminal, mock_game_state_manager, mock_effect_manager):
    keyword = "nonexistentkeyword123"
    player_role = ROLE_GREY_HAT
    _handle_msf_search(keyword, mock_terminal, mock_game_state_manager, mock_effect_manager, player_role)
    mock_terminal.add_line.assert_any_call(f"No modules found matching '{keyword}'.")

def test_handle_msf_use_valid_module(mock_terminal, mock_game_state_manager, mock_effect_manager):
    from command_handler import MSF_SIMULATED_MODULES
    player_role = ROLE_GREY_HAT
    module_name = MSF_SIMULATED_MODULES[0] # Use the first simulated module

    _handle_msf_use(module_name, mock_terminal, mock_game_state_manager, mock_effect_manager, player_role)
    mock_terminal.set_prompt_override.assert_called_once_with(f"msf6 exploit({module_name}) > ")
    mock_terminal.add_line.assert_not_called()

def test_handle_msf_use_invalid_module(mock_terminal, mock_game_state_manager, mock_effect_manager):
    player_role = ROLE_GREY_HAT
    module_name = "exploit/non/existent/module"
    _handle_msf_use(module_name, mock_terminal, mock_game_state_manager, mock_effect_manager, player_role)
    mock_terminal.add_line.assert_called_once_with(f"Failed to load module: {module_name}", style_key='error')
    mock_terminal.set_prompt_override.assert_not_called()

def test_handle_msf_use_no_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    player_role = ROLE_GREY_HAT
    _handle_msf_use("  ", mock_terminal, mock_game_state_manager, mock_effect_manager, player_role)
    mock_terminal.add_line.assert_called_once_with("Usage: use <module_path>", style_key='error')

# Helper to set current MSF module for tests
def _set_current_msf_module_for_test(terminal_mock, module_name):
    if module_name:
        terminal_mock.prompt_override = f"msf6 exploit({module_name}) > "
    else:
        terminal_mock.prompt_override = "msf6 > "


def test_handle_msf_info_with_current_module(mock_terminal, mock_game_state_manager, mock_effect_manager):
    from command_handler import MSF_SIMULATED_MODULES
    player_role = ROLE_GREY_HAT
    current_module = MSF_SIMULATED_MODULES[0] # e.g., "exploit/windows/smb/ms08_067_netapi"
    _set_current_msf_module_for_test(mock_terminal, current_module)

    _handle_msf_info("", mock_terminal, mock_game_state_manager, mock_effect_manager, player_role)
    mock_terminal.add_line.assert_any_call(f"\nName: {current_module}", style_key="highlight")
    # Add more assertions for specific info output if necessary

def test_handle_msf_info_with_arg_module(mock_terminal, mock_game_state_manager, mock_effect_manager):
    from command_handler import MSF_SIMULATED_MODULES
    player_role = ROLE_GREY_HAT
    module_to_info = MSF_SIMULATED_MODULES[1] # e.g., "exploit/windows/smb/ms17_010_eternalblue"
    _set_current_msf_module_for_test(mock_terminal, None) # No current module initially

    _handle_msf_info(module_to_info, mock_terminal, mock_game_state_manager, mock_effect_manager, player_role)
    mock_terminal.add_line.assert_any_call(f"\nName: {module_to_info}", style_key="highlight")

def test_handle_msf_info_module_not_found(mock_terminal, mock_game_state_manager, mock_effect_manager):
    player_role = ROLE_GREY_HAT
    module_name = "fake/module"
    _set_current_msf_module_for_test(mock_terminal, None)
    _handle_msf_info(module_name, mock_terminal, mock_game_state_manager, mock_effect_manager, player_role)
    mock_terminal.add_line.assert_called_with(f"Module not found: {module_name}", style_key='error')

def test_handle_msf_info_no_module_selected_or_arg(mock_terminal, mock_game_state_manager, mock_effect_manager):
    player_role = ROLE_GREY_HAT
    _set_current_msf_module_for_test(mock_terminal, None) # No current module
    _handle_msf_info("", mock_terminal, mock_game_state_manager, mock_effect_manager, player_role)
    mock_terminal.add_line.assert_called_with("No module selected. Use 'info <module>' or 'use <module>' first.", style_key='error')


def test_handle_msf_show_options_module_selected(mock_terminal, mock_game_state_manager, mock_effect_manager):
    from command_handler import MSF_SIMULATED_MODULES
    player_role = ROLE_GREY_HAT
    current_module = MSF_SIMULATED_MODULES[0] # "exploit/windows/smb/ms08_067_netapi"
    _set_current_msf_module_for_test(mock_terminal, current_module)

    _handle_msf_show_options("", mock_terminal, mock_game_state_manager, mock_effect_manager, player_role)
    mock_terminal.add_line.assert_any_call(f"\nModule options ({current_module}):", style_key='highlight')
    mock_terminal.add_line.assert_any_call("   RHOSTS                    yes       The target address range or CIDR identifier")


def test_handle_msf_show_options_no_module_selected(mock_terminal, mock_game_state_manager, mock_effect_manager):
    player_role = ROLE_GREY_HAT
    _set_current_msf_module_for_test(mock_terminal, None)
    _handle_msf_show_options("", mock_terminal, mock_game_state_manager, mock_effect_manager, player_role)
    mock_terminal.add_line.assert_called_with("No module selected. Use 'use <module>' first.", style_key='error')

def test_handle_msf_set_valid_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    player_role = ROLE_GREY_HAT
    args = "RHOSTS 192.168.1.100"
    _handle_msf_set(args, mock_terminal, mock_game_state_manager, mock_effect_manager, player_role)
    mock_terminal.add_line.assert_called_once_with("RHOSTS => 192.168.1.100")

def test_handle_msf_set_invalid_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    player_role = ROLE_GREY_HAT
    _handle_msf_set("RHOSTS_ONLY", mock_terminal, mock_game_state_manager, mock_effect_manager, player_role)
    mock_terminal.add_line.assert_called_once_with("Usage: set <option> <value>", style_key='error')

    mock_terminal.reset_mock()
    _handle_msf_set("", mock_terminal, mock_game_state_manager, mock_effect_manager, player_role)
    mock_terminal.add_line.assert_called_once_with("Usage: set <option> <value>", style_key='error')


def test_handle_msf_run_exploit_grey_hat_module_selected(mock_terminal, mock_game_state_manager, mock_effect_manager):
    from command_handler import MSF_SIMULATED_MODULES, get_current_theme
    player_role = ROLE_GREY_HAT
    current_module = MSF_SIMULATED_MODULES[0] # "exploit/windows/smb/ms08_067_netapi"
    _set_current_msf_module_for_test(mock_terminal, current_module)
    mock_game_state_manager.get_player_role.return_value = player_role
    
    # Mock get_current_theme as it's used by the on_complete_callback for meterpreter prompt
    with patch('command_handler.get_current_theme', return_value={'prompt': (0,255,0)}):
        _handle_msf_run_exploit("", mock_terminal, mock_game_state_manager, mock_effect_manager, player_role)

    mock_terminal.add_line.assert_any_call(f"[*] Started reverse TCP handler on 10.0.2.15:4444", style_key='highlight')
    mock_effect_manager.start_typing_effect.assert_called_once()
    # Check the on_complete_callback of the typing effect
    args, kwargs = mock_effect_manager.start_typing_effect.call_args
    on_complete_callback = kwargs.get('on_complete_callback')
    assert callable(on_complete_callback)
    # Execute the callback to ensure it calls add_line for meterpreter prompt
    on_complete_callback()
    mock_terminal.add_line.assert_any_call("meterpreter > ", fg_color=(0,255,0))


def test_handle_msf_run_exploit_white_hat_permission_denied(mock_terminal, mock_game_state_manager, mock_effect_manager):
    player_role = ROLE_WHITE_HAT
    _set_current_msf_module_for_test(mock_terminal, "exploit/dummy") # Module selected
    mock_game_state_manager.get_player_role.return_value = player_role

    _handle_msf_run_exploit("", mock_terminal, mock_game_state_manager, mock_effect_manager, player_role)
    mock_terminal.add_line.assert_called_once_with("msf6> Command 'run'/'exploit' not permitted for White Hat alignment.", style_key='error')
    mock_effect_manager.start_typing_effect.assert_not_called()

def test_handle_msf_run_exploit_no_module_selected(mock_terminal, mock_game_state_manager, mock_effect_manager):
    player_role = ROLE_GREY_HAT
    _set_current_msf_module_for_test(mock_terminal, None) # No module
    mock_game_state_manager.get_player_role.return_value = player_role

    _handle_msf_run_exploit("", mock_terminal, mock_game_state_manager, mock_effect_manager, player_role)
    mock_terminal.add_line.assert_called_once_with("No module selected or exploit context not set.", style_key='error')


def test_handle_msf_sessions_list_active(mock_terminal, mock_game_state_manager, mock_effect_manager):
    player_role = ROLE_GREY_HAT
    # Simulate a session opened line in buffer
    mock_terminal.buffer = [("Previous command output", {}), ("Meterpreter session 1 opened (10.0.2.15:4444 -> 192.168.1.100:1028)", {'style_key': 'success'})]
    
    _handle_msf_sessions("-l", mock_terminal, mock_game_state_manager, mock_effect_manager, player_role)
    mock_terminal.add_line.assert_any_call("\nActive sessions", style_key="highlight")
    mock_terminal.add_line.assert_any_call("  1   meterpreter  NT AUTHORITY\\SYSTEM @ VICTIMPC  10.0.2.15:4444 -> 192.168.1.100:1028 (192.168.1.100)")

def test_handle_msf_sessions_list_no_active(mock_terminal, mock_game_state_manager, mock_effect_manager):
    player_role = ROLE_GREY_HAT
    mock_terminal.buffer = [] # No session line
    _handle_msf_sessions("-l", mock_terminal, mock_game_state_manager, mock_effect_manager, player_role)
    mock_terminal.add_line.assert_called_with("No active sessions.")

    mock_terminal.reset_mock()
    mock_terminal.buffer = []
    _handle_msf_sessions("", mock_terminal, mock_game_state_manager, mock_effect_manager, player_role) # No args also lists
    mock_terminal.add_line.assert_called_with("No active sessions.")


def test_handle_msf_sessions_interact_placeholder(mock_terminal, mock_game_state_manager, mock_effect_manager):
    player_role = ROLE_GREY_HAT
    _handle_msf_sessions("-i 1", mock_terminal, mock_game_state_manager, mock_effect_manager, player_role)
    mock_terminal.add_line.assert_called_with("Session interaction not fully implemented. Example: sessions -i 1", style_key="highlight")

def test_handle_msf_sessions_invalid_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    player_role = ROLE_GREY_HAT
    _handle_msf_sessions("-x", mock_terminal, mock_game_state_manager, mock_effect_manager, player_role)
    mock_terminal.add_line.assert_called_with("Usage: sessions [-l | -i <id>]", style_key="error")


# --- Tests for process_msfconsole_command ---

def test_process_msfconsole_command_dispatch_exit(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_specific_handler = MagicMock()
    with patch.dict(MSF_COMMAND_HANDLERS, {'exit': mock_specific_handler}):
        process_msfconsole_command("exit", mock_terminal, mock_game_state_manager, mock_effect_manager)
        mock_specific_handler.assert_called_once()

def test_process_msfconsole_command_dispatch_use_with_args(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_specific_handler = MagicMock()
    with patch.dict(MSF_COMMAND_HANDLERS, {'use': mock_specific_handler}):
        module_name = "exploit/windows/smb/ms08_067_netapi"
        process_msfconsole_command(f"use {module_name}", mock_terminal, mock_game_state_manager, mock_effect_manager)
        expected_player_role = mock_game_state_manager.get_player_role()
        mock_specific_handler.assert_called_once_with(module_name, mock_terminal, mock_game_state_manager, mock_effect_manager, expected_player_role)

def test_process_msfconsole_command_unknown(mock_terminal, mock_game_state_manager, mock_effect_manager):
    command = "nonexistent_msf_cmd"
    process_msfconsole_command(command, mock_terminal, mock_game_state_manager, mock_effect_manager)
    mock_terminal.add_line.assert_called_with(f"msf6> Unknown command: {command}", style_key='error')

def test_process_msfconsole_command_role_permission_denied_for_run(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_game_state_manager.get_player_role.return_value = ROLE_WHITE_HAT # White Hat cannot run/exploit
    
    # Ensure 'run' is in MSF_COMMAND_HANDLERS for the dispatch logic to reach the permission check
    # The actual _handle_msf_run_exploit also has a check, but process_msfconsole_command has one too.
    # We are testing the dispatcher's check here.
    original_run_handler = MSF_COMMAND_HANDLERS.get("run") # Save original if needed, though not strictly for this test
    
    # We don't need to mock the handler itself, just ensure the command is recognized by the dispatcher
    # and then denied by the role check within process_msfconsole_command.
    if "run" in MSF_COMMAND_HANDLERS:
        process_msfconsole_command("run", mock_terminal, mock_game_state_manager, mock_effect_manager)
        mock_terminal.add_line.assert_called_with(
            "msf6> Command 'run' not available for your current operational alignment.",
            style_key='error'
        )
    else:
        pytest.fail("'run' command not found in MSF_COMMAND_HANDLERS for testing permission denial.")

def test_process_msfconsole_command_role_permission_allowed_for_search_white_hat(mock_terminal, mock_game_state_manager, mock_effect_manager):
    mock_game_state_manager.get_player_role.return_value = ROLE_WHITE_HAT # White Hat can search
    mock_search_handler = MagicMock()
    
    with patch.dict(MSF_COMMAND_HANDLERS, {'search': mock_search_handler}):
        process_msfconsole_command("search eternalblue", mock_terminal, mock_game_state_manager, mock_effect_manager)
        mock_search_handler.assert_called_once_with(
            "eternalblue", mock_terminal, mock_game_state_manager, mock_effect_manager, ROLE_WHITE_HAT
        )
        # Ensure no permission denied message
        for call_args in mock_terminal.add_line.call_args_list:
            assert "not available for your current operational alignment" not in call_args[0][0]

def test_process_msfconsole_command_exit_back_help_always_allowed(mock_terminal, mock_game_state_manager, mock_effect_manager):
    # Even if a role (e.g., a hypothetical restricted one) doesn't list 'exit', 'back', or 'help'
    # in its allowed_msf commands, they should still work.
    mock_game_state_manager.get_player_role.return_value = ROLE_WHITE_HAT # White hat might not list them explicitly but they are universal
    
    mock_exit_handler = MagicMock()
    mock_help_handler = MagicMock()

    with patch.dict(MSF_COMMAND_HANDLERS, {'exit': mock_exit_handler, 'help': mock_help_handler}):
        # Simulate COMMAND_ACCESS where White Hat doesn't explicitly list 'exit' or 'help'
        # This requires patching COMMAND_ACCESS or ensuring the test setup reflects this.
        # For simplicity, we rely on the logic in process_msfconsole_command that explicitly allows them.
        
        process_msfconsole_command("exit", mock_terminal, mock_game_state_manager, mock_effect_manager)
        mock_exit_handler.assert_called_once()
        
        mock_terminal.reset_mock() # Reset for next command
        mock_exit_handler.reset_mock()

        process_msfconsole_command("help", mock_terminal, mock_game_state_manager, mock_effect_manager)
        mock_help_handler.assert_called_once()

        # Ensure no permission denied message for these commands
        for call_args in mock_terminal.add_line.call_args_list:
            assert "not available for your current operational alignment" not in call_args[0][0]

# --- Tests for MSFConsole Tab Completion ---










# Ensure MSF_SIMULATED_MODULES is available for tests that might use it indirectly
# via the handlers being tested.
# from command_handler import MSF_SIMULATED_MODULES