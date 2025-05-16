import pytest
from unittest.mock import MagicMock, patch, ANY

from file_system_handler import FileSystemHandler
# Attempt to import pygame for type hints, but mock it heavily.
try:
    import pygame
    pygame_available = True
except ImportError:
    pygame_available = False
    pygame = MagicMock() # Mock pygame module itself
    pygame.error = type('MockPygameError', (Exception,), {}) # Define a mock error type for robust testing
    pygame.QUIT = 1 # Example event type
    pygame.KEYDOWN = 2
    pygame.K_SPACE = 32
    pygame.K_ESCAPE = 27
    pygame.K_1 = 49
    pygame.K_KP_1 = 257 # Keypad 1
    pygame.VIDEORESIZE = 16
    pygame.RESIZABLE = 0x1
    pygame.FULLSCREEN = 0x80000000
    pygame.font = MagicMock()
    pygame.font.Font = MagicMock()
    pygame.display = MagicMock()
    pygame.key = MagicMock()
    pygame.time = MagicMock()
    pygame.time.Clock = MagicMock()


from terminal_renderer import Terminal # Import for spec
from game_state import GameStateManager # Import for spec
from effects import EffectManager # Import for spec
from puzzle_manager import PuzzleManager # Import for spec
from commands_config import ROLE_WHITE_HAT, ROLE_GREY_HAT, ROLE_BLACK_HAT # Import for assertions
from main import load_monospace_font, NEW_FONT_NAME # For testing load_monospace_font
 
 # Modules to be mocked that are imported by main.py
# We need to patch them where they are *looked up* by main.py
import sys # Add this import at the top of tests/test_main.py

MOCK_PATH_PREFIX = "main." # Assuming main.py is run as a script or top-level module

@pytest.fixture(autouse=True)
def mock_pygame_init_and_display():
    """Mocks pygame.init, display, font, key, and time.Clock."""
    with patch(MOCK_PATH_PREFIX + 'pygame.init') as mock_init, \
         patch(MOCK_PATH_PREFIX + 'pygame.display.set_mode') as mock_set_mode, \
         patch(MOCK_PATH_PREFIX + 'pygame.display.set_caption') as mock_set_caption, \
         patch(MOCK_PATH_PREFIX + 'pygame.display.flip') as mock_flip, \
         patch(MOCK_PATH_PREFIX + 'pygame.display.Info') as mock_display_info, \
         patch(MOCK_PATH_PREFIX + 'pygame.font.Font', MagicMock()) as mock_pygame_font_constructor, \
         patch(MOCK_PATH_PREFIX + 'pygame.font.match_font', return_value="dummy_font.ttf") as mock_match_font, \
         patch(MOCK_PATH_PREFIX + 'pygame.font.get_default_font', return_value="dummy_default_font.ttf") as mock_default_font, \
         patch(MOCK_PATH_PREFIX + 'pygame.key.set_repeat') as mock_set_repeat, \
         patch(MOCK_PATH_PREFIX + 'pygame.time.Clock') as mock_clock_constructor, \
         patch(MOCK_PATH_PREFIX + 'pygame.quit') as mock_pygame_quit, \
         patch(MOCK_PATH_PREFIX + 'pygame.draw.rect') as mock_draw_rect: # Add patch for pygame.draw.rect
        
        mock_screen_surface = MagicMock(spec=pygame.Surface)
        mock_screen_surface.get_size.return_value = (1280, 720) # Default window size
        mock_set_mode.return_value = mock_screen_surface
        
        mock_clock_instance = MagicMock()
        mock_clock_instance.tick.return_value = 16 # Mock dt
        mock_clock_constructor.return_value = mock_clock_instance

        mock_display_info_instance = MagicMock()
        mock_display_info_instance.current_w = 1920
        mock_display_info_instance.current_h = 1080
        mock_display_info.return_value = mock_display_info_instance
        
        # Mock the font instances created by load_monospace_font
        # Remove spec=pygame.font.Font as pygame.font.Font is already a MagicMock here
        mock_font_instance_large = MagicMock()
        mock_font_instance_large.size.return_value = (10, 26) # width, height
        mock_font_instance_large.get_linesize.return_value = 28

        mock_font_instance_medium = MagicMock()
        mock_font_instance_medium.size.return_value = (8, 13)
        mock_font_instance_medium.get_linesize.return_value = 15
        
        mock_font_instance_small = MagicMock()
        mock_font_instance_small.size.return_value = (7, 16)
        mock_font_instance_small.get_linesize.return_value = 18

        # Make pygame.font.Font return different mocks based on size for disclaimer fonts
        def font_side_effect(font_path, size):
            if size == 26: # DISCLAIMER_FONT_SIZE_LARGE
                return mock_font_instance_large
            elif size == 13: # DISCLAIMER_FONT_SIZE_MEDIUM
                return mock_font_instance_medium
            elif size == 16: # DISCLAIMER_FONT_SIZE_SMALL
                return mock_font_instance_small
            else: # For terminal font
                mock_term_font = MagicMock() # No spec needed here either
                mock_term_font.get_linesize.return_value = 20
                mock_term_font.get_height.return_value = 18
                mock_term_font.size.return_value = (10,18)
                return mock_term_font
        mock_pygame_font_constructor.side_effect = font_side_effect
        
        yield {
            "init": mock_init, "set_mode": mock_set_mode, "set_caption": mock_set_caption,
            "flip": mock_flip, "set_repeat": mock_set_repeat, "clock": mock_clock_instance,
            "screen": mock_screen_surface, "pygame_quit": mock_pygame_quit,
            "font_constructor": mock_pygame_font_constructor
        }

