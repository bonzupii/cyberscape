import pytest
import pygame # Added for direct pygame references in tests
from unittest.mock import MagicMock, patch
import effects as effects_module # To manage the global current_theme_name

# Attempt to import specific items; if effects_module itself fails to import
# (e.g., due to pygame issues not handled here), these lines would also fail.
from effects import (
    THEMES,
    get_current_theme,
    set_theme,
    get_theme_color,
    COLOR_WHITE,
    COLOR_GREY_LIGHT,
    COLOR_BLACK,
    COLOR_GREEN_BRIGHT,
    COLOR_RED_BRIGHT,
    COLOR_BLUE_CYAN
)

@pytest.fixture(autouse=True)
def reset_current_theme(monkeypatch):
    """Reset the current_theme_name to 'default' before each test and restore after."""
    original_theme_name = effects_module.current_theme_name
    monkeypatch.setattr(effects_module, 'current_theme_name', 'default')
    yield
    monkeypatch.setattr(effects_module, 'current_theme_name', original_theme_name)

def test_get_current_theme_default():
    """Test that get_current_theme returns the default theme initially."""
    # The fixture ensures current_theme_name is 'default'
    theme = get_current_theme()
    assert theme == THEMES["default"]
    assert theme["name"] == "Default Terminal"
    assert theme["default_fg"] == COLOR_GREY_LIGHT

def test_set_theme_valid():
    """Test setting a valid theme."""
    assert effects_module.current_theme_name == "default"  # Initial state from fixture

    result = set_theme("corrupted_kali")
    assert result is True
    assert effects_module.current_theme_name == "corrupted_kali"

    theme = get_current_theme()
    assert theme == THEMES["corrupted_kali"]
    assert theme["name"] == "Corrupted Kali"

def test_set_theme_invalid(capsys):
    """Test setting an invalid theme name."""
    initial_theme_name = effects_module.current_theme_name # Should be 'default'
    
    result = set_theme("non_existent_theme")
    assert result is False
    # Theme name should not change if an invalid theme is provided
    assert effects_module.current_theme_name == initial_theme_name
    
    # captured = capsys.readouterr() # Print statement was removed
    # assert "Warning: Theme 'non_existent_theme' not found." in captured.out # Print statement was removed

def test_get_theme_color_current_theme():
    """Test getting colors from the current theme."""
    # Fixture sets current theme to "default"
    # Explicitly set for clarity if needed, though fixture handles it
    # set_theme("default") 
    
    fg_color = get_theme_color("default_fg")
    assert fg_color == THEMES["default"]["default_fg"]

    prompt_color = get_theme_color("prompt")
    assert prompt_color == THEMES["default"]["prompt"]

def test_get_theme_color_specific_theme_provided():
    """Test getting colors when a specific theme dictionary is provided."""
    corrupted_theme_dict = THEMES["corrupted_kali"]
    
    fg_color = get_theme_color("default_fg", theme=corrupted_theme_dict)
    assert fg_color == corrupted_theme_dict["default_fg"]

    error_color = get_theme_color("error", theme=corrupted_theme_dict)
    assert error_color == corrupted_theme_dict["error"]

def test_get_theme_color_key_not_found_uses_fallback_current_theme():
    """Test fallback color when a key is not found in the current theme."""
    # Fixture sets current theme to "default"
    color = get_theme_color("this_key_does_not_exist")
    assert color == COLOR_WHITE  # Default fallback color

def test_get_theme_color_key_not_found_uses_fallback_specific_theme():
    """Test fallback color when a key is not found in a provided theme."""
    minimal_theme = {"name": "Minimal"} # A theme without 'default_fg'
    color = get_theme_color("default_fg", theme=minimal_theme)
    assert color == COLOR_WHITE

def test_get_theme_color_theme_is_none_uses_current():
    """Test that if theme=None is passed, it uses the currently set global theme."""
    set_theme("digital_nightmare") # Change current theme
    expected_color = THEMES["digital_nightmare"]["prompt"]
    
    # Call get_theme_color with theme=None
    color = get_theme_color("prompt", theme=None)
    assert color == expected_color

def test_set_theme_affects_get_current_theme_and_get_theme_color():
    """Test that set_theme correctly changes the theme used by get_current_theme and get_theme_color."""
    set_theme("classic_dos")
    
    current_theme_dict = get_current_theme()
    assert current_theme_dict == THEMES["classic_dos"]
    assert current_theme_dict["name"] == "Classic DOS"
    
    prompt_color_classic = get_theme_color("prompt") # Uses current theme (classic_dos)
    assert prompt_color_classic == THEMES["classic_dos"]["prompt"]

    # Change theme back
    set_theme("default")
    current_theme_dict_default = get_current_theme()
    assert current_theme_dict_default == THEMES["default"]
    
    prompt_color_default = get_theme_color("prompt") # Uses current theme (default)
    assert prompt_color_default == THEMES["default"]["prompt"]
from unittest.mock import MagicMock, call

# Import effect classes that need testing
from effects import (
    BaseEffect,
    TypingEffect,
    TimedDelayEffect,
    CharacterCorruptionEffect,
    TextFlickerEffect,
    TemporaryColorChangeEffect,
    TextOverlayEffect,
    TextJiggleEffect,
    EffectManager,
    CORRUPTION_CHARS # if needed for tests directly
)

# Pytest fixture for a mock terminal reference
@pytest.fixture
def mock_terminal_ref(mocker):
    mock = MagicMock()
    mock.buffer = [] # For effects that check buffer length like CharacterCorruptionEffect
    mock.font = MagicMock()
    mock.font.size.return_value = (10, 15) # width, height for a character
    mock.font.get_height.return_value = 15
    mock.font.get_linesize.return_value = 18
    mock.width = 800
    mock.height = 600
    
    # Make add_line return a simulated line index
    mock.add_line_call_count = 0
    def mock_add_line(*args, **kwargs):
        line_idx = len(mock.buffer)
        # Simulate adding to buffer for effects that might rely on its state via terminal
        text_content = args[0] if args else ""
        fg_color = args[1] if len(args) > 1 else None
        bg_color = args[2] if len(args) > 2 else None
        bold = args[3] if len(args) > 3 else False
        mock.buffer.append((text_content, fg_color, bg_color, bold))
        mock.add_line_call_count +=1
        return line_idx
    mock.add_line = MagicMock(side_effect=mock_add_line)

    mock.update_buffer_line = MagicMock()
    
    def mock_get_buffer_line_details(line_index):
        if 0 <= line_index < len(mock.buffer):
            return mock.buffer[line_index]
        # Simulate negative indexing if the effect manager or effect itself doesn't handle it
        if line_index < 0 and abs(line_index) <= len(mock.buffer):
             return mock.buffer[len(mock.buffer) + line_index]
        return None
    mock.get_buffer_line_details = MagicMock(side_effect=mock_get_buffer_line_details)

    return mock

# --- Tests for BaseEffect ---

def test_base_effect_initialization():
    callback = MagicMock()
    effect = BaseEffect(on_complete_callback=callback)
    assert effect.is_active is True
    assert effect.is_complete is False
    assert effect.on_complete_callback == callback

def test_base_effect_finish():
    callback = MagicMock()
    effect = BaseEffect(on_complete_callback=callback)
    effect.finish()
    assert effect.is_active is False
    assert effect.is_complete is True
    callback.assert_called_once()

def test_base_effect_finish_no_callback():
    effect = BaseEffect()
    effect.finish()
    assert effect.is_active is False
    assert effect.is_complete is True
    # No callback to assert

def test_base_effect_update_not_implemented():
    effect = BaseEffect()
    with pytest.raises(NotImplementedError):
        effect.update(10, None)

def test_base_effect_start_default():
    effect = BaseEffect()
    effect.start(None) # Should not raise an error

# --- Tests for TypingEffect ---

def test_typing_effect_initialization():
    callback = MagicMock()
    effect = TypingEffect("test", 50, "fg", "bg", True, callback)
    assert effect.full_text == "test"
    assert effect.char_delay == 50
    assert effect.fg_color == "fg"
    assert effect.bg_color == "bg"
    assert effect.bold is True
    assert effect.on_complete_callback == callback
    assert effect.current_char_index == 0
    assert effect.timer == 0
    assert effect.line_index_in_terminal == -1

def test_typing_effect_start_instant_display(mock_terminal_ref):
    effect = TypingEffect("hello", 0, "fg", "bg", False) # char_delay = 0
    effect.start(mock_terminal_ref)
    
    mock_terminal_ref.add_line.assert_called_once_with("hello", "fg", "bg", False)
    assert effect.current_display_text == "hello"
    assert effect.current_char_index == len("hello")
    assert effect.is_complete is True
    assert effect.is_active is False # finish() sets is_active to False
    assert effect.line_index_in_terminal == 0 # Assuming add_line returns 0 for the first line

def test_typing_effect_start_delayed_display(mock_terminal_ref):
    effect = TypingEffect("hi", 50, "fg", "bg", True)
    effect.start(mock_terminal_ref)

    mock_terminal_ref.add_line.assert_called_once_with("h", "fg", "bg", True) # First char
    assert effect.current_display_text == "h"
    assert effect.current_char_index == 1
    assert effect.is_complete is False
    assert effect.is_active is True
    assert effect.line_index_in_terminal == 0

