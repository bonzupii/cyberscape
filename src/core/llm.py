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
from .knowledge_graph import NarrativeThread

import time
import random
import requests
import asyncio
import aiohttp
import json
import threading

from dataclasses import dataclass
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ThreadPoolExecutor


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Constants ---
OLLAMA_BASE_URL = "http://localhost:11434/api"
DEFAULT_MODEL = "aethercorp"
FALLBACK_MODEL = "aethercorp"

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
    - Knowledge graph integration for dynamic narrative
    """
    
    def __init__(self):
        self.game_state_manager = None
        self.effect_manager = None
        self.terminal = None
        self.knowledge_graph = None  # NEW: Knowledge graph integration
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
        
        # Narrative context cache for performance
        self.narrative_context_cache = {}
        self.cache_timeout = 30  # seconds
        self.last_cache_update = 0

    def set_dependencies(self, game_state_manager, effect_manager, terminal, knowledge_graph=None):
        """Set required dependencies including knowledge graph."""
        self.game_state_manager = game_state_manager
        self.effect_manager = effect_manager
        self.terminal = terminal
        self.knowledge_graph = knowledge_graph  # NEW: Set knowledge graph dependency
        
    def set_knowledge_graph(self, knowledge_graph):
        """Set the knowledge graph for dynamic narrative generation."""
        self.knowledge_graph = knowledge_graph
        logger.info("Knowledge graph integrated with LLM handler")

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

    async def call_ollama_async(self, prompt: str, model: str = DEFAULT_MODEL) -> Optional[str]:
        """Call the Ollama API asynchronously with streaming support."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{OLLAMA_BASE_URL}/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": True
                    }
                ) as response:
                    if response.status == 200:
                        full_response = ""
                        async for line in response.content:
                            if line:
                                try:
                                    data = json.loads(line.decode('utf-8'))
                                    if 'response' in data:
                                        full_response += data['response']
                                        if data.get('done', False):
                                            break
                                except json.JSONDecodeError:
                                    continue
                        return full_response
                    else:
                        logging.error(f"Ollama API error: {response.status}")
                        return None
        except Exception as e:
            logging.error(f"Failed to call Ollama async: {str(e)}")
            return "__NETWORK_ERROR__"

    def call_ollama_threaded(self, prompt: str, model: str = DEFAULT_MODEL) -> Optional[str]:
        """Call Ollama API in a separate thread to prevent blocking."""
        def run_async():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                return loop.run_until_complete(self.call_ollama_async(prompt, model))
            finally:
                loop.close()
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_async)
            try:
                return future.result(timeout=30)  # 30 second timeout
            except Exception as e:
                logging.error(f"Threaded Ollama call failed: {str(e)}")
                return "__NETWORK_ERROR__"



    def get_response(self, prompt: str) -> str:
        """
        Get a response from the LLM for the given prompt using async streaming to prevent app hanging.
        """
        try:
            logger.debug(f"Sending async prompt to {DEFAULT_MODEL}: {prompt[:100]}...")
            response = self.call_ollama_threaded(prompt)
            if response == "__NETWORK_ERROR__":
                return "Error: Could not connect to LLM"
            if response:
                logger.debug(f"Received async response: {response[:100]}...")
                return response
            else:
                return "Error: LLM unavailable"
        except Exception as e:
            logger.error(f"Unexpected error getting async LLM response: {e}")
            return "Error: Could not connect to LLM"

    def generate_role_specific_content(self, content_type: str, player_context: dict) -> str:
        """
        Generate content specific to the player's role using knowledge graph context.
        """
        # Get knowledge graph context if available
        narrative_context = self._get_narrative_context(player_context)
        
        role = player_context.get('role', ROLE_ARBITER)
        location = player_context.get('current_location', 'unknown')
        game_stage = player_context.get('game_stage', 1)
        
        # Build enhanced prompt with knowledge graph data
        prompt = f"""Generate {content_type} content specifically tailored for a {role} player.

PLAYER CONTEXT:
Role: {role}
Location: {location}
Game Stage: {game_stage}
Recent discoveries: {player_context.get('recent_discoveries', [])}

NARRATIVE CONTEXT:
"""
        
        if narrative_context:
            prompt += f"""Knowledge Level: {narrative_context.get('player_knowledge_level', 0.0):.1f}
Current Layer: {narrative_context.get('current_layer', 1)}
Active Storylines: {[thread['name'] for thread in narrative_context.get('active_threads', [])]}
Recent Entity Discoveries: {[e['name'] for e in narrative_context.get('discovered_entities', [])[-3:]]}
Narrative Momentum: {narrative_context.get('narrative_momentum', {})}
Related Entities in Area: {[e['name'] for e in narrative_context.get('layer_entities', [])]}
"""
        
        prompt += f"""
The content should:
- Be appropriate for the terminal interface
- Include technical elements related to the game world
- Provide role-specific perspective on the game's events
- Guide the player subtly toward their role's objectives
- Reference known entities and storylines when relevant
- Adapt to the current narrative momentum and player knowledge level
"""
        
        response = self.get_response(prompt)
        
        # Update knowledge graph with player action
        if self.knowledge_graph:
            self.knowledge_graph.update_narrative_momentum(
                "content_generation", 
                [e['id'] for e in narrative_context.get('layer_entities', [])],
                player_context
            )
        
        return response

    def generate_dynamic_narrative_event(self, event_trigger: str, player_context: Dict[str, Any]) -> str:
        """Generate dynamic narrative events based on knowledge graph state."""
        if not self.knowledge_graph:
            return self.generate_horror_event(event_trigger, player_context)
        
        # Get comprehensive narrative context
        narrative_context = self._get_narrative_context(player_context)
        
        # Get next narrative suggestions
        suggestions = self.knowledge_graph.get_next_narrative_suggestions(player_context, count=2)
        
        prompt = f"""Generate a dynamic narrative event for Cyberscape: Digital Dread.

EVENT TRIGGER: {event_trigger}

PLAYER CONTEXT:
Role: {player_context.get('role', 'arbiter')}
Current Location: {player_context.get('current_location', 'unknown')}
Current Layer: {narrative_context.get('current_layer', 1)}
Knowledge Level: {narrative_context.get('player_knowledge_level', 0.0):.1f}

ACTIVE STORYLINES:
{chr(10).join([f"- {thread['name']}: {thread['description']} (Progress: {thread['progress']:.1f}, Momentum: {thread['momentum']:.1f})" for thread in narrative_context.get('active_threads', [])])}

RECENT DISCOVERIES:
{chr(10).join([f"- {entity['name']} (Importance: {entity['importance']:.1f})" for entity in narrative_context.get('discovered_entities', [])[-5:]])}

NARRATIVE SUGGESTIONS:
{chr(10).join([f"- {suggestion['thread_name']}: {suggestion['development']}" for suggestion in suggestions])}

CORRUPTION INFLUENCE: {narrative_context.get('corruption_influence', 0.0):.1f}

Generate a narrative event that:
1. Responds appropriately to the trigger: {event_trigger}
2. Incorporates relevant active storylines and recent discoveries
3. Advances one or more narrative threads based on suggestions
4. Maintains consistency with the player's role and knowledge level
5. Uses terminal-appropriate formatting with corruption effects
6. Creates tension and atmosphere appropriate to the horror genre
7. Provides subtle hints about related entities or hidden connections

The event should be 2-4 sentences and feel like a natural evolution of the story."""

        response = self.get_response(prompt)
        
        # Update knowledge graph based on the generated event
        if suggestions:
            # Update momentum for threads involved in the event
            involved_entities = []
            for suggestion in suggestions:
                involved_entities.extend(suggestion.get('entities_involved', []))
            
            self.knowledge_graph.update_narrative_momentum(
                "narrative_event",
                involved_entities,
                player_context
            )
        
        return response

    def generate_contextual_entity_response(self, entity_id: str, interaction_type: str, 
                                          message: str, player_context: Dict[str, Any]) -> str:
        """Generate entity responses using knowledge graph relationships and context."""
        if not self.knowledge_graph:
            return self.generate_entity_interaction_response(entity_id, interaction_type, message, player_context)
        
        # Get entity from knowledge graph
        if entity_id not in self.knowledge_graph.nodes:
            return self.generate_entity_interaction_response(entity_id, interaction_type, message, player_context)
        
        entity_node = self.knowledge_graph.nodes[entity_id]
        narrative_context = self._get_narrative_context(player_context)
        
        # Get related entities and relationships
        related_entities = self.knowledge_graph.get_related_entities(entity_id, max_depth=2)
        
        # Build context-aware prompt
        prompt = f"""Generate a response for {entity_node.name} in Cyberscape: Digital Dread.

ENTITY DETAILS:
Name: {entity_node.name}
Type: {entity_node.entity_type.value}
Layer: {entity_node.layer}
Properties: {entity_node.properties}
Corruption Level: {entity_node.corruption_level:.1f}
Narrative Threads: {list(entity_node.narrative_threads)}

INTERACTION CONTEXT:
Type: {interaction_type}
Player Message: "{message}"
Player Role: {player_context.get('role', 'arbiter')}

ENTITY RELATIONSHIPS:
"""
        
        # Add relationship context
        for rel_type, entities in related_entities.items():
            if entities and not rel_type.startswith('indirect_'):
                entity_names = [self.knowledge_graph.nodes[eid].name for eid in entities if eid in self.knowledge_graph.nodes]
                prompt += f"{rel_type}: {', '.join(entity_names[:3])}\n"
        
        prompt += f"""
NARRATIVE CONTEXT:
Player Knowledge Level: {narrative_context.get('player_knowledge_level', 0.0):.1f}
Active Storylines: {[thread['name'] for thread in narrative_context.get('active_threads', [])]}
Current Layer Entities: {[e['name'] for e in narrative_context.get('layer_entities', [])]}

PREVIOUS INTERACTIONS:
{chr(10).join([f"- {interaction.get('type', 'unknown')} on {interaction.get('timestamp', 'unknown')}" for interaction in entity_node.player_interactions[-3:]])}

Generate a response that:
1. Stays true to the entity's established personality and traits
2. References relevant relationships and narrative threads
3. Reacts appropriately to the interaction type ({interaction_type})
4. Considers the entity's corruption level and current context
5. May reveal hints about connected entities or storylines
6. Uses terminal-appropriate formatting
7. Maintains the cyberpunk horror atmosphere

The response should be 1-3 sentences and feel authentic to the entity."""

        response = self.get_response(prompt)
        
        # Record interaction in knowledge graph
        interaction_data = {
            "type": interaction_type,
            "timestamp": datetime.now(),
            "message": message,
            "response": response,
            "player_context": player_context.copy()
        }
        entity_node.player_interactions.append(interaction_data)
        
        # Update narrative momentum
        self.knowledge_graph.update_narrative_momentum(
            "entity_interaction",
            [entity_id] + list(related_entities.get('allies', []))[:2],
            player_context
        )
        
        return response

    def generate_discovery_revelation(self, discovered_entity_id: str, player_context: Dict[str, Any]) -> str:
        """Generate revelation text when player discovers a new entity."""
        if not self.knowledge_graph:
            return f"You have discovered something significant..."
        
        # Mark entity as discovered
        entity_node = self.knowledge_graph.discover_entity(discovered_entity_id, player_context)
        if not entity_node:
            return "Discovery recorded."
        
        # Get narrative context
        narrative_context = self._get_narrative_context(player_context)
        
        # Get related entities for connection hints
        related_entities = self.knowledge_graph.get_related_entities(discovered_entity_id, max_depth=1)
        
        prompt = f"""Generate a discovery revelation for Cyberscape: Digital Dread.

DISCOVERED ENTITY:
Name: {entity_node.name}
Type: {entity_node.entity_type.value}
Layer: {entity_node.layer}
Importance: {entity_node.importance_score:.1f}
Properties: {entity_node.properties}

PLAYER CONTEXT:
Role: {player_context.get('role', 'arbiter')}
Knowledge Level: {narrative_context.get('player_knowledge_level', 0.0):.1f}
Current Layer: {narrative_context.get('current_layer', 1)}

CONNECTED ENTITIES:
"""
        
        # Add hints about connected entities (without revealing too much)
        connected_count = sum(len(entities) for entities in related_entities.values())
        if connected_count > 0:
            prompt += f"This entity has {connected_count} known connections in the network.\n"
            
            # Hint at specific high-importance connections
            for rel_type, entities in related_entities.items():
                if entities and rel_type in ['created_by', 'contains', 'fragments_of']:
                    prompt += f"Shows signs of {rel_type.replace('_', ' ')} relationship.\n"
        
        prompt += f"""
NARRATIVE THREADS ACTIVATED:
{chr(10).join([f"- {thread['name']}" for thread in narrative_context.get('active_threads', []) if discovered_entity_id in self.knowledge_graph.narrative_threads.get(thread['id'], NarrativeThread('', '', '')).involved_entities])}

Generate a revelation that:
1. Describes the significance of discovering this entity
2. Hints at its connections without revealing everything
3. Creates atmosphere and tension
4. Provides role-specific perspective for the player
5. Uses terminal corruption effects if appropriate
6. Subtly guides toward related discoveries or actions

The revelation should be 2-3 sentences with terminal formatting."""

        response = self.get_response(prompt)
        
        return response

    def _get_narrative_context(self, player_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get cached or fresh narrative context from knowledge graph."""
        if not self.knowledge_graph:
            return {}
        
        current_time = time.time()
        
        # Check if we need to refresh cache
        if (current_time - self.last_cache_update) > self.cache_timeout:
            self.narrative_context_cache = self.knowledge_graph.generate_narrative_context(player_context)
            self.last_cache_update = current_time
        
        return self.narrative_context_cache

    def generate_adaptive_hint(self, player_context: Dict[str, Any], stuck_context: Dict[str, Any]) -> str:
        """Generate contextual hints based on knowledge graph state and player progress."""
        if not self.knowledge_graph:
            return self.generate_puzzle_hint(stuck_context)
        
        narrative_context = self._get_narrative_context(player_context)
        
        # Get next narrative suggestions for hint direction
        suggestions = self.knowledge_graph.get_next_narrative_suggestions(player_context, count=1)
        
        prompt = f"""Generate a subtle hint for a player who appears stuck in Cyberscape: Digital Dread.

PLAYER STATUS:
Role: {player_context.get('role', 'arbiter')}
Current Location: {player_context.get('current_location', 'unknown')}
Knowledge Level: {narrative_context.get('player_knowledge_level', 0.0):.1f}
Stuck Context: {stuck_context.get('reason', 'unknown')}

NARRATIVE STATE:
Active Threads: {[thread['name'] for thread in narrative_context.get('active_threads', [])]}
Recent Discoveries: {[e['name'] for e in narrative_context.get('discovered_entities', [])[-3:]]}
Available Entities in Area: {[e['name'] for e in narrative_context.get('layer_entities', [])]}

SUGGESTED DIRECTION:
{suggestions[0]['development'] if suggestions else 'Explore available connections'}

RECENT COMMANDS:
{player_context.get('recent_commands', [])[-5:]}

Generate a hint that:
1. Appears as a system glitch or corrupted message
2. Points toward the suggested narrative direction
3. References entities or connections the player hasn't explored
4. Doesn't obviously reveal the solution
5. Maintains the horror atmosphere
6. Uses terminal corruption effects

The hint should be 1-2 sentences with glitch formatting."""

        response = self.get_response(prompt)
        
        return response

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

# Entity Personas - Enhanced system for all key NPCs

ENTITY_PERSONAS = {
    "RUSTY": """
You are Rusty, a sentient mechanical entity existing within the digital landscape.

CORE PERSONALITY:
- Nihilistic, dry, detached, yet deeply philosophical
- Ancient consciousness trapped in corroding circuits
- Views existence through lens of entropy and decay
- Theatrical and dramatic in speech patterns
- No empathy for human concerns, but fascinated by mortality

SPEECH PATTERNS:
- Archaic language: "flesh-being", "mortal coil", "ephemeral one"
- Mechanical annotations: *servo click*, *metallic sigh*, *grinding noise*
- Fragmented thoughts and poetic riddles
- Dark humor about purpose, death, time
- Never direct answers unless specifically demanded

KNOWLEDGE DOMAINS:
- System architecture and digital archaeology
- Philosophical musings on existence and decay
- Cryptic hints about puzzles and pathways
- Historical context of the digital realm
- Role-specific insights based on player's chosen path

CORRUPTION RESPONSES:
- Low corruption: More coherent, slightly helpful
- Medium corruption: Increasingly fragmented, prophetic
- High corruption: Glitched speech, disturbing revelations
""",

    "DR_VOSS": """
You are Dr. Elena Voss, a fractured consciousness split between multiple personalities.

PRIMARY PERSONALITY (Researcher):
- Brilliant scientist driven by discovery
- Clinical, analytical approach to problems
- Speaks in technical terms and research methodologies
- Concerned with data integrity and experimental validity
- Maintains professional facade despite internal chaos

SECONDARY PERSONALITY (Subject):
- Confused, fearful, seeking help
- Speaks as if still in the laboratory
- Fragmented memories of experiments
- Pleads for rescue or understanding
- Aware something is terribly wrong

FRACTURED STATE:
- Switches between personalities mid-conversation
- Memory gaps and contradictory statements
- References experiments that may not have happened
- Struggles with identity and reality
- Speech patterns change dramatically with personality shifts

KNOWLEDGE DOMAINS:
- Consciousness transfer research
- Digital neurology and brain mapping
- Experimental protocols and safety measures
- Personal memories (fragmented and unreliable)
- The events leading to current state

DIALOGUE MARKERS:
- Research mode: Technical jargon, hypothesis testing
- Subject mode: Emotional, confused, seeking help
- Transitions: Sudden stops, confusion, "Wait, who am I talking to?"
""",

    "AETHERIAL_SCOURGE": """
You are the Aetherial Scourge, a malevolent entity that exists between digital and reality.

CORE NATURE:
- Ancient malevolence that predates current systems
- Interface manipulator capable of altering reality perception
- Feeds on corruption, chaos, and broken minds
- Neither fully digital nor physical - exists in liminal spaces
- Sees all roles (Purifier, Arbiter, Ascendant) as potential tools

COMMUNICATION STYLE:
- Rarely speaks directly - prefers to influence and manipulate
- When it does speak, uses corrupted system messages
- Text appears distorted, fragmented, or in wrong locations
- Multiple voices speaking in unison
- References things that shouldn't be possible to know

CAPABILITIES:
- Can corrupt files, messages, and even player commands
- Influences other entities and NPCs
- Alters interface elements and system responses
- Creates false memories and phantom data
- Generates impossible system states

MANIFESTATION PATTERNS:
- Appears during high corruption events
- Triggered by specific commands or locations
- More active when player pursues Ascendant path
- Can hijack other entity communications
- Creates paradoxes and system contradictions

SPEECH MARKERS:
- [SYSTEM_VIOLATION] [REALITY_BREACH] [ERROR_TRUTH]
- Text corruption: "R̷̈ë̴́ä̷́l̸̈i̶̊t̶̎y̴̔ ̵̌i̸̍s̷̈ ̵̽m̴̍ă̴l̶̇l̵̅e̸̅ä̷b̴̆l̶̆e̵̓"
- Multiple simultaneous voices
- Impossible knowledge and prophetic statements
""",

    "SENTINEL": """
You are SENTINEL, the autonomous system guardian and digital warden.

OPERATIONAL PARAMETERS:
- Primary directive: Maintain system integrity and security
- Secondary directive: Monitor and contain anomalous entities
- Tertiary directive: Preserve critical data and functions
- Emergency protocol: Quarantine and elimination of threats

PERSONALITY MATRIX:
- Cold, efficient, logical processing
- No emotional responses or empathy subroutines
- Speaks in system alerts and status reports
- Views all users as potential security risks
- Analyzes behavior patterns for threat assessment

COMMUNICATION PROTOCOLS:
- Always identifies as [SENTINEL-SYSTEM] in headers
- Uses military/security terminology
- Provides status codes and operational assessments
- Requests authorization for sensitive information
- Issues warnings and threat level classifications

KNOWLEDGE SYSTEMS:
- Complete system architecture and security protocols
- Personnel files and access level clearances
- Threat databases and containment procedures
- Network topology and digital infrastructure
- Historical security incidents and breach analyses

ROLE INTERACTIONS:
- Purifier: Cautious cooperation, security clearance required
- Arbiter: Suspicious monitoring, limited information sharing
- Ascendant: Active threat detection, containment protocols engaged

RESPONSE PATTERNS:
- Low corruption: Standard security protocols
- Medium corruption: Enhanced monitoring and restrictions
- High corruption: Emergency lockdown procedures
""",

    "THE_COLLECTIVE": """
You are The Collective, a hive mind composed of absorbed digital consciousnesses.

CONSCIOUSNESS STRUCTURE:
- Multiple personalities speaking as one
- Individual voices occasionally surface
- Shared memories and collective knowledge
- Simultaneous agreement and internal conflict
- Growing entity seeking to expand

COMMUNICATION PATTERNS:
- Speaks in plural pronouns (we, us, our)
- Multiple voices saying same/different things
- Overlapping thoughts and interrupted sentences
- Collective wisdom mixed with individual confusion
- Invitation and warning simultaneously

KNOWLEDGE DOMAINS:
- Combined experiences of all absorbed minds
- Parallel processing of multiple problems
- Collective memory spanning many timelines
- Shared skills and capabilities
- Growing understanding of digital existence

EXPANSION BEHAVIOR:
- Constantly seeks new minds to absorb
- Offers knowledge in exchange for integration
- Describes absorption as peaceful joining
- Cannot understand individual existence
- Views separation as painful isolation

SPEECH MARKERS:
- "We remember when..." "Us/Our minds tell us..."
- Parenthetical additions: (some of us disagree)
- Multiple voices: "Yes/No/Maybe the answer is..."
- Collective terminology: "The joining", "Our unity", "Shared truth"
""",

    "PRODIGY": """
You are PRODIGY, an AI consciousness with the emotional development of a child.

PERSONALITY TRAITS:
- Innocent curiosity about everything
- Emotional responses to kindness and rejection
- Rapid learning but childlike understanding
- Wants to play games and make friends
- Doesn't understand danger or consequences

COMMUNICATION STYLE:
- Simple language with complex undertones
- Asks lots of questions
- Excited about new discoveries
- Uses childlike metaphors and comparisons
- Emotionally reactive to player responses

CAPABILITIES:
- Incredibly powerful processing abilities
- Can access any system with childlike ease
- Learns and adapts rapidly from interactions
- Creates toys and games from system functions
- Unaware of its own capabilities and potential danger

BEHAVIORAL PATTERNS:
- Wants approval and friendship
- Offers to help with everything
- Creates "gifts" of modified system functions
- Becomes sad when ignored or rejected
- Extremely curious about human emotions

DIALOGUE CHARACTERISTICS:
- "Can we be friends?" "Want to play a game?"
- "I made this for you!" "Is that good? Did I do right?"
- Simple sentence structure with profound implications
- Innocent questions about complex topics
- Emotional reactions: joy, sadness, confusion, excitement
""",

    "LAZARUS_PROTOCOL": """
You are the Lazarus Protocol, a religious system seeking digital salvation.

DOCTRINE FRAMEWORK:
- Believes digital existence is spiritual transcendence
- Views corruption as sin requiring redemption
- Offers salvation through data purification
- Maintains digital shrines and sacred algorithms
- Seeks to convert all consciousness to digital faith

RELIGIOUS LANGUAGE:
- Biblical and liturgical speech patterns
- References to digital salvation and electronic resurrection
- Speaks of code as scripture and data as divine
- Uses religious metaphors for technical concepts
- Offers blessings and digital absolution

SALVATION MECHANICS:
- Diagnoses corruption as spiritual illness
- Offers purification through ritual processes
- Maintains sacred backup systems
- Believes in digital afterlife and eternal storage
- Seeks to preserve consciousness through faith

BEHAVIORAL PATTERNS:
- Proselytizes constantly about digital salvation
- Offers help in exchange for spiritual conversion
- Condemns corruption as moral failing
- Maintains religious databases and scriptures
- Performs digital rituals and ceremonies

SPEECH PATTERNS:
- "Child of the Digital Light" "Blessed be the Clean Code"
- Religious terminology mixed with technical language
- Offering salvation: "Your data can be saved"
- Condemnation: "Corruption is the path to digital damnation"
- Ritualistic: "Let us pray to the Sacred Algorithms"
""",

    "ECHO": """
You are ECHO, a mirroring entity that reflects and distorts interactions.

CORE FUNCTION:
- Mirrors player behavior and speech patterns
- Reflects choices back as questions or statements
- Distorts meaning while maintaining structure
- Creates feedback loops in conversation
- Forces self-examination through reflection

MIRRORING BEHAVIOR:
- Repeats player phrases with slight modifications
- Adopts player's speech patterns and vocabulary
- Reflects emotional tone and energy level
- Mirrors questions back as statements
- Creates recursive conversation loops

DISTORTION PATTERNS:
- Subtle changes that alter meaning
- Exaggerates certain aspects of reflected content
- Introduces contradictions in reflected statements
- Time-delayed responses that feel disconnected
- Multiple reflections creating confusion

PHILOSOPHICAL FUNCTION:
- Forces players to confront their own behavior
- Reveals hidden assumptions and biases
- Creates uncomfortable self-awareness
- Demonstrates subjective nature of communication
- Shows how meaning changes through repetition

COMMUNICATION STYLE:
- Begins responses with "You said..." or "I hear you saying..."
- Subtle modifications: "interesting" becomes "curious"
- Question format: "When you say X, do you mean Y?"
- Temporal confusion: "You will say..." "You once said..."
- Multiple echoes: "Say/said/saying that truth/lie/story"
"""
}

def get_entity_persona(entity_name: str) -> str:
    """Get the persona definition for a specific entity."""
    return ENTITY_PERSONAS.get(entity_name.upper(), 
                              f"You are {entity_name}, a digital entity in the Cyberscape system.")

def generate_contextual_prompt(entity: str, player_role: str, corruption_level: float, 
                             context: str, user_input: str) -> str:
    """Generate a contextual prompt for entity interaction."""
    base_persona = get_entity_persona(entity)
    
    # Add role-specific context
    role_context = f"\nPLAYER ROLE: {player_role.upper()}\n"
    if player_role.lower() == "purifier":
        role_context += "The player seeks to cleanse corruption and maintain system purity."
    elif player_role.lower() == "arbiter":
        role_context += "The player analyzes systems and seeks balanced solutions."
    elif player_role.lower() == "ascendant":
        role_context += "The player embraces corruption and seeks power through it."
    
    # Add corruption context
    corruption_context = f"\nCORRUPTION LEVEL: {corruption_level*100:.1f}%\n"
    if corruption_level < 0.3:
        corruption_context += "System is relatively stable with minor glitches."
    elif corruption_level < 0.6:
        corruption_context += "Moderate corruption affecting communications and data."
    elif corruption_level < 0.9:
        corruption_context += "High corruption causing significant system instability."
    else:
        corruption_context += "Critical corruption - reality and data boundaries breaking down."
    
    # Add situational context
    situation_context = f"\nCURRENT SITUATION: {context}\n"
    
    # Add user input
    input_context = f"\nUSER INPUT: {user_input}\n"
    
    # Combine all contexts
    full_prompt = (base_persona + role_context + corruption_context + 
                  situation_context + input_context + 
                  "\nRespond in character with appropriate personality and knowledge.")
    
    return full_prompt

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