"""Game state manager for Cyberscape: Digital Dread.

This module manages the game state, including:
- Player role and attributes
- Corruption level
- Game progress
- Event handling
"""

import enum
import json
import logging
import os
from typing import Dict, List, Optional, Any, Set, Tuple
import pygame
import time
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GameState(enum.Enum):
    """Enum representing different game states."""
    MAIN_TERMINAL = "main_terminal"
    PUZZLE_ACTIVE = "puzzle_active"
    DIALOG_ACTIVE = "dialog_active"
    CUTSCENE = "cutscene"
    MENU = "menu"
    GAME_OVER = "game_over"
    VICTORY = "victory"
    LOADING = "loading"
    SAVE = "save"
    LOAD = "load"
    SETTINGS = "settings"
    HELP = "help"
    INVALID_STATE = "invalid_state"

class PlayerRole(enum.Enum):
    """Enum representing different player roles."""
    PURIFIER = "purifier"
    ASCENDANT = "ascendant"
    ARBITER = "arbiter"
    SCRIPT_KIDDIE = "script_kiddie"
    SYSTEM_ADMIN = "system_admin"
    SECURITY_EXPERT = "security_expert"
    INVALID_ROLE = "invalid_role"

class CorruptionLevel(enum.Enum):
    """Enum representing different corruption levels."""
    NORMAL = 0.0
    ELEVATED = 0.3
    HIGH = 0.6
    CRITICAL = 0.9
    MAXIMUM = 1.0

@dataclass
class GameEvent:
    """Represents a game event."""
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            event_type=d["event_type"],
            data=d["data"],
            timestamp=datetime.fromisoformat(d["timestamp"])
        )

# --- Game States ---
# Using strings for now, can be an Enum or more complex objects later
STATE_DISCLAIMER = "DISCLAIMER"
STATE_MAIN_TERMINAL = "MAIN_TERMINAL"
STATE_MINIGAME = "MINIGAME"
STATE_NARRATIVE_SCREEN = "NARRATIVE_SCREEN"
STATE_SAVE_MENU = "SAVE_MENU"
STATE_LLM_OUTPUT = "LLM_OUTPUT"
STATE_MSFCONSOLE = "MSFCONSOLE" # New state for msfconsole
STATE_ROLE_SELECTION = "ROLE_SELECTION" # New state for choosing a role
STATE_PUZZLE_ACTIVE = "PUZZLE_ACTIVE" # New state for when a puzzle is active
STATE_SCOURGE_TAKEOVER = "SCOURGE_TAKEOVER"  # New state for Aetherial Scourge takeover
# Add more states as needed

# --- Player Roles ---
ROLE_NONE = None # Default before selection
ROLE_PURIFIER = "PURIFIER"
ROLE_ARBITER = "ARBITER"
ROLE_ASCENDANT = "ASCENDANT"

# --- State Transition Rules ---
# Define valid state transitions and their requirements
STATE_TRANSITIONS: Dict[str, Set[str]] = {
    STATE_DISCLAIMER: {STATE_ROLE_SELECTION, STATE_MAIN_TERMINAL},  # Allow direct transition to MAIN_TERMINAL
    STATE_ROLE_SELECTION: {STATE_MAIN_TERMINAL},
    STATE_MAIN_TERMINAL: {
        STATE_MSFCONSOLE,
        STATE_PUZZLE_ACTIVE,
        STATE_NARRATIVE_SCREEN,
        STATE_SAVE_MENU,
        STATE_LLM_OUTPUT,
        STATE_SCOURGE_TAKEOVER
    },
    STATE_MSFCONSOLE: {STATE_MAIN_TERMINAL, STATE_SCOURGE_TAKEOVER},
    STATE_PUZZLE_ACTIVE: {STATE_MAIN_TERMINAL, STATE_SCOURGE_TAKEOVER},
    STATE_NARRATIVE_SCREEN: {STATE_MAIN_TERMINAL, STATE_SCOURGE_TAKEOVER},
    STATE_SAVE_MENU: {STATE_MAIN_TERMINAL, STATE_SCOURGE_TAKEOVER},
    STATE_LLM_OUTPUT: {STATE_MAIN_TERMINAL, STATE_SCOURGE_TAKEOVER},
    STATE_MINIGAME: {STATE_MAIN_TERMINAL, STATE_SCOURGE_TAKEOVER},
    STATE_SCOURGE_TAKEOVER: {
        STATE_MAIN_TERMINAL, STATE_MSFCONSOLE, STATE_PUZZLE_ACTIVE, STATE_NARRATIVE_SCREEN, STATE_SAVE_MENU, STATE_LLM_OUTPUT, STATE_MINIGAME
    }
}