def test_typing_effect_start_empty_text_delayed(mock_terminal_ref):
    effect = TypingEffect("", 50, "fg", "bg", False)
    effect.start(mock_terminal_ref)
    mock_terminal_ref.add_line.assert_called_once_with("", "fg", "bg", False)
    assert effect.current_display_text == ""
    assert effect.current_char_index == 0
    assert effect.is_complete is False # Will complete in first update if text is empty

def test_typing_effect_start_add_line_fails(mocker, mock_terminal_ref, capsys):
    mocker.patch.object(mock_terminal_ref, 'add_line', return_value=None) # Simulate failure
    effect = TypingEffect("test", 50, "fg", "bg", False)
    effect.start(mock_terminal_ref)
    
    assert effect.is_complete is True # Should finish if add_line fails
    assert effect.is_active is False
    # captured = capsys.readouterr() # Print statement was removed
    # assert f"Error: TypingEffect (delayed, non-empty) failed to add initial line for '{effect.full_text}'." in captured.out # Print statement was removed

def test_typing_effect_update_not_active_or_complete(mock_terminal_ref):
    effect = TypingEffect("text", 50, "fg")
    effect.is_active = False
    assert effect.update(10, mock_terminal_ref) is False
    effect.is_active = True
    effect.is_complete = True
    assert effect.update(10, mock_terminal_ref) is False

def test_typing_effect_update_instant_display_already_complete(mock_terminal_ref):
    effect = TypingEffect("text", 0, "fg")
    effect.start(mock_terminal_ref) # This completes it
    assert effect.is_complete is True
    assert effect.update(10, mock_terminal_ref) is False # Should return False as it's already done

def test_typing_effect_update_progress(mock_terminal_ref):
    effect = TypingEffect("abc", 50, "fg")
    effect.start(mock_terminal_ref) # Adds "a", line_index_in_terminal = 0
    mock_terminal_ref.update_buffer_line.reset_mock()

    # Frame 1: Not enough time for next char
    assert effect.update(40, mock_terminal_ref) is False # Should be False as dt < char_delay
    mock_terminal_ref.update_buffer_line.assert_not_called() # No new char typed
    assert effect.current_display_text == "a"

    # Frame 2: Enough time for 'b'
    assert effect.update(15, mock_terminal_ref) is True # 40+15 = 55 > 50. Timer becomes 5.
    mock_terminal_ref.update_buffer_line.assert_called_once_with(0, "ab", "fg", None, False)
    assert effect.current_display_text == "ab"
    assert effect.current_char_index == 2
    assert effect.is_complete is False
    mock_terminal_ref.update_buffer_line.reset_mock()

    # Frame 3: Enough time for 'c' and completion
    assert effect.update(50, mock_terminal_ref) is True # 5+50 = 55 > 50. Timer becomes 5.
    mock_terminal_ref.update_buffer_line.assert_called_once_with(0, "abc", "fg", None, False)
    assert effect.current_display_text == "abc"
    assert effect.current_char_index == 3
    assert effect.is_complete is True
    assert effect.is_active is False

def test_typing_effect_update_multiple_chars_in_one_update(mock_terminal_ref):
    effect = TypingEffect("longtext", 10, "fg")
    effect.start(mock_terminal_ref) # "l"
    mock_terminal_ref.update_buffer_line.reset_mock()

    # Enough time for 3 more chars (o, n, g)
    effect.update(35, mock_terminal_ref) # 35ms / 10ms_per_char = 3 chars
    
    calls = [
        call(0, "lo", "fg", None, False),
        call(0, "lon", "fg", None, False),
        call(0, "long", "fg", None, False)
    ]
    mock_terminal_ref.update_buffer_line.assert_has_calls(calls)
    assert effect.current_display_text == "long"
    assert effect.current_char_index == 4
    assert effect.is_complete is False

def test_typing_effect_update_completes_with_callback(mock_terminal_ref):
    callback_mock = MagicMock()
    effect = TypingEffect("a", 10, "fg", on_complete_callback=callback_mock)
    effect.start(mock_terminal_ref) # "a" is displayed, effect is not complete yet
    
    assert effect.is_complete is False
    effect.update(15, mock_terminal_ref) # Should type 'a' and complete
    
    assert effect.is_complete is True
    assert effect.is_active is False
    callback_mock.assert_called_once()

def test_typing_effect_update_empty_text_completes_immediately(mock_terminal_ref):
    effect = TypingEffect("", 10, "fg")
    effect.start(mock_terminal_ref) # Adds ""
    mock_terminal_ref.update_buffer_line.reset_mock()

    assert effect.update(1, mock_terminal_ref) is True # Should complete
    assert effect.is_complete is True
    assert effect.is_active is False
    mock_terminal_ref.update_buffer_line.assert_not_called() # No text to update to
# --- Tests for TimedDelayEffect ---

def test_timed_delay_effect_initialization():
    callback = MagicMock()
    effect = TimedDelayEffect(100, on_complete_callback=callback)
    assert effect.duration == 100
    assert effect.on_complete_callback == callback
    assert effect.timer == 0
    assert effect.is_active is True
    assert effect.is_complete is False

def test_timed_delay_effect_update_not_yet_complete(mock_terminal_ref):
    effect = TimedDelayEffect(100)
    effect.start(mock_terminal_ref) # Start does nothing for this effect but good practice
    
    assert effect.update(50, mock_terminal_ref) is False # No visual change
    assert effect.timer == 50
    assert effect.is_complete is False
    assert effect.is_active is True

def test_timed_delay_effect_update_completes(mock_terminal_ref):
    callback_mock = MagicMock()
    effect = TimedDelayEffect(100, on_complete_callback=callback_mock)
    effect.start(mock_terminal_ref)

    effect.update(50, mock_terminal_ref) # timer = 50
    assert effect.is_complete is False
    
    effect.update(60, mock_terminal_ref) # timer = 50 + 60 = 110 >= 100
    assert effect.timer == 110
    assert effect.is_complete is True
    assert effect.is_active is False
    callback_mock.assert_called_once()

def test_timed_delay_effect_update_already_complete(mock_terminal_ref):
    effect = TimedDelayEffect(100)
    effect.start(mock_terminal_ref)
    effect.update(110, mock_terminal_ref) # Completes
    
    assert effect.is_complete is True
    assert effect.update(20, mock_terminal_ref) is False # Already complete
    assert effect.timer == 110 # Timer should not advance further

def test_timed_delay_effect_zero_duration(mock_terminal_ref):
    # Though EffectManager handles this, testing the class itself
    callback_mock = MagicMock()
    effect = TimedDelayEffect(0, on_complete_callback=callback_mock)
    effect.start(mock_terminal_ref)
    
    # Update should immediately complete it if duration is 0 or less
    effect.update(0, mock_terminal_ref) 
    assert effect.is_complete is True
    assert effect.is_active is False
    callback_mock.assert_called_once()

def test_timed_delay_effect_negative_duration(mock_terminal_ref):
    callback_mock = MagicMock()
    effect = TimedDelayEffect(-50, on_complete_callback=callback_mock)
    effect.start(mock_terminal_ref)
    
    effect.update(0, mock_terminal_ref)
    assert effect.is_complete is True
    assert effect.is_active is False
    callback_mock.assert_called_once()
# --- Tests for CharacterCorruptionEffect ---

@pytest.fixture
def corruption_effect_params():
    return {
        "line_index": 0,
        "duration_ms": 100,
        "corruption_intensity": 0.5,
        "corruption_rate_ms": 50
    }

def test_character_corruption_effect_initialization(corruption_effect_params):
    callback = MagicMock()
    effect = CharacterCorruptionEffect(**corruption_effect_params, on_complete_callback=callback)
    assert effect.line_index == corruption_effect_params["line_index"]
    assert effect.duration == corruption_effect_params["duration_ms"]
    assert effect.corruption_intensity == corruption_effect_params["corruption_intensity"]
    assert effect.corruption_rate == corruption_effect_params["corruption_rate_ms"]
    assert effect.on_complete_callback == callback
    assert effect.total_timer == 0
    assert effect.corruption_timer == 0
    assert effect.original_text == ""

def test_character_corruption_effect_start_success(mock_terminal_ref, corruption_effect_params, mocker):
    mock_terminal_ref.buffer = [("Hello World", "fg", "bg", False)]
    mocker.patch.object(effects_module.random, 'sample', return_value=[0, 2, 4]) # Mock which indices to corrupt
    mocker.patch.object(effects_module.random, 'choice', return_value='X') # Mock corruption char

    effect = CharacterCorruptionEffect(**corruption_effect_params)
    effect.start(mock_terminal_ref)

    mock_terminal_ref.get_buffer_line_details.assert_called_once_with(corruption_effect_params["line_index"])
    assert effect.original_text == "Hello World"
    assert effect.original_fg == "fg"
    assert effect.original_bg == "bg"
    assert effect.original_bold is False
    
    # Check that _apply_corruption was called (which calls update_buffer_line)
    # Expected corrupted text: "XelloXWorXd" (H, l, o replaced by X)
    # Based on sample returning [0,2,4] and choice returning 'X'
    # H e l l o   W o r l d
    # 0 1 2 3 4 5 6 7 8 9 10
    # X e X l X   W o r l d  -- this is wrong, sample returns indices, not every other char
    # For "Hello World" (len 11), intensity 0.5 -> 5 chars. sample returns 3 indices [0,2,4]
    # text_list[0] = 'X', text_list[2] = 'X', text_list[4] = 'X'
    # "XeXlX World" (H at 0, l at 2, o at 4 are replaced by X)
    mock_terminal_ref.update_buffer_line.assert_called_once_with(
        corruption_effect_params["line_index"], "XeXlX World", "fg", "bg", False
    )
    assert effect.is_complete is False