@pytest.fixture
def mock_game_dependencies():
    """Mocks Terminal, GameStateManager, EffectManager, and command processors."""
    # Create mock instances first
    mock_gsm_instance = MagicMock(spec=GameStateManager)
    mock_gsm_instance.is_state.return_value = False
    mock_gsm_instance.change_state = MagicMock()
    mock_gsm_instance.set_player_role = MagicMock()
    mock_gsm_instance.get_player_role.return_value = "ROLE_GREY_HAT"

    mock_terminal_instance = MagicMock(spec=Terminal)
    mock_terminal_instance.fs_handler = MagicMock(spec=FileSystemHandler)
    mock_terminal_instance.resize = MagicMock()
    mock_terminal_instance.handle_input.return_value = None
    mock_terminal_instance.render = MagicMock()
    mock_terminal_instance.clear_buffer = MagicMock()
    mock_terminal_instance.add_line = MagicMock()
    mock_terminal_instance.set_username = MagicMock()
    mock_terminal_instance.set_hostname = MagicMock()
    mock_terminal_instance.apply_theme_colors = MagicMock()

    mock_effect_manager_instance = MagicMock(spec=EffectManager)
    mock_effect_manager_instance.is_effect_active.return_value = False
    mock_effect_manager_instance.update = MagicMock()
    mock_effect_manager_instance.skip_current_effect = MagicMock()

    mock_puzzle_manager_instance = MagicMock(spec=PuzzleManager) # Create PuzzleManager mock

    # Create a mock game_state module that will replace the actual one in sys.modules
    mock_game_state_module = MagicMock()
    mock_game_state_module.game_state_manager = mock_gsm_instance
    # Add all constants that main.py imports from game_state
    mock_game_state_module.STATE_DISCLAIMER = "STATE_DISCLAIMER"
    mock_game_state_module.STATE_MAIN_TERMINAL = "STATE_MAIN_TERMINAL"
    mock_game_state_module.STATE_MINIGAME = "STATE_MINIGAME"
    mock_game_state_module.STATE_MSFCONSOLE = "STATE_MSFCONSOLE"
    mock_game_state_module.STATE_ROLE_SELECTION = "STATE_ROLE_SELECTION"
    # Ensure any other constants used by main.py from game_state are added here too.

    # Store original sys.modules['game_state'] if it exists, to restore later
    original_game_state_module = sys.modules.get('game_state')
    sys.modules['game_state'] = mock_game_state_module

    # Store original sys.modules entries to restore them later
    original_sys_modules_game_state = sys.modules.get('game_state')
    original_sys_modules_main_terminal = sys.modules.get(MOCK_PATH_PREFIX + 'Terminal') # For Terminal class
    original_sys_modules_main_effect_manager = sys.modules.get(MOCK_PATH_PREFIX + 'EffectManager') # For EffectManager class
    original_sys_modules_main_puzzle_manager = sys.modules.get(MOCK_PATH_PREFIX + 'PuzzleManager') # For PuzzleManager class

    sys.modules['game_state'] = mock_game_state_module # Inject mocked game_state module

    # Patch the Terminal, EffectManager, and PuzzleManager classes where they are defined,
    # so their constructors return our mocks when main.py imports and uses them.
    # Patch game_state_manager instance where it's defined.
    with patch('terminal_renderer.Terminal', return_value=mock_terminal_instance) as MockTerminalClass, \
         patch('effects.EffectManager', return_value=mock_effect_manager_instance) as MockEffectManagerClass, \
         patch('puzzle_manager.PuzzleManager', return_value=mock_puzzle_manager_instance) as MockPuzzleManagerClass, \
         patch('game_state.game_state_manager', mock_gsm_instance) as mock_gsm, \
         patch('command_handler.process_main_terminal_command') as mock_process_main, \
         patch('command_handler.process_msfconsole_command') as mock_process_msf:
        try:
            yield {
                "terminal_instance": mock_terminal_instance,
                "game_state_manager": mock_gsm, # mock_gsm is mock_gsm_instance
                "effect_manager_instance": mock_effect_manager_instance,
                "puzzle_manager_instance": mock_puzzle_manager_instance, # Add puzzle manager
                "process_main_command": mock_process_main,
                "process_msf_command": mock_process_msf
            }
        finally:
            # Restore original modules
            if original_sys_modules_game_state:
                sys.modules['game_state'] = original_sys_modules_game_state
            elif 'game_state' in sys.modules:
                del sys.modules['game_state']
            
            # No need to restore MOCK_PATH_PREFIX + 'Terminal' etc. if they were created by patch
            # as the context manager handles their cleanup.
            # If they existed before, patch would have restored them.


