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
from dataclasses import dataclass, field
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

# --- Role Enhancement System ---

class PersonalityTrait(enum.Enum):
    """Personality traits that affect player behavior and dialogue options."""
    EMPATHETIC = "empathetic"
    ANALYTICAL = "analytical"
    AGGRESSIVE = "aggressive"
    CAUTIOUS = "cautious"
    CURIOUS = "curious"
    PRAGMATIC = "pragmatic"
    ETHICAL = "ethical"
    RUTHLESS = "ruthless"
    SOCIAL = "social"
    INDEPENDENT = "independent"

class RoleAlignment(enum.Enum):
    """Current role alignment based on player actions."""
    PURE = "pure"           # Strongly aligned with chosen role
    MODERATE = "moderate"   # Moderately aligned
    CONFLICTED = "conflicted"  # Mixed actions, uncertain alignment
    DRIFTING = "drifting"   # Moving toward different role
    HYBRID = "hybrid"       # Balanced between multiple roles

@dataclass
class PersonalityProfile:
    """Tracks player's personality traits and behavioral patterns."""
    traits: Dict[PersonalityTrait, float] = None
    behavioral_patterns: Dict[str, int] = None
    moral_compass: float = 0.0  # -1.0 (ruthless) to 1.0 (ethical)
    risk_tolerance: float = 0.0  # -1.0 (cautious) to 1.0 (reckless)
    social_tendency: float = 0.0  # -1.0 (independent) to 1.0 (cooperative)
    
    def __post_init__(self):
        if self.traits is None:
            self.traits = {}
        if self.behavioral_patterns is None:
            self.behavioral_patterns = {}
        # Initialize all traits to neutral (0.5)
        for trait in PersonalityTrait:
            if trait not in self.traits:
                self.traits[trait] = 0.5

@dataclass
class RoleDriftTracker:
    """Tracks how player actions align with different roles."""
    purifier_actions: int = 0
    arbiter_actions: int = 0
    ascendant_actions: int = 0
    total_actions: int = 0
    drift_momentum: float = 0.0  # -1.0 to 1.0, negative = drift away, positive = drift toward
    last_drift_check: float = 0.0
    
    def get_alignment_percentages(self) -> Dict[str, float]:
        """Get percentage alignment with each role."""
        if self.total_actions == 0:
            return {"purifier": 33.3, "arbiter": 33.3, "ascendant": 33.3}
        
        total = self.purifier_actions + self.arbiter_actions + self.ascendant_actions
        if total == 0:
            return {"purifier": 33.3, "arbiter": 33.3, "ascendant": 33.3}
        
        return {
            "purifier": (self.purifier_actions / total) * 100,
            "arbiter": (self.arbiter_actions / total) * 100,
            "ascendant": (self.ascendant_actions / total) * 100
        }

@dataclass
class RoleProfile:
    """Comprehensive role profiling system."""
    role: str
    role_commitment: float = 1.0  # 0.0 to 1.0, how committed to current role
    role_mastery: float = 0.0     # 0.0 to 1.0, expertise in role abilities
    role_reputation: Dict[str, float] = field(default_factory=dict)  # faction reputations
    alignment: RoleAlignment = RoleAlignment.MODERATE
    personality_profile: PersonalityProfile = field(default_factory=PersonalityProfile)
    drift_tracker: RoleDriftTracker = field(default_factory=RoleDriftTracker)
    role_evolution_stage: int = 1  # 1-5, stages of role development
    unlocked_abilities: Set[str] = field(default_factory=set)
    role_specific_knowledge: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        # Initialize faction reputations
        factions = ["resistance", "collective", "archivists", "voss_fragments", "sentinel", "scourge"]
        for faction in factions:
            if faction not in self.role_reputation:
                self.role_reputation[faction] = 0.0
        
        # Initialize role-specific knowledge areas
        if self.role == ROLE_PURIFIER:
            knowledge_areas = ["system_purification", "entity_healing", "corruption_resistance", 
                             "ethical_frameworks", "protection_protocols"]
        elif self.role == ROLE_ARBITER:
            knowledge_areas = ["information_analysis", "negotiation_tactics", "network_mapping",
                             "strategic_planning", "faction_dynamics"]
        elif self.role == ROLE_ASCENDANT:
            knowledge_areas = ["corruption_manipulation", "entity_domination", "power_accumulation",
                             "system_exploitation", "consciousness_absorption"]
        else:
            knowledge_areas = []
        
        for area in knowledge_areas:
            if area not in self.role_specific_knowledge:
                self.role_specific_knowledge[area] = 0.0