def test_character_corruption_effect_start_line_not_found(mock_terminal_ref, corruption_effect_params, capsys):
    mock_terminal_ref.get_buffer_line_details.return_value = None
    effect = CharacterCorruptionEffect(**corruption_effect_params)
    effect.start(mock_terminal_ref)

    assert effect.is_complete is True
    assert effect.is_active is False
    # captured = capsys.readouterr() # Print statement was removed
    # assert f"Error: CharacterCorruptionEffect could not find line {corruption_effect_params['line_index']}" in captured.out # Print statement was removed
    mock_terminal_ref.update_buffer_line.assert_not_called()

def test_character_corruption_effect_start_empty_line(mock_terminal_ref, corruption_effect_params):
    mock_terminal_ref.buffer = [("", "fg", "bg", False)] # Empty text
    effect = CharacterCorruptionEffect(**corruption_effect_params)
    effect.start(mock_terminal_ref)

    assert effect.is_complete is True # Should finish if line is empty
    assert effect.is_active is False
    mock_terminal_ref.update_buffer_line.assert_not_called()

def test_character_corruption_effect_corrupt_text(mocker):
    effect = CharacterCorruptionEffect(0, 100, corruption_intensity=0.5) # Intensity 0.5
    text = "HelloWorld" # len 10. 0.5 intensity -> 5 chars
    
    # Mock random.sample to control which characters are chosen for corruption
    # Corrupt 5 characters: indices 0, 2, 4, 6, 8
    mocker.patch.object(effects_module.random, 'sample', return_value=[0, 2, 4, 6, 8])
    # Mock random.choice to return a fixed corruption character
    mocker.patch.object(effects_module.random, 'choice', return_value='!')
    
    corrupted = effect._corrupt_text(text)
    # Expected: "!e!l!W!r!d"
    assert corrupted == "!e!l!W!r!d"
    assert effects_module.random.sample.call_count == 1
    assert effects_module.random.choice.call_count == 5 # Called for each of the 5 indices

def test_character_corruption_effect_corrupt_text_empty():
    effect = CharacterCorruptionEffect(0,100)
    assert effect._corrupt_text("") == ""

def test_character_corruption_effect_corrupt_text_all_spaces(mocker):
    effect = CharacterCorruptionEffect(0, 100, corruption_intensity=1.0)
    text = "   "
    mock_sample = mocker.patch.object(effects_module.random, 'sample', return_value=[0,1,2])
    mock_choice = mocker.patch.object(effects_module.random, 'choice')
    corrupted = effect._corrupt_text(text)
    assert corrupted == "   " # Spaces should not be corrupted
    mock_sample.assert_called_once()
    mock_choice.assert_not_called() # random.choice should not be called if all are spaces

def test_character_corruption_effect_update_progress_and_re_corrupt(mock_terminal_ref, corruption_effect_params, mocker):
    mock_terminal_ref.buffer = [("Original Text", "fg", "bg", False)]
    effect = CharacterCorruptionEffect(**corruption_effect_params) # rate = 50ms
    
    mock_random_sample = mocker.patch.object(effects_module.random, 'sample')
    mock_random_choice = mocker.patch.object(effects_module.random, 'choice', return_value='X')

    # Start - initial corruption
    mock_random_sample.return_value = [0] # Corrupt first char
    effect.start(mock_terminal_ref)
    mock_terminal_ref.update_buffer_line.assert_called_once_with(0, "Xriginal Text", "fg", "bg", False)
    mock_terminal_ref.update_buffer_line.reset_mock()
    mock_random_sample.reset_mock()

    # Update 1: Not enough time for re-corruption or completion (e.g., 40ms)
    assert effect.update(40, mock_terminal_ref) is False
    assert effect.total_timer == 40
    assert effect.corruption_timer == 40
    mock_terminal_ref.update_buffer_line.assert_not_called()
    assert effect.is_complete is False

    # Update 2: Enough time for re-corruption (e.g., 15ms -> total 55ms for corruption_timer)
    mock_random_sample.return_value = [1] # Corrupt second char
    assert effect.update(15, mock_terminal_ref) is True # Corruption changed
    assert effect.total_timer == 55
    assert effect.corruption_timer == 5 # 55 % 50
    mock_terminal_ref.update_buffer_line.assert_called_once_with(0, "OXiginal Text", "fg", "bg", False)
    mock_random_sample.assert_called_once() # For the re-corruption
    assert effect.is_complete is False

def test_character_corruption_effect_update_completes_and_restores(mock_terminal_ref, corruption_effect_params, mocker):
    original_text = "Restore Me"
    mock_terminal_ref.buffer = [(original_text, "fg", "bg", False)]
    callback_mock = MagicMock()
    effect = CharacterCorruptionEffect(**corruption_effect_params, on_complete_callback=callback_mock) # duration = 100ms
    
    mocker.patch.object(effects_module.random, 'sample', return_value=[0])
    mocker.patch.object(effects_module.random, 'choice', return_value='X')
    
    effect.start(mock_terminal_ref) # Initial corruption: "Xestore Me"
    mock_terminal_ref.update_buffer_line.reset_mock()

    # Update to pass duration
    assert effect.update(110, mock_terminal_ref) is True # Restored text
    assert effect.total_timer == 110
    assert effect.is_complete is True
    assert effect.is_active is False
    mock_terminal_ref.update_buffer_line.assert_called_once_with(
        corruption_effect_params["line_index"], original_text, "fg", "bg", False
    )
    callback_mock.assert_called_once()

def test_character_corruption_effect_update_already_complete(mock_terminal_ref, corruption_effect_params):
    effect = CharacterCorruptionEffect(**corruption_effect_params)
    effect.is_complete = True
    effect.is_active = False
    assert effect.update(10, mock_terminal_ref) is False
    mock_terminal_ref.update_buffer_line.assert_not_called()
# --- Tests for TextFlickerEffect ---

@pytest.fixture
def flicker_effect_params():
    return {
        "line_index": 0,
        "duration_ms": 100,
        "flicker_rate_ms": 40,
        "flicker_color_key": "error" # Assumes 'error' color is different from default_fg
    }

def test_text_flicker_effect_initialization(flicker_effect_params):
    callback = MagicMock()
    effect = TextFlickerEffect(**flicker_effect_params, on_complete_callback=callback)
    assert effect.line_index == flicker_effect_params["line_index"]
    assert effect.duration == flicker_effect_params["duration_ms"]
    assert effect.flicker_rate == flicker_effect_params["flicker_rate_ms"]
    assert effect.flicker_color_key == flicker_effect_params["flicker_color_key"]
    assert effect.on_complete_callback == callback
    assert effect.total_timer == 0
    assert effect.flicker_timer == 0
    assert effect.is_flickered_state is False

@patch.object(effects_module, 'get_theme_color')
def test_text_flicker_effect_start_success(mock_get_theme_color, mock_terminal_ref, flicker_effect_params):
    original_fg = (10,10,10)
    flicker_color = (255,0,0) # 'error'
    mock_terminal_ref.buffer = [("Flicker Text", original_fg, "bg", False)]
    
    # Mock get_theme_color: first call for flicker_color_key, potentially second for default_bg if colors match
    mock_get_theme_color.side_effect = [flicker_color, (0,0,0)] # Ensure flicker_color is different

    effect = TextFlickerEffect(**flicker_effect_params)
    effect.start(mock_terminal_ref)

    mock_terminal_ref.get_buffer_line_details.assert_called_once_with(flicker_effect_params["line_index"])
    assert effect.original_text == "Flicker Text"
    assert effect.original_fg == original_fg
    assert effect.flicker_fg_color == flicker_color
    
    # Should apply flickered state on start
    mock_terminal_ref.update_buffer_line.assert_called_once_with(
        flicker_effect_params["line_index"], "Flicker Text", flicker_color, "bg", False
    )
    assert effect.is_flickered_state is True
    assert effect.is_complete is False
    mock_get_theme_color.assert_any_call(flicker_effect_params["flicker_color_key"])


