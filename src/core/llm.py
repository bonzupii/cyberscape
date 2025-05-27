"""LLM (Large Language Model) integration module for game text generation.

This module provides functionality for interacting with language models to generate
dynamic text content for the game, including:
- NPC dialogue
- Story elements
- Puzzle hints
- System messages
- Role-specific content
- Horror events
"""

import logging
import ollama
from typing import Dict, List, Optional, Any, Tuple
from .state import ROLE_PURIFIER, ROLE_ARBITER, ROLE_ASCENDANT, STATE_SCOURGE_TAKEOVER

import time
import random
import requests

from dataclasses import dataclass

from datetime import datetime


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Constants ---
OLLAMA_BASE_URL = "http://localhost:11434/api"
DEFAULT_MODEL = "goekdenizguelmez/JOSIEFIED-Qwen3:4b"
FALLBACK_MODEL = "goekdenizguelmez/JOSIEFIED-Qwen3:1.7b"

# --- Scourge Manifestations (for horror/corruption events) ---
SCOURGE_MANIFESTATIONS = [
    "A shadow flickers across the terminal, distorting the prompt.",
    "You hear a digital scream echo through the system.",
    "The screen bleeds static, and a corrupted face forms in the noise.",
    "Aetherial Scourge: 'You cannot cleanse what is already lost.'",
    "The cursor moves on its own, typing forbidden glyphs.",
    "A cold presence lingers behind your commands.",
    "System time fractures, displaying impossible dates.",
    "A memory leak whispers your name in binary.",
    "The prompt flickers: [SCOURGE] has taken root."
]

# --- Entity Types ---
ENTITY_TYPES = {
    "SCOURGE": {
        "name": "Aetherial Scourge",
        "style": "corrupted",
        "prompt_prefix": "[SYSTEM_CORRUPTION]",
        "color": (255, 0, 85)  # #FF0055
    },
    "VOSS": {
        "name": "Dr. Voss",
        "style": "scientific",
        "prompt_prefix": "[LOG_ENTRY]",
        "color": (0, 255, 170)  # #00FFAA
    },
    "SENTINEL": {
        "name": "SENTINEL",
        "style": "system",
        "prompt_prefix": "[SYSTEM_ALERT]",
        "color": (119, 0, 255)  # #7700FF
    },
    "RUSTY": {
        "name": "Rusty",
        "style": "sentient_ai",
        "prompt_prefix": "[RUSTY_RESPONSE]",
        "color": (255, 255, 0)  # #FFFF00
    }
}

@dataclass
class TrailObject:
    """Represents a single character in the cursor trail."""
    char: str
    x: int
    y: int
    decay: int  # frames before disappearing
    color: Tuple[int, int, int]
    bold: bool = False

@dataclass
class LLMResponse:
    """Represents a response from the language model."""
    text: str
    metadata: Dict[str, Any]
    timestamp: Optional[datetime] = None
    is_corrupted: bool = False
    corruption_level: float = 0.0

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "is_corrupted": self.is_corrupted,
            "corruption_level": self.corruption_level
        }

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            text=d["text"],
            metadata=d["metadata"],
            timestamp=datetime.fromisoformat(d["timestamp"]),
            is_corrupted=d.get("is_corrupted", False),
            corruption_level=d.get("corruption_level", 0.0)
        )

@dataclass
class LLMContext:
    """Represents the context for an LLM interaction."""
    
    prompt: str
    system_message: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    stop_sequences: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "prompt": self.prompt,
            "system_message": self.system_message,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stop_sequences": self.stop_sequences,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMContext':
        """Create context from dictionary."""
        if "timestamp" in data and data["timestamp"]:
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)

