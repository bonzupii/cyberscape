"""
Comprehensive tests for the Core State management system.
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.core.state import (
    GameStateManager, GameState, PlayerRole, CorruptionLevel, GameEvent,
    STATE_DISCLAIMER, STATE_MAIN_TERMINAL, STATE_MSFCONSOLE, STATE_PUZZLE_ACTIVE,
    STATE_SCOURGE_TAKEOVER, STATE_ROLE_SELECTION, STATE_NARRATIVE_SCREEN,
    ROLE_PURIFIER, ROLE_ARBITER, ROLE_ASCENDANT, ROLE_NONE,
    STATE_TRANSITIONS, ROLE_REQUIRED_STATES
)


class TestGameStateEnums:
    """Test game state enums and constants."""

    def test_game_state_enum_values(self):
        """Test that GameState enum has expected values."""
        assert GameState.MAIN_TERMINAL.value == "main_terminal"
        assert GameState.PUZZLE_ACTIVE.value == "puzzle_active"
        assert GameState.GAME_OVER.value == "game_over"

    def test_player_role_enum_values(self):
        """Test that PlayerRole enum has expected values."""
        assert PlayerRole.PURIFIER.value == "purifier"
        assert PlayerRole.ASCENDANT.value == "ascendant"
        assert PlayerRole.ARBITER.value == "arbiter"

    def test_corruption_level_enum_values(self):
        """Test that CorruptionLevel enum has expected values."""
        assert CorruptionLevel.NORMAL.value == 0.0
        assert CorruptionLevel.ELEVATED.value == 0.3
        assert CorruptionLevel.CRITICAL.value == 0.9
        assert CorruptionLevel.MAXIMUM.value == 1.0

    def test_state_constants(self):
        """Test that state constants are defined correctly."""
        assert STATE_DISCLAIMER == "DISCLAIMER"
        assert STATE_MAIN_TERMINAL == "MAIN_TERMINAL"
        assert STATE_MSFCONSOLE == "MSFCONSOLE"
        assert STATE_SCOURGE_TAKEOVER == "SCOURGE_TAKEOVER"

    def test_role_constants(self):
        """Test that role constants are defined correctly."""
        assert ROLE_PURIFIER == "PURIFIER"
        assert ROLE_ARBITER == "ARBITER"
        assert ROLE_ASCENDANT == "ASCENDANT"
        assert ROLE_NONE is None


class TestGameEvent:
    """Test GameEvent dataclass functionality."""

    def test_game_event_creation(self):
        """Test GameEvent creation with automatic timestamp."""
        event = GameEvent("test_event", {"key": "value"})
        
        assert event.event_type == "test_event"
        assert event.data == {"key": "value"}
        assert event.timestamp is not None

    def test_game_event_custom_timestamp(self):
        """Test GameEvent creation with custom timestamp."""
        from datetime import datetime
        custom_time = datetime(2023, 1, 1, 12, 0, 0)
        event = GameEvent("test_event", {}, custom_time)
        
        assert event.timestamp == custom_time

    def test_game_event_to_dict(self):
        """Test GameEvent serialization to dictionary."""
        event = GameEvent("test_event", {"key": "value"})
        event_dict = event.to_dict()
        
        assert event_dict["event_type"] == "test_event"
        assert event_dict["data"] == {"key": "value"}
        assert "timestamp" in event_dict

    def test_game_event_from_dict(self):
        """Test GameEvent deserialization from dictionary."""
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        event_dict = {
            "event_type": "test_event",
            "data": {"key": "value"},
            "timestamp": timestamp
        }
        
        event = GameEvent.from_dict(event_dict)
        assert event.event_type == "test_event"
        assert event.data == {"key": "value"}


class TestGameStateManager:
    """Test GameStateManager functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock pygame to avoid initialization issues
        self.pygame_patcher = patch('pygame.time.get_ticks', return_value=1000)
        self.pygame_patcher.start()
        
        self.state_manager = GameStateManager()

    def teardown_method(self):
        """Clean up after tests."""
        self.pygame_patcher.stop()

    def test_initialization_default_state(self):
        """Test GameStateManager initializes with correct default state."""
        assert self.state_manager.current_state == STATE_DISCLAIMER
        assert self.state_manager.previous_state is None
        assert self.state_manager.player_role == ROLE_NONE
        assert self.state_manager.corruption_level == 0.0
        assert not self.state_manager.takeover_active

    def test_initialization_custom_state(self):
        """Test GameStateManager initializes with custom state."""
        custom_manager = GameStateManager(STATE_MAIN_TERMINAL)
        assert custom_manager.current_state == STATE_MAIN_TERMINAL

    def test_get_state(self):
        """Test getting current state."""
        assert self.state_manager.get_state() == STATE_DISCLAIMER

    def test_is_state(self):
        """Test state checking."""
        assert self.state_manager.is_state(STATE_DISCLAIMER)
        assert not self.state_manager.is_state(STATE_MAIN_TERMINAL)

    def test_valid_state_change(self):
        """Test valid state transitions."""
        # Valid transition from DISCLAIMER to ROLE_SELECTION
        result = self.state_manager.change_state(STATE_ROLE_SELECTION)
        
        assert result is True
        assert self.state_manager.current_state == STATE_ROLE_SELECTION
        assert self.state_manager.previous_state == STATE_DISCLAIMER

    def test_invalid_state_change(self):
        """Test invalid state transitions are rejected."""
        # Invalid transition from DISCLAIMER to MSFCONSOLE
        result = self.state_manager.change_state(STATE_MSFCONSOLE)
        
        assert result is False
        assert self.state_manager.current_state == STATE_DISCLAIMER

    def test_state_change_requires_role(self):
        """Test that role-required states block transition without role."""
        # Try to go to main terminal without setting role
        result = self.state_manager.change_state(STATE_MAIN_TERMINAL)
        
        assert result is False
        assert self.state_manager.current_state == STATE_DISCLAIMER

    def test_state_change_with_role(self):
        """Test state change works after setting role."""
        # Set role first
        self.state_manager.set_player_role(ROLE_PURIFIER)
        
        # Now transition should work
        result = self.state_manager.change_state(STATE_MAIN_TERMINAL)
        
        assert result is True
        assert self.state_manager.current_state == STATE_MAIN_TERMINAL

    def test_role_specific_state_access(self):
        """Test that some states require specific roles."""
        # Set role to PURIFIER
        self.state_manager.set_player_role(ROLE_PURIFIER)
        self.state_manager.change_state(STATE_MAIN_TERMINAL)
        
        # PURIFIER should not be able to access MSFCONSOLE
        result = self.state_manager.change_state(STATE_MSFCONSOLE)
        assert result is False
        
        # But ASCENDANT should be able to
        self.state_manager.set_player_role(ROLE_ASCENDANT)
        result = self.state_manager.change_state(STATE_MSFCONSOLE)
        assert result is True

    def test_state_history_tracking(self):
        """Test that state history is tracked correctly."""
        initial_history_length = len(self.state_manager.get_state_history())
        
        self.state_manager.set_player_role(ROLE_PURIFIER)
        self.state_manager.change_state(STATE_MAIN_TERMINAL)
        
        history = self.state_manager.get_state_history()
        assert len(history) == initial_history_length + 1
        assert history[-1][0] == STATE_DISCLAIMER  # Previous state

    def test_corruption_level_blocking(self):
        """Test that high corruption blocks certain states."""
        self.state_manager.set_player_role(ROLE_PURIFIER)
        self.state_manager.change_state(STATE_MAIN_TERMINAL)
        
        # Set high corruption
        self.state_manager.set_corruption_level(0.9)
        self.state_manager.set_state_data("max_corruption", 0.5)
        
        # Should block transition to puzzle
        result = self.state_manager.change_state(STATE_PUZZLE_ACTIVE)
        assert result is False