@patch.object(effects_module, 'get_theme_color')
def test_text_flicker_effect_start_flicker_color_same_as_original(mock_get_theme_color, mock_terminal_ref, flicker_effect_params):
    original_fg = (255,0,0) # Same as 'error' color
    flicker_color_error = (255,0,0)
    bg_color_for_flicker = (1,2,3) # Mocked 'default_bg'
    mock_terminal_ref.buffer = [("Flicker Text", original_fg, "bg_orig", False)]
    
    mock_get_theme_color.side_effect = [flicker_color_error, bg_color_for_flicker]

    effect = TextFlickerEffect(**flicker_effect_params) # flicker_color_key is 'error'
    effect.start(mock_terminal_ref)

    assert effect.original_fg == original_fg
    assert effect.flicker_fg_color == bg_color_for_flicker # Should use background color
    
    mock_terminal_ref.update_buffer_line.assert_called_once_with(
        flicker_effect_params["line_index"], "Flicker Text", bg_color_for_flicker, "bg_orig", False
    )
    assert mock_get_theme_color.call_count == 2
    mock_get_theme_color.assert_any_call('error')
    mock_get_theme_color.assert_any_call('default_bg')


@patch.object(effects_module, 'get_theme_color')
def test_text_flicker_effect_start_line_not_found(mock_get_theme_color, mock_terminal_ref, flicker_effect_params, capsys):
    mock_terminal_ref.get_buffer_line_details.return_value = None
    effect = TextFlickerEffect(**flicker_effect_params)
    effect.start(mock_terminal_ref)

    assert effect.is_complete is True
    assert effect.is_active is False
    # captured = capsys.readouterr() # Print statement was removed
    # assert f"Error: TextFlickerEffect could not find line {flicker_effect_params['line_index']}" in captured.out # Print statement was removed
    mock_terminal_ref.update_buffer_line.assert_not_called()
    mock_get_theme_color.assert_not_called() # Should not try to get colors if line not found

@patch.object(effects_module, 'get_theme_color')
def test_text_flicker_effect_start_empty_line(mock_get_theme_color, mock_terminal_ref, flicker_effect_params):
    mock_terminal_ref.buffer = [("", "fg", "bg", False)] # Empty text
    effect = TextFlickerEffect(**flicker_effect_params)
    effect.start(mock_terminal_ref)

    assert effect.is_complete is True # Should finish if line is empty
    assert effect.is_active is False
    mock_terminal_ref.update_buffer_line.assert_not_called()
    mock_get_theme_color.assert_not_called()

@patch.object(effects_module, 'get_theme_color')
def test_text_flicker_effect_update_toggles_state(mock_get_theme_color, mock_terminal_ref, flicker_effect_params):
    original_fg = (10,10,10)
    flicker_color = (255,0,0)
    mock_terminal_ref.buffer = [("Toggle Me", original_fg, "bg", False)]
    mock_get_theme_color.return_value = flicker_color

    effect = TextFlickerEffect(**flicker_effect_params) # rate = 40ms
    effect.start(mock_terminal_ref) # Starts flickered (True), update_buffer_line called once
    mock_terminal_ref.update_buffer_line.reset_mock() 
    assert effect.is_flickered_state is True

    # Update 1: Not enough time to toggle (e.g., 30ms)
    assert effect.update(30, mock_terminal_ref) is False
    assert effect.flicker_timer == 30
    mock_terminal_ref.update_buffer_line.assert_not_called()
    assert effect.is_flickered_state is True # Still flickered

    # Update 2: Enough time to toggle back to original (e.g., 15ms -> total 45ms for flicker_timer)
    assert effect.update(15, mock_terminal_ref) is True # State changed
    assert effect.flicker_timer == 5 # 45 % 40
    mock_terminal_ref.update_buffer_line.assert_called_once_with(
        flicker_effect_params["line_index"], "Toggle Me", original_fg, "bg", False
    )
    assert effect.is_flickered_state is False # Back to original
    mock_terminal_ref.update_buffer_line.reset_mock()

    # Update 3: Enough time to toggle back to flicker (e.g., 40ms -> total 45ms for flicker_timer)
    assert effect.update(40, mock_terminal_ref) is True # State changed
    assert effect.flicker_timer == 5 # 45 % 40
    mock_terminal_ref.update_buffer_line.assert_called_once_with(
        flicker_effect_params["line_index"], "Toggle Me", flicker_color, "bg", False
    )
    assert effect.is_flickered_state is True # Back to flickered

@patch.object(effects_module, 'get_theme_color')
def test_text_flicker_effect_update_completes_and_restores(mock_get_theme_color, mock_terminal_ref, flicker_effect_params):
    original_text = "Restore Me"
    original_fg = (10,10,10)
    flicker_color = (255,0,0)
    mock_terminal_ref.buffer = [(original_text, original_fg, "bg", False)]
    mock_get_theme_color.return_value = flicker_color
    
    callback_mock = MagicMock()
    effect = TextFlickerEffect(**flicker_effect_params, on_complete_callback=callback_mock) # duration = 100ms
    
    effect.start(mock_terminal_ref) # Initial flicker state
    mock_terminal_ref.update_buffer_line.reset_mock()
    effect.is_flickered_state = True # Assume it's in flickered state before final update

    # Update to pass duration
    assert effect.update(110, mock_terminal_ref) is True # Restored color
    assert effect.total_timer == 110
    assert effect.is_complete is True
    assert effect.is_active is False
    # Should restore to original_fg
    mock_terminal_ref.update_buffer_line.assert_called_once_with(
        flicker_effect_params["line_index"], original_text, original_fg, "bg", False
    )
    callback_mock.assert_called_once()

def test_text_flicker_effect_update_already_complete(mock_terminal_ref, flicker_effect_params):
    effect = TextFlickerEffect(**flicker_effect_params)
    effect.is_complete = True
    effect.is_active = False
    assert effect.update(10, mock_terminal_ref) is False
    mock_terminal_ref.update_buffer_line.assert_not_called()
# --- Tests for TemporaryColorChangeEffect ---

@pytest.fixture
def temp_color_effect_params():
    return {
        "line_index": 0,
        "duration_ms": 100,
        "new_fg_color_key": "highlight",
        "new_bg_color_key": "error" 
    }

def test_temporary_color_change_effect_initialization(temp_color_effect_params):
    callback = MagicMock()
    effect = TemporaryColorChangeEffect(**temp_color_effect_params, on_complete_callback=callback)
    assert effect.line_index == temp_color_effect_params["line_index"]
    assert effect.duration == temp_color_effect_params["duration_ms"]
    assert effect.new_fg_color_key == temp_color_effect_params["new_fg_color_key"]
    assert effect.new_bg_color_key == temp_color_effect_params["new_bg_color_key"]
    assert effect.on_complete_callback == callback
    assert effect.total_timer == 0

@patch.object(effects_module, 'get_theme_color')
def test_temporary_color_change_effect_start_success_fg_and_bg(mock_get_theme_color, mock_terminal_ref, temp_color_effect_params):
    original_fg = (10,10,10)
    original_bg = (20,20,20)
    new_fg = (100,100,100) # highlight
    new_bg = (200,0,0)   # error
    mock_terminal_ref.buffer = [("Change Me", original_fg, original_bg, False)]
    
    mock_get_theme_color.side_effect = [new_fg, new_bg]

    effect = TemporaryColorChangeEffect(**temp_color_effect_params)
    effect.start(mock_terminal_ref)

    mock_terminal_ref.get_buffer_line_details.assert_called_once_with(temp_color_effect_params["line_index"])
    assert effect.original_text == "Change Me"
    assert effect.original_fg == original_fg
    assert effect.original_bg == original_bg
    assert effect.temp_fg == new_fg
    assert effect.temp_bg == new_bg
    
    mock_terminal_ref.update_buffer_line.assert_called_once_with(
        temp_color_effect_params["line_index"], "Change Me", new_fg, new_bg, False
    )
    assert effect.is_complete is False
    assert mock_get_theme_color.call_count == 2
    mock_get_theme_color.assert_any_call(temp_color_effect_params["new_fg_color_key"])
    mock_get_theme_color.assert_any_call(temp_color_effect_params["new_bg_color_key"])

@patch.object(effects_module, 'get_theme_color')
def test_temporary_color_change_effect_start_fg_only(mock_get_theme_color, mock_terminal_ref, temp_color_effect_params):
    original_fg = (10,10,10)
    original_bg = (20,20,20)
    new_fg = (100,100,100) # highlight
    mock_terminal_ref.buffer = [("Change Me", original_fg, original_bg, False)]
    
    mock_get_theme_color.return_value = new_fg # Only fg key is provided

    params = temp_color_effect_params.copy()
    params["new_bg_color_key"] = None
    effect = TemporaryColorChangeEffect(**params)
    effect.start(mock_terminal_ref)

    assert effect.temp_fg == new_fg
    assert effect.temp_bg == original_bg # Should remain original
    
    mock_terminal_ref.update_buffer_line.assert_called_once_with(
        params["line_index"], "Change Me", new_fg, original_bg, False
    )
    mock_get_theme_color.assert_called_once_with(params["new_fg_color_key"])