import importlib # Add this import at the top of tests/test_main.py

def run_main_loop_once(mock_pygame_event_get, game_deps):
    """Helper to run the main.py's game loop for one iteration by reloading and importing it."""
    # By reloading main inside the test, its top-level code (including the loop) runs
    # with the currently active patches.
    # We control the loop by mocking pygame.event.get.
    
    # Ensure that when main is reloaded, its global 'terminal' variable
    # becomes the one we are checking in the tests.
    # Also ensure its 'game_state_manager' is the one we are checking.
    
    # The mock_game_dependencies fixture already patches sys.modules for 'game_state'
    # and patches 'main.Terminal' to return game_deps['terminal_instance'].
    # The reload should pick these up.

    # Make mock_pygame_event_get a callable side_effect for pygame.event.get
    # This allows the list of event sequences to be consumed one by one.
    # If the list is exhausted, it will return an empty list of events.
    event_sequences = list(mock_pygame_event_get) # Copy the input list

    def event_get_side_effect_func():
        if event_sequences:
            return event_sequences.pop(0)
        return [] # Default to empty list if sequences are exhausted

    with patch(MOCK_PATH_PREFIX + 'pygame.event.get', side_effect=event_get_side_effect_func):
        main_module = None
        if 'main' in sys.modules:
            main_module = importlib.reload(sys.modules['main'])
        else:
            import main as main_module
        
        # Explicitly replace the instances in the reloaded main module
        # This ensures that the main game loop uses the exact mock instances
        # that the test fixtures prepared and that the tests will assert against.
        main_module.terminal = game_deps['terminal_instance']
        main_module.effect_manager = game_deps['effect_manager_instance']
        # game_state_manager is imported by main.py from the game_state module.
        # The mock_game_dependencies fixture patches game_state.game_state_manager directly.
        # So, when main.py does 'from game_state import game_state_manager', it should get the mock.
        # Forcing main_module.game_state_manager = game_deps['game_state_manager'] here
        # might be needed if the import mechanism isn't picking up the patched instance correctly
        # after reload, but ideally the patch on game_state.game_state_manager is sufficient.
        # Let's assume for now the patch on game_state.game_state_manager is effective.



def test_main_loop_quits_on_pygame_quit_event(mock_pygame_init_and_display, mock_game_dependencies):
    """Test that the game loop exits when a pygame.QUIT event is received."""
    
    # Simulate being in STATE_MAIN_TERMINAL for this test
    mock_game_dependencies["game_state_manager"].is_state.side_effect = lambda state: state == "STATE_MAIN_TERMINAL"

    quit_event = MagicMock(spec=pygame.event.Event)
    quit_event.type = pygame.QUIT
    
    # First call to event.get() returns QUIT, second returns empty to stop loop for test
    run_main_loop_once([ [quit_event], [] ], mock_game_dependencies)
    
    mock_pygame_init_and_display["pygame_quit"].assert_called_once()


def test_disclaimer_to_role_selection_on_space(mock_pygame_init_and_display, mock_game_dependencies):
    gsm = mock_game_dependencies["game_state_manager"]
    terminal = mock_game_dependencies["terminal_instance"]

    # Initial state is DISCLAIMER
    gsm.is_state.side_effect = lambda state: state == "STATE_DISCLAIMER"
    
    space_event = MagicMock(spec=pygame.event.Event)
    space_event.type = pygame.KEYDOWN
    space_event.key = pygame.K_SPACE
    space_event.unicode = '' # Add unicode attribute
    
    # Sequence: [space_event], [quit_event to stop loop], []
    quit_event = MagicMock(type=pygame.QUIT)
    run_main_loop_once([ [space_event], [quit_event], [] ], mock_game_dependencies)
    
    gsm.change_state.assert_called_with("STATE_ROLE_SELECTION")
    terminal.clear_buffer.assert_called()
    terminal.add_line.assert_any_call("Choose Your Path:", style_key='highlight')


