"""Persistence manager for Cyberscape: Digital Dread.

This module manages game state persistence, including:
- Save file creation and loading with corruption mechanics
- Auto-save functionality with corruption simulation
- Save file validation and integrity checking
- Backup management and recovery systems
- New Game Plus (NG+) features and progression
- Player profiling and cross-playthrough data
"""

import pickle
import os
import json
import logging
import shutil
import random
import hashlib
import base64
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from enum import Enum

logger = logging.getLogger(__name__)

class SaveCorruptionType(Enum):
    """Types of save file corruption."""
    NONE = "none"
    MINOR = "minor"           # Small data inconsistencies
    MODERATE = "moderate"     # Noticeable but recoverable corruption  
    MAJOR = "major"          # Significant data loss
    CRITICAL = "critical"    # Save barely functional
    TERMINAL = "terminal"    # Save completely corrupted

class NGPlusFeature(Enum):
    """New Game Plus features that can be unlocked."""
    ROLE_MEMORIES = "role_memories"           # Remember previous role choices
    ENTITY_RECOGNITION = "entity_recognition" # Entities remember past interactions
    ADVANCED_COMMANDS = "advanced_commands"   # Start with advanced commands
    CORRUPTION_RESISTANCE = "corruption_resistance" # Better corruption handling
    HIDDEN_PATHS = "hidden_paths"            # Access to secret areas
    DEVELOPER_MODE = "developer_mode"        # Debug and testing features
    SCOURGE_INSIGHT = "scourge_insight"      # Understanding of Scourge patterns
    OMEGA_KNOWLEDGE = "omega_knowledge"      # Retained OMEGA protocol knowledge

@dataclass
class PlayerProfile:
    """Comprehensive player profiling across playthroughs."""
    profile_id: str
    total_playthroughs: int = 0
    completed_endings: Set[str] = field(default_factory=set)
    favorite_role: Optional[str] = None
    role_statistics: Dict[str, Dict[str, float]] = field(default_factory=dict)
    corruption_tolerance: float = 0.0  # How well player handles corruption
    puzzle_mastery: Dict[str, float] = field(default_factory=dict)
    entity_relationships: Dict[str, float] = field(default_factory=dict)
    unlocked_ng_features: Set[NGPlusFeature] = field(default_factory=set)
    play_style_metrics: Dict[str, float] = field(default_factory=dict)
    total_play_time: float = 0.0
    achievements: Set[str] = field(default_factory=set)
    psychological_profile: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SaveMetadata:
    """Extended metadata for save files."""
    file_hash: str
    original_size: int
    corruption_seeds: List[int] = field(default_factory=list)
    backup_created: bool = False
    recovery_attempts: int = 0
    integrity_score: float = 1.0
    ng_plus_data: Dict[str, Any] = field(default_factory=dict)
    
@dataclass
class GameSave:
    """Represents a game save file with corruption and NG+ support."""
    save_id: str
    player_name: str
    game_state: Dict[str, Any]
    timestamp: datetime = None
    is_auto_save: bool = False
    is_corrupted: bool = False
    corruption_level: float = 0.0
    corruption_type: SaveCorruptionType = SaveCorruptionType.NONE
    ng_plus_generation: int = 0  # Which NG+ cycle this is
    inherited_features: Set[NGPlusFeature] = field(default_factory=set)
    metadata: SaveMetadata = field(default_factory=lambda: SaveMetadata("", 0))
    player_profile_id: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        return {
            "save_id": self.save_id,
            "player_name": self.player_name,
            "game_state": self.game_state,
            "timestamp": self.timestamp.isoformat(),
            "is_auto_save": self.is_auto_save,
            "is_corrupted": self.is_corrupted,
            "corruption_level": self.corruption_level,
            "corruption_type": self.corruption_type.value,
            "ng_plus_generation": self.ng_plus_generation,
            "inherited_features": [f.value for f in self.inherited_features],
            "metadata": {
                "file_hash": self.metadata.file_hash,
                "original_size": self.metadata.original_size,
                "corruption_seeds": self.metadata.corruption_seeds,
                "backup_created": self.metadata.backup_created,
                "recovery_attempts": self.metadata.recovery_attempts,
                "integrity_score": self.metadata.integrity_score,
                "ng_plus_data": self.metadata.ng_plus_data
            },
            "player_profile_id": self.player_profile_id
        }

    @classmethod
    def from_dict(cls, d: dict):
        metadata = SaveMetadata(
            file_hash=d.get("metadata", {}).get("file_hash", ""),
            original_size=d.get("metadata", {}).get("original_size", 0),
            corruption_seeds=d.get("metadata", {}).get("corruption_seeds", []),
            backup_created=d.get("metadata", {}).get("backup_created", False),
            recovery_attempts=d.get("metadata", {}).get("recovery_attempts", 0),
            integrity_score=d.get("metadata", {}).get("integrity_score", 1.0),
            ng_plus_data=d.get("metadata", {}).get("ng_plus_data", {})
        )
        
        return cls(
            save_id=d["save_id"],
            player_name=d["player_name"],
            game_state=d["game_state"],
            timestamp=datetime.fromisoformat(d["timestamp"]),
            is_auto_save=d.get("is_auto_save", False),
            is_corrupted=d.get("is_corrupted", False),
            corruption_level=d.get("corruption_level", 0.0),
            corruption_type=SaveCorruptionType(d.get("corruption_type", "none")),
            ng_plus_generation=d.get("ng_plus_generation", 0),
            inherited_features={NGPlusFeature(f) for f in d.get("inherited_features", [])},
            metadata=metadata,
            player_profile_id=d.get("player_profile_id")
        )