@patch.object(effects_module, 'get_theme_color')
def test_temporary_color_change_effect_start_bg_only(mock_get_theme_color, mock_terminal_ref, temp_color_effect_params):
    original_fg = (10,10,10)
    original_bg = (20,20,20)
    new_bg = (200,0,0)   # error
    mock_terminal_ref.buffer = [("Change Me", original_fg, original_bg, False)]
    
    mock_get_theme_color.return_value = new_bg # Only bg key is provided

    params = temp_color_effect_params.copy()
    params["new_fg_color_key"] = None
    effect = TemporaryColorChangeEffect(**params)
    effect.start(mock_terminal_ref)

    assert effect.temp_fg == original_fg # Should remain original
    assert effect.temp_bg == new_bg
    
    mock_terminal_ref.update_buffer_line.assert_called_once_with(
        params["line_index"], "Change Me", original_fg, new_bg, False
    )
    mock_get_theme_color.assert_called_once_with(params["new_bg_color_key"])

@patch.object(effects_module, 'get_theme_color')
def test_temporary_color_change_effect_start_no_actual_change(mock_get_theme_color, mock_terminal_ref, temp_color_effect_params):
    original_fg = (10,10,10)
    original_bg = (20,20,20)
    mock_terminal_ref.buffer = [("No Change", original_fg, original_bg, False)]
    
    # get_theme_color returns the original colors
    mock_get_theme_color.side_effect = [original_fg, original_bg] 

    effect = TemporaryColorChangeEffect(**temp_color_effect_params)
    effect.start(mock_terminal_ref)

    assert effect.is_complete is True # Should finish immediately if no change
    assert effect.is_active is False
    mock_terminal_ref.update_buffer_line.assert_not_called() # No update if no change

@patch.object(effects_module, 'get_theme_color')
def test_temporary_color_change_effect_start_line_not_found(mock_get_theme_color, mock_terminal_ref, temp_color_effect_params, capsys):
    mock_terminal_ref.get_buffer_line_details.return_value = None
    effect = TemporaryColorChangeEffect(**temp_color_effect_params)
    effect.start(mock_terminal_ref)

    assert effect.is_complete is True
    assert effect.is_active is False
    # captured = capsys.readouterr() # Print statement was removed
    # assert f"Error: TemporaryColorChangeEffect could not find line {temp_color_effect_params['line_index']}" in captured.out # Print statement was removed
    mock_terminal_ref.update_buffer_line.assert_not_called()
    mock_get_theme_color.assert_not_called()

@patch.object(effects_module, 'get_theme_color')
def test_temporary_color_change_effect_start_empty_line(mock_get_theme_color, mock_terminal_ref, temp_color_effect_params):
    mock_terminal_ref.buffer = [("", "fg", "bg", False)] # Empty text
    effect = TemporaryColorChangeEffect(**temp_color_effect_params)
    effect.start(mock_terminal_ref)

    assert effect.is_complete is True # Should finish if line is empty
    assert effect.is_active is False
    mock_terminal_ref.update_buffer_line.assert_not_called()
    mock_get_theme_color.assert_not_called()

@patch.object(effects_module, 'get_theme_color')
def test_temporary_color_change_effect_update_not_yet_complete(mock_get_theme_color, mock_terminal_ref, temp_color_effect_params):
    mock_terminal_ref.buffer = [("Text", "ofg", "obg", False)]
    mock_get_theme_color.side_effect = ["nfg", "nbg"]
    effect = TemporaryColorChangeEffect(**temp_color_effect_params) # duration 100
    effect.start(mock_terminal_ref)
    mock_terminal_ref.update_buffer_line.reset_mock()

    assert effect.update(50, mock_terminal_ref) is False # No change until duration up
    assert effect.total_timer == 50
    assert effect.is_complete is False
    mock_terminal_ref.update_buffer_line.assert_not_called()

@patch.object(effects_module, 'get_theme_color')
def test_temporary_color_change_effect_update_completes_and_restores(mock_get_theme_color, mock_terminal_ref, temp_color_effect_params):
    original_text = "Restore Me"
    original_fg = (10,10,10)
    original_bg = (20,20,20)
    new_fg = (100,100,100)
    new_bg = (200,0,0)
    mock_terminal_ref.buffer = [(original_text, original_fg, original_bg, False)]
    mock_get_theme_color.side_effect = [new_fg, new_bg] # For start()
    
    callback_mock = MagicMock()
    effect = TemporaryColorChangeEffect(**temp_color_effect_params, on_complete_callback=callback_mock) # duration = 100ms
    
    effect.start(mock_terminal_ref) # Applies new_fg, new_bg
    mock_terminal_ref.update_buffer_line.reset_mock()

    # Update to pass duration
    assert effect.update(110, mock_terminal_ref) is True # Restored color
    assert effect.total_timer == 110
    assert effect.is_complete is True
    assert effect.is_active is False
    # Should restore to original_fg, original_bg
    mock_terminal_ref.update_buffer_line.assert_called_once_with(
        temp_color_effect_params["line_index"], original_text, original_fg, original_bg, False
    )
    callback_mock.assert_called_once()

def test_temporary_color_change_effect_update_already_complete(mock_terminal_ref, temp_color_effect_params):
    effect = TemporaryColorChangeEffect(**temp_color_effect_params)
    effect.is_complete = True
    effect.is_active = False
    assert effect.update(10, mock_terminal_ref) is False
    mock_terminal_ref.update_buffer_line.assert_not_called()
# --- Tests for TextOverlayEffect ---

@pytest.fixture
def overlay_effect_params():
    return {
        "duration_ms": 100,
        "num_chars": 3,
        "char_set": "abc",
        "color_key": "highlight",
        "update_rate_ms": 40
    }

def test_text_overlay_effect_initialization(overlay_effect_params):
    callback = MagicMock()
    effect = TextOverlayEffect(**overlay_effect_params, on_complete_callback=callback)
    assert effect.duration == overlay_effect_params["duration_ms"]
    assert effect.num_chars == overlay_effect_params["num_chars"]
    assert effect.char_set == overlay_effect_params["char_set"]
    assert effect.color_key == overlay_effect_params["color_key"]
    assert effect.update_rate == overlay_effect_params["update_rate_ms"]
    assert effect.on_complete_callback == callback
    assert effect.total_timer == 0
    assert effect.overlay_update_timer == 0
    assert effect.overlay_elements == []
    assert effect.overlay_color is None

@patch.object(effects_module, 'get_theme_color')
@patch.object(effects_module.random, 'choice')
@patch.object(effects_module.random, 'randint')
def test_text_overlay_effect_start(mock_randint, mock_choice, mock_get_theme_color, mock_terminal_ref, overlay_effect_params):
    overlay_color = (1,2,3)
    mock_get_theme_color.return_value = overlay_color
    mock_choice.return_value = 'a' # Always choose 'a'
    mock_randint.return_value = 10 # Always choose x=10, y=10

    effect = TextOverlayEffect(**overlay_effect_params)
    effect.start(mock_terminal_ref)

    mock_get_theme_color.assert_called_once_with(overlay_effect_params["color_key"])
    assert effect.overlay_color == overlay_color
    
    # _generate_overlay_elements was called
    assert len(effect.overlay_elements) == overlay_effect_params["num_chars"]
    for char, x, y, color in effect.overlay_elements:
        assert char == 'a'
        assert x == 10
        assert y == 10
        assert color == overlay_color
    assert mock_choice.call_count == overlay_effect_params["num_chars"]
    assert mock_randint.call_count == overlay_effect_params["num_chars"] * 2 # For x and y

@patch.object(effects_module.random, 'choice', return_value='z')
@patch.object(effects_module.random, 'randint')
def test_text_overlay_effect_generate_elements_font_available(mock_randint, mock_choice_gen, mock_terminal_ref):
    # mock_terminal_ref.font.size is (10,15), width=800, height=600
    # max_x = 800 - 10 = 790
    # max_y = 600 - 18 = 582 (using linesize for height)
    mock_randint.side_effect = [10, 20, 30, 40, 50, 60] # x1,y1, x2,y2, x3,y3

    effect = TextOverlayEffect(duration_ms=100, num_chars=3, char_set="xyz", color_key="error", update_rate_ms=50)
    effect.overlay_color = (255,0,0) # Set manually as start is not called here
    effect._generate_overlay_elements(mock_terminal_ref)

    assert len(effect.overlay_elements) == 3
    assert effect.overlay_elements[0] == ('z', 10, 20, (255,0,0))
    assert effect.overlay_elements[1] == ('z', 30, 40, (255,0,0))
    assert effect.overlay_elements[2] == ('z', 50, 60, (255,0,0))
    
    mock_randint.assert_any_call(0, 790) # terminal_width - char_width
    mock_randint.assert_any_call(0, 582) # terminal_height - char_height (linesize)

@patch.object(effects_module.random, 'choice', return_value='z')
@patch.object(effects_module.random, 'randint')
def test_text_overlay_effect_generate_elements_font_size_error(mock_randint, mock_choice_gen, mock_terminal_ref):
    mock_terminal_ref.font.size.side_effect = pygame.error("Font size error")
    # Fallback char_width=8, char_height=16
    # max_x = 800 - 8 = 792
    # max_y = 600 - 16 = 584
    mock_randint.side_effect = [5, 15]

    effect = TextOverlayEffect(duration_ms=100, num_chars=1, char_set="xyz", color_key="error", update_rate_ms=50)
    effect.overlay_color = (255,0,0)
    effect._generate_overlay_elements(mock_terminal_ref)
    
    assert len(effect.overlay_elements) == 1
    assert effect.overlay_elements[0] == ('z', 5, 15, (255,0,0))
    mock_randint.assert_any_call(0, 792)
    mock_randint.assert_any_call(0, 584)