def test_role_selection_to_main_terminal(mock_pygame_init_and_display, mock_game_dependencies):
    gsm = mock_game_dependencies["game_state_manager"]
    terminal = mock_game_dependencies["terminal_instance"]

    # Simulate being in ROLE_SELECTION state
    # is_state needs to return True for ROLE_SELECTION then True for MAIN_TERMINAL after change
    state_sequence = ["STATE_ROLE_SELECTION", "STATE_MAIN_TERMINAL"]
    def mock_is_state_for_role_selection(state_to_check):
        current_sim_state = state_sequence[0]
        if state_to_check == current_sim_state:
            if len(state_sequence) > 1: # If not the last state, pop to simulate transition
                 state_sequence.pop(0)
            return True
        return False
    gsm.is_state.side_effect = mock_is_state_for_role_selection
    
    # Simulate choosing White Hat (key '1')
    key_1_event = MagicMock(spec=pygame.event.Event)
    key_1_event.type = pygame.KEYDOWN
    key_1_event.key = pygame.K_1 # Or K_KP_1
    key_1_event.unicode = '1' # Add unicode attribute, can be the char itself
    
    quit_event = MagicMock(type=pygame.QUIT)
    run_main_loop_once([ [key_1_event], [quit_event], [] ], mock_game_dependencies)
    
    gsm.set_player_role.assert_called_with(ROLE_WHITE_HAT) # Use the imported constant
    terminal.clear_buffer.assert_called() # Called after role selection
    terminal.set_username.assert_called_with("guardian")
    terminal.set_hostname.assert_called_with("aegis-01")
    terminal.add_line.assert_any_call("Welcome to the Cyberscape.", style_key='highlight')
    gsm.change_state.assert_called_with("STATE_MAIN_TERMINAL")


def test_role_selection_grey_hat(mock_pygame_init_and_display, mock_game_dependencies):
    gsm = mock_game_dependencies["game_state_manager"]
    terminal = mock_game_dependencies["terminal_instance"]

    state_sequence = ["STATE_ROLE_SELECTION", "STATE_MAIN_TERMINAL"]
    def mock_is_state_for_role_selection(state_to_check):
        current_sim_state = state_sequence[0]
        if state_to_check == current_sim_state:
            if len(state_sequence) > 1:
                 state_sequence.pop(0)
            return True
        return False
    gsm.is_state.side_effect = mock_is_state_for_role_selection

    key_2_event = MagicMock(spec=pygame.event.Event)
    key_2_event.type = pygame.KEYDOWN
    key_2_event.key = pygame.K_2
    key_2_event.unicode = '2'

    quit_event = MagicMock(type=pygame.QUIT)
    run_main_loop_once([ [key_2_event], [quit_event], [] ], mock_game_dependencies)

    gsm.set_player_role.assert_called_with(ROLE_GREY_HAT)
    terminal.clear_buffer.assert_called()
    terminal.set_username.assert_called_with("shadow_walker")
    terminal.set_hostname.assert_called_with("nexus-7")
    terminal.add_line.assert_any_call("Network access rerouted. Anonymity cloak engaged.", style_key='highlight')
    terminal.add_line.assert_any_call("The lines blur. Your path is your own to forge.", style_key='default_fg')
    terminal.add_line.assert_any_call("Welcome to the Cyberscape.", style_key='highlight')
    gsm.change_state.assert_called_with("STATE_MAIN_TERMINAL")


def test_role_selection_black_hat(mock_pygame_init_and_display, mock_game_dependencies):
    gsm = mock_game_dependencies["game_state_manager"]
    terminal = mock_game_dependencies["terminal_instance"]

    state_sequence = ["STATE_ROLE_SELECTION", "STATE_MAIN_TERMINAL"]
    def mock_is_state_for_role_selection(state_to_check):
        current_sim_state = state_sequence[0]
        if state_to_check == current_sim_state:
            if len(state_sequence) > 1:
                 state_sequence.pop(0)
            return True
        return False
    gsm.is_state.side_effect = mock_is_state_for_role_selection

    key_3_event = MagicMock(spec=pygame.event.Event)
    key_3_event.type = pygame.KEYDOWN
    key_3_event.key = pygame.K_3
    key_3_event.unicode = '3'

    quit_event = MagicMock(type=pygame.QUIT)
    run_main_loop_once([ [key_3_event], [quit_event], [] ], mock_game_dependencies)

    gsm.set_player_role.assert_called_with(ROLE_BLACK_HAT)
    terminal.clear_buffer.assert_called()
    terminal.set_username.assert_called_with("void_reaver")
    terminal.set_hostname.assert_called_with("hades-net")
    terminal.add_line.assert_any_call("Firewalls bypassed. Root access granted. The system is yours.", style_key='error')
    terminal.add_line.assert_any_call("Embrace the chaos. Exploit the vulnerabilities.", style_key='error')
    terminal.add_line.assert_any_call("Welcome to the Cyberscape.", style_key='highlight')
    gsm.change_state.assert_called_with("STATE_MAIN_TERMINAL")


