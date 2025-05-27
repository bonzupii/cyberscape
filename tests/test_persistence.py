"""Tests for src/core/persistence.py"""

import pytest
import pickle
import json
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, mock_open
from datetime import datetime
from dataclasses import asdict

from src.core.persistence import GameSave, PersistenceManager


class TestGameSave:
    """Test cases for GameSave class."""

    def test_game_save_initialization_default(self):
        """Test GameSave initialization with default values."""
        game_state = {"level": 1, "score": 100}
        save = GameSave("save001", "Player1", game_state)
        
        assert save.save_id == "save001"
        assert save.player_name == "Player1"
        assert save.game_state == game_state
        assert isinstance(save.timestamp, datetime)
        assert save.is_auto_save is False
        assert save.is_corrupted is False
        assert save.corruption_level == 0.0

    def test_game_save_initialization_custom(self):
        """Test GameSave initialization with custom values."""
        timestamp = datetime(2025, 1, 1, 12, 0, 0)
        game_state = {"level": 5, "corruption": 0.3}
        
        save = GameSave(
            save_id="auto001",
            player_name="TestPlayer",
            game_state=game_state,
            timestamp=timestamp,
            is_auto_save=True,
            is_corrupted=True,
            corruption_level=0.3
        )
        
        assert save.save_id == "auto001"
        assert save.player_name == "TestPlayer"
        assert save.timestamp == timestamp
        assert save.is_auto_save is True
        assert save.is_corrupted is True
        assert save.corruption_level == 0.3

    def test_game_save_to_dict(self):
        """Test GameSave to_dict method."""
        timestamp = datetime(2025, 1, 1, 12, 0, 0)
        game_state = {"test": "data"}
        
        save = GameSave("test", "player", game_state, timestamp)
        result = save.to_dict()
        
        expected = {
            "save_id": "test",
            "player_name": "player",
            "game_state": {"test": "data"},
            "timestamp": "2025-01-01T12:00:00",
            "is_auto_save": False,
            "is_corrupted": False,
            "corruption_level": 0.0
        }
        
        assert result == expected

    def test_game_save_from_dict(self):
        """Test GameSave from_dict class method."""
        data = {
            "save_id": "from_dict",
            "player_name": "DictPlayer",
            "game_state": {"level": 3},
            "timestamp": "2025-01-01T12:00:00",
            "is_auto_save": True,
            "is_corrupted": False,
            "corruption_level": 0.1
        }
        
        save = GameSave.from_dict(data)
        
        assert save.save_id == "from_dict"
        assert save.player_name == "DictPlayer"
        assert save.game_state == {"level": 3}
        assert save.is_auto_save is True
        assert save.corruption_level == 0.1