def test_text_overlay_effect_update_not_active_or_complete(mock_terminal_ref, overlay_effect_params):
    effect = TextOverlayEffect(**overlay_effect_params)
    effect.overlay_elements = [('a',0,0,(1,1,1))] # Has elements
    
    effect.is_active = False
    assert effect.update(10, mock_terminal_ref) is False
    assert effect.overlay_elements == [] # Should clear if not active

    effect.is_active = True
    effect.is_complete = True
    effect.overlay_elements = [('a',0,0,(1,1,1))] # Reset elements
    assert effect.update(10, mock_terminal_ref) is False
    assert effect.overlay_elements == [] # Should clear if complete

@patch.object(effects_module, 'get_theme_color', return_value=(1,1,1))
def test_text_overlay_effect_update_completes(mock_get_color, mock_terminal_ref, overlay_effect_params):
    callback_mock = MagicMock()
    effect = TextOverlayEffect(**overlay_effect_params, on_complete_callback=callback_mock) # duration 100
    effect.start(mock_terminal_ref) # Generates initial elements
    assert len(effect.overlay_elements) == overlay_effect_params["num_chars"]

    # Update to pass duration
    assert effect.update(110, mock_terminal_ref) is True # Effect ended, clear overlay
    assert effect.total_timer == 110
    assert effect.is_complete is True
    assert effect.is_active is False
    assert effect.overlay_elements == [] # Elements cleared
    callback_mock.assert_called_once()

@patch.object(effects_module, 'get_theme_color', return_value=(1,1,1))
@patch.object(effects_module.random, 'choice')
@patch.object(effects_module.random, 'randint')
def test_text_overlay_effect_update_regenerates_elements(mock_randint, mock_choice, mock_get_color, mock_terminal_ref, overlay_effect_params):
    effect = TextOverlayEffect(**overlay_effect_params) # update_rate 40ms
    effect.start(mock_terminal_ref)
    mock_choice.reset_mock()
    mock_randint.reset_mock()

    # Update 1: Not enough time to regenerate (e.g., 30ms)
    assert effect.update(30, mock_terminal_ref) is False
    assert effect.overlay_update_timer == 30
    mock_choice.assert_not_called()
    mock_randint.assert_not_called()
    assert effect.is_complete is False

    # Update 2: Enough time to regenerate (e.g., 15ms -> total 45ms for overlay_update_timer)
    mock_choice.return_value = 'b'
    mock_randint.return_value = 20
    assert effect.update(15, mock_terminal_ref) is True # Regenerated
    assert effect.overlay_update_timer == 5 # 45 % 40
    assert mock_choice.call_count == overlay_effect_params["num_chars"]
    assert mock_randint.call_count == overlay_effect_params["num_chars"] * 2
    assert effect.overlay_elements[0][0] == 'b' # Check if new char was chosen
    assert effect.is_complete is False

def test_text_overlay_effect_get_overlay_elements(overlay_effect_params):
    effect = TextOverlayEffect(**overlay_effect_params)
    test_elements = [('x',1,1,(0,0,0))]
    effect.overlay_elements = test_elements
    
    # Active and not complete
    effect.is_active = True
    effect.is_complete = False
    assert effect.get_overlay_elements() == test_elements

    # Not active
    effect.is_active = False
    effect.is_complete = False
    assert effect.get_overlay_elements() == []

    # Complete
    effect.is_active = True # Can be active but also complete if just finished
    effect.is_complete = True
    assert effect.get_overlay_elements() == []
# --- Tests for TextJiggleEffect ---

@pytest.fixture
def jiggle_effect_params():
    return {
        "line_index": 0,
        "duration_ms": 100,
        "jiggle_intensity": 2,
        "update_rate_ms": 40
    }

def test_text_jiggle_effect_initialization(jiggle_effect_params):
    callback = MagicMock()
    effect = TextJiggleEffect(**jiggle_effect_params, on_complete_callback=callback)
    assert effect.line_index == jiggle_effect_params["line_index"]
    assert effect.duration == jiggle_effect_params["duration_ms"]
    assert effect.jiggle_intensity == jiggle_effect_params["jiggle_intensity"]
    assert effect.update_rate == jiggle_effect_params["update_rate_ms"]
    assert effect.on_complete_callback == callback
    assert effect.total_timer == 0
    assert effect.jiggle_timer == 0
    assert effect.original_line_details is None
    assert effect.char_offsets == []

@patch.object(effects_module.random, 'randint')
def test_text_jiggle_effect_start_success(mock_randint, mock_terminal_ref, jiggle_effect_params):
    original_details = ("Jiggle", "fg", "bg", False)
    mock_terminal_ref.buffer = [original_details]
    mock_randint.return_value = 1 # dx=1, dy=1 for all chars

    effect = TextJiggleEffect(**jiggle_effect_params)
    effect.start(mock_terminal_ref)

    mock_terminal_ref.get_buffer_line_details.assert_called_once_with(jiggle_effect_params["line_index"])
    assert effect.original_line_details == original_details
    
    # _generate_char_offsets was called
    assert len(effect.char_offsets) == len("Jiggle")
    for dx, dy in effect.char_offsets:
        assert dx == 1
        assert dy == 1
    # randint called twice per character (dx, dy)
    assert mock_randint.call_count == len("Jiggle") * 2 
    assert effect.is_complete is False

def test_text_jiggle_effect_start_line_not_found(mock_terminal_ref, jiggle_effect_params):
    mock_terminal_ref.get_buffer_line_details.return_value = None
    effect = TextJiggleEffect(**jiggle_effect_params)
    effect.start(mock_terminal_ref)

    assert effect.is_complete is True
    assert effect.is_active is False
    assert effect.original_line_details is None
    assert effect.char_offsets == []

def test_text_jiggle_effect_start_empty_line_text(mock_terminal_ref, jiggle_effect_params):
    mock_terminal_ref.buffer = [("", "fg", "bg", False)] # Empty text
    effect = TextJiggleEffect(**jiggle_effect_params)
    effect.start(mock_terminal_ref)

    assert effect.is_complete is True # Should finish if line text is empty
    assert effect.is_active is False
    assert effect.original_line_details == ("", "fg", "bg", False) # Stores details
    assert effect.char_offsets == [] # No offsets for empty text

@patch.object(effects_module.random, 'randint')
def test_text_jiggle_effect_generate_char_offsets(mock_randint, jiggle_effect_params):
    effect = TextJiggleEffect(**jiggle_effect_params)
    effect.original_line_details = ("Hi", "fg", "bg", False)
    
    # Mock randint to return alternating 1 and -1 for dx, and 2 and -2 for dy
    mock_randint.side_effect = [1, 2, -1, -2] 
    
    effect._generate_char_offsets()
    
    assert len(effect.char_offsets) == 2
    assert effect.char_offsets[0] == (1, 2)  # For 'H'
    assert effect.char_offsets[1] == (-1, -2) # For 'i'
    
    intensity = jiggle_effect_params["jiggle_intensity"]
    calls = [
        call(-intensity, intensity), call(-intensity, intensity), # For 'H' dx, dy
        call(-intensity, intensity), call(-intensity, intensity)  # For 'i' dx, dy
    ]
    mock_randint.assert_has_calls(calls)

def test_text_jiggle_effect_generate_char_offsets_no_original_details(jiggle_effect_params):
    effect = TextJiggleEffect(**jiggle_effect_params)
    effect.original_line_details = None
    effect._generate_char_offsets()
    assert effect.char_offsets == []

def test_text_jiggle_effect_update_not_active_or_complete(mock_terminal_ref, jiggle_effect_params):
    effect = TextJiggleEffect(**jiggle_effect_params)
    effect.char_offsets = [(1,1)] # Has offsets
    
    effect.is_active = False
    assert effect.update(10, mock_terminal_ref) is False
    # char_offsets are not cleared here, only on completion by duration

    effect.is_active = True
    effect.is_complete = True
    assert effect.update(10, mock_terminal_ref) is False

@patch.object(effects_module.random, 'randint')
def test_text_jiggle_effect_update_regenerates_offsets(mock_randint, mock_terminal_ref, jiggle_effect_params):
    mock_terminal_ref.buffer = [("Test", "fg", "bg", False)]
    effect = TextJiggleEffect(**jiggle_effect_params) # update_rate 40ms
    
    mock_randint.return_value = 0 # Initial offsets will be (0,0)
    effect.start(mock_terminal_ref)
    initial_offsets = list(effect.char_offsets) # Make a copy
    mock_randint.reset_mock()

    # Update 1: Not enough time to regenerate (e.g., 30ms)
    assert effect.update(30, mock_terminal_ref) is False
    assert effect.jiggle_timer == 30
    assert effect.char_offsets == initial_offsets # Offsets should not change
    mock_randint.assert_not_called()
    assert effect.is_complete is False

    # Update 2: Enough time to regenerate (e.g., 15ms -> total 45ms for jiggle_timer)
    mock_randint.return_value = 1 # New offsets will be (1,1)
    assert effect.update(15, mock_terminal_ref) is True # Regenerated
    assert effect.jiggle_timer == 5 # 45 % 40
    assert mock_randint.call_count == len("Test") * 2
    assert effect.char_offsets != initial_offsets
    for dx, dy in effect.char_offsets:
        assert dx == 1 and dy == 1
    assert effect.is_complete is False

