import pytest
from game_state import (
    GameStateManager,
    STATE_DISCLAIMER,
    STATE_MAIN_TERMINAL,
    STATE_MINIGAME,
    STATE_NARRATIVE_SCREEN,
    STATE_SAVE_MENU,
    STATE_LLM_OUTPUT,
    STATE_MSFCONSOLE,
    STATE_ROLE_SELECTION,
    ROLE_NONE,
    ROLE_WHITE_HAT,
    ROLE_GREY_HAT,
    ROLE_BLACK_HAT
)

# Test the constants themselves
def test_state_constants():
    assert STATE_DISCLAIMER == "DISCLAIMER"
    assert STATE_MAIN_TERMINAL == "MAIN_TERMINAL"
    assert STATE_MINIGAME == "MINIGAME"
    assert STATE_NARRATIVE_SCREEN == "NARRATIVE_SCREEN"
    assert STATE_SAVE_MENU == "SAVE_MENU"
    assert STATE_LLM_OUTPUT == "LLM_OUTPUT"
    assert STATE_MSFCONSOLE == "MSFCONSOLE"
    assert STATE_ROLE_SELECTION == "ROLE_SELECTION"

def test_role_constants():
    assert ROLE_NONE is None
    assert ROLE_WHITE_HAT == "WHITE_HAT"
    assert ROLE_GREY_HAT == "GREY_HAT"
    assert ROLE_BLACK_HAT == "BLACK_HAT"

@pytest.fixture
def manager():
    """Provides a GameStateManager instance for each test."""
    return GameStateManager()

@pytest.fixture
def manager_with_custom_initial_state():
    """Provides a GameStateManager instance with a non-default initial state."""
    return GameStateManager(initial_state=STATE_MAIN_TERMINAL)

def test_initialization_default(manager):
    assert manager.current_state == STATE_DISCLAIMER
    assert manager.previous_state is None
    assert manager.player_role == ROLE_NONE

def test_initialization_custom(manager_with_custom_initial_state):
    manager = manager_with_custom_initial_state
    assert manager.current_state == STATE_MAIN_TERMINAL
    assert manager.previous_state is None
    assert manager.player_role == ROLE_NONE

def test_get_state(manager):
    assert manager.get_state() == STATE_DISCLAIMER
    manager.current_state = STATE_MINIGAME # Directly modify for testing get_state
    assert manager.get_state() == STATE_MINIGAME

def test_is_state(manager):
    assert manager.is_state(STATE_DISCLAIMER) is True
    assert manager.is_state(STATE_MAIN_TERMINAL) is False
    manager.current_state = STATE_MAIN_TERMINAL # Directly modify for testing
    assert manager.is_state(STATE_MAIN_TERMINAL) is True

def test_change_state_new_state(manager, capsys):
    initial_state = manager.get_state()
    new_state = STATE_MAIN_TERMINAL
    
    manager.change_state(new_state)
    
    assert manager.current_state == new_state
    assert manager.previous_state == initial_state
    assert manager.get_state() == new_state
    
    # captured = capsys.readouterr() # Print statement was removed
    # assert f"Game state changed from {initial_state} to {new_state}" in captured.out # Print statement was removed

def test_change_state_same_state(manager, capsys):
    initial_state = manager.get_state()
    manager.previous_state = "SOME_PREVIOUS_STATE" # Set a distinct previous state
    
    manager.change_state(initial_state) # Attempt to change to the same state
    
    assert manager.current_state == initial_state
    assert manager.previous_state == "SOME_PREVIOUS_STATE" # Previous state should not change
    
    # captured = capsys.readouterr() # Print statement was removed
    # assert f"Attempted to change to the same state: {initial_state}" in captured.out # Print statement was removed