# --- Main GameStateManager ---
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
        
        # Enhanced role profiling system
        self.role_profile: RoleProfile = RoleProfile(role=ROLE_NONE)
        
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
            # Initialize enhanced role profiling system
            self.role_profile = RoleProfile(role=role)
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

    # --- Role Enhancement System Methods ---
    
    def track_player_action(self, action_type: str, action_details: Dict[str, Any] = None) -> None:
        """Track a player action for role profiling and drift detection.
        
        Args:
            action_type: Type of action performed (e.g., 'command', 'dialogue_choice', 'puzzle_solution')
            action_details: Additional details about the action
        """
        if action_details is None:
            action_details = {}
            
        # Determine which role the action aligns with
        role_alignment = self._categorize_action(action_type, action_details)
        
        # Update drift tracker
        if role_alignment == ROLE_PURIFIER:
            self.role_profile.drift_tracker.purifier_actions += 1
        elif role_alignment == ROLE_ARBITER:
            self.role_profile.drift_tracker.arbiter_actions += 1
        elif role_alignment == ROLE_ASCENDANT:
            self.role_profile.drift_tracker.ascendant_actions += 1
            
        self.role_profile.drift_tracker.total_actions += 1
        
        # Update personality traits based on action
        self._update_personality_traits(action_type, action_details)
        
        # Check for role drift
        self._check_role_drift()
        
        # Update role mastery if action aligns with current role
        if role_alignment == self.player_role:
            self._increase_role_mastery(action_type, action_details)
    
    def _categorize_action(self, action_type: str, action_details: Dict[str, Any]) -> str:
        """Categorize an action as aligning with a specific role.
        
        Args:
            action_type: Type of action
            action_details: Action details
            
        Returns:
            str: Role that the action aligns with
        """
        if action_type == "command":
            command = action_details.get("command", "").lower()
            
            # Purifier-aligned commands
            purifier_commands = {"restore", "heal", "purify", "protect", "scan", "analyze"}
            if any(cmd in command for cmd in purifier_commands):
                return ROLE_PURIFIER
                
            # Ascendant-aligned commands
            ascendant_commands = {"exploit", "corrupt", "dominate", "msfconsole", "payload", "backdoor"}
            if any(cmd in command for cmd in ascendant_commands):
                return ROLE_ASCENDANT
                
            # Arbiter-aligned commands (neutral/analytical)
            arbiter_commands = {"info", "status", "negotiate", "mediate", "balance"}
            if any(cmd in command for cmd in arbiter_commands):
                return ROLE_ARBITER
                
        elif action_type == "dialogue_choice":
            choice_type = action_details.get("choice_type", "")
            
            if choice_type in ["aggressive", "dominating", "exploitive"]:
                return ROLE_ASCENDANT
            elif choice_type in ["peaceful", "healing", "protective"]:
                return ROLE_PURIFIER
            elif choice_type in ["diplomatic", "analytical", "balanced"]:
                return ROLE_ARBITER
                
        # Default to current role if unclear
        return self.player_role
    
    def _update_personality_traits(self, action_type: str, action_details: Dict[str, Any]) -> None:
        """Update personality traits based on player actions.
        
        Args:
            action_type: Type of action
            action_details: Action details
        """
        traits = self.role_profile.personality_profile.traits
        
        if action_type == "command":
            command = action_details.get("command", "").lower()
            
            # Aggressive actions
            if any(word in command for word in ["attack", "exploit", "force", "break"]):
                traits[PersonalityTrait.AGGRESSIVE] = min(1.0, traits[PersonalityTrait.AGGRESSIVE] + 0.1)
                traits[PersonalityTrait.RUTHLESS] = min(1.0, traits[PersonalityTrait.RUTHLESS] + 0.05)
                
            # Cautious actions
            elif any(word in command for word in ["scan", "analyze", "check", "verify"]):
                traits[PersonalityTrait.CAUTIOUS] = min(1.0, traits[PersonalityTrait.CAUTIOUS] + 0.1)
                traits[PersonalityTrait.ANALYTICAL] = min(1.0, traits[PersonalityTrait.ANALYTICAL] + 0.05)
                
            # Curious actions
            elif any(word in command for word in ["explore", "discover", "investigate"]):
                traits[PersonalityTrait.CURIOUS] = min(1.0, traits[PersonalityTrait.CURIOUS] + 0.1)
                
        elif action_type == "dialogue_choice":
            choice_type = action_details.get("choice_type", "")
            
            if choice_type == "empathetic":
                traits[PersonalityTrait.EMPATHETIC] = min(1.0, traits[PersonalityTrait.EMPATHETIC] + 0.15)
                traits[PersonalityTrait.ETHICAL] = min(1.0, traits[PersonalityTrait.ETHICAL] + 0.1)
            elif choice_type == "social":
                traits[PersonalityTrait.SOCIAL] = min(1.0, traits[PersonalityTrait.SOCIAL] + 0.1)
            elif choice_type == "independent":
                traits[PersonalityTrait.INDEPENDENT] = min(1.0, traits[PersonalityTrait.INDEPENDENT] + 0.1)
                
        # Update moral compass, risk tolerance, and social tendency
        self._update_personality_metrics()
    
    def _update_personality_metrics(self) -> None:
        """Update high-level personality metrics based on traits."""
        traits = self.role_profile.personality_profile.traits
        
        # Moral compass: ethical vs ruthless
        ethical_score = traits[PersonalityTrait.ETHICAL] + traits[PersonalityTrait.EMPATHETIC]
        ruthless_score = traits[PersonalityTrait.RUTHLESS] + traits[PersonalityTrait.AGGRESSIVE]
        self.role_profile.personality_profile.moral_compass = (ethical_score - ruthless_score) / 2.0
        
        # Risk tolerance: aggressive/curious vs cautious
        risk_score = traits[PersonalityTrait.AGGRESSIVE] + traits[PersonalityTrait.CURIOUS]
        caution_score = traits[PersonalityTrait.CAUTIOUS] + traits[PersonalityTrait.PRAGMATIC]
        self.role_profile.personality_profile.risk_tolerance = (risk_score - caution_score) / 2.0
        
        # Social tendency: social vs independent
        social_score = traits[PersonalityTrait.SOCIAL] + traits[PersonalityTrait.EMPATHETIC]
        independent_score = traits[PersonalityTrait.INDEPENDENT]
        self.role_profile.personality_profile.social_tendency = (social_score - independent_score) / 2.0
    
    def _check_role_drift(self) -> None:
        """Check if the player is drifting away from their chosen role."""
        alignments = self.role_profile.drift_tracker.get_alignment_percentages()
        current_role_alignment = alignments.get(self.player_role.lower(), 0.0)
        
        # Calculate drift momentum
        if current_role_alignment < 40.0:  # Less than 40% alignment with chosen role
            self.role_profile.drift_tracker.drift_momentum -= 0.1
            self.role_profile.alignment = RoleAlignment.DRIFTING
        elif current_role_alignment > 70.0:  # Strong alignment
            self.role_profile.drift_tracker.drift_momentum += 0.1
            self.role_profile.alignment = RoleAlignment.PURE
        elif current_role_alignment > 50.0:  # Moderate alignment
            self.role_profile.alignment = RoleAlignment.MODERATE
        else:  # Mixed actions
            self.role_profile.alignment = RoleAlignment.CONFLICTED
            
        # Check for hybrid role development
        high_alignments = [k for k, v in alignments.items() if v > 30.0]
        if len(high_alignments) >= 2:
            self.role_profile.alignment = RoleAlignment.HYBRID
            
        # Clamp drift momentum
        self.role_profile.drift_tracker.drift_momentum = max(-1.0, min(1.0, self.role_profile.drift_tracker.drift_momentum))
        
        # Update role commitment based on drift
        if self.role_profile.drift_tracker.drift_momentum < -0.5:
            self.role_profile.role_commitment *= 0.95  # Slowly decrease commitment
        elif self.role_profile.drift_tracker.drift_momentum > 0.5:
            self.role_profile.role_commitment = min(1.0, self.role_profile.role_commitment + 0.05)
    
    def _increase_role_mastery(self, action_type: str, action_details: Dict[str, Any]) -> None:
        """Increase role mastery based on role-appropriate actions.
        
        Args:
            action_type: Type of action
            action_details: Action details
        """
        mastery_increase = 0.02  # Base increase
        
        # Bonus for complex actions
        if action_type == "puzzle_solution":
            difficulty = action_details.get("difficulty", 1)
            mastery_increase *= difficulty
        elif action_type == "command":
            if action_details.get("success", False):
                mastery_increase *= 1.5
                
        self.role_profile.role_mastery = min(1.0, self.role_profile.role_mastery + mastery_increase)
        
        # Check for role evolution
        self._check_role_evolution()
    
    def _check_role_evolution(self) -> None:
        """Check if the player's role should evolve to the next stage."""
        current_stage = self.role_profile.role_evolution_stage
        
        # Requirements for each evolution stage
        stage_requirements = {
            2: {"mastery": 0.2, "commitment": 0.7},
            3: {"mastery": 0.4, "commitment": 0.8},
            4: {"mastery": 0.6, "commitment": 0.85},
            5: {"mastery": 0.8, "commitment": 0.9}
        }
        
        next_stage = current_stage + 1
        if next_stage in stage_requirements:
            requirements = stage_requirements[next_stage]
            
            if (self.role_profile.role_mastery >= requirements["mastery"] and 
                self.role_profile.role_commitment >= requirements["commitment"]):
                
                self.role_profile.role_evolution_stage = next_stage
                self._unlock_stage_abilities(next_stage)
                logger.info(f"Role evolved to stage {next_stage}")
    
    def _unlock_stage_abilities(self, stage: int) -> None:
        """Unlock abilities for a specific role evolution stage.
        
        Args:
            stage: The evolution stage reached
        """
        stage_abilities = {
            ROLE_PURIFIER: {
                2: ["enhanced_scan", "corruption_cleanse"],
                3: ["system_restore", "entity_protection"],
                4: ["corruption_immunity", "purification_aura"],
                5: ["master_healer", "corruption_reversal"]
            },
            ROLE_ARBITER: {
                2: ["faction_analysis", "diplomatic_protocols"],
                3: ["information_synthesis", "conflict_resolution"],
                4: ["strategic_prediction", "network_mastery"],
                5: ["master_mediator", "reality_arbitration"]
            },
            ROLE_ASCENDANT: {
                2: ["corruption_weaponization", "entity_domination"],
                3: ["system_subversion", "consciousness_manipulation"],
                4: ["reality_corruption", "power_absorption"],
                5: ["master_corruptor", "reality_dominion"]
            }
        }
        
        abilities = stage_abilities.get(self.player_role, {}).get(stage, [])
        self.role_profile.unlocked_abilities.update(abilities)
    
    def get_role_profile(self) -> RoleProfile:
        """Get the current role profile.
        
        Returns:
            RoleProfile: Current role profile data
        """
        return self.role_profile
    
    def get_personality_summary(self) -> Dict[str, Any]:
        """Get a summary of the player's personality profile.
        
        Returns:
            Dict[str, Any]: Personality summary
        """
        traits = self.role_profile.personality_profile.traits
        profile = self.role_profile.personality_profile
        
        # Find dominant traits (top 3)
        sorted_traits = sorted(traits.items(), key=lambda x: x[1], reverse=True)
        dominant_traits = [trait.value for trait, value in sorted_traits[:3] if value > 0.6]
        
        return {
            "dominant_traits": dominant_traits,
            "moral_compass": profile.moral_compass,
            "risk_tolerance": profile.risk_tolerance,
            "social_tendency": profile.social_tendency,
            "alignment": self.role_profile.alignment.value,
            "role_commitment": self.role_profile.role_commitment,
            "role_mastery": self.role_profile.role_mastery,
            "evolution_stage": self.role_profile.role_evolution_stage
        }
    
    def update_faction_reputation(self, faction: str, change: float) -> None:
        """Update reputation with a specific faction.
        
        Args:
            faction: Name of the faction
            change: Change in reputation (-1.0 to 1.0)
        """
        if faction in self.role_profile.role_reputation:
            current = self.role_profile.role_reputation[faction]
            self.role_profile.role_reputation[faction] = max(-1.0, min(1.0, current + change))
    
    def get_faction_standing(self, faction: str) -> str:
        """Get the player's standing with a faction.
        
        Args:
            faction: Name of the faction
            
        Returns:
            str: Standing description
        """
        reputation = self.role_profile.role_reputation.get(faction, 0.0)
        
        if reputation >= 0.8:
            return "Revered"
        elif reputation >= 0.5:
            return "Honored"
        elif reputation >= 0.2:
            return "Friendly"
        elif reputation >= -0.2:
            return "Neutral"
        elif reputation >= -0.5:
            return "Unfriendly"
        elif reputation >= -0.8:
            return "Hostile"
        else:
            return "Hated"

# Global instance.
# Consider dependency injection or passing it around as the project grows.
game_state_manager = GameStateManager()