# --- Role Requirements ---
# Define which states require a role to be set
ROLE_REQUIRED_STATES = {
    STATE_MAIN_TERMINAL,
    STATE_MSFCONSOLE,
    STATE_PUZZLE_ACTIVE,
    STATE_NARRATIVE_SCREEN,
    STATE_SAVE_MENU,
    STATE_LLM_OUTPUT,
    STATE_MINIGAME
}

class GameStateManager:
    """Manages the game's state and player role.
    
    This class handles:
    - Tracking the current game state
    - Managing player role and alignment
    - Validating state transitions
    - Maintaining game progression
    """
    
    def __init__(self, initial_state=STATE_DISCLAIMER):
        """Initialize the game state manager.
        
        Args:
            initial_state: The initial game state
        """
        self.current_state = initial_state
        self.previous_state = None
        self.player_role = ROLE_NONE
        self.player_attributes = {}
        self.state_history: List[Tuple[str, float]] = []  # (state, timestamp)
        self.state_data: Dict[str, Any] = {}  # State-specific data
        self.transition_callbacks: Dict[str, List[callable]] = {}  # State transition callbacks
        
        # Aetherial Scourge takeover state
        self.takeover_active = False
        self.takeover_start_time = 0
        self.takeover_duration = 20  # seconds
        self.takeover_intensity = 0.0  # 0.0 to 1.0
        self.takeover_effects = []
        self.takeover_text = ""
        self.takeover_corruption_level = 0.0
        
        self.corruption_level = 0.0  # Add corruption level attribute
        
        self.last_command = None
        
    def change_state(self, new_state: str) -> bool:
        """Changes the current game state with validation.
        
        Args:
            new_state: The new state to transition to
            
        Returns:
            bool: True if state change was successful
        """
        if not self._validate_state_transition(new_state):
            logger.warning(f"Invalid state transition from {self.current_state} to {new_state}")
            return False
            
        # Store current state in history
        self.state_history.append((self.current_state, pygame.time.get_ticks()))
        
        # Call transition callbacks
        self._call_transition_callbacks(self.current_state, new_state)
        
        # Update state
        self.previous_state = self.current_state
        self.current_state = new_state
        
        logger.info(f"Game state changed from {self.previous_state} to {self.current_state}")
        return True
    
    def _validate_state_transition(self, new_state: str) -> bool:
        """Validate if a state transition is allowed.
        
        Args:
            new_state: The state to transition to
            
        Returns:
            bool: True if transition is valid
        """
        # Check if new state exists in transitions
        if new_state not in STATE_TRANSITIONS:
            logger.error(f"Invalid state: {new_state}")
            return False
            
        # Check if transition is allowed
        if new_state not in STATE_TRANSITIONS[self.current_state]:
            logger.error(f"Invalid transition from {self.current_state} to {new_state}")
            return False
            
        # Check role requirements
        if new_state in ROLE_REQUIRED_STATES:
            if self.player_role == ROLE_NONE:
                logger.error(f"Role required for state {new_state}")
                return False
                
            # Check role-specific state access
            if new_state == STATE_MSFCONSOLE and self.player_role != ROLE_ASCENDANT:
                logger.error(f"Only Ascendant role can access MSF Console")
                return False
                
            if new_state == STATE_PUZZLE_ACTIVE:
                required_skill = self.get_state_data("required_skill", 0)
                if self.player_attributes.get("hacking_skill", 0) < required_skill:
                    logger.error(f"Insufficient hacking skill for puzzle (required: {required_skill})")
                    return False
                    
        # Check corruption level for certain states
        if new_state in {STATE_MSFCONSOLE, STATE_PUZZLE_ACTIVE}:
            max_corruption = self.get_state_data("max_corruption", 1.0)
            if self.corruption_level > max_corruption:
                logger.error(f"Corruption level too high for state {new_state}")
                return False
                
        return True
    
    def _call_transition_callbacks(self, old_state: str, new_state: str) -> None:
        """Call registered callbacks for state transition.
        
        Args:
            old_state: The previous state
            new_state: The new state
        """
        # Call exit callbacks for old state
        for callback in self.transition_callbacks.get(f"exit_{old_state}", []):
            try:
                callback(old_state, new_state)
            except Exception as e:
                logger.error(f"Error in exit callback for {old_state}: {e}")
        
        # Call enter callbacks for new state
        for callback in self.transition_callbacks.get(f"enter_{new_state}", []):
            try:
                callback(old_state, new_state)
            except Exception as e:
                logger.error(f"Error in enter callback for {new_state}: {e}")
    
    def register_transition_callback(self, state: str, callback: callable, transition_type: str = "enter") -> None:
        """Register a callback for state transitions.
        
        Args:
            state: The state to register callback for
            callback: The callback function
            transition_type: Either "enter" or "exit"
        """
        key = f"{transition_type}_{state}"
        if key not in self.transition_callbacks:
            self.transition_callbacks[key] = []
        self.transition_callbacks[key].append(callback)
    
    def get_state(self) -> str:
        """Returns the current game state."""
        return self.current_state
    
    def is_state(self, state_to_check: str) -> bool:
        """Checks if the current state matches the given state."""
        return self.current_state == state_to_check
    
    def set_player_role(self, role: str) -> bool:
        """Sets the player's chosen role and initializes their attributes.
        
        Args:
            role: The role to set
            
        Returns:
            bool: True if role was set successfully
        """
        if role in [ROLE_PURIFIER, ROLE_ARBITER, ROLE_ASCENDANT]:
            self.player_role = role
            self.initialize_player_attributes()
            logger.info(f"Player role set to: {self.player_role}")
            return True
        logger.warning(f"Attempted to set invalid role: {role}")
        return False
    
    def initialize_player_attributes(self) -> None:
        """Initialize player attributes based on their role."""
        if self.player_role == ROLE_NONE:
            return
        # Base attributes for all roles
        self.player_attributes = {
            "health": 100,
            "corruption_resistance": 0,
            "hacking_skill": 0,
            "stealth": 0,
            "detection_risk": 0.0,
            "inventory": [],
            "discovered_files": set(),
            "completed_puzzles": set(),
            "current_mission": None,
            "mission_progress": 0.0,
            "last_save_time": time.time(),
            "play_time": 0.0,
            "corruption_exposure": 0.0,
            "scourge_awareness": 0.0,
            "system_access_level": 0,
            "unlocked_commands": set(),
            "active_effects": set(),
            "known_vulnerabilities": set(),
            "security_clearance": 0,
            "reputation": 0.0
        }
        # Role-specific attributes (match test expectations)
        if self.player_role == ROLE_PURIFIER:
            self.player_attributes.update({
                "corruption_resistance": 8,
                "hacking_skill": 5,
                "stealth": 3,
                "detection_risk": 0.2,
                "system_access_level": 1,
                "security_clearance": 2,
                "reputation": 0.5,
                "unlocked_commands": {"ls", "cd", "cat", "help", "clear", "whoami", "hostname"}
            })
        elif self.player_role == ROLE_ARBITER:
            self.player_attributes.update({
                "corruption_resistance": 5,
                "hacking_skill": 7,
                "stealth": 7,
                "detection_risk": 0.4,
                "system_access_level": 2,
                "security_clearance": 1,
                "reputation": 0.3,
                "unlocked_commands": {"ls", "cd", "cat", "help", "clear", "whoami", "hostname", "mv", "cp", "rm"}
            })
        elif self.player_role == ROLE_ASCENDANT:
            self.player_attributes.update({
                "corruption_resistance": 3,
                "hacking_skill": 9,
                "stealth": 5,
                "detection_risk": 0.6,
                "system_access_level": 3,
                "security_clearance": 0,
                "reputation": 0.1,
                "unlocked_commands": {"ls", "cd", "cat", "help", "clear", "whoami", "hostname", "mv", "cp", "rm", "msfconsole"}
            })
        logger.info(f"Initialized player attributes for role: {self.player_role}")
    
    def get_player_role(self) -> str:
        """Returns the player's chosen role."""
        return self.player_role
    
    def get_player_attribute(self, attribute_name: str) -> Any:
        """Returns a specific player attribute, or None if not found."""
        return self.player_attributes.get(attribute_name)
    
    def set_state_data(self, key: str, value: Any) -> None:
        """Set state-specific data.
        
        Args:
            key: Data key
            value: Data value
        """
        self.state_data[key] = value
    
    def get_state_data(self, key: str, default: Any = None) -> Any:
        """Get state-specific data.
        
        Args:
            key: Data key
            default: Default value if key not found
            
        Returns:
            Any: The stored data or default value
        """
        return self.state_data.get(key, default)
    
    def clear_state_data(self) -> None:
        """Clear all state-specific data."""
        self.state_data.clear()
    
    def get_state_history(self) -> List[Tuple[str, float]]:
        """Get the history of state transitions.
        
        Returns:
            List[Tuple[str, float]]: List of (state, timestamp) pairs
        """
        return self.state_history.copy()
    
    def get_time_in_state(self, state: str) -> float:
        """Get the total time spent in a state.
        
        Args:
            state: The state to check
            
        Returns:
            float: Total time in milliseconds
        """
        total_time = 0.0
        for i in range(len(self.state_history) - 1):
            if self.state_history[i][0] == state:
                total_time += self.state_history[i + 1][1] - self.state_history[i][1]
        return total_time

    def start_scourge_takeover(self, duration=20, intensity=0.5):
        """Start an Aetherial Scourge takeover event.
        
        Args:
            duration: Duration of the takeover in seconds
            intensity: Intensity of the takeover (0.0 to 1.0)
        """
        if not self.takeover_active:
            self.takeover_active = True
            self.takeover_start_time = time.time()
            self.takeover_duration = duration
            self.takeover_intensity = max(0.0, min(1.0, intensity))
            self.takeover_effects = []
            self.takeover_text = ""
            self.takeover_corruption_level = 0.0
            
            # Change state to takeover
            self.change_state(STATE_SCOURGE_TAKEOVER)
            
            # Initialize takeover effects
            self._initialize_takeover_effects()
            
            logger.info(f"Started Aetherial Scourge takeover (duration: {duration}s, intensity: {intensity})")

    def _initialize_takeover_effects(self):
        """Initialize effects for the takeover event."""
        # Add visual effects
        self.takeover_effects.extend([
            {"type": "screen_shake", "intensity": self.takeover_intensity * 0.5},
            {"type": "text_corruption", "intensity": self.takeover_intensity},
            {"type": "color_shift", "intensity": self.takeover_intensity * 0.7},
            {"type": "glitch", "intensity": self.takeover_intensity * 0.8}
        ])
        
        # Add audio effects
        self.takeover_effects.extend([
            {"type": "static", "intensity": self.takeover_intensity * 0.6},
            {"type": "whisper", "intensity": self.takeover_intensity * 0.4},
            {"type": "ambient", "intensity": self.takeover_intensity * 0.3}
        ])

    def update_takeover(self):
        """Update the takeover state and effects."""
        if not self.takeover_active:
            return
            
        current_time = time.time()
        elapsed = current_time - self.takeover_start_time
        
        # Check if takeover should end
        if elapsed >= self.takeover_duration:
            self.end_scourge_takeover()
            return
            
        # Update corruption level based on elapsed time
        progress = elapsed / self.takeover_duration
        self.takeover_corruption_level = self.takeover_intensity * (1.0 - abs(2 * progress - 1))
        
        # Update effects based on corruption level
        for effect in self.takeover_effects:
            effect["intensity"] = self.takeover_corruption_level * effect.get("base_intensity", 1.0)

    def end_scourge_takeover(self):
        """End the Aetherial Scourge takeover event."""
        if self.takeover_active:
            self.takeover_active = False
            self.takeover_effects = []
            self.takeover_text = ""
            self.takeover_corruption_level = 0.0
            self.takeover_intensity = 0.0  # Reset intensity when ending takeover
            # Return to previous state
            if self.previous_state:
                self.change_state(self.previous_state)
            else:
                self.change_state(STATE_MAIN_TERMINAL)
            logger.info("Ended Aetherial Scourge takeover")

    def is_takeover_active(self):
        """Check if a takeover event is currently active."""
        return self.takeover_active

    def get_takeover_effects(self):
        """Get the current takeover effects."""
        return self.takeover_effects

    def get_takeover_corruption_level(self):
        """Get the current corruption level during takeover."""
        return self.takeover_corruption_level

    def get_corruption_level(self) -> float:
        """Get the current corruption level."""
        return self.corruption_level

    def set_corruption_level(self, value: float) -> None:
        """Set the corruption level (clamped between 0.0 and 1.0)."""
        self.corruption_level = max(0.0, min(1.0, value))

    def set_last_command(self, command):
        self.last_command = command

# Global instance.
# Consider dependency injection or passing it around as the project grows.
game_state_manager = GameStateManager()