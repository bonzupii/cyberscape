"""Story manager for Cyberscape: Digital Dread.

This module manages the game's narrative, character interactions, and story progression.
It integrates with the LLM handler for dynamic content generation and the effects system
for visual/audio feedback.
"""

import random
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from ..core.llm import LLMHandler
from ..core.effects import EffectManager
from ..core.state import GameStateManager
from ..story.narrative_content import (
    VOSS_LOG_ENTRIES,
    PROJECT_ETERNAL_DOCS,
    SCOURGE_MANIFESTATIONS,
    CORRUPTION_EVENTS,
    CHARACTER_INTERACTIONS,
    STORY_EVENTS
)

logger = logging.getLogger(__name__)

@dataclass
class Character:
    """Represents a non-player character in the game."""
    name: str
    role: str
    personality: Dict[str, float]  # Personality traits and their values
    knowledge: Dict[str, str]  # Known information and their descriptions
    trust_level: float  # Player's trust level with this character
    corruption_level: float  # Character's corruption level
    last_interaction: datetime
    interaction_history: List[Tuple[str, str]]  # List of (player_input, character_response) pairs

    def generate_response(self, player_input: str, player_role: str) -> str:
        """Generate a response based on the character's personality and knowledge."""
        # Use LLM to generate contextual response
        prompt = f"""
        Character: {self.name}
        Role: {self.role}
        Personality: {self.personality}
        Trust Level: {self.trust_level}
        Corruption Level: {self.corruption_level}
        Player Role: {player_role}
        Player Input: {player_input}
        Previous Interactions: {self.interaction_history[-3:] if self.interaction_history else []}
        
        Generate a response that:
        1. Matches the character's personality and current state
        2. Reflects the trust level and corruption level
        3. Is appropriate for the player's role
        4. Maintains narrative consistency
        """
        
        response = LLMHandler.generate_text(prompt)
        # Profanity escalation: replace some words with profane variants as corruption increases
        corruption = self.corruption_level
        import random
        def profanify(text, corruption):
            if corruption < 0.3:
                return text
            profanities = ["fuck", "shit", "bastard", "damn", "ass", "hell", "crap", "bitch"]
            words = text.split()
            for i in range(len(words)):
                if random.random() < corruption * 0.15:
                    words[i] = random.choice(profanities)
            return " ".join(words)
        response = profanify(response, corruption)
        self.interaction_history.append((player_input, response))
        return response