def test_set_player_role_valid(manager, capsys):
    assert manager.player_role == ROLE_NONE
    
    manager.set_player_role(ROLE_WHITE_HAT)
    assert manager.player_role == ROLE_WHITE_HAT
    assert manager.get_player_role() == ROLE_WHITE_HAT
    # captured_white = capsys.readouterr() # Print statement was removed
    # assert f"Player role set to: {ROLE_WHITE_HAT}" in captured_white.out # Print statement was removed

    manager.set_player_role(ROLE_GREY_HAT)
    assert manager.player_role == ROLE_GREY_HAT
    # captured_grey = capsys.readouterr() # Print statement was removed
    # assert f"Player role set to: {ROLE_GREY_HAT}" in captured_grey.out # Print statement was removed

    manager.set_player_role(ROLE_BLACK_HAT)
    assert manager.player_role == ROLE_BLACK_HAT
    # captured_black = capsys.readouterr() # Print statement was removed
    # assert f"Player role set to: {ROLE_BLACK_HAT}" in captured_black.out # Print statement was removed

def test_set_player_role_invalid(manager, capsys):
    initial_role = manager.get_player_role() # Should be ROLE_NONE
    invalid_role = "INVALID_ROLE"
    
    manager.set_player_role(invalid_role)
    
    assert manager.player_role == initial_role # Role should not change
    assert manager.get_player_role() == initial_role
    
    # captured = capsys.readouterr() # Print statement was removed
    # assert f"Attempted to set invalid role: {invalid_role}" in captured.out # Print statement was removed

def test_get_player_role(manager):
    assert manager.get_player_role() == ROLE_NONE
    manager.player_role = ROLE_GREY_HAT # Directly modify for testing get_player_role
    assert manager.get_player_role() == ROLE_GREY_HAT

def test_initialize_player_attributes(manager):
    """Test that player attributes are correctly initialized based on role."""
    roles_and_expected_attributes = {
        ROLE_WHITE_HAT: {
            'background': "Former Aether Corp Security Specialist",
            'motivation': "Redemption and Protection",
            'initial_skill_focus': "System Integrity"
        },
        ROLE_GREY_HAT: {
            'background': "Investigative Journalist / Info Broker",
            'motivation': "Truth and Balance",
            'initial_skill_focus': "Information Gathering"
        },
        ROLE_BLACK_HAT: {
            'background': "Terminally Ill Programmer seeking Digital Transcendence",
            'motivation': "Power and Evolution",
            'initial_skill_focus': "Exploitation"
        }
    }

    for role, expected_attributes in roles_and_expected_attributes.items():
        manager.set_player_role(role)
        assert manager.player_attributes is not None
        assert manager.player_attributes == expected_attributes
        # Test getting individual attributes
        for attr_name, attr_value in expected_attributes.items():
            assert manager.get_player_attribute(attr_name) == attr_value

    # Test with an invalid role (attributes should remain empty or previous state)
    # Test with an invalid role (attributes should remain unchanged from the last valid role set)
    last_valid_role_attributes = manager.player_attributes.copy() # Capture attributes before invalid attempt
    manager.set_player_role("INVALID_ROLE")
    assert manager.player_attributes == last_valid_role_attributes # Attributes should not change


def test_state_transitions_and_role_setting(manager):
    # Initial
    assert manager.is_state(STATE_DISCLAIMER)
    assert manager.get_player_role() == ROLE_NONE

    # Change to role selection
    manager.change_state(STATE_ROLE_SELECTION)
    assert manager.is_state(STATE_ROLE_SELECTION)
    assert manager.previous_state == STATE_DISCLAIMER

    # Set role
    manager.set_player_role(ROLE_GREY_HAT)
    assert manager.get_player_role() == ROLE_GREY_HAT

    # Change to main terminal
    manager.change_state(STATE_MAIN_TERMINAL)
    assert manager.is_state(STATE_MAIN_TERMINAL)
    assert manager.previous_state == STATE_ROLE_SELECTION
    assert manager.get_player_role() == ROLE_GREY_HAT # Role persists

    # Change to MSFConsole
    manager.change_state(STATE_MSFCONSOLE)
    assert manager.is_state(STATE_MSFCONSOLE)
    assert manager.previous_state == STATE_MAIN_TERMINAL

    # Back to main terminal (simulating 'back' command)
    manager.change_state(STATE_MAIN_TERMINAL)
    assert manager.is_state(STATE_MAIN_TERMINAL)
    assert manager.previous_state == STATE_MSFCONSOLE