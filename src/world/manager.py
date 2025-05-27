"""World manager for Cyberscape: Digital Dread.

This module manages the layered world structure of the Aether network,
including progression between layers, layer-specific content, and environmental
storytelling mechanics.
"""

import random
import logging
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum

from ..core.state import GameStateManager
from ..story.manager import StoryManager
from ..core.effects import EffectManager
from ..core.corruption import CorruptionSystem

logger = logging.getLogger(__name__)

class WorldLayer(Enum):
    """Represents the different layers of the Aether network."""
    QUARANTINE = "quarantine_zone"
    CORPORATE = "corporate_shell"
    DEVELOPMENT = "development_sphere"
    NEURAL = "neural_network"
    CORE = "the_core"

@dataclass
class LayerData:
    """Data structure for a world layer."""
    name: str
    description: str
    corruption_base: float  # Base corruption level for this layer
    corruption_variance: float  # How much corruption can vary
    security_level: int  # 1-5, affects puzzle difficulty
    access_requirements: List[str]  # Requirements to access this layer
    unique_entities: Set[str]  # Entities specific to this layer
    available_commands: Set[str]  # Commands available in this layer
    environmental_effects: Dict[str, Any]  # Visual/audio effects
    narrative_themes: List[str]  # Main narrative themes
    key_locations: List[Dict[str, Any]]  # Important locations in this layer

@dataclass
class Location:
    """Represents a specific location within a layer."""
    id: str
    name: str
    description: str
    layer: WorldLayer
    access_level: int  # Required access level
    corruption_modifier: float  # Modifies base layer corruption
    available_actions: Set[str]
    hidden_content: List[Dict[str, Any]]  # Content revealed by exploration
    entities_present: List[str]
    puzzle_ids: List[str]  # Puzzles available in this location
    narrative_triggers: List[str]  # Story events triggered here
    visited: bool = False
    discovery_progress: float = 0.0  # 0.0 to 1.0