class StoryManager:
    """Manages the game's narrative and story progression."""
    
    def __init__(self, game_state: GameStateManager, effects_manager: EffectManager):
        self.game_state = game_state
        self.effects_manager = effects_manager
        self.llm_handler = LLMHandler()
        
        # Initialize characters
        self.characters = {
            "voss_visionary": Character(
                name="Dr. Elena Voss (Visionary)",
                role="Lead Researcher",
                personality={
                    "ambition": 0.9,
                    "arrogance": 0.8,
                    "desperation": 0.7,
                    "genius": 0.95
                },
                knowledge=PROJECT_ETERNAL_DOCS,
                trust_level=0.0,
                corruption_level=0.3,
                last_interaction=datetime.now(),
                interaction_history=[]
            ),
            "voss_penitent": Character(
                name="Dr. Elena Voss (Penitent)",
                role="Former Lead Researcher",
                personality={
                    "remorse": 0.9,
                    "fear": 0.8,
                    "determination": 0.7,
                    "wisdom": 0.85
                },
                knowledge=PROJECT_ETERNAL_DOCS,
                trust_level=0.0,
                corruption_level=0.5,
                last_interaction=datetime.now(),
                interaction_history=[]
            ),
            "voss_survivor": Character(
                name="Dr. Elena Voss (Survivor)",
                role="Digital Entity",
                personality={
                    "adaptation": 0.9,
                    "curiosity": 0.8,
                    "alienation": 0.7,
                    "evolution": 0.95
                },
                knowledge=PROJECT_ETERNAL_DOCS,
                trust_level=0.0,
                corruption_level=0.7,
                last_interaction=datetime.now(),
                interaction_history=[]
            )
        }
        
        # Story progression state
        self.story_progress = {
            "discovery": 0.0,  # Progress in discovering the truth
            "corruption": 0.0,  # System corruption level
            "resolution": None  # Final resolution path
        }
        
        # Available story branches based on player role
        self.story_branches = {
            "purifier": {
                "primary": "containment",
                "secondary": "escape",
                "tertiary": "merger"
            },
            "arbiter": {
                "primary": "merger",
                "secondary": "containment",
                "tertiary": "destruction"
            },
            "ascendant": {
                "primary": "destruction",
                "secondary": "merger",
                "tertiary": "escape"
            }
        }
        
        # Initialize narrative content
        self.log_entries = VOSS_LOG_ENTRIES
        self.scourge_manifestations = SCOURGE_MANIFESTATIONS
        self.corruption_events = CORRUPTION_EVENTS
        self.character_interactions = CHARACTER_INTERACTIONS
        self.story_events = STORY_EVENTS

    def get_character(self, character_id: str) -> Optional[Character]:
        """Get a character by their ID."""
        return self.characters.get(character_id)

    def update_trust_level(self, character_id: str, delta: float) -> None:
        """Update the trust level with a character."""
        if character := self.characters.get(character_id):
            character.trust_level = max(0.0, min(1.0, character.trust_level + delta))

    def update_corruption_level(self, character_id: str, delta: float) -> None:
        """Update a character's corruption level."""
        if character := self.characters.get(character_id):
            character.corruption_level = max(0.0, min(1.0, character.corruption_level + delta))
            self.story_progress["corruption"] = character.corruption_level

    def get_narrative_content(self, content_type: str, content_id: str) -> str:
        """Get narrative content based on type and ID."""
        content_map = {
            "log": self.log_entries,
            "scourge": self.scourge_manifestations,
            "corruption": self.corruption_events,
            "character": self.character_interactions,
            "story": self.story_events
        }
        
        if content := content_map.get(content_type):
            if isinstance(content, list):
                return content[int(content_id)] if content_id.isdigit() else ""
            return content.get(content_id, "")
        return ""

    def trigger_story_event(self, event_type: str, event_id: str) -> None:
        """Trigger a story event and update game state."""
        event_content = self.get_narrative_content("story", f"{event_type}.{event_id}")
        if not event_content:
            return
            
        # Update story progress
        if event_type == "discovery":
            self.story_progress["discovery"] = min(1.0, self.story_progress["discovery"] + 0.2)
        elif event_type == "corruption":
            self.story_progress["corruption"] = min(1.0, self.story_progress["corruption"] + 0.2)
        elif event_type == "resolution":
            self.story_progress["resolution"] = event_id
            
        # Apply effects based on event type
        if event_type == "corruption":
            self.effects_manager.trigger_corruption_effect(
                intensity=self.story_progress["corruption"]
            )
        elif event_type == "resolution":
            self.effects_manager.trigger_resolution_effect(event_id)
            
        # Update game state
        self.game_state.update_story_state(
            progress=self.story_progress,
            current_event=f"{event_type}.{event_id}"
        )

    def get_available_story_branches(self) -> List[str]:
        """Get available story branches based on player role and progress."""
        role = self.game_state.role
        if not role or role not in self.story_branches:
            return []
            
        branches = self.story_branches[role]
        available = []
        
        # Primary branch always available
        available.append(branches["primary"])
        
        # Secondary branch available at 50% discovery
        if self.story_progress["discovery"] >= 0.5:
            available.append(branches["secondary"])
            
        # Tertiary branch available at 80% discovery
        if self.story_progress["discovery"] >= 0.8:
            available.append(branches["tertiary"])
            
        return available

    def generate_dynamic_content(self, context: Dict[str, any]) -> str:
        """Generate dynamic narrative content based on game context."""
        prompt = f"""
        Generate narrative content for:
        Player Role: {self.game_state.role}
        Story Progress: {self.story_progress}
        Corruption Level: {self.story_progress['corruption']}
        Context: {context}
        
        The content should:
        1. Match the current story progression
        2. Reflect the player's role and choices
        3. Include appropriate corruption effects
        4. Maintain narrative consistency
        """
        
        return self.llm_handler.generate_text(prompt)

    def handle_character_interaction(self, character_id: str, player_input: str) -> str:
        """Handle player interaction with a character."""
        character = self.get_character(character_id)
        if not character:
            return "Character not found."
            
        # Update last interaction time
        character.last_interaction = datetime.now()
        
        # Generate response
        response = character.generate_response(
            player_input=player_input,
            player_role=self.game_state.role
        )
        
        # Update trust and corruption based on response
        trust_delta = random.uniform(-0.1, 0.1)
        corruption_delta = random.uniform(0.0, 0.05)
        
        self.update_trust_level(character_id, trust_delta)
        self.update_corruption_level(character_id, corruption_delta)
        
        return response

    def get_corruption_effect(self, effect_type: str) -> str:
        """Get a corruption effect message based on type."""
        effects = self.corruption_events.get(effect_type, [])
        return random.choice(effects) if effects else ""

    def get_scourge_manifestation(self, manifestation_type: str) -> str:
        """Get a Scourge manifestation message."""
        return self.scourge_manifestations.get(manifestation_type, "")

    def get_log_entry(self, entry_index: int) -> str:
        """Get a log entry by index."""
        return self.log_entries[entry_index] if 0 <= entry_index < len(self.log_entries) else "" 