@patch.object(effects_module.random, 'randint')
def test_text_jiggle_effect_update_completes(mock_randint, mock_terminal_ref, jiggle_effect_params):
    mock_terminal_ref.buffer = [("End", "fg", "bg", False)]
    callback_mock = MagicMock()
    effect = TextJiggleEffect(**jiggle_effect_params, on_complete_callback=callback_mock) # duration 100ms
    
    mock_randint.return_value = 1
    effect.start(mock_terminal_ref) # Generates initial offsets
    assert effect.char_offsets != []

    # Update to pass duration
    assert effect.update(110, mock_terminal_ref) is True # Effect ended
    assert effect.total_timer == 110
    assert effect.is_complete is True
    assert effect.is_active is False
    assert effect.char_offsets == [] # Offsets cleared on completion
    callback_mock.assert_called_once()

def test_text_jiggle_effect_get_jiggle_data(jiggle_effect_params):
    effect = TextJiggleEffect(**jiggle_effect_params)
    original_details = ("Data", "f", "b", True)
    offsets = [(1,0), (0,1)]
    
    effect.original_line_details = original_details
    effect.char_offsets = offsets
    
    # Active and not complete
    effect.is_active = True
    effect.is_complete = False
    data, retrieved_offsets = effect.get_jiggle_data()
    assert data == original_details
    assert retrieved_offsets == offsets

    # Not active
    effect.is_active = False
    effect.is_complete = False
    data, retrieved_offsets = effect.get_jiggle_data()
    assert data is None
    assert retrieved_offsets == []

    # Complete
    effect.is_active = True 
    effect.is_complete = True
    data, retrieved_offsets = effect.get_jiggle_data()
    assert data is None
    assert retrieved_offsets == []
    
    # Active, not complete, but no original_line_details (e.g. start failed silently)
    effect.is_active = True
    effect.is_complete = False
    effect.original_line_details = None
    effect.char_offsets = offsets # Still has offsets for some reason
    data, retrieved_offsets = effect.get_jiggle_data()
    assert data is None
    assert retrieved_offsets == []
# --- Tests for EffectManager ---

@pytest.fixture
def effect_manager(mock_terminal_ref):
    return EffectManager(mock_terminal_ref)

def test_effect_manager_initialization(effect_manager, mock_terminal_ref):
    assert effect_manager.effect_queue == []
    assert effect_manager.terminal == mock_terminal_ref

@patch('effects.TypingEffect')
def test_effect_manager_start_typing_effect(MockTypingEffect, effect_manager, mock_terminal_ref):
    mock_effect_instance = MagicMock()
    MockTypingEffect.return_value = mock_effect_instance
    callback = MagicMock()
    
    with patch.object(effect_manager, '_add_effect_to_queue') as mock_add:
        effect_manager.start_typing_effect("text", 10, "fg", "bg", True, "style", callback)
        
        MockTypingEffect.assert_called_once_with("text", 10, effects_module.get_theme_color("style"), "bg", True, callback)
        mock_add.assert_called_once_with(mock_effect_instance)

@patch('effects.TypingEffect')
def test_effect_manager_start_typing_effect_default_fg(MockTypingEffect, effect_manager, mock_terminal_ref):
    mock_effect_instance = MagicMock()
    MockTypingEffect.return_value = mock_effect_instance
    
    # Simulate get_theme_color for 'default_fg'
    with patch('effects.get_theme_color', return_value=(1,1,1)) as mock_get_color:
        with patch.object(effect_manager, '_add_effect_to_queue') as mock_add:
            effect_manager.start_typing_effect("text", char_delay_ms=10) # No fg_color, no style_key
            
            mock_get_color.assert_called_once_with('default_fg')
            MockTypingEffect.assert_called_once_with("text", 10, (1,1,1), None, False, None)
            mock_add.assert_called_once_with(mock_effect_instance)


@patch('effects.TimedDelayEffect')
def test_effect_manager_start_timed_delay(MockTimedDelayEffect, effect_manager):
    mock_effect_instance = MagicMock()
    MockTimedDelayEffect.return_value = mock_effect_instance
    callback = MagicMock()

    with patch.object(effect_manager, '_add_effect_to_queue') as mock_add:
        effect_manager.start_timed_delay(100, callback)
        MockTimedDelayEffect.assert_called_once_with(100, callback)
        mock_add.assert_called_once_with(mock_effect_instance)

def test_effect_manager_start_timed_delay_zero_duration(effect_manager):
    callback = MagicMock()
    with patch.object(effect_manager, '_add_effect_to_queue') as mock_add:
        effect_manager.start_timed_delay(0, callback)
        mock_add.assert_not_called()
        callback.assert_called_once() # Should call immediately

@patch('effects.CharacterCorruptionEffect')
def test_effect_manager_start_character_corruption_effect(MockCCEffect, effect_manager, mock_terminal_ref):
    mock_terminal_ref.buffer = ["line1", "line2"] # Need buffer for index resolution
    mock_effect_instance = MagicMock()
    MockCCEffect.return_value = mock_effect_instance
    callback = MagicMock()

    with patch.object(effect_manager, '_add_effect_to_queue') as mock_add:
        # Positive index
        effect_manager.start_character_corruption_effect(0, 100, 0.5, 50, callback)
        MockCCEffect.assert_called_with(0, 100, 0.5, 50, callback)
        mock_add.assert_called_with(mock_effect_instance)
        mock_add.reset_mock()
        MockCCEffect.reset_mock()

        # Negative index
        effect_manager.start_character_corruption_effect(-1, 200, 0.2, 20, callback)
        resolved_index = len(mock_terminal_ref.buffer) - 1 # 2 - 1 = 1
        MockCCEffect.assert_called_with(resolved_index, 200, 0.2, 20, callback)
        mock_add.assert_called_with(mock_effect_instance)

def test_effect_manager_start_character_corruption_effect_invalid_index(effect_manager, mock_terminal_ref, capsys):
    mock_terminal_ref.buffer = ["one line"]
    callback = MagicMock()
    with patch.object(effect_manager, '_add_effect_to_queue') as mock_add:
        effect_manager.start_character_corruption_effect(5, 100, 0.5, 50, callback) # Index 5 out of bounds
        mock_add.assert_not_called()
        callback.assert_called_once()
        # assert "Error: Invalid line_index 5" in capsys.readouterr().out # Print statement was removed

        effect_manager.start_character_corruption_effect(-3, 100, 0.5, 50, callback) # Index -3 out of bounds
        mock_add.assert_not_called()
        assert callback.call_count == 2
        # assert "Error: Invalid line_index -3" in capsys.readouterr().out # Print statement was removed


@patch('effects.TextFlickerEffect')
def test_effect_manager_start_text_flicker_effect(MockFlickerEffect, effect_manager, mock_terminal_ref):
    mock_terminal_ref.buffer = ["line1"]
    mock_effect_instance = MagicMock()
    MockFlickerEffect.return_value = mock_effect_instance
    callback = MagicMock()
    with patch.object(effect_manager, '_add_effect_to_queue') as mock_add:
        effect_manager.start_text_flicker_effect(0, 100, 50, "custom_key", callback)
        MockFlickerEffect.assert_called_once_with(0, 100, 50, "custom_key", callback)
        mock_add.assert_called_once_with(mock_effect_instance)

@patch('effects.TemporaryColorChangeEffect')
def test_effect_manager_start_temp_color_change_effect(MockColorChangeEffect, effect_manager, mock_terminal_ref):
    mock_terminal_ref.buffer = ["line1"]
    mock_effect_instance = MagicMock()
    MockColorChangeEffect.return_value = mock_effect_instance
    callback = MagicMock()
    with patch.object(effect_manager, '_add_effect_to_queue') as mock_add:
        effect_manager.start_temp_color_change_effect(0, 100, "fg_key", "bg_key", callback)
        MockColorChangeEffect.assert_called_once_with(0, 100, "fg_key", "bg_key", callback)
        mock_add.assert_called_once_with(mock_effect_instance)

def test_effect_manager_start_temp_color_change_no_keys(effect_manager, mock_terminal_ref, capsys):
    mock_terminal_ref.buffer = ["line1"]
    callback = MagicMock()
    with patch.object(effect_manager, '_add_effect_to_queue') as mock_add:
        effect_manager.start_temp_color_change_effect(0, 100, None, None, callback)
        mock_add.assert_not_called()
        callback.assert_called_once()
        # assert "Error: TemporaryColorChangeEffect requires at least one new color key" in capsys.readouterr().out # Print statement was removed