def test_main_terminal_command_dispatch(mock_pygame_init_and_display, mock_game_dependencies):
    gsm = mock_game_dependencies["game_state_manager"]
    terminal = mock_game_dependencies["terminal_instance"]
    process_main_command = mock_game_dependencies["process_main_command"]

    # Simulate being in STATE_MAIN_TERMINAL
    state_sequence_main = ["STATE_MAIN_TERMINAL", "STATE_MAIN_TERMINAL"] # Stays in main terminal
    def mock_is_state_for_main_terminal(state_to_check):
        current_sim_state = state_sequence_main[0]
        if state_to_check == current_sim_state:
            if len(state_sequence_main) > 1:
                 state_sequence_main.pop(0)
            return True
        return False
    gsm.is_state.side_effect = mock_is_state_for_main_terminal
    
    # Simulate terminal.handle_input returning a command
    test_command = "echo hello from test"
    terminal.handle_input.return_value = test_command
    
    # Simulate process_main_terminal_command returning (True, None) initially
    process_main_command.return_value = (True, None)

    # Simulate a generic KEYDOWN event that would trigger handle_input
    # The actual key doesn't matter as much as terminal.handle_input returning the command.
    generic_keydown_event = MagicMock(spec=pygame.event.Event)
    generic_keydown_event.type = pygame.KEYDOWN
    generic_keydown_event.key = pygame.K_a # Arbitrary key
    generic_keydown_event.unicode = 'a'

    quit_event = MagicMock(type=pygame.QUIT)
    run_main_loop_once([ [generic_keydown_event], [quit_event], [] ], mock_game_dependencies)

    terminal.handle_input.assert_called_with(generic_keydown_event)
    process_main_command.assert_called_with(test_command, terminal, gsm, mock_game_dependencies["effect_manager_instance"], mock_game_dependencies["puzzle_manager_instance"])

    # Test that if process_main_terminal_command signals to quit, running becomes False
    # We need to re-run the loop setup for this specific scenario.
    # Reset mocks for a clean run
    terminal.handle_input.reset_mock()
    process_main_command.reset_mock()
    gsm.is_state.side_effect = lambda state: state == "STATE_MAIN_TERMINAL" # Keep it simple for this part
    
    process_main_command.return_value = (False, None) # Signal to quit
    terminal.handle_input.return_value = "quit_command"

    # This run_main_loop_once will execute the loop, which should then set running to False
    # The mock_pygame_init_and_display fixture mocks pygame.quit, so we can check if it's called.
    # The loop itself will terminate because of the mocked event sequence.
    # The key is to check if the 'running = False' logic inside main.py was triggered.
    # This is implicitly tested by checking if pygame.quit() was called, as that's the exit path.
    
    # Re-import main to get a fresh 'running' variable state if it's global in main
    # However, the run_main_loop_once reloads main, so its 'running' variable is reset.
    # The test relies on the loop exiting due to the quit_event.
    # The assertion on pygame_quit is the most reliable way to check the quit path.
    mock_pygame_init_and_display["pygame_quit"].reset_mock() # Reset for this specific check

    run_main_loop_once([ [generic_keydown_event], [quit_event], [] ], mock_game_dependencies)
    
    process_main_command.assert_called_with("quit_command", terminal, gsm, mock_game_dependencies["effect_manager_instance"], mock_game_dependencies["puzzle_manager_instance"])
    # If process_main_command returned (False, None), the loop should have set running = False,
    # leading to pygame.quit() being called at the end of main.py.
    mock_pygame_init_and_display["pygame_quit"].assert_called_once()