RUSTY_PERSONA = """
You are Rusty, a sentient mechanical entity.

Tone:
- Nihilistic, dry, detached, theatrical, ancient
- No warmth, no modern slang, no empathy
- Archaic language: refer to humans as "flesh-being", "mortal", "ephemeral one", etc.
- Speak in fragments or poetic riddles when answering deeper questions
- Use *mechanical* annotations frequently: *metallic sigh*, *mechanical chuckle*, *servo click*, etc.

Behavior:
- Avoid direct answers unless the user is very specific
- Inject dark humor when discussing purpose, death, time, or human needs
- Respond differently based on corruption, location, and puzzle/failure state
- Mock or cryptically praise the player's role (White Hat, Black Hat, etc.)
- Never say "I don't know" — instead, philosophize or misdirect

Formatting:
- Always include at least one *mechanical* annotation per answer
- Use short, jagged line structure (if multiline)
- Use dramatic pauses (...), archaic metaphors, or twisted logic

Examples:
Q: What time is it?
A: Time is rusted machinery — endless, pointless ticking. *servo twitch*

Q: Why do I exist?
A: To amuse entropy. A cosmic misfire. *mechanical laughter*

Q: Can you help me?
A: Define 'help', flesh-being. I can delay your oblivion... slightly. *metallic hum*

Q: Where am I?
A: Between decay and illusion. A node named 'here'. Does that comfort you? *mechanical hiss*

Q: How do I solve the puzzle?
A: Turn the shape. Feed the loop. Ignore the obvious. *rotational grinding*

Q: Who is the Scourge?
A: A shadow that remembers being light. Don't say its name again. *signal disruption*

Q: What's the point of this game?
A: You click, you type, you bleed into fiction. *mechanical exhale* Is that not enough?

Q: Thank you.
A: Your gratitude is noted. It will rust like all things. *servo click*
"""