class TestPersistenceManager:
    """Test cases for PersistenceManager class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def persistence_manager(self, temp_dir):
        """Create PersistenceManager instance for testing."""
        return PersistenceManager(save_directory=temp_dir)

    def test_persistence_manager_initialization(self, temp_dir):
        """Test PersistenceManager initialization."""
        manager = PersistenceManager(save_directory=temp_dir)
        assert manager.save_directory == temp_dir
        assert manager.max_saves == 10
        assert manager.auto_save_interval == 300
        assert isinstance(manager.saves_cache, dict)

    def test_persistence_manager_initialization_default(self):
        """Test PersistenceManager initialization with defaults."""
        with patch('os.makedirs'):
            manager = PersistenceManager()
            assert manager.save_directory.endswith("saves")

    def test_save_game_success(self, persistence_manager, temp_dir):
        """Test successful game save."""
        game_state = {"level": 1, "score": 100}
        save_id = persistence_manager.save_game("TestPlayer", game_state)
        
        assert save_id is not None
        assert save_id in persistence_manager.saves_cache
        
        # Check file was created
        save_path = os.path.join(temp_dir, f"{save_id}.pkl")
        assert os.path.exists(save_path)

    def test_save_game_with_save_id(self, persistence_manager):
        """Test saving game with specific save ID."""
        game_state = {"test": "data"}
        save_id = persistence_manager.save_game("Player", game_state, save_id="custom001")
        
        assert save_id == "custom001"
        assert save_id in persistence_manager.saves_cache

    def test_save_game_auto_save(self, persistence_manager):
        """Test auto save functionality."""
        game_state = {"auto": "save"}
        save_id = persistence_manager.save_game("Player", game_state, is_auto_save=True)
        
        assert save_id.startswith("auto_")
        assert persistence_manager.saves_cache[save_id].is_auto_save is True

    def test_save_game_failure(self, persistence_manager):
        """Test save game failure handling."""
        with patch('builtins.open', side_effect=IOError("Write error")):
            save_id = persistence_manager.save_game("Player", {"test": "data"})
            assert save_id is None

    def test_load_game_success(self, persistence_manager, temp_dir):
        """Test successful game loading."""
        # First save a game
        game_state = {"level": 2, "items": ["sword", "potion"]}
        save_id = persistence_manager.save_game("LoadTest", game_state)
        
        # Then load it
        loaded_save = persistence_manager.load_game(save_id)
        
        assert loaded_save is not None
        assert loaded_save.save_id == save_id
        assert loaded_save.player_name == "LoadTest"
        assert loaded_save.game_state == game_state

    def test_load_game_not_found(self, persistence_manager):
        """Test loading non-existent game."""
        loaded_save = persistence_manager.load_game("nonexistent")
        assert loaded_save is None

    def test_load_game_corrupted_file(self, persistence_manager, temp_dir):
        """Test loading corrupted save file."""
        # Create corrupted file
        corrupted_path = os.path.join(temp_dir, "corrupted.pkl")
        with open(corrupted_path, "wb") as f:
            f.write(b"corrupted data")
        
        loaded_save = persistence_manager.load_game("corrupted")
        assert loaded_save is None

    def test_list_saves(self, persistence_manager):
        """Test listing available saves."""
        # Create some saves
        persistence_manager.save_game("Player1", {"level": 1})
        persistence_manager.save_game("Player2", {"level": 2})
        
        saves = persistence_manager.list_saves()
        assert len(saves) == 2
        assert all(isinstance(save, GameSave) for save in saves)

    def test_list_saves_sorted(self, persistence_manager):
        """Test that saves are listed in chronological order."""
        with patch('src.core.persistence.datetime') as mock_datetime:
            # Mock different timestamps
            mock_datetime.now.side_effect = [
                datetime(2025, 1, 1, 10, 0, 0),
                datetime(2025, 1, 1, 11, 0, 0),
                datetime(2025, 1, 1, 9, 0, 0)
            ]
            
            save_id1 = persistence_manager.save_game("Player1", {"test": 1})
            save_id2 = persistence_manager.save_game("Player2", {"test": 2})
            save_id3 = persistence_manager.save_game("Player3", {"test": 3})
            
            saves = persistence_manager.list_saves()
            # Should be sorted by timestamp (newest first)
            timestamps = [save.timestamp for save in saves]
            assert timestamps == sorted(timestamps, reverse=True)

    def test_delete_save_success(self, persistence_manager, temp_dir):
        """Test successful save deletion."""
        # Create a save
        save_id = persistence_manager.save_game("DeleteTest", {"test": "data"})
        save_path = os.path.join(temp_dir, f"{save_id}.pkl")
        
        assert os.path.exists(save_path)
        assert save_id in persistence_manager.saves_cache
        
        # Delete it
        result = persistence_manager.delete_save(save_id)
        
        assert result is True
        assert not os.path.exists(save_path)
        assert save_id not in persistence_manager.saves_cache

    def test_delete_save_not_found(self, persistence_manager):
        """Test deleting non-existent save."""
        result = persistence_manager.delete_save("nonexistent")
        assert result is False

    def test_delete_save_file_error(self, persistence_manager):
        """Test delete save with file error."""
        save_id = persistence_manager.save_game("ErrorTest", {"test": "data"})
        
        with patch('os.remove', side_effect=OSError("Delete error")):
            result = persistence_manager.delete_save(save_id)
            assert result is False

    def test_create_backup(self, persistence_manager, temp_dir):
        """Test backup creation."""
        # Create some saves
        persistence_manager.save_game("Player1", {"level": 1})
        persistence_manager.save_game("Player2", {"level": 2})
        
        backup_path = persistence_manager.create_backup()
        
        assert backup_path is not None
        assert os.path.exists(backup_path)
        assert backup_path.endswith(".zip")

    def test_create_backup_failure(self, persistence_manager):
        """Test backup creation failure."""
        with patch('zipfile.ZipFile', side_effect=IOError("Zip error")):
            backup_path = persistence_manager.create_backup()
            assert backup_path is None

    def test_restore_backup_success(self, persistence_manager, temp_dir):
        """Test successful backup restoration."""
        # Create backup first
        persistence_manager.save_game("BackupTest", {"test": "data"})
        backup_path = persistence_manager.create_backup()
        
        # Clear saves
        persistence_manager.saves_cache.clear()
        
        # Restore backup
        result = persistence_manager.restore_backup(backup_path)
        
        assert result is True
        assert len(persistence_manager.saves_cache) > 0

    def test_restore_backup_not_found(self, persistence_manager):
        """Test restoring non-existent backup."""
        result = persistence_manager.restore_backup("nonexistent.zip")
        assert result is False

    def test_cleanup_old_saves(self, persistence_manager):
        """Test cleaning up old saves when limit is exceeded."""
        # Set low max_saves for testing
        persistence_manager.max_saves = 3
        
        # Create more saves than the limit
        for i in range(5):
            persistence_manager.save_game(f"Player{i}", {"level": i})
        
        # Should only keep 3 saves
        assert len(persistence_manager.saves_cache) == 3

    def test_auto_save_timing(self, persistence_manager):
        """Test auto save timing functionality."""
        with patch('time.time') as mock_time:
            mock_time.side_effect = [0, 100, 400]  # Simulate time progression
            
            persistence_manager.last_auto_save = 0
            persistence_manager.auto_save_interval = 300
            
            # Should not auto save yet (100 seconds elapsed)
            assert not persistence_manager.should_auto_save()
            
            # Should auto save now (400 seconds elapsed)
            assert persistence_manager.should_auto_save()

    def test_validate_save_file_valid(self, persistence_manager, temp_dir):
        """Test validating valid save file."""
        save_id = persistence_manager.save_game("ValidTest", {"test": "data"})
        is_valid = persistence_manager.validate_save_file(save_id)
        assert is_valid is True

    def test_validate_save_file_invalid(self, persistence_manager, temp_dir):
        """Test validating invalid save file."""
        # Create invalid file
        invalid_path = os.path.join(temp_dir, "invalid.pkl")
        with open(invalid_path, "wb") as f:
            f.write(b"invalid pickle data")
        
        is_valid = persistence_manager.validate_save_file("invalid")
        assert is_valid is False

    def test_get_save_metadata(self, persistence_manager):
        """Test getting save metadata."""
        save_id = persistence_manager.save_game("MetaTest", {"level": 5})
        metadata = persistence_manager.get_save_metadata(save_id)
        
        assert metadata is not None
        assert metadata["save_id"] == save_id
        assert metadata["player_name"] == "MetaTest"
        assert "timestamp" in metadata

    def test_corruption_simulation(self, persistence_manager):
        """Test corruption simulation in saves."""
        # Create save with corruption
        game_state = {"corruption_level": 0.7}
        save_id = persistence_manager.save_game("CorruptTest", game_state)
        
        # Simulate corruption
        save = persistence_manager.saves_cache[save_id]
        save.is_corrupted = True
        save.corruption_level = 0.7
        
        assert save.is_corrupted is True
        assert save.corruption_level == 0.7

    def test_concurrent_save_handling(self, persistence_manager):
        """Test handling concurrent save operations."""
        import threading
        
        results = []
        
        def save_game():
            save_id = persistence_manager.save_game("ConcurrentTest", {"test": "data"})
            results.append(save_id)
        
        # Create multiple threads
        threads = [threading.Thread(target=save_game) for _ in range(3)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # All saves should succeed
        assert all(result is not None for result in results)
        assert len(set(results)) == 3  # All unique save IDs