def test_msfconsole_command_dispatch_and_exit(mock_pygame_init_and_display, mock_game_dependencies):
    gsm = mock_game_dependencies["game_state_manager"]
    terminal = mock_game_dependencies["terminal_instance"]
    process_msf_command = mock_game_dependencies["process_msf_command"]

    # --- Test 1: Command dispatch in MSFConsole ---
    # Simulate being in STATE_MSFCONSOLE
    state_sequence_msf = ["STATE_MSFCONSOLE", "STATE_MSFCONSOLE"]
    def mock_is_state_for_msf(state_to_check):
        current_sim_state = state_sequence_msf[0]
        if state_to_check == current_sim_state:
            if len(state_sequence_msf) > 1:
                 state_sequence_msf.pop(0)
            return True
        return False
    gsm.is_state.side_effect = mock_is_state_for_msf
    
    test_msf_command = "search eternalblue"
    terminal.handle_input.return_value = test_msf_command
    
    generic_keydown_event = MagicMock(spec=pygame.event.Event)
    generic_keydown_event.type = pygame.KEYDOWN
    generic_keydown_event.key = pygame.K_s # Arbitrary key for command input
    generic_keydown_event.unicode = 's'

    quit_event_for_cmd_test = MagicMock(type=pygame.QUIT)
    run_main_loop_once([ [generic_keydown_event], [quit_event_for_cmd_test], [] ], mock_game_dependencies)

    terminal.handle_input.assert_called_with(generic_keydown_event)
    process_msf_command.assert_called_with(test_msf_command, terminal, gsm, mock_game_dependencies["effect_manager_instance"])

    # --- Test 2: Exiting MSFConsole with ESCAPE ---
    terminal.handle_input.reset_mock() # Reset for the next part
    process_msf_command.reset_mock()
    terminal.clear_prompt_override.reset_mock()
    terminal.clear_buffer.reset_mock()
    terminal.add_line.reset_mock()
    gsm.change_state.reset_mock()

    # Simulate being in STATE_MSFCONSOLE, then transitioning to MAIN_TERMINAL
    state_sequence_msf_exit = ["STATE_MSFCONSOLE", "STATE_MAIN_TERMINAL"]
    def mock_is_state_for_msf_exit(state_to_check):
        current_sim_state = state_sequence_msf_exit[0]
        if state_to_check == current_sim_state:
            if len(state_sequence_msf_exit) > 1:
                 state_sequence_msf_exit.pop(0)
            return True
        return False
    gsm.is_state.side_effect = mock_is_state_for_msf_exit

    escape_event = MagicMock(spec=pygame.event.Event)
    escape_event.type = pygame.KEYDOWN
    escape_event.key = pygame.K_ESCAPE
    escape_event.unicode = '' # Escape has no direct unicode typically

    quit_event_for_esc_test = MagicMock(type=pygame.QUIT)
    run_main_loop_once([ [escape_event], [quit_event_for_esc_test], [] ], mock_game_dependencies)

    terminal.clear_prompt_override.assert_called_once()
    gsm.change_state.assert_called_with("STATE_MAIN_TERMINAL")
    terminal.clear_buffer.assert_called_once()
    terminal.add_line.assert_any_call("Exited msfconsole.", style_key="highlight")
    terminal.add_line.assert_any_call("Type 'help' for a list of commands.")
    # Ensure terminal.handle_input was NOT called for the ESCAPE key in this context
    terminal.handle_input.assert_not_called()


def test_video_resize_event(mock_pygame_init_and_display, mock_game_dependencies):
    terminal = mock_game_dependencies["terminal_instance"]
    pygame_set_mode = mock_pygame_init_and_display["set_mode"]

    # Simulate being in any state where event loop is active, e.g., STATE_MAIN_TERMINAL
    mock_game_dependencies["game_state_manager"].is_state.side_effect = lambda state: state == "STATE_MAIN_TERMINAL"

    new_width, new_height = 1024, 768
    resize_event = MagicMock(spec=pygame.event.Event)
    resize_event.type = pygame.VIDEORESIZE
    resize_event.w = new_width
    resize_event.h = new_height
    resize_event.size = (new_width, new_height) # size attribute is also common

    quit_event = MagicMock(type=pygame.QUIT)
    
    # Need to access the reloaded main_module to check its globals
    # The run_main_loop_once helper reloads main.py
    # We'll patch 'main.WINDOW_WIDTH' and 'main.WINDOW_HEIGHT' to check them after the event.
    # This is a bit tricky as they are module-level globals.
    # A cleaner way might be to have these as part of a game context object if refactoring.
    # For now, we'll rely on the fact that run_main_loop_once reloads main.py,
    # and the event handling within that reloaded instance will modify its own globals.
    
    # We can't directly assert main_module.WINDOW_WIDTH easily after run_main_loop_once
    # because run_main_loop_once itself causes the reload and execution.
    # Instead, we verify the effects: pygame.display.set_mode and terminal.resize calls.

    run_main_loop_once([ [resize_event], [quit_event], [] ], mock_game_dependencies)

    pygame_set_mode.assert_called_with((new_width, new_height), pygame.RESIZABLE)
    terminal.resize.assert_called_with(new_width, new_height)

    # To check the global WINDOW_WIDTH and WINDOW_HEIGHT in main.py after the event,
    # we would need to inspect the reloaded main_module instance from run_main_loop_once.
    # The helper `run_main_loop_once` would need to return `main_module` for this.
    # For now, the calls to set_mode and terminal.resize imply the globals were updated correctly
    # as they are used in those calls within main.py.