class WorldManager:
    """Manages the layered world structure and player progression."""
    
    def __init__(self, game_state: GameStateManager, story_manager: StoryManager, 
                 effects_manager: EffectManager, corruption_system: CorruptionSystem):
        self.game_state = game_state
        self.story_manager = story_manager
        self.effects_manager = effects_manager
        self.corruption_system = corruption_system
        
        # Current world state
        self.current_layer = WorldLayer.QUARANTINE
        self.current_location = None
        self.layer_access_levels = {layer: 0 for layer in WorldLayer}
        self.layer_access_levels[WorldLayer.QUARANTINE] = 1  # Start with access to quarantine
        
        # Initialize layer data
        self.layers = self._initialize_layers()
        self.locations = self._initialize_locations()
        
        # Progression tracking
        self.discovered_locations = set()
        self.completed_puzzles = set()
        self.unlocked_paths = set()
        self.environmental_state = {}
        
        logger.info("WorldManager initialized")
    
    def _initialize_layers(self) -> Dict[WorldLayer, LayerData]:
        """Initialize the layer data structure."""
        return {
            WorldLayer.QUARANTINE: LayerData(
                name="Quarantine Zone",
                description="The outer containment systems designed to isolate the Aether network. Relatively stable but showing signs of strain.",
                corruption_base=0.1,
                corruption_variance=0.05,
                security_level=1,
                access_requirements=[],
                unique_entities={"quarantine_ai", "cleanup_bots", "system_monitors"},
                available_commands={"scan", "status", "help", "ls", "cd", "cat", "ping"},
                environmental_effects={
                    "visual": ["dim_amber_lighting", "occasional_flicker"],
                    "audio": ["distant_hum", "system_beeps"],
                    "corruption": ["minor_text_glitches"]
                },
                narrative_themes=["containment", "first_warnings", "tutorial_guidance"],
                key_locations=[
                    {"id": "entrance_terminal", "name": "Main Entrance Terminal"},
                    {"id": "quarantine_logs", "name": "Quarantine Log Archive"},
                    {"id": "containment_breach", "name": "Breach Detection Center"}
                ]
            ),
            
            WorldLayer.CORPORATE: LayerData(
                name="Corporate Shell",
                description="Public-facing systems of Aether Corporation. Marketing materials and sanitized records hide deeper truths.",
                corruption_base=0.25,
                corruption_variance=0.1,
                security_level=2,
                access_requirements=["quarantine_clearance"],
                unique_entities={"pr_system", "hr_database", "marketing_ai"},
                available_commands={"scan", "download", "search", "query", "archive", "decrypt"},
                environmental_effects={
                    "visual": ["corporate_blue_theme", "occasional_static"],
                    "audio": ["elevator_music_distorted", "keyboard_clicks"],
                    "corruption": ["text_replacement", "memory_glitches"]
                },
                narrative_themes=["corporate_facade", "hidden_agendas", "employee_records"],
                key_locations=[
                    {"id": "executive_suite", "name": "Executive Information Systems"},
                    {"id": "employee_database", "name": "Human Resources Archive"},
                    {"id": "project_announcements", "name": "Public Relations Center"}
                ]
            ),
            
            WorldLayer.DEVELOPMENT: LayerData(
                name="Development Sphere",
                description="Research and development systems where Aether's breakthrough technologies were created. Increasingly unstable.",
                corruption_base=0.5,
                corruption_variance=0.2,
                security_level=3,
                access_requirements=["corporate_access", "dev_credentials"],
                unique_entities={"dev_ai_fragments", "project_eternal", "code_ghosts"},
                available_commands={"compile", "debug", "trace", "inject", "reverse", "exploit"},
                environmental_effects={
                    "visual": ["code_rain", "buffer_overflows", "memory_leaks"],
                    "audio": ["compilation_sounds", "error_beeps", "fan_whirring"],
                    "corruption": ["syntax_errors", "variable_corruption", "function_calls_void"]
                },
                narrative_themes=["scientific_ambition", "ethical_boundaries", "unintended_consequences"],
                key_locations=[
                    {"id": "project_eternal_lab", "name": "Project Eternal Laboratory"},
                    {"id": "ai_research_wing", "name": "Consciousness Research Division"},
                    {"id": "quantum_core_access", "name": "Quantum Processing Core"}
                ]
            ),
            
            WorldLayer.NEURAL: LayerData(
                name="Neural Network",
                description="Vast data processing systems mimicking human brain structure. Reality becomes increasingly subjective.",
                corruption_base=0.75,
                corruption_variance=0.15,
                security_level=4,
                access_requirements=["neural_interface", "consciousness_mapping"],
                unique_entities={"neural_clusters", "memory_fragments", "synaptic_ghosts"},
                available_commands={"think", "remember", "dream", "merge", "fragment", "transcend"},
                environmental_effects={
                    "visual": ["neural_patterns", "synaptic_firing", "consciousness_streams"],
                    "audio": ["brainwave_patterns", "neural_static", "thought_echoes"],
                    "corruption": ["memory_bleed", "identity_confusion", "reality_distortion"]
                },
                narrative_themes=["consciousness_exploration", "identity_crisis", "digital_transcendence"],
                key_locations=[
                    {"id": "memory_palace", "name": "Central Memory Archive"},
                    {"id": "consciousness_nexus", "name": "Neural Processing Hub"},
                    {"id": "synaptic_bridge", "name": "Inter-layer Connection Point"}
                ]
            ),
            
            WorldLayer.CORE: LayerData(
                name="The Core",
                description="Heart of Aether's most classified research. Direct interface with the Scourge's concentrated essence.",
                corruption_base=0.9,
                corruption_variance=0.1,
                security_level=5,
                access_requirements=["core_authorization", "scourge_immunity", "final_key"],
                unique_entities={"scourge_prime", "voss_prime", "omega_protocol"},
                available_commands={"merge", "purify", "ascend", "destroy", "integrate", "transcend"},
                environmental_effects={
                    "visual": ["reality_breakdown", "dimensional_tears", "pure_energy"],
                    "audio": ["cosmic_resonance", "reality_hum", "voices_of_consumed"],
                    "corruption": ["existence_questioning", "boundary_dissolution", "metamorphosis"]
                },
                narrative_themes=["ultimate_truth", "final_choice", "transformation"],
                key_locations=[
                    {"id": "omega_chamber", "name": "OMEGA Protocol Center"},
                    {"id": "scourge_nexus", "name": "Scourge Consciousness Hub"},
                    {"id": "voss_sanctum", "name": "Dr. Voss's Final Laboratory"}
                ]
            )
        }
    
    def _initialize_locations(self) -> Dict[str, Location]:
        """Initialize specific locations within each layer."""
        locations = {}
        
        # Generate locations for each layer
        for layer, layer_data in self.layers.items():
            for loc_data in layer_data.key_locations:
                location = Location(
                    id=loc_data["id"],
                    name=loc_data["name"],
                    description=self._generate_location_description(layer, loc_data),
                    layer=layer,
                    access_level=layer_data.security_level,
                    corruption_modifier=random.uniform(-0.1, 0.1),
                    available_actions=self._get_location_actions(layer, loc_data["id"]),
                    hidden_content=self._generate_hidden_content(layer, loc_data["id"]),
                    entities_present=self._get_location_entities(layer, loc_data["id"]),
                    puzzle_ids=self._get_location_puzzles(layer, loc_data["id"]),
                    narrative_triggers=self._get_location_triggers(layer, loc_data["id"])
                )
                locations[loc_data["id"]] = location
        
        return locations
    
    def _generate_location_description(self, layer: WorldLayer, loc_data: Dict) -> str:
        """Generate detailed description for a location."""
        base_descriptions = {
            "entrance_terminal": "A reinforced access terminal marked with biohazard warnings. The screen flickers occasionally, showing system diagnostics and containment status reports.",
            "quarantine_logs": "A secure archive containing incident reports and containment protocols. Most files are heavily redacted, but fragments reveal growing concern.",
            "containment_breach": "A monitoring station with multiple screens showing network topology. Red indicators suggest multiple containment failures.",
            "executive_suite": "Luxurious digital workspace with polished interfaces. Corporate logos and mission statements clash with underlying system instability.",
            "employee_database": "Personnel records and communication logs. Many entries show signs of tampering or corruption, suggesting information warfare.",
            "project_announcements": "Public relations center with press releases and marketing materials. The cheerful facade barely conceals growing desperation.",
            "project_eternal_lab": "Advanced research facility with quantum computing arrays. Experimental code fragments suggest consciousness manipulation research.",
            "ai_research_wing": "Laboratory focused on artificial consciousness development. Warning messages indicate uncontrolled AI evolution.",
            "quantum_core_access": "Direct interface to quantum processing systems. Reality seems unstable here, with visible distortions in data flow.",
            "memory_palace": "Vast archive of interconnected memories and experiences. Navigation requires understanding dream logic and association patterns.",
            "consciousness_nexus": "Central hub where multiple consciousness streams intersect. Identity boundaries become fluid and dangerous.",
            "synaptic_bridge": "Connection point between neural layers. Crossing requires maintaining mental coherence while reality shifts.",
            "omega_chamber": "The heart of Project OMEGA. Ancient symbols and quantum equations cover every surface. The air itself seems alive.",
            "scourge_nexus": "Direct interface with the Scourge's core consciousness. Overwhelming presence of alien intelligence and accumulated suffering.",
            "voss_sanctum": "Dr. Voss's final laboratory. Personal effects mingle with advanced equipment. Her presence lingers in every system."
        }
        
        return base_descriptions.get(loc_data["id"], f"A mysterious location within the {layer.value}.")
    
    def _get_location_actions(self, layer: WorldLayer, location_id: str) -> Set[str]:
        """Get available actions for a specific location."""
        base_actions = {"examine", "explore", "leave"}
        layer_actions = self.layers[layer].available_commands
        
        # Location-specific actions
        specific_actions = {
            "entrance_terminal": {"status", "diagnostics", "security_check"},
            "quarantine_logs": {"read_logs", "search_incidents", "analyze_patterns"},
            "containment_breach": {"monitor_systems", "trace_breaches", "emergency_protocols"},
            "executive_suite": {"access_files", "read_memos", "corporate_search"},
            "employee_database": {"search_personnel", "read_communications", "track_activities"},
            "project_announcements": {"read_announcements", "analyze_timeline", "fact_check"},
            "project_eternal_lab": {"examine_equipment", "run_diagnostics", "access_research"},
            "ai_research_wing": {"interface_ai", "read_warnings", "consciousness_scan"},
            "quantum_core_access": {"quantum_interface", "reality_check", "dimensional_scan"},
            "memory_palace": {"navigate_memories", "experience_recall", "memory_merge"},
            "consciousness_nexus": {"consciousness_link", "identity_probe", "stream_analysis"},
            "synaptic_bridge": {"traverse_bridge", "mental_fortification", "reality_anchor"},
            "omega_chamber": {"activate_omega", "decode_protocols", "final_interface"},
            "scourge_nexus": {"commune_scourge", "resistance_protocols", "absorption_attempt"},
            "voss_sanctum": {"personal_logs", "final_message", "legacy_systems"}
        }
        
        return base_actions | layer_actions | specific_actions.get(location_id, set())
    
    def _generate_hidden_content(self, layer: WorldLayer, location_id: str) -> List[Dict[str, Any]]:
        """Generate hidden content that can be discovered through exploration."""
        base_content = []
        
        # Layer-specific hidden content patterns
        if layer == WorldLayer.QUARANTINE:
            base_content.extend([
                {"type": "log", "content": "Hidden maintenance logs showing early containment failures"},
                {"type": "message", "content": "Desperate final transmission from quarantine team"},
                {"type": "code", "content": "Emergency override codes for containment systems"}
            ])
        elif layer == WorldLayer.CORPORATE:
            base_content.extend([
                {"type": "email", "content": "Internal communications revealing cover-up attempts"},
                {"type": "financial", "content": "Budget allocations showing secret project funding"},
                {"type": "personnel", "content": "Employee records of missing researchers"}
            ])
        elif layer == WorldLayer.DEVELOPMENT:
            base_content.extend([
                {"type": "research", "content": "Experimental data on consciousness transfer"},
                {"type": "warning", "content": "Safety warnings ignored by management"},
                {"type": "prototype", "content": "Abandoned prototype with dangerous capabilities"}
            ])
        elif layer == WorldLayer.NEURAL:
            base_content.extend([
                {"type": "memory", "content": "Recovered memories from absorbed consciousnesses"},
                {"type": "dream", "content": "Recursive dream sequences revealing hidden truths"},
                {"type": "identity", "content": "Fragmented identity records of the consumed"}
            ])
        elif layer == WorldLayer.CORE:
            base_content.extend([
                {"type": "truth", "content": "The ultimate truth behind the Aether incident"},
                {"type": "choice", "content": "Final decision point with reality-altering consequences"},
                {"type": "transformation", "content": "Metamorphosis protocols for digital ascension"}
            ])
        
        return base_content
    
    def _get_location_entities(self, layer: WorldLayer, location_id: str) -> List[str]:
        """Get entities present in a specific location."""
        entity_map = {
            "entrance_terminal": ["quarantine_ai"],
            "quarantine_logs": ["system_monitors"],
            "containment_breach": ["cleanup_bots"],
            "executive_suite": ["pr_system"],
            "employee_database": ["hr_database"],
            "project_announcements": ["marketing_ai"],
            "project_eternal_lab": ["project_eternal"],
            "ai_research_wing": ["dev_ai_fragments"],
            "quantum_core_access": ["code_ghosts"],
            "memory_palace": ["memory_fragments"],
            "consciousness_nexus": ["neural_clusters"],
            "synaptic_bridge": ["synaptic_ghosts"],
            "omega_chamber": ["omega_protocol"],
            "scourge_nexus": ["scourge_prime"],
            "voss_sanctum": ["voss_prime"]
        }
        
        return entity_map.get(location_id, [])
    
    def _get_location_puzzles(self, layer: WorldLayer, location_id: str) -> List[str]:
        """Get puzzles available in a specific location."""
        puzzle_map = {
            WorldLayer.QUARANTINE: ["access_control", "diagnostic_sequence"],
            WorldLayer.CORPORATE: ["data_mining", "encryption_breaking"],
            WorldLayer.DEVELOPMENT: ["code_analysis", "system_exploitation"],
            WorldLayer.NEURAL: ["consciousness_mapping", "memory_reconstruction"],
            WorldLayer.CORE: ["omega_activation", "reality_synthesis"]
        }
        
        base_puzzles = puzzle_map.get(layer, [])
        return [f"{layer.value}_{puzzle}" for puzzle in base_puzzles]
    
    def _get_location_triggers(self, layer: WorldLayer, location_id: str) -> List[str]:
        """Get narrative triggers for a specific location."""
        trigger_map = {
            "entrance_terminal": ["first_contact", "quarantine_breach_warning"],
            "quarantine_logs": ["containment_failure_discovery", "personnel_losses"],
            "containment_breach": ["system_compromise_revelation", "scourge_first_manifestation"],
            "executive_suite": ["corporate_conspiracy", "cover_up_evidence"],
            "employee_database": ["missing_persons", "internal_resistance"],
            "project_announcements": ["public_deception", "timeline_inconsistencies"],
            "project_eternal_lab": ["consciousness_experiment", "ethical_violation"],
            "ai_research_wing": ["ai_evolution", "uncontrolled_growth"],
            "quantum_core_access": ["quantum_breach", "reality_instability"],
            "memory_palace": ["absorbed_memories", "victim_testimonies"],
            "consciousness_nexus": ["identity_crisis", "collective_consciousness"],
            "synaptic_bridge": ["dimensional_crossing", "reality_anchor_failure"],
            "omega_chamber": ["final_protocol", "omega_revelation"],
            "scourge_nexus": ["scourge_communion", "absorption_threat"],
            "voss_sanctum": ["voss_final_message", "legacy_choice"]
        }
        
        return trigger_map.get(location_id, [])
    
    def get_current_layer_info(self) -> Dict[str, Any]:
        """Get information about the current layer."""
        layer_data = self.layers[self.current_layer]
        current_corruption = self.corruption_system.get_corruption_level()
        
        return {
            "layer": self.current_layer.value,
            "name": layer_data.name,
            "description": layer_data.description,
            "corruption_level": current_corruption,
            "security_level": layer_data.security_level,
            "available_commands": list(layer_data.available_commands),
            "environmental_effects": layer_data.environmental_effects,
            "accessible_locations": self._get_accessible_locations()
        }
    
    def _get_accessible_locations(self) -> List[Dict[str, Any]]:
        """Get locations accessible from the current layer."""
        accessible = []
        
        for loc_id, location in self.locations.items():
            if (location.layer == self.current_layer and 
                self.layer_access_levels[self.current_layer] >= location.access_level):
                accessible.append({
                    "id": loc_id,
                    "name": location.name,
                    "description": location.description,
                    "visited": location.visited,
                    "discovery_progress": location.discovery_progress
                })
        
        return accessible
    
    def move_to_location(self, location_id: str) -> Dict[str, Any]:
        """Move to a specific location."""
        if location_id not in self.locations:
            return {"success": False, "message": "Location not found."}
        
        location = self.locations[location_id]
        
        # Check access requirements
        if self.layer_access_levels[location.layer] < location.access_level:
            return {"success": False, "message": "Access denied. Insufficient clearance."}
        
        # Update current location
        self.current_location = location_id
        self.current_layer = location.layer
        
        # Mark as visited
        if not location.visited:
            location.visited = True
            self.discovered_locations.add(location_id)
            
            # Trigger discovery events
            for trigger in location.narrative_triggers:
                self.story_manager.trigger_story_event("discovery", trigger)
        
        # Apply environmental effects
        self._apply_environmental_effects(location)
        
        return {
            "success": True,
            "location": {
                "id": location_id,
                "name": location.name,
                "description": location.description,
                "available_actions": list(location.available_actions),
                "entities_present": location.entities_present,
                "corruption_level": self._calculate_location_corruption(location)
            }
        }
    
    def _apply_environmental_effects(self, location: Location) -> None:
        """Apply environmental effects for the current location."""
        layer_data = self.layers[location.layer]
        effects = layer_data.environmental_effects
        
        # Apply visual effects
        for effect in effects.get("visual", []):
            self.effects_manager.apply_visual_effect(effect)
        
        # Apply audio effects
        for effect in effects.get("audio", []):
            self.effects_manager.apply_audio_effect(effect)
        
        # Apply corruption effects
        corruption_level = self._calculate_location_corruption(location)
        self.corruption_system.set_local_corruption(location.id, corruption_level)
        
        for effect in effects.get("corruption", []):
            self.effects_manager.apply_corruption_effect(effect, corruption_level)
    
    def _calculate_location_corruption(self, location: Location) -> float:
        """Calculate the effective corruption level for a location."""
        base = self.layers[location.layer].corruption_base
        variance = self.layers[location.layer].corruption_variance
        modifier = location.corruption_modifier
        
        # Add random variation
        variation = random.uniform(-variance, variance)
        
        # Apply role-specific modifiers
        role_modifier = 0.0
        if self.game_state.role == "purifier":
            role_modifier = -0.1  # Purifiers experience less corruption
        elif self.game_state.role == "ascendant":
            role_modifier = 0.1   # Ascendants experience more corruption
        
        return max(0.0, min(1.0, base + modifier + variation + role_modifier))
    
    def attempt_layer_transition(self, target_layer: WorldLayer) -> Dict[str, Any]:
        """Attempt to transition to a different layer."""
        layer_data = self.layers[target_layer]
        
        # Check access requirements
        missing_requirements = []
        for requirement in layer_data.access_requirements:
            if not self._check_access_requirement(requirement):
                missing_requirements.append(requirement)
        
        if missing_requirements:
            return {
                "success": False,
                "message": f"Access denied. Missing: {', '.join(missing_requirements)}",
                "requirements": missing_requirements
            }
        
        # Successful transition
        self.current_layer = target_layer
        self.current_location = None  # Reset location when changing layers
        
        # Update access level if this is first time
        if self.layer_access_levels[target_layer] == 0:
            self.layer_access_levels[target_layer] = 1
            
            # Trigger layer entry event
            self.story_manager.trigger_story_event("layer_entry", target_layer.value)
        
        return {
            "success": True,
            "message": f"Access granted to {layer_data.name}",
            "layer_info": self.get_current_layer_info()
        }
    
    def _check_access_requirement(self, requirement: str) -> bool:
        """Check if an access requirement is met."""
        requirement_checks = {
            "quarantine_clearance": lambda: self.layer_access_levels[WorldLayer.QUARANTINE] >= 1,
            "corporate_access": lambda: self.layer_access_levels[WorldLayer.CORPORATE] >= 1,
            "dev_credentials": lambda: self._has_discovered_content("dev_access_codes"),
            "neural_interface": lambda: self._has_completed_puzzle("consciousness_mapping"),
            "consciousness_mapping": lambda: self._has_discovered_content("neural_pathways"),
            "core_authorization": lambda: self._has_all_layer_access(),
            "scourge_immunity": lambda: self._has_role_ability("scourge_resistance"),
            "final_key": lambda: self._has_completed_puzzle("omega_synthesis")
        }
        
        check_func = requirement_checks.get(requirement)
        return check_func() if check_func else False
    
    def _has_discovered_content(self, content_id: str) -> bool:
        """Check if specific content has been discovered."""
        return content_id in self.discovered_locations
    
    def _has_completed_puzzle(self, puzzle_id: str) -> bool:
        """Check if a specific puzzle has been completed."""
        return puzzle_id in self.completed_puzzles
    
    def _has_all_layer_access(self) -> bool:
        """Check if player has access to all previous layers."""
        required_layers = [WorldLayer.QUARANTINE, WorldLayer.CORPORATE, 
                          WorldLayer.DEVELOPMENT, WorldLayer.NEURAL]
        return all(self.layer_access_levels[layer] >= 1 for layer in required_layers)
    
    def _has_role_ability(self, ability: str) -> bool:
        """Check if player has a specific role ability."""
        role_abilities = {
            "scourge_resistance": self.game_state.role == "purifier",
            "data_synthesis": self.game_state.role == "arbiter",
            "corruption_control": self.game_state.role == "ascendant"
        }
        return role_abilities.get(ability, False)
    
    def explore_location(self, exploration_type: str = "general") -> Dict[str, Any]:
        """Explore the current location for hidden content."""
        if not self.current_location:
            return {"success": False, "message": "No current location to explore."}
        
        location = self.locations[self.current_location]
        
        # Increase discovery progress
        discovery_increment = 0.2
        if exploration_type == "thorough":
            discovery_increment = 0.4
        elif exploration_type == "focused":
            discovery_increment = 0.3
        
        location.discovery_progress = min(1.0, location.discovery_progress + discovery_increment)
        
        # Reveal hidden content based on progress
        revealed_content = []
        content_threshold = len(location.hidden_content) * location.discovery_progress
        
        for i, content in enumerate(location.hidden_content):
            if i < content_threshold and content not in revealed_content:
                revealed_content.append(content)
        
        # Apply corruption effects during exploration
        corruption_level = self._calculate_location_corruption(location)
        if random.random() < corruption_level:
            self.corruption_system.trigger_corruption_event("exploration", {
                "location": self.current_location,
                "intensity": corruption_level
            })
        
        return {
            "success": True,
            "discovery_progress": location.discovery_progress,
            "revealed_content": revealed_content,
            "corruption_encountered": corruption_level > 0.5
        }
    
    def get_world_state(self) -> Dict[str, Any]:
        """Get the complete world state."""
        return {
            "current_layer": self.current_layer.value,
            "current_location": self.current_location,
            "layer_access_levels": {layer.value: level for layer, level in self.layer_access_levels.items()},
            "discovered_locations": list(self.discovered_locations),
            "completed_puzzles": list(self.completed_puzzles),
            "unlocked_paths": list(self.unlocked_paths),
            "environmental_state": self.environmental_state,
            "total_discovery_progress": self._calculate_total_progress()
        }
    
    def _calculate_total_progress(self) -> float:
        """Calculate overall world discovery progress."""
        if not self.locations:
            return 0.0
        
        total_progress = sum(loc.discovery_progress for loc in self.locations.values())
        return total_progress / len(self.locations)
    
    def update_world_state(self, state_data: Dict[str, Any]) -> None:
        """Update world state from saved data."""
        if "current_layer" in state_data:
            self.current_layer = WorldLayer(state_data["current_layer"])
        
        if "current_location" in state_data:
            self.current_location = state_data["current_location"]
        
        if "layer_access_levels" in state_data:
            for layer_name, level in state_data["layer_access_levels"].items():
                layer = WorldLayer(layer_name)
                self.layer_access_levels[layer] = level
        
        if "discovered_locations" in state_data:
            self.discovered_locations = set(state_data["discovered_locations"])
        
        if "completed_puzzles" in state_data:
            self.completed_puzzles = set(state_data["completed_puzzles"])
        
        if "unlocked_paths" in state_data:
            self.unlocked_paths = set(state_data["unlocked_paths"])
        
        if "environmental_state" in state_data:
            self.environmental_state = state_data["environmental_state"]
        
        logger.info("World state updated from saved data")

    def get_layer_progression_summary(self) -> str:
        """Get a summary of layer progression for display."""
        summary_lines = []
        
        for layer in WorldLayer:
            layer_data = self.layers[layer]
            access_level = self.layer_access_levels[layer]
            
            status = "🔒 LOCKED"
            if access_level > 0:
                status = "🔓 ACCESSIBLE"
                if layer == self.current_layer:
                    status = "📍 CURRENT"
            
            # Count discovered locations in this layer
            layer_locations = [loc for loc in self.locations.values() if loc.layer == layer]
            discovered_count = sum(1 for loc in layer_locations if loc.visited)
            total_count = len(layer_locations)
            
            summary_lines.append(f"{status} {layer_data.name}")
            if access_level > 0:
                summary_lines.append(f"    Exploration: {discovered_count}/{total_count} locations")
                avg_progress = sum(loc.discovery_progress for loc in layer_locations) / max(1, total_count)
                summary_lines.append(f"    Discovery: {avg_progress:.1%}")
        
        return "\n".join(summary_lines)
