"""
Knowledge Graph system for dynamic narrative generation and entity relationship management.

This module implements a sophisticated knowledge graph that tracks:
- Entity relationships and interactions
- Narrative threads and their connections
- Player action consequences and ripple effects
- Dynamic story generation based on accumulated knowledge
- Cross-layer information propagation
"""

import logging
import json
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import networkx as nx
from collections import defaultdict

logger = logging.getLogger(__name__)

class RelationshipType(Enum):
    """Types of relationships between entities"""
    ALLIES = "allies"
    ENEMIES = "enemies"
    NEUTRAL = "neutral"
    CREATED_BY = "created_by"
    CORRUPTED_BY = "corrupted_by"
    CONTAINS = "contains"
    CONNECTED_TO = "connected_to"
    DEPENDS_ON = "depends_on"
    INFLUENCES = "influences"
    MEMORIES_OF = "memories_of"
    FRAGMENTS_OF = "fragments_of"
    PROTECTS = "protects"
    THREATENS = "threatens"
    COMMUNICATES_WITH = "communicates_with"

class EntityType(Enum):
    """Types of entities in the knowledge graph"""
    PLAYER = "player"
    NPC = "npc"
    DIGITAL_ENTITY = "digital_entity"
    LOCATION = "location"
    SYSTEM = "system"
    ARTIFACT = "artifact"
    MEMORY = "memory"
    FACTION = "faction"
    EVENT = "event"
    CONCEPT = "concept"

@dataclass
class KnowledgeNode:
    """Represents a node in the knowledge graph"""
    id: str
    name: str
    entity_type: EntityType
    layer: int = 1  # Which layer this entity primarily exists in
    properties: Dict[str, Any] = field(default_factory=dict)
    discovery_timestamp: datetime = field(default_factory=datetime.now)
    corruption_level: float = 0.0
    importance_score: float = 1.0  # How important this node is for narrative generation
    narrative_threads: Set[str] = field(default_factory=set)  # Which story threads this connects to
    player_interactions: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        if isinstance(self.discovery_timestamp, str):
            self.discovery_timestamp = datetime.fromisoformat(self.discovery_timestamp)

@dataclass
class KnowledgeEdge:
    """Represents a relationship between two entities"""
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    strength: float = 1.0  # Strength of the relationship (0.0 to 1.0)
    discovered: bool = False  # Whether player has discovered this relationship
    properties: Dict[str, Any] = field(default_factory=dict)
    discovery_timestamp: Optional[datetime] = None
    narrative_significance: float = 1.0  # How significant this relationship is for story
    
    def __post_init__(self):
        if isinstance(self.discovery_timestamp, str) and self.discovery_timestamp:
            self.discovery_timestamp = datetime.fromisoformat(self.discovery_timestamp)

@dataclass
class NarrativeThread:
    """Represents an ongoing narrative thread"""
    id: str
    name: str
    description: str
    active: bool = True
    completion_progress: float = 0.0
    involved_entities: Set[str] = field(default_factory=set)
    key_events: List[str] = field(default_factory=list)
    player_role_relevance: Dict[str, float] = field(default_factory=dict)  # How relevant to each role
    next_potential_developments: List[str] = field(default_factory=list)