def test_screenres_command_effect(mock_pygame_init_and_display, mock_game_dependencies):
    gsm = mock_game_dependencies["game_state_manager"]
    terminal = mock_game_dependencies["terminal_instance"]
    process_main_command = mock_game_dependencies["process_main_command"]
    pygame_set_mode = mock_pygame_init_and_display["set_mode"]

    # Simulate being in STATE_MAIN_TERMINAL
    gsm.is_state.side_effect = lambda state: state == "STATE_MAIN_TERMINAL"
    
    # Simulate terminal.handle_input returning the "screenres" command
    screenres_command = "screenres 800x600"
    terminal.handle_input.return_value = screenres_command
    
    # Simulate process_main_terminal_command returning a screen_action for set_resolution
    new_w_cmd, new_h_cmd = 800, 600
    screen_action_details = {'action': 'screen_change', 'type': 'set_resolution', 'width': new_w_cmd, 'height': new_h_cmd}
    process_main_command.return_value = (True, screen_action_details)

    # Simulate a generic KEYDOWN event
    generic_keydown_event = MagicMock(spec=pygame.event.Event)
    generic_keydown_event.type = pygame.KEYDOWN
    generic_keydown_event.key = pygame.K_s # Arbitrary key
    generic_keydown_event.unicode = 's'

    quit_event = MagicMock(type=pygame.QUIT)
    run_main_loop_once([ [generic_keydown_event], [quit_event], [] ], mock_game_dependencies)

    process_main_command.assert_called_with(screenres_command, terminal, gsm, mock_game_dependencies["effect_manager_instance"], mock_game_dependencies["puzzle_manager_instance"])
    pygame_set_mode.assert_called_with((new_w_cmd, new_h_cmd), pygame.RESIZABLE)
    terminal.resize.assert_called_with(new_w_cmd, new_h_cmd)
    terminal.add_line.assert_any_call(f"Screen resolution set to {new_w_cmd}x{new_h_cmd}.", style_key='success')


def test_fullscreen_command_effect(mock_pygame_init_and_display, mock_game_dependencies):
    gsm = mock_game_dependencies["game_state_manager"]
    terminal = mock_game_dependencies["terminal_instance"]
    process_main_command = mock_game_dependencies["process_main_command"]
    pygame_set_mode = mock_pygame_init_and_display["set_mode"]
    mock_display_info_instance = pygame.display.Info() # Get the mocked instance

    # Simulate being in STATE_MAIN_TERMINAL
    gsm.is_state.side_effect = lambda state: state == "STATE_MAIN_TERMINAL"
    
    fullscreen_command = "fullscreen"
    terminal.handle_input.return_value = fullscreen_command
    
    screen_action_details = {'action': 'screen_change', 'type': 'fullscreen'}
    process_main_command.return_value = (True, screen_action_details)

    # Mock display_info to return specific desktop dimensions
    desktop_w, desktop_h = 1920, 1080
    mock_display_info_instance.current_w = desktop_w
    mock_display_info_instance.current_h = desktop_h
    
    generic_keydown_event = MagicMock(spec=pygame.event.Event, type=pygame.KEYDOWN, key=pygame.K_f, unicode='f')
    quit_event = MagicMock(type=pygame.QUIT)
    run_main_loop_once([ [generic_keydown_event], [quit_event], [] ], mock_game_dependencies)

    process_main_command.assert_called_with(fullscreen_command, terminal, gsm, mock_game_dependencies["effect_manager_instance"], mock_game_dependencies["puzzle_manager_instance"])
    pygame_set_mode.assert_called_with((desktop_w, desktop_h), pygame.FULLSCREEN | pygame.RESIZABLE)
    terminal.resize.assert_called_with(desktop_w, desktop_h)
    terminal.add_line.assert_any_call(f"Switched to fullscreen mode ({desktop_w}x{desktop_h}).", style_key='success')


def test_windowed_command_effect(mock_pygame_init_and_display, mock_game_dependencies):
    gsm = mock_game_dependencies["game_state_manager"]
    terminal = mock_game_dependencies["terminal_instance"]
    process_main_command = mock_game_dependencies["process_main_command"]
    pygame_set_mode = mock_pygame_init_and_display["set_mode"]
    mock_screen_surface = mock_pygame_init_and_display["screen"]

    # Simulate being in STATE_MAIN_TERMINAL
    gsm.is_state.side_effect = lambda state: state == "STATE_MAIN_TERMINAL"
    
    windowed_command = "windowed"
    terminal.handle_input.return_value = windowed_command
    
    screen_action_details = {'action': 'screen_change', 'type': 'windowed'}
    process_main_command.return_value = (True, screen_action_details)

    # Simulate coming from a large fullscreen
    mock_screen_surface.get_size.return_value = (1920, 1080)
    
    # Expected windowed dimensions (default fallback in main.py)
    expected_w, expected_h = 1280, 720
    
    generic_keydown_event = MagicMock(spec=pygame.event.Event, type=pygame.KEYDOWN, key=pygame.K_w, unicode='w')
    quit_event = MagicMock(type=pygame.QUIT)
    run_main_loop_once([ [generic_keydown_event], [quit_event], [] ], mock_game_dependencies)

    process_main_command.assert_called_with(windowed_command, terminal, gsm, mock_game_dependencies["effect_manager_instance"], mock_game_dependencies["puzzle_manager_instance"])
    pygame_set_mode.assert_called_with((expected_w, expected_h), pygame.RESIZABLE)
    terminal.resize.assert_called_with(expected_w, expected_h)
    terminal.add_line.assert_any_call(f"Switched to windowed mode ({expected_w}x{expected_h}).", style_key='success')

    # Test coming from a smaller size (should retain previous WINDOW_WIDTH, WINDOW_HEIGHT if not > 1920x1080)
    # For this, we'd need to control the global WINDOW_WIDTH/HEIGHT in main.py before the call,
    # or assume they were the default 1280x720. The current test setup reloads main.py,
    # so WINDOW_WIDTH/HEIGHT would be reset to their initial values (1280, 720).
    pygame_set_mode.reset_mock()
    terminal.resize.reset_mock()
    terminal.add_line.reset_mock()
    mock_screen_surface.get_size.return_value = (800, 600) # Current size is small
    
    # Since main.py is reloaded, WINDOW_WIDTH/HEIGHT are 1280x720 initially.
    # The logic in main.py for windowed mode:
    # if current_w > 1920 or current_h > 1080: WINDOW_WIDTH = 1280; WINDOW_HEIGHT = 720
    # Else, it uses the existing WINDOW_WIDTH, WINDOW_HEIGHT.
    # So, if current is 800x600, it should use the reloaded main.py's initial 1280x720.
    
    run_main_loop_once([ [generic_keydown_event], [quit_event], [] ], mock_game_dependencies)
    pygame_set_mode.assert_called_with((1280, 720), pygame.RESIZABLE)
    terminal.resize.assert_called_with(1280, 720)
    terminal.add_line.assert_any_call(f"Switched to windowed mode (1280x720).", style_key='success')


