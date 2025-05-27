"""Persistence manager for Cyberscape: Digital Dread.

This module manages game state persistence, including:
- Save file creation and loading
- Auto-save functionality
- Save file validation
- Backup management
"""

import pickle
import os
import json
import logging
import shutil
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

@dataclass
class GameSave:
    """Represents a game save file."""
    save_id: str
    player_name: str
    game_state: Dict[str, Any]
    timestamp: datetime = None
    is_auto_save: bool = False
    is_corrupted: bool = False
    corruption_level: float = 0.0

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
            "corruption_level": self.corruption_level
        }

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            save_id=d["save_id"],
            player_name=d["player_name"],
            game_state=d["game_state"],
            timestamp=datetime.fromisoformat(d["timestamp"]),
            is_auto_save=d.get("is_auto_save", False),
            is_corrupted=d.get("is_corrupted", False),
            corruption_level=d.get("corruption_level", 0.0)
        )

class PersistenceManager:
    def __init__(self, save_dir="saves"):
        self.save_dir = save_dir
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    def save_game(self, game_state, filename="autosave.pkl"):
        filepath = os.path.join(self.save_dir, filename)
        try:
            with open(filepath, "wb") as f:
                pickle.dump(game_state, f)
            print(f"Game saved to {filepath}")
            return True
        except Exception as e:
            print(f"Error saving game: {e}")
            return False

    def load_game(self, filename="autosave.pkl"):
        filepath = os.path.join(self.save_dir, filename)
        try:
            with open(filepath, "rb") as f:
                game_state = pickle.load(f)
            print(f"Game loaded from {filepath}")
            return game_state
        except FileNotFoundError:
            print("Save file not found.")
            return None
        except Exception as e:
            print(f"Error loading game: {e}")
            return None

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