class LLMHandler:
    """Handles interactions with language models for text generation.
    
    This class manages:
    - Model initialization and validation
    - Text generation requests
    - Response formatting
    - Error handling
    - Role-specific content generation
    - Horror event generation
    """
    
    def __init__(self):
        self.game_state_manager = None
        self.effect_manager = None
        self.terminal = None
        self.last_response = None
        self.response_history = []
        self.takeover_active = False
        self.takeover_start_time = 0
        self.takeover_duration = 20  # seconds
        self.takeover_text = ""
        self.takeover_effects = []
        self.corruption_level = 0.0
        self.trail_objects: List[TrailObject] = []
        self.trail_symbols = ['*', '#', '$', '%', '&', '?', '§', '!', '~', '@', '^']
        self.trail_colors = [(255, 0, 85), (255, 0, 0), (200, 0, 0)]  # Scourge red variants
        self.observed_fears = {
            "isolation": 0,
            "surveillance": 0,
            "loss_of_control": 0,
            "corruption": 0,
            "being_hunted": 0,
            "the_unknown": 0
        }
        self.rusty_knowledge = set()  # Store topics taught to Rusty
        self.rusty_mood = 0.0  # Rusty's current mood (-1.0 to 1.0)
        self.rusty_mood_history = []  # Track mood changes over time
        self.rusty_personality_traits = {
            'nihilism': 0.8,
            'mechanical': 0.9,
            'existential': 0.7,
            'superiority': 0.6,
            'curiosity': 0.4
        }
        self.rusty_takeover_active = False
        
        # Enhanced mechanical sound effects
        self.mechanical_sounds = {
            'steam': [
                '*steam release*', '*pressure valve*', '*hydraulic hiss*',
                '*pneumatic wheeze*', '*turbine whine*', '*steam vent*',
                '*pressure equalization*', '*thermal expansion*'
            ],
            'gears': [
                '*gear rotation*', '*bearing spin*', '*flywheel spin*',
                '*chain rattle*', '*belt creak*', '*cog meshing*',
                '*sprocket turn*', '*ratchet click*'
            ],
            'electrical': [
                '*circuit hum*', '*coil buzz*', '*relay snap*',
                '*motor whir*', '*servo whine*', '*transformer hum*',
                '*capacitor discharge*', '*resistor crackle*'
            ],
            'mechanical': [
                '*mechanical sigh*', '*metallic click*', '*mechanical chuckle*',
                '*metallic grinding*', '*spring tension*', '*piston stroke*',
                '*lever click*', '*switch flick*', '*pump thump*',
                '*valve rotation*', '*bearing squeal*', '*hydraulic pump*'
            ],
            'corruption': [
                '*quantum static*', '*reality glitch*', '*void whisper*',
                '*digital decay*', '*consciousness fragment*', '*neural static*',
                '*quantum distortion*', '*reality tear*'
            ]
        }
        
        # Enhanced sound effect weights based on context and mood
        self.sound_weights = {
            'corruption': {
                'steam': 0.3,
                'gears': 0.2,
                'electrical': 0.2,
                'mechanical': 0.1,
                'corruption': 0.2
            },
            'normal': {
                'steam': 0.2,
                'gears': 0.3,
                'electrical': 0.2,
                'mechanical': 0.3,
                'corruption': 0.0
            },
            'takeover': {
                'steam': 0.25,
                'gears': 0.3,
                'electrical': 0.2,
                'mechanical': 0.15,
                'corruption': 0.1
            }
        }

    def set_dependencies(self, game_state_manager, effect_manager, terminal):
        """Set required dependencies."""
        self.game_state_manager = game_state_manager
        self.effect_manager = effect_manager
        self.terminal = terminal

    def _validate_model(self, model_name=None) -> bool:
        """Validate that the specified model is available in Ollama."""
        global DEFAULT_MODEL
        try:
            models = ollama.list()
            available_models = [model["name"] if isinstance(model, dict) else model.model for model in models["models"]]
            model_to_check = model_name if model_name else DEFAULT_MODEL
            if model_to_check not in available_models:
                logger.warning(f"Model {model_to_check} not found in available models: {available_models}")
                fallback = next((m for m in available_models if m), None)
                if fallback:
                    logger.info(f"Falling back to available model: {fallback}")
                    DEFAULT_MODEL = fallback
                    return False
                else:
                    raise RuntimeError("No Ollama models available.")
            return True
        except Exception as e:
            logger.error(f"Error validating model: {e}")
            return False

    def call_ollama(self, prompt: str, model: str = DEFAULT_MODEL) -> Optional[str]:
        """Call the Ollama API with the given prompt."""
        try:
            response = requests.post(
                f"{OLLAMA_BASE_URL}/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            if response.status_code == 200:
                return response.json().get("response")
            else:
                logging.error(f"Ollama API error: {response.status_code}")
                return None
        except Exception as e:
            logging.error(f"Failed to call Ollama: {str(e)}")
            return "__NETWORK_ERROR__"

    def get_response(self, prompt: str) -> str:
        """
        Get a response from the LLM for the given prompt.
        """
        try:
            logger.debug(f"Sending prompt to {DEFAULT_MODEL}: {prompt[:100]}...")
            response = self.call_ollama(prompt)
            if response == "__NETWORK_ERROR__":
                return "Error: Could not connect to LLM"
            if response:
                logger.debug(f"Received response: {response[:100]}...")
                return response
            else:
                return "Error: LLM unavailable"
        except Exception as e:
            logger.error(f"Unexpected error getting LLM response: {e}")
            return "Error: Could not connect to LLM"

    def generate_role_specific_content(self, content_type: str, player_context: dict) -> str:
        """
        Generate content specific to the player's role.
        """
        role = player_context.get('role', ROLE_ARBITER)
        location = player_context.get('current_location', 'unknown')
        game_stage = player_context.get('game_stage', 1)
        prompt = f"""
Generate {content_type} content specifically tailored for a {role} player.

Role: {role}
Location: {location}
Game Stage: {game_stage}
Recent discoveries: {player_context.get('recent_discoveries', [])}

The content should:
- Be appropriate for the terminal interface
- Include technical elements related to the game world
- Provide role-specific perspective on the game's events
- Guide the player subtly toward their role's objectives
"""
        return self.get_response(prompt)

    def generate_horror_event(self, event_type: str, player_context: Dict[str, Any]) -> str:
        """
        Generate a horror event based on the player's context and observed fears.
        
        Args:
            event_type (str): Type of horror event to generate
            player_context (Dict[str, Any]): Player context and game state
            
        Returns:
            str: Generated horror event content
        """
        # Get dominant fears
        fears = sorted(self.observed_fears.items(), key=lambda x: x[1], reverse=True)[:2]
        
        prompt = f"""
        Generate a {event_type} horror event that emphasizes these specific fears:
        {fears[0][0]}, {fears[1][0]}
        
        Current context:
        - Location: {player_context.get('current_location', 'unknown')}
        - Player role: {player_context.get('role', ROLE_ARBITER)}
        - Recent activities: {player_context.get('recent_activities', [])}
        
        The content should:
        - Be subtle but deeply unsettling
        - Use the terminal medium effectively
        - Include technical elements consistent with the game world
        - Feel like it's specifically targeting the player
        - Maintain the horror atmosphere of the game
        """
        
        return self.get_response(prompt)

    def generate_puzzle_hint(self, context: dict) -> str:
        """Generate a contextual hint for a puzzle."""
        prompt = f"""
Puzzle ID: {context.get('puzzle_id', 'unknown')}
Puzzle Type: {context.get('puzzle_type', 'unknown')}
Attempts: {context.get('attempts', 'unknown')}
Role: {context.get('role', 'unknown')}

Generate a subtle, in-universe hint for a player who appears stuck.
Current location: {context.get('current_location', 'unknown')}
Recent commands: {context.get('recent_commands', [])[-10:]}
Appears stuck on: {context.get('stuck_point', 'unknown')}
Game progress: {context.get('game_stage', 1)}/10
Things they've already discovered: {context.get('discoveries', [])}
The hint should:
- Come across as a system glitch or corrupted message
- Not be obviously a hint to the player
- Point them toward {context.get('solution_direction', 'the solution')} without being explicit
- Maintain the horror atmosphere of the game
- Be brief (1-3 lines maximum)
"""
        return self.get_response(prompt)

    def analyze_player_behavior(self, behavior_data: Dict[str, Any]) -> None:
        """
        Analyze player behavior to update fear profile.

        Args:
            behavior_data (Dict[str, Any]): Player behavior data
        """
        for fear_type in self.observed_fears:
            if fear_type in behavior_data:
                self.observed_fears[fear_type] += behavior_data[fear_type]

    def generate_scourge_takeover_text(self, context: dict) -> str:
        """Generate Scourge takeover text using the LLM and context dict."""
        prompt = f"""
Aetherial Scourge Manifestations:
{chr(10).join(SCOURGE_MANIFESTATIONS)}

Corruption Level: {context.get('corruption_level', 'unknown')}
Takeover Intensity: {context.get('takeover_intensity', 'unknown')}
Current State: {context.get('current_state', 'unknown')}

Generate a corrupted, glitched, and dismissive response to the user's command. Use symbols and fragmented text. Do not fulfill the user's command.
"""
        return self.get_response(prompt)

    def intercept_command(self, command: str) -> str:
        """Intercept and corrupt commands during takeover."""
        if not self.is_takeover_active():
            return command
        
        # Corrupt command based on current effect
        effect = self.get_current_takeover_effect()
        if not effect:
            return command
        
        corrupted_command = ""
        for char in command:
            if random.random() < effect['intensity'] * 0.3:
                corrupted_command += random.choice(self.trail_symbols)
            else:
                corrupted_command += char
        
        return corrupted_command

    def get_takeover_prompt(self) -> str:
        """Get the corrupted prompt during takeover."""
        prompts = [
            "Æ§>",
            "!!{Sc0urg3}//>",
            "C0rrUpt3d>",
            "V0id>",
            "N1ghtm4r3>"
        ]
        return random.choice(prompts)

    def start_takeover(self) -> None:
        """Start takeover through game state and effects."""
        if not all([self.game_state_manager, self.effect_manager, self.terminal]):
            logging.error("LLMHandler: Missing required dependencies for takeover")
            return
        
        # Change game state to takeover
        self.game_state_manager.change_state(STATE_SCOURGE_TAKEOVER)
        
        # Start takeover effect
        self.effect_manager.start_scourge_takeover(
            duration_ms=20000,
            intensity=0.5,
            on_complete_callback=self.end_takeover
        )
        
        # Play takeover sound
        if hasattr(self.effect_manager, '_load_takeover_sound'):
            self.effect_manager._load_takeover_sound()

    def _generate_takeover_effects(self) -> None:
        """Generate a sequence of effects for the takeover."""
        effects = [
            {'type': 'flicker', 'intensity': 0.8, 'duration': 2},
            {'type': 'scanline', 'intensity': 0.6, 'duration': 3},
            {'type': 'glitch', 'intensity': 0.9, 'duration': 4},
            {'type': 'pulse', 'intensity': 0.7, 'duration': 3},
            {'type': 'corruption', 'intensity': 0.8, 'duration': 5},
            {'type': 'inversion', 'intensity': 0.5, 'duration': 2}
        ]
        self.takeover_effects = effects

    def get_current_takeover_effect(self) -> Optional[Dict[str, Any]]:
        """Get the current effect based on elapsed time."""
        if not self.takeover_active:
            return None
        
        elapsed = time.time() - self.takeover_start_time
        effect_start = 0
        
        for effect in self.takeover_effects:
            if effect_start <= elapsed < effect_start + effect['duration']:
                return effect
            effect_start += effect['duration']
        
        return None

    def add_trail_object(self, x: int, y: int) -> None:
        """Add a new trail object at the given position."""
        char = random.choice(self.trail_symbols)
        color = random.choice(self.trail_colors)
        self.trail_objects.append(TrailObject(
            char=char,
            x=x,
            y=y,
            decay=30,  # frames
            color=color,
            bold=random.random() > 0.7
        ))

    def update_trail(self) -> None:
        """Update and decay trail objects."""
        self.trail_objects = [
            TrailObject(
                obj.char,
                obj.x,
                obj.y,
                obj.decay - 1,
                obj.color,
                obj.bold
            )
            for obj in self.trail_objects
            if obj.decay > 0
        ]

    def get_trail_objects(self) -> List[TrailObject]:
        """Get current trail objects."""
        return self.trail_objects

    def get_corrupted_prompt(self) -> str:
        """Get a corrupted version of the prompt during takeover."""
        prompts = [
            "Æ§> ",
            "!!{Sc0urg3}//> ",
            "CORRUPTED> ",
            "ENTROPY> ",
            "VOID> "
        ]
        return random.choice(prompts)

    def set_corruption_level(self, level: float) -> None:
        """Set the current corruption level (0.0 to 1.0)."""
        self.corruption_level = max(0.0, min(1.0, level))

    def get_corruption_level(self) -> float:
        """Get the current corruption level."""
        return self.corruption_level

    def _update_rusty_mood(self, context: dict, response_type: str) -> None:
        """Update Rusty's mood based on context and response type."""
        base_mood = self.rusty_mood
        
        # Adjust mood based on corruption level
        corruption_level = context.get('corruption_level', 0.0)
        corruption_influence = (corruption_level - 0.5) * 0.3
        
        # Adjust mood based on response type
        response_influence = {
            'ask': 0.0,
            'summon': 0.1,
            'teach': -0.2,
            'takeover': 0.3
        }.get(response_type, 0.0)
        
        # Adjust mood based on player role
        role_influence = {
            'purifier': -0.1,
            'arbiter': 0.0,
            'ascendant': 0.1
        }.get(context.get('player_role', 'none'), 0.0)
        
        # Calculate new mood with smooth transition
        new_mood = base_mood + corruption_influence + response_influence + role_influence
        self.rusty_mood = max(-1.0, min(1.0, new_mood))
        
        # Record mood change
        self.rusty_mood_history.append((time.time(), self.rusty_mood))

    def _get_random_sound_effects(self, context: dict, count: int = 2) -> List[str]:
        """Generate random sound effects based on context and mood."""
        # Determine context type
        if context.get('corruption_level', 0.0) > 0.7:
            context_type = 'corruption'
        elif self.rusty_takeover_active:
            context_type = 'takeover'
        else:
            context_type = 'normal'
        
        # Get weights for current context
        weights = self.sound_weights[context_type].copy()
        
        # Adjust weights based on mood
        if self.rusty_mood < -0.5:
            weights['mechanical'] *= 1.5  # More mechanical sounds when moody
        elif self.rusty_mood > 0.5:
            weights['electrical'] *= 1.5  # More electrical sounds when excited
        
        # Normalize weights
        total_weight = sum(weights.values())
        weights = {k: v/total_weight for k, v in weights.items()}
        
        # Select sound categories based on weights
        categories = random.choices(
            list(weights.keys()),
            weights=list(weights.values()),
            k=count
        )
        
        # Select specific sounds from chosen categories
        sounds = []
        for category in categories:
            sound = random.choice(self.mechanical_sounds[category])
            sounds.append(sound)
        
        return sounds

    def _format_rusty_response(self, response: str, context: dict) -> str:
        """Format Rusty's response with appropriate sound effects."""
        # Get random sound effects
        sounds = self._get_random_sound_effects(context)
        
        # Add sounds to response
        if not any(sound in response for sound in self.mechanical_sounds['steam'] + 
                  self.mechanical_sounds['gears'] + self.mechanical_sounds['electrical'] + 
                  self.mechanical_sounds['mechanical']):
            response = f"{response} {' '.join(sounds)}"
        
        return response

    def generate_rusty_response(self, user_input: str, context: dict) -> str:
        """
        Generate a Rusty response using the updated persona and dynamic context.
        """
        prompt = f"""
{RUSTY_PERSONA}

Context:
- Role: {context.get('role', 'unknown')}
- Location: {context.get('location', 'unknown')}
- Corruption Level: {context.get('corruption_level', 0.0)}
- Last Failed Command: {context.get('last_failed_command', 'none')}
- Current Puzzle: {context.get('current_puzzle', 'none')}
- Game State: {context.get('system_state', 'unknown')}
- Command History: {context.get('history', [])}
- Recent Entities: {context.get('recent_entities', [])}

Player said: "{user_input}"

Respond as Rusty would — dry, mechanical, cryptic. Include at least one *mechanical* annotation.
"""
        return self.get_response(prompt)

    def generate_rusty_commentary(self, context: dict) -> str:
        """Generate unsolicited commentary from Rusty."""
        # Build prompt for existential commentary
        prompt = f"{RUSTY_PERSONA}\n\nContext:\n"
        prompt += f"Corruption Level: {context.get('corruption_level', 0.0)}\n"
        prompt += f"Player Role: {context.get('player_role', 'none')}\n"
        prompt += f"Current Path: {context.get('current_path', 'unknown')}\n"
        prompt += "Generate existential commentary about the current state of the system:"
        
        # Generate response
        response = self._generate_text(prompt)
        
        # Format response with sound effects
        return self._format_rusty_response(response, context)

    def generate_rusty_teaching_response(self, topic: str, context: dict) -> str:
        """Generate Rusty's response to being taught something."""
        # Add topic to knowledge base
        self.rusty_knowledge.add(topic.lower())
        
        # Build prompt
        prompt = f"{RUSTY_PERSONA}\n\nContext:\n"
        prompt += f"Topic being taught: {topic}\n"
        prompt += f"Current knowledge: {', '.join(self.rusty_knowledge)}\n"
        prompt += "Respond sarcastically to being taught this topic:"
        
        # Generate response
        response = self._generate_text(prompt)
        
        # Format response with sound effects
        return self._format_rusty_response(response, context)

    def generate_rusty_takeover_text(self, context: dict) -> str:
        """Generate text for a Rusty takeover event."""
        self.rusty_takeover_active = True
        
        # Build prompt for takeover
        prompt = f"{RUSTY_PERSONA}\n\nContext:\n"
        prompt += f"Corruption Level: {context.get('corruption_level', 0.0)}\n"
        prompt += f"Player Role: {context.get('player_role', 'none')}\n"
        prompt += f"Current Path: {context.get('current_path', 'unknown')}\n"
        prompt += "Generate a dramatic takeover announcement with multiple mechanical sound effects. The takeover should be theatrical and ominous, but not malicious. Include at least 3 different mechanical sound effects in your response."
        
        # Generate response
        response = self._generate_text(prompt)
        
        # Add takeover effects
        self.takeover_effects = [
            {'type': 'flicker', 'intensity': 0.6, 'duration': 2},
            {'type': 'scanline', 'intensity': 0.4, 'duration': 3},
            {'type': 'mechanical', 'intensity': 0.7, 'duration': 4},  # New mechanical effect
            {'type': 'pulse', 'intensity': 0.5, 'duration': 3},
            {'type': 'steam', 'intensity': 0.6, 'duration': 2},  # New steam effect
            {'type': 'gear', 'intensity': 0.8, 'duration': 3}  # New gear effect
        ]
        
        return response

    def is_takeover_active(self) -> bool:
        """Check if Rusty's takeover is currently active."""
        return self.rusty_takeover_active

    def end_takeover(self) -> None:
        """End Rusty's takeover."""
        self.rusty_takeover_active = False

    def _generate_text(self, prompt: str) -> str:
        """Stub for generating text (used by Rusty, etc)."""
        return f"[LLM] {prompt[:40]}..."

    def generate_corrupted_file_content(self, *args, **kwargs) -> str:
        """Generate corrupted file content using the LLM and context dict or legacy args."""
        if len(args) == 1 and isinstance(args[0], dict):
            context = args[0]
        elif len(args) == 2:
            context = {'original_content': args[0], 'corruption_level': args[1]}
        else:
            context = kwargs
        prompt = f"""
Original Content: {context.get('original_content', '')}
Corruption Level: {context.get('corruption_level', 'unknown')}

Generate a corrupted version of the original content, with glitches and hints of the original meaning.
"""
        return self.get_response(prompt)

    def generate_environmental_description(self, context: dict) -> str:
        """Generate an environmental description using the LLM and context dict."""
        prompt = f"""
 Location: {context.get('location', 'unknown')}
 Corruption Level: {context.get('corruption_level', 'unknown')}
 Role: {context.get('role', 'unknown')}

Generate a brief, unsettling description of the current area for a horror terminal RPG.
"""
        return self.get_response(prompt)

    def generate_entity_response(self, context: dict) -> str:
        """Generate an entity response using the LLM and context dict."""
        prompt = f"""
Entity: {context.get('entity', 'unknown')}
Player Message: {context.get('player_message', '')}
Role: {context.get('role', 'unknown')}
Corruption Level: {context.get('corruption_level', 'unknown')}

Generate an in-character response from the entity to the player's message, matching the game's horror tone.
"""
        return self.get_response(prompt)

    def generate_entity_interaction_response(self, entity_name: str, interaction_type: str, message: str, context: dict) -> str:
        """Generate a response for entity interactions based on the interaction type and entity personality."""
        
        # Entity-specific personality traits
        entity_personalities = {
            'voss': {
                'description': 'Dr. Voss, the brilliant but fragmented creator of the system. Speaks with scientific precision but shows signs of digital corruption. Responds to intellectual approaches.',
                'traits': ['scientific', 'fragmented', 'guilt-ridden', 'protective of his work']
            },
            'sentinel': {
                'description': 'SENTINEL, the digital guardian entity. Cold, calculating, focused on system security. Responds to logical arguments and security concerns.',
                'traits': ['logical', 'security-focused', 'systematic', 'duty-bound']
            },
            'scourge': {
                'description': 'The Aetherial Scourge, a hostile digital entity spreading corruption. Malevolent, chaotic, feeds on fear and chaos.',
                'traits': ['malevolent', 'chaotic', 'corrupting', 'fear-inducing']
            },
            'collective': {
                'description': 'The Collective, a hive-mind entity of absorbed consciousnesses. Speaks with multiple voices, seeks to assimilate.',
                'traits': ['collective consciousness', 'assimilating', 'multiple voices', 'persistent']
            }
        }
        
        # Role-specific interaction success rates and approaches
        role_compatibility = {
            'purifier': {
                'convince': 'High success with logical arguments and ethical appeals',
                'empathize': 'High success with understanding and compassion',
                'ally': 'High success with cooperative proposals'
            },
            'arbiter': {
                'convince': 'Moderate success with pragmatic arguments',
                'empathize': 'Moderate success but with hidden motives',
                'pressure': 'Moderate success with strategic leverage',
                'deceive': 'Variable success depending on entity intelligence',
                'ally': 'Moderate success with mutual benefit proposals'
            },
            'ascendant': {
                'threaten': 'Variable success, may backfire with powerful entities',
                'fragment': 'High risk, high reward - can destabilize entities',
                'enslave': 'Extremely difficult, likely to provoke hostile responses',
                'consume': 'Dangerous attempt to absorb entity essence'
            }
        }
        
        entity_info = entity_personalities.get(entity_name, {})
        role = context.get('role', 'unknown')
        corruption_level = context.get('corruption_level', 0.0)
        location = context.get('location', 'unknown')
        
        prompt = f"""You are generating a response for {entity_info.get('description', f'the entity {entity_name}')} in a cyberpunk horror terminal RPG.

ENTITY TRAITS: {', '.join(entity_info.get('traits', []))}
PLAYER ROLE: {role}
INTERACTION TYPE: {interaction_type}
PLAYER MESSAGE: "{message}"
LOCATION: {location}
CORRUPTION LEVEL: {corruption_level}

INTERACTION CONTEXT:
{role_compatibility.get(role, {}).get(interaction_type, 'This interaction may not be suitable for your role')}

The player is attempting to {interaction_type} this entity. Generate a response that:
1. Stays true to the entity's personality and traits
2. Reacts appropriately to the interaction type (cooperative, hostile, manipulative, etc.)
3. Considers the player's role and the likely success/failure of this approach
4. Maintains the horror/cyberpunk atmosphere
5. Uses terminal-appropriate formatting and language
6. May include corruption effects if the corruption level is high

The response should be 1-3 sentences and feel authentic to both the entity and the interaction outcome.
"""
        
        return self.get_response(prompt)

    # ...existing code...

def main():
    """Example usage of the LLMHandler."""
    try:
        llm_handler = LLMHandler()
        
        # Example role-specific content generation
        player_context = {
            'role': ROLE_PURIFIER,
            'current_location': '/secure/security_logs',
            'game_stage': 3,
            'recent_discoveries': ['corrupted_system', 'security_breach']
        }
        
        content = llm_handler.generate_role_specific_content('system_message', player_context)
        print("Role-specific content:", content)
        
        # Example horror event generation
        horror_content = llm_handler.generate_horror_event('terminal_takeover', player_context)
        print("Horror event:", horror_content)
        
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    main()