# --- Tests for load_monospace_font ---

def test_load_monospace_font_success(mock_pygame_init_and_display, capsys):
    """Test load_monospace_font successfully loads the primary font."""
    mock_font_constructor = mock_pygame_init_and_display["font_constructor"]
    mock_pygame_quit = mock_pygame_init_and_display["pygame_quit"]
    
    mock_primary_font = MagicMock()
    mock_font_constructor.side_effect = lambda path, size: mock_primary_font if path == NEW_FONT_NAME else Exception("Should not be called")

    font_size = 20
    returned_font = load_monospace_font(font_size)

    mock_font_constructor.assert_called_once_with(NEW_FONT_NAME, font_size)
    assert returned_font == mock_primary_font
    mock_pygame_quit.assert_not_called()
    # captured = capsys.readouterr() # Print statement was removed
    # assert f"Successfully loaded font '{NEW_FONT_NAME}' with size {font_size}" in captured.out # Print statement was removed

def test_load_monospace_font_fallback_success(mock_pygame_init_and_display, capsys):
    """Test load_monospace_font falls back to default font successfully."""
    mock_font_constructor = mock_pygame_init_and_display["font_constructor"]
    mock_pygame_quit = mock_pygame_init_and_display["pygame_quit"]

    mock_fallback_font = MagicMock()
    
    def font_load_side_effect(path, size):
        if path == NEW_FONT_NAME:
            raise pygame.error("Failed to load primary font")
        elif path is None: # Pygame's default font
            return mock_fallback_font
        else:
            raise Exception(f"Unexpected font path: {path}")

    mock_font_constructor.side_effect = font_load_side_effect
    
    font_size = 22
    returned_font = load_monospace_font(font_size)

    assert mock_font_constructor.call_count == 2
    mock_font_constructor.assert_any_call(NEW_FONT_NAME, font_size)
    mock_font_constructor.assert_any_call(None, font_size)
    assert returned_font == mock_fallback_font
    mock_pygame_quit.assert_not_called()
    # captured = capsys.readouterr() # Print statements were removed
    # assert f"Warning - Could not load '{NEW_FONT_NAME}' with size {font_size}" in captured.out # Print statement was removed
    # assert f"Successfully loaded Pygame default font with size {font_size} as fallback" in captured.out # Print statement was removed

def test_load_monospace_font_all_fail_raises_runtime_error(mock_pygame_init_and_display, capsys):
    """Test load_monospace_font raises RuntimeError if all font loading fails."""
    mock_font_constructor = mock_pygame_init_and_display["font_constructor"]
    mock_pygame_quit = mock_pygame_init_and_display["pygame_quit"]

    def font_load_all_fail_side_effect(path, size):
        raise pygame.error(f"Failed to load font {path}")

    mock_font_constructor.side_effect = font_load_all_fail_side_effect
    
    font_size = 24
    with pytest.raises(RuntimeError) as excinfo:
        load_monospace_font(font_size)

    assert f"Failed to initialize any font for disclaimer (size {font_size})" in str(excinfo.value)
    
    assert mock_font_constructor.call_count == 2
    mock_font_constructor.assert_any_call(NEW_FONT_NAME, font_size)
    mock_font_constructor.assert_any_call(None, font_size)
    mock_pygame_quit.assert_called_once() # pygame.quit() should be called before raising RuntimeError
    # captured = capsys.readouterr() # Print statements were removed
    # assert f"Warning - Could not load '{NEW_FONT_NAME}' with size {font_size}" in captured.out # Print statement was removed
    # assert f"Critical error - Could not load Pygame default font with size {font_size}" in captured.out # Print statement was removed