class KnowledgeGraph:
    """Advanced knowledge graph for dynamic narrative generation"""
    
    def __init__(self):
        """Initialize the knowledge graph"""
        self.graph = nx.MultiDiGraph()  # Directed graph allowing multiple edges
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.edges: Dict[Tuple[str, str, str], KnowledgeEdge] = {}  # (source, target, type) -> edge
        self.narrative_threads: Dict[str, NarrativeThread] = {}
        
        # Narrative generation state
        self.player_knowledge_level = 0.0  # Overall player knowledge accumulation
        self.corruption_influence = 0.0    # How much corruption affects narrative generation
        self.active_storylines: Set[str] = set()
        self.narrative_momentum: Dict[str, float] = defaultdict(float)  # Thread momentum scores
        
        # Initialize with base game entities
        self._initialize_base_entities()
        
    def _initialize_base_entities(self):
        """Initialize the knowledge graph with base game entities"""
        # Core locations
        self.add_entity("quarantine_zone", "Quarantine Zone", EntityType.LOCATION, 
                       layer=1, properties={"security_level": "maximum", "corruption_level": 0.1})
        self.add_entity("corporate_shell", "Corporate Shell", EntityType.LOCATION,
                       layer=2, properties={"security_level": "high", "corruption_level": 0.3})
        self.add_entity("development_sphere", "Development Sphere", EntityType.LOCATION,
                       layer=3, properties={"security_level": "medium", "corruption_level": 0.5})
        self.add_entity("neural_network", "Neural Network", EntityType.LOCATION,
                       layer=4, properties={"security_level": "low", "corruption_level": 0.7})
        self.add_entity("core_system", "Core System", EntityType.LOCATION,
                       layer=5, properties={"security_level": "minimal", "corruption_level": 0.9})
        
        # Core entities
        self.add_entity("voss_visionary", "Dr. Voss (Visionary)", EntityType.DIGITAL_ENTITY,
                       layer=5, properties={"personality": "ambitious", "corruption_level": 0.3})
        self.add_entity("voss_penitent", "Dr. Voss (Penitent)", EntityType.DIGITAL_ENTITY,
                       layer=5, properties={"personality": "remorseful", "corruption_level": 0.5})
        self.add_entity("voss_survivor", "Dr. Voss (Survivor)", EntityType.DIGITAL_ENTITY,
                       layer=5, properties={"personality": "adaptive", "corruption_level": 0.7})
        self.add_entity("aetherial_scourge", "Aetherial Scourge", EntityType.DIGITAL_ENTITY,
                       layer=5, properties={"threat_level": "maximum", "corruption_level": 1.0})
        self.add_entity("sentinel", "SENTINEL", EntityType.DIGITAL_ENTITY,
                       layer=2, properties={"role": "security", "corruption_level": 0.2})
        self.add_entity("rusty", "Rusty", EntityType.DIGITAL_ENTITY,
                       layer=1, properties={"role": "guide", "corruption_level": 0.1})
        
        # Core factions
        self.add_entity("resistance", "Digital Resistance", EntityType.FACTION,
                       properties={"alignment": "purifier", "influence": 0.6})
        self.add_entity("collective", "The Collective", EntityType.FACTION,
                       properties={"alignment": "neutral", "influence": 0.8})
        self.add_entity("archivists", "Data Archivists", EntityType.FACTION,
                       properties={"alignment": "arbiter", "influence": 0.5})
        
        # Initialize base relationships
        self._initialize_base_relationships()
        
        # Initialize narrative threads
        self._initialize_narrative_threads()
    
    def _initialize_base_relationships(self):
        """Initialize base relationships between entities"""
        # Location connections (layer progression)
        self.add_relationship("quarantine_zone", "corporate_shell", RelationshipType.CONNECTED_TO, 0.8)
        self.add_relationship("corporate_shell", "development_sphere", RelationshipType.CONNECTED_TO, 0.7)
        self.add_relationship("development_sphere", "neural_network", RelationshipType.CONNECTED_TO, 0.6)
        self.add_relationship("neural_network", "core_system", RelationshipType.CONNECTED_TO, 0.5)
        
        # Voss fragment relationships
        self.add_relationship("voss_visionary", "voss_penitent", RelationshipType.FRAGMENTS_OF, 1.0)
        self.add_relationship("voss_visionary", "voss_survivor", RelationshipType.FRAGMENTS_OF, 1.0)
        self.add_relationship("voss_penitent", "voss_survivor", RelationshipType.FRAGMENTS_OF, 1.0)
        
        # Scourge relationships
        self.add_relationship("aetherial_scourge", "voss_visionary", RelationshipType.CREATED_BY, 0.9)
        self.add_relationship("aetherial_scourge", "core_system", RelationshipType.CONTAINS, 1.0)
        
        # Entity-location relationships
        self.add_relationship("voss_visionary", "core_system", RelationshipType.CONNECTED_TO, 1.0)
        self.add_relationship("sentinel", "corporate_shell", RelationshipType.PROTECTS, 0.8)
        self.add_relationship("rusty", "quarantine_zone", RelationshipType.CONNECTED_TO, 0.7)
    
    def _initialize_narrative_threads(self):
        """Initialize base narrative threads"""
        # Core mystery thread
        self.add_narrative_thread(
            "core_mystery",
            "The Aether Incident",
            "Uncover the truth behind what happened at Aether Corporation",
            involved_entities={"voss_visionary", "aetherial_scourge", "core_system"},
            player_role_relevance={"purifier": 0.9, "arbiter": 1.0, "ascendant": 0.8}
        )
        
        # Voss fragments thread
        self.add_narrative_thread(
            "voss_fragments",
            "Scattered Consciousness",
            "Understand the different aspects of Dr. Voss's fragmented mind",
            involved_entities={"voss_visionary", "voss_penitent", "voss_survivor"},
            player_role_relevance={"purifier": 0.8, "arbiter": 0.9, "ascendant": 0.7}
        )
        
        # Corruption spread thread
        self.add_narrative_thread(
            "corruption_spread",
            "Digital Plague",
            "Track and potentially stop the spread of corruption through the network",
            involved_entities={"aetherial_scourge", "neural_network", "core_system"},
            player_role_relevance={"purifier": 1.0, "arbiter": 0.6, "ascendant": 0.4}
        )
        
        # Power accumulation thread (ascendant-focused)
        self.add_narrative_thread(
            "power_accumulation",
            "Digital Ascension",
            "Gain control over digital entities and systems",
            involved_entities={"aetherial_scourge", "collective", "neural_network"},
            player_role_relevance={"purifier": 0.2, "arbiter": 0.5, "ascendant": 1.0}
        )
    
    def add_entity(self, entity_id: str, name: str, entity_type: EntityType, 
                   layer: int = 1, properties: Optional[Dict[str, Any]] = None,
                   importance_score: float = 1.0) -> KnowledgeNode:
        """Add a new entity to the knowledge graph"""
        if properties is None:
            properties = {}
            
        node = KnowledgeNode(
            id=entity_id,
            name=name,
            entity_type=entity_type,
            layer=layer,
            properties=properties,
            importance_score=importance_score
        )
        
        self.nodes[entity_id] = node
        self.graph.add_node(entity_id, **properties)
        
        logger.debug(f"Added entity: {name} ({entity_id}) to layer {layer}")
        return node
    
    def add_relationship(self, source_id: str, target_id: str, 
                        relationship_type: RelationshipType, strength: float = 1.0,
                        properties: Optional[Dict[str, Any]] = None,
                        discovered: bool = False) -> KnowledgeEdge:
        """Add a relationship between two entities"""
        if properties is None:
            properties = {}
            
        edge_key = (source_id, target_id, relationship_type.value)
        edge = KnowledgeEdge(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            strength=strength,
            properties=properties,
            discovered=discovered
        )
        
        self.edges[edge_key] = edge
        self.graph.add_edge(source_id, target_id, type=relationship_type.value, 
                           strength=strength, **properties)
        
        logger.debug(f"Added relationship: {source_id} --{relationship_type.value}--> {target_id}")
        return edge
    
    def add_narrative_thread(self, thread_id: str, name: str, description: str,
                           involved_entities: Optional[Set[str]] = None,
                           player_role_relevance: Optional[Dict[str, float]] = None) -> NarrativeThread:
        """Add a new narrative thread"""
        if involved_entities is None:
            involved_entities = set()
        if player_role_relevance is None:
            player_role_relevance = {}
            
        thread = NarrativeThread(
            id=thread_id,
            name=name,
            description=description,
            involved_entities=involved_entities,
            player_role_relevance=player_role_relevance
        )
        
        self.narrative_threads[thread_id] = thread
        self.active_storylines.add(thread_id)
        
        # Update entity narrative thread references
        for entity_id in involved_entities:
            if entity_id in self.nodes:
                self.nodes[entity_id].narrative_threads.add(thread_id)
        
        logger.debug(f"Added narrative thread: {name} ({thread_id})")
        return thread
    
    def discover_entity(self, entity_id: str, player_context: Dict[str, Any]) -> Optional[KnowledgeNode]:
        """Mark an entity as discovered by the player"""
        if entity_id not in self.nodes:
            logger.warning(f"Attempted to discover unknown entity: {entity_id}")
            return None
            
        node = self.nodes[entity_id]
        
        # Record player interaction
        interaction = {
            "type": "discovery",
            "timestamp": datetime.now(),
            "context": player_context.copy(),
            "player_role": player_context.get("role", "unknown")
        }
        node.player_interactions.append(interaction)
        
        # Update player knowledge level
        self.player_knowledge_level += node.importance_score * 0.1
        
        # Check for narrative thread activations
        self._check_narrative_activations(entity_id, player_context)
        
        logger.info(f"Entity discovered: {node.name} by {player_context.get('role', 'unknown')}")
        return node
    
    def discover_relationship(self, source_id: str, target_id: str, 
                            relationship_type: RelationshipType) -> Optional[KnowledgeEdge]:
        """Mark a relationship as discovered by the player"""
        edge_key = (source_id, target_id, relationship_type.value)
        if edge_key not in self.edges:
            logger.warning(f"Attempted to discover unknown relationship: {edge_key}")
            return None
            
        edge = self.edges[edge_key]
        edge.discovered = True
        edge.discovery_timestamp = datetime.now()
        
        # Update player knowledge level
        self.player_knowledge_level += edge.narrative_significance * 0.05
        
        logger.info(f"Relationship discovered: {source_id} --{relationship_type.value}--> {target_id}")
        return edge
    
    def _check_narrative_activations(self, entity_id: str, player_context: Dict[str, Any]):
        """Check if discovering this entity activates new narrative threads"""
        node = self.nodes[entity_id]
        player_role = player_context.get("role", "arbiter")
        
        for thread_id in node.narrative_threads:
            if thread_id not in self.active_storylines:
                thread = self.narrative_threads[thread_id]
                
                # Check if this discovery meets activation criteria
                relevance = thread.player_role_relevance.get(player_role, 0.5)
                if relevance > 0.6 and self.player_knowledge_level > 0.3:
                    self.active_storylines.add(thread_id)
                    self.narrative_momentum[thread_id] = relevance
                    logger.info(f"Activated narrative thread: {thread.name}")
    
    def get_related_entities(self, entity_id: str, relationship_types: Optional[List[RelationshipType]] = None,
                           max_depth: int = 2) -> Dict[str, List[str]]:
        """Get entities related to the given entity"""
        if entity_id not in self.nodes:
            return {}
            
        related = defaultdict(list)
        
        # Direct relationships
        for (source, target, rel_type) in self.edges:
            if relationship_types and RelationshipType(rel_type.split('.')[-1] if '.' in rel_type else rel_type) not in relationship_types:
                continue
                
            if source == entity_id:
                related[rel_type].append(target)
            elif target == entity_id:
                # Add reverse relationship
                related[f"reverse_{rel_type}"].append(source)
        
        # Extended relationships (if max_depth > 1)
        if max_depth > 1:
            for rel_entities in list(related.values()):
                for related_entity in rel_entities:
                    sub_related = self.get_related_entities(related_entity, relationship_types, max_depth - 1)
                    for sub_rel_type, sub_entities in sub_related.items():
                        related[f"indirect_{sub_rel_type}"].extend(sub_entities)
        
        return dict(related)
    
    def generate_narrative_context(self, player_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate rich narrative context for LLM prompts"""
        player_role = player_context.get("role", "arbiter")
        current_layer = player_context.get("current_layer", 1)
        
        # Get relevant entities for current context
        layer_entities = [node for node in self.nodes.values() if node.layer == current_layer]
        discovered_entities = [node for node in self.nodes.values() 
                             if any(interaction["type"] == "discovery" for interaction in node.player_interactions)]
        
        # Get active narrative threads relevant to player role
        relevant_threads = []
        for thread_id in self.active_storylines:
            thread = self.narrative_threads[thread_id]
            relevance = thread.player_role_relevance.get(player_role, 0.0)
            if relevance > 0.4:
                relevant_threads.append({
                    "id": thread_id,
                    "name": thread.name,
                    "description": thread.description,
                    "progress": thread.completion_progress,
                    "relevance": relevance,
                    "momentum": self.narrative_momentum.get(thread_id, 0.0)
                })
        
        # Sort by relevance and momentum
        relevant_threads.sort(key=lambda x: x["relevance"] * x["momentum"], reverse=True)
        
        # Get relationship insights
        discovered_relationships = []
        for edge in self.edges.values():
            if edge.discovered:
                discovered_relationships.append({
                    "source": self.nodes[edge.source_id].name,
                    "target": self.nodes[edge.target_id].name,
                    "type": edge.relationship_type.value,
                    "strength": edge.strength
                })
        
        # Generate context summary
        context = {
            "player_knowledge_level": self.player_knowledge_level,
            "corruption_influence": self.corruption_influence,
            "current_layer": current_layer,
            "layer_entities": [{"id": e.id, "name": e.name, "type": e.entity_type.value} for e in layer_entities],
            "discovered_entities": [{"id": e.id, "name": e.name, "importance": e.importance_score} for e in discovered_entities],
            "active_threads": relevant_threads[:3],  # Top 3 most relevant threads
            "recent_relationships": discovered_relationships[-5:],  # 5 most recent discoveries
            "narrative_momentum": dict(self.narrative_momentum),
            "total_entities_discovered": len(discovered_entities),
            "relationship_discovery_rate": len(discovered_relationships) / max(len(self.edges), 1)
        }
        
        return context
    
    def update_narrative_momentum(self, action_type: str, entities_involved: List[str], 
                                player_context: Dict[str, Any]):
        """Update narrative momentum based on player actions"""
        player_role = player_context.get("role", "arbiter")
        
        # Identify affected narrative threads
        affected_threads = set()
        for entity_id in entities_involved:
            if entity_id in self.nodes:
                affected_threads.update(self.nodes[entity_id].narrative_threads)
        
        # Update momentum based on action type and role alignment
        momentum_changes = {
            "discovery": 0.1,
            "interaction": 0.05,
            "conflict": 0.15,
            "cooperation": 0.08,
            "betrayal": 0.2,
            "sacrifice": 0.25
        }
        
        base_change = momentum_changes.get(action_type, 0.05)
        
        for thread_id in affected_threads:
            if thread_id in self.narrative_threads:
                thread = self.narrative_threads[thread_id]
                role_multiplier = thread.player_role_relevance.get(player_role, 0.5)
                self.narrative_momentum[thread_id] += base_change * role_multiplier
                
                # Cap momentum at 1.0
                self.narrative_momentum[thread_id] = min(1.0, self.narrative_momentum[thread_id])
    
    def get_next_narrative_suggestions(self, player_context: Dict[str, Any], 
                                     count: int = 3) -> List[Dict[str, Any]]:
        """Get suggestions for next narrative developments"""
        context = self.generate_narrative_context(player_context)
        suggestions = []
        
        # Get high-momentum threads with potential developments
        for thread_data in context["active_threads"]:
            thread_id = thread_data["id"]
            thread = self.narrative_threads[thread_id]
            momentum = self.narrative_momentum.get(thread_id, 0.0)
            
            if momentum > 0.3 and thread.next_potential_developments:
                for development in thread.next_potential_developments[:2]:  # Top 2 per thread
                    suggestions.append({
                        "thread_id": thread_id,
                        "thread_name": thread.name,
                        "development": development,
                        "priority": momentum * thread_data["relevance"],
                        "entities_involved": list(thread.involved_entities)
                    })
        
        # Sort by priority and return top suggestions
        suggestions.sort(key=lambda x: x["priority"], reverse=True)
        return suggestions[:count]
    
    def export_graph_data(self) -> Dict[str, Any]:
        """Export the knowledge graph for persistence"""
        return {
            "nodes": {node_id: {
                "id": node.id,
                "name": node.name,
                "entity_type": node.entity_type.value,
                "layer": node.layer,
                "properties": node.properties,
                "discovery_timestamp": node.discovery_timestamp.isoformat(),
                "corruption_level": node.corruption_level,
                "importance_score": node.importance_score,
                "narrative_threads": list(node.narrative_threads),
                "player_interactions": node.player_interactions
            } for node_id, node in self.nodes.items()},
            
            "edges": {f"{edge.source_id}-{edge.target_id}-{edge.relationship_type.value}": {
                "source_id": edge.source_id,
                "target_id": edge.target_id,
                "relationship_type": edge.relationship_type.value,
                "strength": edge.strength,
                "discovered": edge.discovered,
                "properties": edge.properties,
                "discovery_timestamp": edge.discovery_timestamp.isoformat() if edge.discovery_timestamp else None,
                "narrative_significance": edge.narrative_significance
            } for edge in self.edges.values()},
            
            "narrative_threads": {thread_id: {
                "id": thread.id,
                "name": thread.name,
                "description": thread.description,
                "active": thread.active,
                "completion_progress": thread.completion_progress,
                "involved_entities": list(thread.involved_entities),
                "key_events": thread.key_events,
                "player_role_relevance": thread.player_role_relevance,
                "next_potential_developments": thread.next_potential_developments
            } for thread_id, thread in self.narrative_threads.items()},
            
            "state": {
                "player_knowledge_level": self.player_knowledge_level,
                "corruption_influence": self.corruption_influence,
                "active_storylines": list(self.active_storylines),
                "narrative_momentum": dict(self.narrative_momentum)
            }
        }
    
    def import_graph_data(self, data: Dict[str, Any]):
        """Import knowledge graph data"""
        # Clear existing data
        self.__init__()
        
        # Import nodes
        for node_data in data.get("nodes", {}).values():
            self.add_entity(
                node_data["id"],
                node_data["name"],
                EntityType(node_data["entity_type"]),
                node_data.get("layer", 1),
                node_data.get("properties", {}),
                node_data.get("importance_score", 1.0)
            )
            
            # Restore additional node data
            node = self.nodes[node_data["id"]]
            node.discovery_timestamp = datetime.fromisoformat(node_data["discovery_timestamp"])
            node.corruption_level = node_data.get("corruption_level", 0.0)
            node.narrative_threads = set(node_data.get("narrative_threads", []))
            node.player_interactions = node_data.get("player_interactions", [])
        
        # Import edges
        for edge_data in data.get("edges", {}).values():
            self.add_relationship(
                edge_data["source_id"],
                edge_data["target_id"],
                RelationshipType(edge_data["relationship_type"]),
                edge_data.get("strength", 1.0),
                edge_data.get("properties", {}),
                edge_data.get("discovered", False)
            )
            
            # Restore additional edge data
            edge_key = (edge_data["source_id"], edge_data["target_id"], edge_data["relationship_type"])
            edge = self.edges[edge_key]
            if edge_data.get("discovery_timestamp"):
                edge.discovery_timestamp = datetime.fromisoformat(edge_data["discovery_timestamp"])
            edge.narrative_significance = edge_data.get("narrative_significance", 1.0)
        
        # Import narrative threads
        for thread_data in data.get("narrative_threads", {}).values():
            self.add_narrative_thread(
                thread_data["id"],
                thread_data["name"],
                thread_data["description"],
                set(thread_data.get("involved_entities", [])),
                thread_data.get("player_role_relevance", {})
            )
            
            # Restore additional thread data
            thread = self.narrative_threads[thread_data["id"]]
            thread.active = thread_data.get("active", True)
            thread.completion_progress = thread_data.get("completion_progress", 0.0)
            thread.key_events = thread_data.get("key_events", [])
            thread.next_potential_developments = thread_data.get("next_potential_developments", [])
        
        # Import state
        state = data.get("state", {})
        self.player_knowledge_level = state.get("player_knowledge_level", 0.0)
        self.corruption_influence = state.get("corruption_influence", 0.0)
        self.active_storylines = set(state.get("active_storylines", []))
        self.narrative_momentum = defaultdict(float, state.get("narrative_momentum", {}))
        
        logger.info("Knowledge graph data imported successfully")