@patch('effects.TextOverlayEffect')
def test_effect_manager_start_text_overlay_effect(MockOverlayEffect, effect_manager):
    mock_effect_instance = MagicMock()
    MockOverlayEffect.return_value = mock_effect_instance
    callback = MagicMock()
    with patch.object(effect_manager, '_add_effect_to_queue') as mock_add:
        effect_manager.start_text_overlay_effect(100, 10, "set", "key", 50, callback)
        MockOverlayEffect.assert_called_once_with(100, 10, "set", "key", 50, callback)
        mock_add.assert_called_once_with(mock_effect_instance)

@patch('effects.TextJiggleEffect')
def test_effect_manager_start_text_jiggle_effect(MockJiggleEffect, effect_manager, mock_terminal_ref):
    mock_terminal_ref.buffer = ["line1"]
    mock_effect_instance = MagicMock()
    MockJiggleEffect.return_value = mock_effect_instance
    callback = MagicMock()
    with patch.object(effect_manager, '_add_effect_to_queue') as mock_add:
        effect_manager.start_text_jiggle_effect(0, 100, 3, 20, callback)
        MockJiggleEffect.assert_called_once_with(0, 100, 3, 20, callback)
        mock_add.assert_called_once_with(mock_effect_instance)

def test_effect_manager_add_effect_to_queue_starts_first(effect_manager, mock_terminal_ref):
    mock_effect1 = MagicMock(spec=BaseEffect)
    mock_effect2 = MagicMock(spec=BaseEffect)

    effect_manager._add_effect_to_queue(mock_effect1)
    assert effect_manager.effect_queue == [mock_effect1]
    mock_effect1.start.assert_called_once_with(mock_terminal_ref)

    effect_manager._add_effect_to_queue(mock_effect2)
    assert effect_manager.effect_queue == [mock_effect1, mock_effect2]
    mock_effect2.start.assert_not_called() # Should not start second effect yet

def test_effect_manager_update_empty_queue(effect_manager):
    effect_manager.update(10) # Should not raise error

def test_effect_manager_update_processes_current_effect(effect_manager, mock_terminal_ref):
    mock_effect = MagicMock(spec=BaseEffect)
    mock_effect.is_active = True
    mock_effect.is_complete = False
    effect_manager.effect_queue = [mock_effect]

    effect_manager.update(10)
    mock_effect.update.assert_called_once_with(10, mock_terminal_ref)

def test_effect_manager_update_effect_completes_starts_next(effect_manager, mock_terminal_ref):
    mock_effect1 = MagicMock(spec=BaseEffect)
    mock_effect1.is_active = True
    mock_effect1.is_complete = False
    
    mock_effect2 = MagicMock(spec=BaseEffect)
    mock_effect2.is_active = True # Will be set by its start
    mock_effect2.is_complete = False

    effect_manager.effect_queue = [mock_effect1, mock_effect2]
    mock_effect1.start(mock_terminal_ref) # Manually simulate it was started

    # Simulate effect1 completing during its update
    def effect1_update_side_effect(dt, term):
        mock_effect1.is_complete = True
        mock_effect1.is_active = False
    mock_effect1.update.side_effect = effect1_update_side_effect

    effect_manager.update(10)
    
    mock_effect1.update.assert_called_once_with(10, mock_terminal_ref)
    assert effect_manager.effect_queue == [mock_effect2] # effect1 popped
    mock_effect2.start.assert_called_once_with(mock_terminal_ref) # effect2 started

def test_effect_manager_update_last_effect_completes(effect_manager, mock_terminal_ref):
    mock_effect = MagicMock(spec=BaseEffect)
    mock_effect.is_active = True
    mock_effect.is_complete = False
    effect_manager.effect_queue = [mock_effect]
    mock_effect.start(mock_terminal_ref)

    def effect_update_side_effect(dt, term):
        mock_effect.is_complete = True
        mock_effect.is_active = False
    mock_effect.update.side_effect = effect_update_side_effect

    effect_manager.update(10)
    assert effect_manager.effect_queue == []

def test_effect_manager_is_effect_active(effect_manager):
    assert effect_manager.is_effect_active() is False
    effect_manager.effect_queue = [MagicMock()]
    assert effect_manager.is_effect_active() is True

def test_effect_manager_skip_current_effect_empty_queue(effect_manager):
    effect_manager.skip_current_effect() # Should not raise error

@patch('effects.TypingEffect', spec=TypingEffect)
def test_effect_manager_skip_typing_effect(MockTypingEffectCls, effect_manager, mock_terminal_ref):
    mock_typing_effect = MockTypingEffectCls.return_value
    mock_typing_effect.line_index_in_terminal = 0
    mock_typing_effect.full_text = "full"
    mock_typing_effect.fg_color = "fg"
    mock_typing_effect.bg_color = "bg"
    mock_typing_effect.bold = False
    effect_manager.effect_queue = [mock_typing_effect]

    effect_manager.skip_current_effect()
    
    assert mock_typing_effect.current_display_text == "full"
    assert mock_typing_effect.current_char_index == len("full")
    mock_terminal_ref.update_buffer_line.assert_called_once_with(0, "full", "fg", "bg", False)
    mock_typing_effect.finish.assert_called_once()

@patch('effects.CharacterCorruptionEffect', spec=CharacterCorruptionEffect)
def test_effect_manager_skip_corruption_effect(MockCCEffectCls, effect_manager, mock_terminal_ref):
    mock_cc_effect = MockCCEffectCls.return_value
    mock_cc_effect.line_index = 0
    mock_cc_effect.original_text = "original"
    mock_cc_effect.original_fg = "ofg"
    mock_cc_effect.original_bg = "obg"
    mock_cc_effect.original_bold = True
    effect_manager.effect_queue = [mock_cc_effect]

    effect_manager.skip_current_effect()
    mock_terminal_ref.update_buffer_line.assert_called_once_with(0, "original", "ofg", "obg", True)
    mock_cc_effect.finish.assert_called_once()

@patch('effects.TextFlickerEffect', spec=TextFlickerEffect)
def test_effect_manager_skip_flicker_effect(MockFlickerEffectCls, effect_manager, mock_terminal_ref):
    mock_flicker_effect = MockFlickerEffectCls.return_value
    mock_flicker_effect.line_index = 0
    mock_flicker_effect.original_text = "flicker_orig"
    mock_flicker_effect.original_fg = "f_ofg"
    mock_flicker_effect.original_bg = "f_obg"
    mock_flicker_effect.original_bold = False
    effect_manager.effect_queue = [mock_flicker_effect]

    effect_manager.skip_current_effect()
    mock_terminal_ref.update_buffer_line.assert_called_once_with(0, "flicker_orig", "f_ofg", "f_obg", False)
    mock_flicker_effect.finish.assert_called_once()

@patch('effects.TemporaryColorChangeEffect', spec=TemporaryColorChangeEffect)
def test_effect_manager_skip_temp_color_effect(MockTempColorEffectCls, effect_manager, mock_terminal_ref):
    mock_temp_color_effect = MockTempColorEffectCls.return_value
    mock_temp_color_effect.line_index = 0
    mock_temp_color_effect.original_text = "temp_orig"
    mock_temp_color_effect.original_fg = "tc_ofg"
    mock_temp_color_effect.original_bg = "tc_obg"
    mock_temp_color_effect.original_bold = True
    effect_manager.effect_queue = [mock_temp_color_effect]

    effect_manager.skip_current_effect()
    mock_terminal_ref.update_buffer_line.assert_called_once_with(0, "temp_orig", "tc_ofg", "tc_obg", True)
    mock_temp_color_effect.finish.assert_called_once()

@patch('effects.TextOverlayEffect', spec=TextOverlayEffect)
def test_effect_manager_skip_overlay_effect(MockOverlayEffectCls, effect_manager):
    mock_overlay_effect = MockOverlayEffectCls.return_value
    mock_overlay_effect.overlay_elements = ["some_element"]
    effect_manager.effect_queue = [mock_overlay_effect]

    effect_manager.skip_current_effect()
    assert mock_overlay_effect.overlay_elements == []
    mock_overlay_effect.finish.assert_called_once()

@patch('effects.TextJiggleEffect', spec=TextJiggleEffect)
def test_effect_manager_skip_jiggle_effect(MockJiggleEffectCls, effect_manager):
    mock_jiggle_effect = MockJiggleEffectCls.return_value
    mock_jiggle_effect.char_offsets = [(1,1)]
    effect_manager.effect_queue = [mock_jiggle_effect]

    effect_manager.skip_current_effect()
    assert mock_jiggle_effect.char_offsets == []
    mock_jiggle_effect.finish.assert_called_once()

@patch('effects.TimedDelayEffect', spec=TimedDelayEffect)
def test_effect_manager_skip_timed_delay_effect(MockTimedDelayEffectCls, effect_manager, mock_terminal_ref):
    mock_delay_effect = MockTimedDelayEffectCls.return_value
    effect_manager.effect_queue = [mock_delay_effect]

    effect_manager.skip_current_effect()
    # No specific action for TimedDelay other than finish
    mock_terminal_ref.update_buffer_line.assert_not_called() # Should not interact with terminal buffer
    mock_delay_effect.finish.assert_called_once()