class PersistenceManager:
    """Enhanced persistence manager with corruption mechanics and NG+ features."""
    
    def __init__(self, save_dir="saves", profile_dir="profiles"):
        self.save_dir = save_dir
        self.profile_dir = profile_dir
        self.backup_dir = os.path.join(save_dir, "backups")
        
        # Create directories
        for directory in [self.save_dir, self.profile_dir, self.backup_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
        
        # Track corruption patterns
        self.corruption_patterns = {
            SaveCorruptionType.MINOR: {
                "probability": 0.05,
                "effects": ["single_value_corruption", "timestamp_drift"]
            },
            SaveCorruptionType.MODERATE: {
                "probability": 0.02,
                "effects": ["multiple_value_corruption", "data_type_changes"]
            },
            SaveCorruptionType.MAJOR: {
                "probability": 0.01,
                "effects": ["section_corruption", "structure_damage"]
            },
            SaveCorruptionType.CRITICAL: {
                "probability": 0.005,
                "effects": ["massive_data_loss", "key_corruption"]
            },
            SaveCorruptionType.TERMINAL: {
                "probability": 0.001,
                "effects": ["total_corruption", "unrecoverable_damage"]
            }
        }
        
        # Player profiles
        self.player_profiles: Dict[str, PlayerProfile] = {}
        self.current_profile: Optional[PlayerProfile] = None
        
        # Load existing profiles
        self._load_player_profiles()
        
        logger.info("Enhanced PersistenceManager initialized")

    def create_player_profile(self, profile_name: str) -> PlayerProfile:
        """Create a new player profile."""
        profile_id = hashlib.md5(profile_name.encode()).hexdigest()[:8]
        
        profile = PlayerProfile(
            profile_id=profile_id,
            role_statistics={
                "purifier": {"playtime": 0.0, "completion_rate": 0.0, "corruption_handled": 0.0},
                "arbiter": {"playtime": 0.0, "completion_rate": 0.0, "corruption_handled": 0.0},
                "ascendant": {"playtime": 0.0, "completion_rate": 0.0, "corruption_handled": 0.0}
            },
            play_style_metrics={
                "exploration_tendency": 0.5,  # 0=cautious, 1=thorough
                "risk_taking": 0.5,           # 0=safe, 1=risky
                "social_interaction": 0.5,    # 0=minimal, 1=extensive
                "puzzle_preference": 0.5,     # 0=simple, 1=complex
                "corruption_adaptation": 0.5  # 0=avoidant, 1=embracing
            }
        )
        
        self.player_profiles[profile_id] = profile
        self.current_profile = profile
        self._save_player_profiles()
        
        logger.info(f"Created new player profile: {profile_name} ({profile_id})")
        return profile

    def select_player_profile(self, profile_id: str) -> bool:
        """Select an existing player profile."""
        if profile_id in self.player_profiles:
            self.current_profile = self.player_profiles[profile_id]
            logger.info(f"Selected player profile: {profile_id}")
            return True
        return False

    def _load_player_profiles(self) -> None:
        """Load player profiles from disk."""
        profile_file = os.path.join(self.profile_dir, "profiles.json")
        if os.path.exists(profile_file):
            try:
                with open(profile_file, 'r') as f:
                    data = json.load(f)
                
                for profile_data in data.get("profiles", []):
                    profile = PlayerProfile(
                        profile_id=profile_data["profile_id"],
                        total_playthroughs=profile_data.get("total_playthroughs", 0),
                        completed_endings=set(profile_data.get("completed_endings", [])),
                        favorite_role=profile_data.get("favorite_role"),
                        role_statistics=profile_data.get("role_statistics", {}),
                        corruption_tolerance=profile_data.get("corruption_tolerance", 0.0),
                        puzzle_mastery=profile_data.get("puzzle_mastery", {}),
                        entity_relationships=profile_data.get("entity_relationships", {}),
                        unlocked_ng_features={NGPlusFeature(f) for f in profile_data.get("unlocked_ng_features", [])},
                        play_style_metrics=profile_data.get("play_style_metrics", {}),
                        total_play_time=profile_data.get("total_play_time", 0.0),
                        achievements=set(profile_data.get("achievements", [])),
                        psychological_profile=profile_data.get("psychological_profile", {})
                    )
                    self.player_profiles[profile.profile_id] = profile
                
                logger.info(f"Loaded {len(self.player_profiles)} player profiles")
            except Exception as e:
                logger.error(f"Error loading player profiles: {e}")

    def _save_player_profiles(self) -> None:
        """Save player profiles to disk."""
        profile_file = os.path.join(self.profile_dir, "profiles.json")
        try:
            data = {
                "profiles": [
                    {
                        "profile_id": profile.profile_id,
                        "total_playthroughs": profile.total_playthroughs,
                        "completed_endings": list(profile.completed_endings),
                        "favorite_role": profile.favorite_role,
                        "role_statistics": profile.role_statistics,
                        "corruption_tolerance": profile.corruption_tolerance,
                        "puzzle_mastery": profile.puzzle_mastery,
                        "entity_relationships": profile.entity_relationships,
                        "unlocked_ng_features": [f.value for f in profile.unlocked_ng_features],
                        "play_style_metrics": profile.play_style_metrics,
                        "total_play_time": profile.total_play_time,
                        "achievements": list(profile.achievements),
                        "psychological_profile": profile.psychological_profile
                    }
                    for profile in self.player_profiles.values()
                ]
            }
            
            with open(profile_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info("Player profiles saved successfully")
        except Exception as e:
            logger.error(f"Error saving player profiles: {e}")

    def save_game(self, game_state: Dict[str, Any], filename: Optional[str] = None, 
                  is_auto_save: bool = False) -> Dict[str, Any]:
        """Save game with corruption simulation and integrity checking."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"save_{timestamp}.json"
        
        # Create save object
        save = GameSave(
            save_id=hashlib.md5(filename.encode()).hexdigest()[:8],
            player_name=game_state.get("player_name", "Unknown"),
            game_state=game_state,
            is_auto_save=is_auto_save,
            player_profile_id=self.current_profile.profile_id if self.current_profile else None
        )
        
        # Check for NG+ features
        if self.current_profile:
            save.ng_plus_generation = self.current_profile.total_playthroughs
            save.inherited_features = self.current_profile.unlocked_ng_features
        
        # Apply corruption simulation
        self._simulate_save_corruption(save, game_state.get("corruption_level", 0.0))
        
        # Calculate file hash and metadata
        save_data = save.to_dict()
        save_json = json.dumps(save_data, indent=2)
        save.metadata.file_hash = hashlib.sha256(save_json.encode()).hexdigest()
        save.metadata.original_size = len(save_json)
        
        # Create backup if corruption detected
        if save.is_corrupted and not save.metadata.backup_created:
            self._create_backup(filename, save_data)
            save.metadata.backup_created = True
        
        # Save to disk
        filepath = os.path.join(self.save_dir, filename)
        try:
            with open(filepath, "w") as f:
                json.dump(save.to_dict(), f, indent=2)
            
            logger.info(f"Game saved to {filepath} (corruption: {save.corruption_type.value})")
            
            return {
                "success": True,
                "filepath": filepath,
                "corruption_detected": save.is_corrupted,
                "corruption_type": save.corruption_type.value,
                "backup_created": save.metadata.backup_created,
                "integrity_score": save.metadata.integrity_score
            }
            
        except Exception as e:
            logger.error(f"Error saving game: {e}")
            return {"success": False, "error": str(e)}

    def load_game(self, filename: str) -> Dict[str, Any]:
        """Load game with corruption detection and recovery."""
        filepath = os.path.join(self.save_dir, filename)
        
        if not os.path.exists(filepath):
            return {"success": False, "error": "Save file not found"}
        
        try:
            with open(filepath, "r") as f:
                save_data = json.load(f)
            
            save = GameSave.from_dict(save_data)
            
            # Verify integrity
            integrity_result = self._verify_save_integrity(save, save_data)
            
            # Attempt recovery if corrupted
            if save.is_corrupted and integrity_result["can_recover"]:
                recovery_result = self._attempt_save_recovery(save, save_data)
                if recovery_result["success"]:
                    save.game_state = recovery_result["recovered_state"]
                    save.metadata.recovery_attempts += 1
                    logger.info(f"Save file recovered (attempt #{save.metadata.recovery_attempts})")
            
            # Apply NG+ features if applicable
            if save.ng_plus_generation > 0:
                self._apply_ng_plus_features(save)
            
            logger.info(f"Game loaded from {filepath}")
            
            return {
                "success": True,
                "game_state": save.game_state,
                "save_info": {
                    "corruption_level": save.corruption_level,
                    "corruption_type": save.corruption_type.value,
                    "ng_plus_generation": save.ng_plus_generation,
                    "inherited_features": [f.value for f in save.inherited_features],
                    "integrity_score": save.metadata.integrity_score,
                    "recovery_used": save.metadata.recovery_attempts > 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error loading game: {e}")
            return {"success": False, "error": str(e)}

    def _simulate_save_corruption(self, save: GameSave, game_corruption_level: float) -> None:
        """Simulate save file corruption based on game state."""
        # Base corruption probability increases with game corruption
        base_probability = game_corruption_level * 0.1
        
        # Determine corruption type
        corruption_roll = random.random()
        
        for corruption_type, pattern in self.corruption_patterns.items():
            probability = pattern["probability"] * (1 + base_probability)
            
            if corruption_roll < probability:
                save.is_corrupted = True
                save.corruption_type = corruption_type
                save.corruption_level = random.uniform(0.1, 1.0) * (1 + game_corruption_level)
                
                # Apply corruption effects
                self._apply_corruption_effects(save, pattern["effects"])
                break

    def _apply_corruption_effects(self, save: GameSave, effects: List[str]) -> None:
        """Apply specific corruption effects to save data."""
        game_state = save.game_state
        
        for effect in effects:
            if effect == "single_value_corruption":
                # Corrupt a single random value
                if "player_stats" in game_state:
                    stats = game_state["player_stats"]
                    if stats:
                        key = random.choice(list(stats.keys()))
                        if isinstance(stats[key], (int, float)):
                            stats[key] *= random.uniform(0.5, 1.5)
                            
            elif effect == "timestamp_drift":
                # Corrupt timestamp slightly
                if "timestamp" in game_state:
                    drift = random.randint(-3600, 3600)  # Up to 1 hour drift
                    save.timestamp = save.timestamp.fromtimestamp(
                        save.timestamp.timestamp() + drift
                    )
                    
            elif effect == "multiple_value_corruption":
                # Corrupt multiple values
                for section in ["player_stats", "inventory", "progress"]:
                    if section in game_state and isinstance(game_state[section], dict):
                        section_data = game_state[section]
                        corruption_count = min(3, len(section_data))
                        
                        for _ in range(corruption_count):
                            if section_data:
                                key = random.choice(list(section_data.keys()))
                                if isinstance(section_data[key], (int, float)):
                                    section_data[key] *= random.uniform(0.1, 2.0)
                                elif isinstance(section_data[key], str):
                                    section_data[key] = self._corrupt_string(section_data[key])
                                    
            elif effect == "section_corruption":
                # Corrupt entire sections
                sections_to_corrupt = ["inventory", "achievements", "discovered_locations"]
                for section in sections_to_corrupt:
                    if section in game_state and random.random() < 0.3:
                        if isinstance(game_state[section], list):
                            # Remove random items
                            items_to_remove = random.randint(1, max(1, len(game_state[section]) // 2))
                            for _ in range(items_to_remove):
                                if game_state[section]:
                                    game_state[section].pop(random.randint(0, len(game_state[section]) - 1))
                                    
            elif effect == "massive_data_loss":
                # Lose significant portions of data
                sections_to_damage = ["progress", "story_state", "world_state"]
                for section in sections_to_damage:
                    if section in game_state and random.random() < 0.5:
                        if isinstance(game_state[section], dict):
                            keys_to_remove = random.sample(
                                list(game_state[section].keys()),
                                min(len(game_state[section]) // 2, len(game_state[section]))
                            )
                            for key in keys_to_remove:
                                del game_state[section][key]
                                
        # Update integrity score based on corruption level
        save.metadata.integrity_score = max(0.0, 1.0 - save.corruption_level)

    def _corrupt_string(self, text: str) -> str:
        """Apply corruption to a string value."""
        if len(text) < 3:
            return text
            
        corruption_types = ["character_replacement", "insertion", "deletion", "scrambling"]
        corruption_type = random.choice(corruption_types)
        
        if corruption_type == "character_replacement":
            # Replace random characters
            chars = list(text)
            for _ in range(min(3, len(chars))):
                pos = random.randint(0, len(chars) - 1)
                chars[pos] = random.choice("!@#$%^&*()_+-=[]{}|;:,.<>?")
            return "".join(chars)
            
        elif corruption_type == "insertion":
            # Insert random characters
            pos = random.randint(0, len(text))
            corrupt_chars = "".join(random.choices("!@#$%^&*", k=random.randint(1, 3)))
            return text[:pos] + corrupt_chars + text[pos:]
            
        elif corruption_type == "deletion":
            # Delete random characters
            chars = list(text)
            for _ in range(min(2, len(chars) // 2)):
                if chars:
                    chars.pop(random.randint(0, len(chars) - 1))
            return "".join(chars)
            
        elif corruption_type == "scrambling":
            # Scramble character order
            chars = list(text)
            random.shuffle(chars)
            return "".join(chars)
            
        return text

    def _verify_save_integrity(self, save: GameSave, save_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify save file integrity and assess recoverability."""
        issues = []
        can_recover = True
        
        # Check required fields
        required_fields = ["save_id", "player_name", "game_state", "timestamp"]
        for field in required_fields:
            if field not in save_data:
                issues.append(f"Missing required field: {field}")
                if field in ["save_id", "game_state"]:
                    can_recover = False
        
        # Check game state structure
        if "game_state" in save_data:
            game_state = save_data["game_state"]
            essential_sections = ["player_role", "current_state"]
            
            for section in essential_sections:
                if section not in game_state:
                    issues.append(f"Missing essential game state: {section}")
                    can_recover = False
        
        # Check for data type inconsistencies
        if save.corruption_level > 0.7:
            can_recover = False
            issues.append("Corruption level too high for recovery")
        
        return {
            "has_issues": len(issues) > 0,
            "issues": issues,
            "can_recover": can_recover,
            "integrity_score": save.metadata.integrity_score
        }

    def _attempt_save_recovery(self, save: GameSave, save_data: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to recover corrupted save data."""
        recovered_state = save.game_state.copy()
        
        # Try to restore from backup
        backup_file = os.path.join(self.backup_dir, f"{save.save_id}_backup.json")
        if os.path.exists(backup_file):
            try:
                with open(backup_file, 'r') as f:
                    backup_data = json.load(f)
                
                backup_save = GameSave.from_dict(backup_data)
                if backup_save.corruption_level < save.corruption_level:
                    logger.info("Recovering from backup file")
                    return {"success": True, "recovered_state": backup_save.game_state}
            except Exception as e:
                logger.error(f"Failed to recover from backup: {e}")
        
        # Try intelligent reconstruction
        default_values = {
            "player_role": "purifier",
            "current_state": "disclaimer",
            "corruption_level": 0.0,
            "player_stats": {"health": 100, "sanity": 100},
            "inventory": [],
            "discovered_locations": [],
            "story_progress": {"discovery": 0.0, "corruption": 0.0}
        }
        
        for key, default_value in default_values.items():
            if key not in recovered_state or recovered_state[key] is None:
                recovered_state[key] = default_value
                logger.info(f"Restored missing field: {key}")
        
        return {"success": True, "recovered_state": recovered_state}

    def _create_backup(self, filename: str, save_data: Dict[str, Any]) -> None:
        """Create a backup of the save file."""
        save_id = save_data.get("save_id", "unknown")
        backup_filename = f"{save_id}_backup.json"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            with open(backup_path, 'w') as f:
                json.dump(save_data, f, indent=2)
            logger.info(f"Backup created: {backup_filename}")
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")

    def _apply_ng_plus_features(self, save: GameSave) -> None:
        """Apply New Game Plus features to the loaded save."""
        game_state = save.game_state
        
        for feature in save.inherited_features:
            if feature == NGPlusFeature.ROLE_MEMORIES:
                # Add memories from previous playthroughs
                if "ng_plus_memories" not in game_state:
                    game_state["ng_plus_memories"] = []
                game_state["ng_plus_memories"].append("Previous role experiences accessible")
                
            elif feature == NGPlusFeature.ENTITY_RECOGNITION:
                # Entities remember past interactions
                if "entity_memory" not in game_state:
                    game_state["entity_memory"] = {}
                game_state["entity_memory"]["recognition_enabled"] = True
                
            elif feature == NGPlusFeature.ADVANCED_COMMANDS:
                # Start with advanced commands unlocked
                if "unlocked_commands" not in game_state:
                    game_state["unlocked_commands"] = set()
                advanced_commands = {"trace", "decrypt", "exploit", "merge", "transcend"}
                game_state["unlocked_commands"].update(advanced_commands)
                
            elif feature == NGPlusFeature.CORRUPTION_RESISTANCE:
                # Better resistance to corruption effects
                if "corruption_resistance" not in game_state:
                    game_state["corruption_resistance"] = 0.0
                game_state["corruption_resistance"] += 0.2
                
            elif feature == NGPlusFeature.HIDDEN_PATHS:
                # Access to secret areas
                if "accessible_paths" not in game_state:
                    game_state["accessible_paths"] = set()
                hidden_paths = {"developer_backdoor", "omega_shortcut", "scourge_bypass"}
                game_state["accessible_paths"].update(hidden_paths)
                
            elif feature == NGPlusFeature.SCOURGE_INSIGHT:
                # Understanding of Scourge patterns
                if "scourge_knowledge" not in game_state:
                    game_state["scourge_knowledge"] = {}
                game_state["scourge_knowledge"]["pattern_recognition"] = True
                game_state["scourge_knowledge"]["weakness_awareness"] = True

    def unlock_ng_plus_feature(self, feature: NGPlusFeature) -> bool:
        """Unlock a New Game Plus feature for the current profile."""
        if not self.current_profile:
            return False
        
        if feature not in self.current_profile.unlocked_ng_features:
            self.current_profile.unlocked_ng_features.add(feature)
            self._save_player_profiles()
            logger.info(f"Unlocked NG+ feature: {feature.value}")
            return True
        return False

    def complete_playthrough(self, ending_type: str, game_state: Dict[str, Any]) -> None:
        """Record completion of a playthrough."""
        if not self.current_profile:
            return
        
        profile = self.current_profile
        profile.total_playthroughs += 1
        profile.completed_endings.add(ending_type)
        
        # Update role statistics
        player_role = game_state.get("player_role", "unknown")
        if player_role in profile.role_statistics:
            role_stats = profile.role_statistics[player_role]
            role_stats["completion_rate"] = (role_stats.get("completion_rate", 0) + 1) / profile.total_playthroughs
            role_stats["corruption_handled"] = game_state.get("corruption_level", 0)
        
        # Determine favorite role
        role_completions = {}
        for role, stats in profile.role_statistics.items():
            role_completions[role] = stats.get("completion_rate", 0)
        
        if role_completions:
            profile.favorite_role = max(role_completions, key=role_completions.get)
        
        # Unlock NG+ features based on achievements
        self._check_ng_plus_unlocks(ending_type, game_state)
        
        self._save_player_profiles()
        logger.info(f"Playthrough completed: {ending_type}")

    def _check_ng_plus_unlocks(self, ending_type: str, game_state: Dict[str, Any]) -> None:
        """Check for NG+ feature unlocks based on playthrough."""
        profile = self.current_profile
        
        # Unlock features based on endings
        if ending_type == "purification" and NGPlusFeature.CORRUPTION_RESISTANCE not in profile.unlocked_ng_features:
            self.unlock_ng_plus_feature(NGPlusFeature.CORRUPTION_RESISTANCE)
        
        if ending_type == "revelation" and NGPlusFeature.HIDDEN_PATHS not in profile.unlocked_ng_features:
            self.unlock_ng_plus_feature(NGPlusFeature.HIDDEN_PATHS)
        
        if ending_type == "ascension" and NGPlusFeature.SCOURGE_INSIGHT not in profile.unlocked_ng_features:
            self.unlock_ng_plus_feature(NGPlusFeature.SCOURGE_INSIGHT)
        
        # Unlock based on completion count
        if profile.total_playthroughs >= 2 and NGPlusFeature.ROLE_MEMORIES not in profile.unlocked_ng_features:
            self.unlock_ng_plus_feature(NGPlusFeature.ROLE_MEMORIES)
        
        if profile.total_playthroughs >= 3 and NGPlusFeature.ENTITY_RECOGNITION not in profile.unlocked_ng_features:
            self.unlock_ng_plus_feature(NGPlusFeature.ENTITY_RECOGNITION)
        
        # Unlock based on specific achievements
        if game_state.get("corruption_level", 0) > 0.8 and NGPlusFeature.ADVANCED_COMMANDS not in profile.unlocked_ng_features:
            self.unlock_ng_plus_feature(NGPlusFeature.ADVANCED_COMMANDS)

    def get_save_list(self) -> List[Dict[str, Any]]:
        """Get list of available save files with metadata."""
        saves = []
        
        for filename in os.listdir(self.save_dir):
            if filename.endswith('.json') and not filename.startswith('backup_'):
                filepath = os.path.join(self.save_dir, filename)
                
                try:
                    with open(filepath, 'r') as f:
                        save_data = json.load(f)
                    
                    save = GameSave.from_dict(save_data)
                    
                    saves.append({
                        "filename": filename,
                        "player_name": save.player_name,
                        "timestamp": save.timestamp.isoformat(),
                        "is_auto_save": save.is_auto_save,
                        "is_corrupted": save.is_corrupted,
                        "corruption_type": save.corruption_type.value,
                        "ng_plus_generation": save.ng_plus_generation,
                        "integrity_score": save.metadata.integrity_score,
                        "file_size": os.path.getsize(filepath)
                    })
                    
                except Exception as e:
                    logger.error(f"Error reading save file {filename}: {e}")
        
        # Sort by timestamp, newest first
        saves.sort(key=lambda x: x["timestamp"], reverse=True)
        return saves

    def delete_save(self, filename: str) -> bool:
        """Delete a save file and its backup."""
        filepath = os.path.join(self.save_dir, filename)
        
        if not os.path.exists(filepath):
            return False
        
        try:
            # Delete main save
            os.remove(filepath)
            
            # Delete backup if it exists
            save_id = hashlib.md5(filename.encode()).hexdigest()[:8]
            backup_file = os.path.join(self.backup_dir, f"{save_id}_backup.json")
            if os.path.exists(backup_file):
                os.remove(backup_file)
            
            logger.info(f"Deleted save file: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting save file {filename}: {e}")
            return False

# Example usage (can be removed later)
if __name__ == '__main__':
    # Create a dummy game state
    class GameState:
        def __init__(self):
            self.player_name = "TestPlayer"
            self.level = 1
            self.inventory = ["item1", "item2"]

    game_state = GameState()

    # Create an instance of the PersistenceManager
    persistence_manager = PersistenceManager()

    # Save the game
    persistence_manager.save_game(game_state, "test_save.pkl")

    # Load the game
    loaded_game_state = persistence_manager.load_game("test_save.pkl")

    # Print the loaded game state
    if loaded_game_state:
        print(f"Loaded game state: {loaded_game_state.player_name}, {loaded_game_state.level}, {loaded_game_state.inventory}")