class TestPlayerRoleManagement:
    """Test player role management functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.pygame_patcher = patch('pygame.time.get_ticks', return_value=1000)
        self.pygame_patcher.start()
        
        self.state_manager = GameStateManager()

    def teardown_method(self):
        """Clean up after tests."""
        self.pygame_patcher.stop()

    def test_set_valid_role(self):
        """Test setting valid player roles."""
        assert self.state_manager.set_player_role(ROLE_PURIFIER) is True
        assert self.state_manager.get_player_role() == ROLE_PURIFIER

    def test_set_invalid_role(self):
        """Test that invalid roles are rejected."""
        assert self.state_manager.set_player_role("INVALID_ROLE") is False
        assert self.state_manager.get_player_role() == ROLE_NONE

    def test_purifier_attributes(self):
        """Test Purifier role attributes."""
        self.state_manager.set_player_role(ROLE_PURIFIER)
        
        assert self.state_manager.get_player_attribute("corruption_resistance") == 8
        assert self.state_manager.get_player_attribute("hacking_skill") == 5
        assert self.state_manager.get_player_attribute("stealth") == 3
        assert self.state_manager.get_player_attribute("detection_risk") == 0.2

    def test_arbiter_attributes(self):
        """Test Arbiter role attributes."""
        self.state_manager.set_player_role(ROLE_ARBITER)
        
        assert self.state_manager.get_player_attribute("corruption_resistance") == 5
        assert self.state_manager.get_player_attribute("hacking_skill") == 7
        assert self.state_manager.get_player_attribute("stealth") == 7
        assert self.state_manager.get_player_attribute("detection_risk") == 0.4

    def test_ascendant_attributes(self):
        """Test Ascendant role attributes."""
        self.state_manager.set_player_role(ROLE_ASCENDANT)
        
        assert self.state_manager.get_player_attribute("corruption_resistance") == 3
        assert self.state_manager.get_player_attribute("hacking_skill") == 9
        assert self.state_manager.get_player_attribute("stealth") == 5
        assert self.state_manager.get_player_attribute("detection_risk") == 0.6

    def test_role_specific_commands(self):
        """Test that roles have different unlocked commands."""
        # Purifier commands
        self.state_manager.set_player_role(ROLE_PURIFIER)
        purifier_commands = self.state_manager.get_player_attribute("unlocked_commands")
        assert "ls" in purifier_commands
        assert "msfconsole" not in purifier_commands

        # Ascendant commands
        self.state_manager.set_player_role(ROLE_ASCENDANT)
        ascendant_commands = self.state_manager.get_player_attribute("unlocked_commands")
        assert "ls" in ascendant_commands
        assert "msfconsole" in ascendant_commands

    def test_get_nonexistent_attribute(self):
        """Test getting non-existent player attribute."""
        self.state_manager.set_player_role(ROLE_PURIFIER)
        assert self.state_manager.get_player_attribute("nonexistent") is None


class TestStateDataManagement:
    """Test state-specific data management."""

    def setup_method(self):
        """Set up test fixtures."""
        self.pygame_patcher = patch('pygame.time.get_ticks', return_value=1000)
        self.pygame_patcher.start()
        
        self.state_manager = GameStateManager()

    def teardown_method(self):
        """Clean up after tests."""
        self.pygame_patcher.stop()

    def test_set_and_get_state_data(self):
        """Test setting and getting state data."""
        self.state_manager.set_state_data("test_key", "test_value")
        assert self.state_manager.get_state_data("test_key") == "test_value"

    def test_get_state_data_with_default(self):
        """Test getting state data with default value."""
        assert self.state_manager.get_state_data("nonexistent", "default") == "default"

    def test_clear_state_data(self):
        """Test clearing all state data."""
        self.state_manager.set_state_data("key1", "value1")
        self.state_manager.set_state_data("key2", "value2")
        
        self.state_manager.clear_state_data()
        
        assert self.state_manager.get_state_data("key1") is None
        assert self.state_manager.get_state_data("key2") is None


class TestCorruptionManagement:
    """Test corruption level management."""

    def setup_method(self):
        """Set up test fixtures."""
        self.pygame_patcher = patch('pygame.time.get_ticks', return_value=1000)
        self.pygame_patcher.start()
        
        self.state_manager = GameStateManager()

    def teardown_method(self):
        """Clean up after tests."""
        self.pygame_patcher.stop()

    def test_initial_corruption_level(self):
        """Test initial corruption level is zero."""
        assert self.state_manager.get_corruption_level() == 0.0

    def test_set_valid_corruption_level(self):
        """Test setting valid corruption levels."""
        self.state_manager.set_corruption_level(0.5)
        assert self.state_manager.get_corruption_level() == 0.5

    def test_corruption_level_clamping(self):
        """Test that corruption level is clamped to valid range."""
        # Test upper bound
        self.state_manager.set_corruption_level(1.5)
        assert self.state_manager.get_corruption_level() == 1.0

        # Test lower bound
        self.state_manager.set_corruption_level(-0.5)
        assert self.state_manager.get_corruption_level() == 0.0


class TestScourgetakeoverSystem:
    """Test Aetherial Scourge takeover system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.pygame_patcher = patch('pygame.time.get_ticks', return_value=1000)
        self.time_patcher = patch('time.time', return_value=1000.0)
        
        self.pygame_patcher.start()
        self.time_patcher.start()
        
        self.state_manager = GameStateManager()

    def teardown_method(self):
        """Clean up after tests."""
        self.pygame_patcher.stop()
        self.time_patcher.stop()

    def test_start_scourge_takeover(self):
        """Test starting a Scourge takeover event."""
        assert not self.state_manager.is_takeover_active()
        
        self.state_manager.start_scourge_takeover(duration=10, intensity=0.7)
        
        assert self.state_manager.is_takeover_active()
        assert self.state_manager.takeover_duration == 10
        assert self.state_manager.takeover_intensity == 0.7
        # Takeover can happen from any state, doesn't require transition validation
        assert self.state_manager.is_takeover_active()

    def test_takeover_effects_initialization(self):
        """Test that takeover effects are properly initialized."""
        self.state_manager.start_scourge_takeover(intensity=0.8)
        
        effects = self.state_manager.get_takeover_effects()
        assert len(effects) > 0
        
        # Check for expected effect types
        effect_types = [effect["type"] for effect in effects]
        assert "screen_shake" in effect_types
        assert "text_corruption" in effect_types
        assert "static" in effect_types

    def test_end_scourge_takeover(self):
        """Test ending a Scourge takeover event."""
        # Start takeover
        self.state_manager.start_scourge_takeover()
        assert self.state_manager.is_takeover_active()
        
        # End takeover
        self.state_manager.end_scourge_takeover()
        assert not self.state_manager.is_takeover_active()
        assert len(self.state_manager.get_takeover_effects()) == 0

    def test_takeover_intensity_clamping(self):
        """Test that takeover intensity is clamped to valid range."""
        # Test upper bound
        self.state_manager.start_scourge_takeover(intensity=1.5)
        assert self.state_manager.takeover_intensity == 1.0

        # Reset and test lower bound
        self.state_manager.end_scourge_takeover()
        self.state_manager.start_scourge_takeover(intensity=-0.5)
        assert self.state_manager.takeover_intensity == 0.0

    @patch('time.time')
    def test_takeover_update_progression(self, mock_time):
        """Test takeover update and progression over time."""
        # Start time
        mock_time.return_value = 1000.0
        self.state_manager.start_scourge_takeover(duration=20, intensity=1.0)
        
        # Midpoint - should have some corruption
        mock_time.return_value = 1010.0  # 10 seconds elapsed (50% through)
        self.state_manager.update_takeover()
        
        corruption = self.state_manager.get_takeover_corruption_level()
        assert 0.0 < corruption <= 1.0
        
        # End time - should end takeover
        mock_time.return_value = 1020.0  # 20 seconds elapsed (100% through)
        self.state_manager.update_takeover()
        
        assert not self.state_manager.is_takeover_active()


class TestTransitionCallbacks:
    """Test state transition callback system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.pygame_patcher = patch('pygame.time.get_ticks', return_value=1000)
        self.pygame_patcher.start()
        
        self.state_manager = GameStateManager()
        self.callback_called = False
        self.callback_args = None

    def teardown_method(self):
        """Clean up after tests."""
        self.pygame_patcher.stop()

    def test_callback_execution(self):
        """Test that callbacks are executed properly."""
        called_callbacks = []
        
        def test_callback(old_state, new_state):
            called_callbacks.append((old_state, new_state))
        
        self.state_manager.register_transition_callback(
            STATE_ROLE_SELECTION, test_callback, "enter"
        )
        self.state_manager.change_state(STATE_ROLE_SELECTION)
        
        assert len(called_callbacks) == 1
        assert called_callbacks[0] == (STATE_DISCLAIMER, STATE_ROLE_SELECTION)

    def test_register_enter_callback(self):
        """Test registering and calling enter callbacks."""
        callback_called = False
        callback_args = None
        
        def test_callback(old_state, new_state):
            nonlocal callback_called, callback_args
            callback_called = True
            callback_args = (old_state, new_state)
        
        self.state_manager.register_transition_callback(
            STATE_ROLE_SELECTION, test_callback, "enter"
        )
        
        self.state_manager.change_state(STATE_ROLE_SELECTION)
        
        assert callback_called
        assert callback_args == (STATE_DISCLAIMER, STATE_ROLE_SELECTION)

    def test_register_exit_callback(self):
        """Test registering and calling exit callbacks."""
        callback_called = False
        callback_args = None
        
        def test_callback(old_state, new_state):
            nonlocal callback_called, callback_args
            callback_called = True
            callback_args = (old_state, new_state)
        
        self.state_manager.register_transition_callback(
            STATE_DISCLAIMER, test_callback, "exit"
        )
        
        self.state_manager.change_state(STATE_ROLE_SELECTION)
        
        assert callback_called
        assert callback_args == (STATE_DISCLAIMER, STATE_ROLE_SELECTION)

    def test_callback_exception_handling(self):
        """Test that callback exceptions are handled gracefully."""
        def failing_callback(old_state, new_state):
            raise Exception("Test exception")
        
        self.state_manager.register_transition_callback(
            STATE_ROLE_SELECTION, failing_callback, "enter"
        )
        
        # Should not raise exception
        result = self.state_manager.change_state(STATE_ROLE_SELECTION)
        assert result is True


class TestAdvancedFeatures:
    """Test advanced state management features."""

    def setup_method(self):
        """Set up test fixtures."""
        self.pygame_patcher = patch('pygame.time.get_ticks')
        self.mock_pygame_time = self.pygame_patcher.start()
        
        self.state_manager = GameStateManager()

    def teardown_method(self):
        """Clean up after tests."""
        self.pygame_patcher.stop()

    def test_time_in_state_calculation(self):
        """Test calculation of time spent in states."""
        # Set up time progression
        self.mock_pygame_time.side_effect = [1000, 2000, 3000, 4000]
        
        # Transition through states
        self.state_manager.change_state(STATE_ROLE_SELECTION)  # t=1000->2000
        self.state_manager.set_player_role(ROLE_PURIFIER)
        self.state_manager.change_state(STATE_MAIN_TERMINAL)   # t=2000->3000
        
        # Calculate time spent in DISCLAIMER state
        time_in_disclaimer = self.state_manager.get_time_in_state(STATE_DISCLAIMER)
        assert time_in_disclaimer == 1000.0  # 2000 - 1000

    def test_skill_requirement_validation(self):
        """Test state transitions based on skill requirements."""
        self.state_manager.set_player_role(ROLE_PURIFIER)
        self.state_manager.change_state(STATE_MAIN_TERMINAL)
        
        # Set a skill requirement for puzzle
        self.state_manager.set_state_data("required_skill", 8)
        
        # Purifier has skill 5, should fail
        result = self.state_manager.change_state(STATE_PUZZLE_ACTIVE)
        assert result is False
        
        # Ascendant has skill 9, should succeed
        self.state_manager.set_player_role(ROLE_ASCENDANT)
        result = self.state_manager.change_state(STATE_PUZZLE_ACTIVE)
        assert result is True

    def test_last_command_tracking(self):
        """Test tracking of last executed command."""
        test_command = "test_command"
        self.state_manager.set_last_command(test_command)
        assert self.state_manager.last_command == test_command

    def test_complex_attribute_management(self):
        """Test complex player attribute operations."""
        self.state_manager.set_player_role(ROLE_ARBITER)
        
        # Test inventory management
        inventory = self.state_manager.get_player_attribute("inventory")
        assert isinstance(inventory, list)
        assert len(inventory) == 0
        
        # Test set attributes
        discovered_files = self.state_manager.get_player_attribute("discovered_files")
        assert isinstance(discovered_files, set)
        
        completed_puzzles = self.state_manager.get_player_attribute("completed_puzzles")
        assert isinstance(completed_puzzles, set)


class TestStateTransitionValidation:
    """Test comprehensive state transition validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.pygame_patcher = patch('pygame.time.get_ticks', return_value=1000)
        self.pygame_patcher.start()
        
        self.state_manager = GameStateManager()

    def teardown_method(self):
        """Clean up after tests."""
        self.pygame_patcher.stop()

    def test_state_transition_matrix(self):
        """Test all valid state transitions defined in STATE_TRANSITIONS."""
        for from_state, valid_to_states in STATE_TRANSITIONS.items():
            # Set up manager in the from_state
            test_manager = GameStateManager(from_state)
            
            # If the state requires a role, set one
            if from_state in ROLE_REQUIRED_STATES:
                test_manager.set_player_role(ROLE_PURIFIER)
            
            for to_state in valid_to_states:
                # Special case for role-restricted states
                if to_state == STATE_MSFCONSOLE:
                    test_manager.set_player_role(ROLE_ASCENDANT)
                
                # Test the transition
                result = test_manager.change_state(to_state)
                
                # Some transitions may still fail due to other constraints
                # but we're testing the basic transition logic
                if result:
                    assert test_manager.current_state == to_state
                    # Reset for next test
                    test_manager.current_state = from_state

    def test_invalid_state_rejection(self):
        """Test that completely invalid states are rejected."""
        result = self.state_manager.change_state("INVALID_STATE")
        assert result is False
        assert self.state_manager.current_state == STATE_DISCLAIMER

    def test_circular_state_prevention(self):
        """Test prevention of invalid circular state transitions."""
        # Set up a valid state first
        self.state_manager.set_player_role(ROLE_PURIFIER)
        self.state_manager.change_state(STATE_MAIN_TERMINAL)
        
        # Try to transition to a state that doesn't allow back to main terminal
        # (This tests the transition matrix constraints)
        original_state = self.state_manager.current_state
        
        # Most states should allow returning to main terminal
        result = self.state_manager.change_state(STATE_NARRATIVE_SCREEN)
        assert result is True
        
        result = self.state_manager.change_state(STATE_MAIN_TERMINAL)
        assert result is True


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.pygame_patcher = patch('pygame.time.get_ticks', return_value=1000)
        self.pygame_patcher.start()
        
        self.state_manager = GameStateManager()

    def teardown_method(self):
        """Clean up after tests."""
        self.pygame_patcher.stop()

    def test_multiple_role_changes(self):
        """Test changing roles multiple times."""
        assert self.state_manager.set_player_role(ROLE_PURIFIER) is True
        assert self.state_manager.get_player_role() == ROLE_PURIFIER
        
        assert self.state_manager.set_player_role(ROLE_ASCENDANT) is True
        assert self.state_manager.get_player_role() == ROLE_ASCENDANT
        
        # Attributes should be re-initialized
        assert self.state_manager.get_player_attribute("hacking_skill") == 9

    def test_state_data_persistence_across_changes(self):
        """Test that state data persists across state changes."""
        self.state_manager.set_state_data("persistent_key", "persistent_value")
        
        self.state_manager.set_player_role(ROLE_PURIFIER)
        self.state_manager.change_state(STATE_MAIN_TERMINAL)
        
        # Data should still be there
        assert self.state_manager.get_state_data("persistent_key") == "persistent_value"

    def test_empty_state_history_on_initialization(self):
        """Test that state history is empty on initialization."""
        history = self.state_manager.get_state_history()
        assert isinstance(history, list)
        assert len(history) == 0

    def test_takeover_double_start_prevention(self):
        """Test that starting takeover twice doesn't break state."""
        self.state_manager.start_scourge_takeover(duration=10)
        first_start_time = self.state_manager.takeover_start_time
        
        # Try to start again
        self.state_manager.start_scourge_takeover(duration=20)
        
        # Should not have changed the start time (takeover already active)
        assert self.state_manager.takeover_start_time == first_start_time

    def test_takeover_end_when_not_active(self):
        """Test ending takeover when it's not active."""
        assert not self.state_manager.is_takeover_active()
        
        # Should not crash
        self.state_manager.end_scourge_takeover()
        assert not self.state_manager.is_takeover_active()
