"""Tests for src/audio/manager.py"""

import pytest
import pygame
import numpy as np
from unittest.mock import Mock, patch, MagicMock, mock_open
import json
import os
from src.audio.manager import SoundEffect, AudioManager


class TestSoundEffect:
    """Test cases for SoundEffect class."""

    def test_sound_effect_initialization_default(self):
        """Test SoundEffect initialization with default values."""
        effect = SoundEffect("test_sound")
        assert effect.name == "test_sound"
        assert effect.file_path == ""
        assert effect.volume == 1.0
        assert effect.pitch == 1.0
        assert effect.loop is False
        assert effect.category == "system"

    def test_sound_effect_initialization_custom(self):
        """Test SoundEffect initialization with custom values."""
        effect = SoundEffect(
            name="custom_sound",
            file_path="/path/to/sound.wav",
            volume=0.5,
            pitch=1.2,
            loop=True,
            category="horror"
        )
        assert effect.name == "custom_sound"
        assert effect.file_path == "/path/to/sound.wav"
        assert effect.volume == 0.5
        assert effect.pitch == 1.2
        assert effect.loop is True
        assert effect.category == "horror"

    def test_sound_effect_type_conversion(self):
        """Test SoundEffect handles type conversion properly."""
        effect = SoundEffect(
            name=123,  # Should convert to string
            file_path=None,  # Should convert to empty string
            volume="0.8",  # Should convert to float
            pitch=None,  # Should default to 1.0
            loop=1,  # Should convert to bool
            category=None  # Should default to "system"
        )
        assert effect.name == "123"
        assert effect.file_path == ""
        assert effect.volume == 0.8
        assert effect.pitch == 1.0
        assert effect.loop is True
        assert effect.category == "system"

    def test_sound_effect_to_dict(self):
        """Test SoundEffect to_dict method."""
        effect = SoundEffect(
            name="test",
            file_path="/test.wav",
            volume=0.7,
            pitch=1.1,
            loop=True,
            category="ambient"
        )
        expected = {
            "name": "test",
            "path": "/test.wav",  # Note: actual implementation uses "path" not "file_path"
            "volume": 0.7,
            "pitch": 1.1,
            "loop": True,
            "category": "ambient"
        }
        assert effect.to_dict() == expected

    def test_sound_effect_from_dict(self):
        """Test SoundEffect from_dict class method."""
        data = {
            "name": "from_dict_test",
            "path": "/dict.wav",  # Note: actual implementation uses "path" not "file_path"
            "volume": 0.6,
            "pitch": 0.9,
            "loop": False,
            "category": "ui"
        }
        effect = SoundEffect.from_dict(data)
        assert effect.name == "from_dict_test"
        assert effect.file_path == "/dict.wav"
        assert effect.volume == 0.6
        assert effect.pitch == 0.9
        assert effect.loop is False
        assert effect.category == "ui"

    def test_sound_effect_from_dict_missing_keys(self):
        """Test SoundEffect from_dict with missing keys uses defaults."""
        data = {"name": "minimal"}
        effect = SoundEffect.from_dict(data)
        assert effect.name == "minimal"
        assert effect.file_path == ""
        assert effect.volume == 1.0
        assert effect.pitch == 1.0
        assert effect.loop is False
        assert effect.category == "system"


class TestAudioManager:
    """Test cases for AudioManager class."""

    @pytest.fixture
    def mock_pygame(self):
        """Mock pygame for testing."""
        with patch('src.audio.manager.pygame') as mock_pg:
            mock_pg.mixer.get_init.return_value = (44100, -16, 2)
            mock_pg.mixer.init.return_value = None
            mock_pg.mixer.quit.return_value = None
            mock_pg.mixer.Sound.return_value = MagicMock()
            mock_pg.mixer.set_num_channels.return_value = None
            mock_pg.error = pygame.error  # Use real pygame.error
            yield mock_pg

    @pytest.fixture
    def audio_manager(self, mock_pygame):
        """Create AudioManager instance for testing."""
        return AudioManager()

    def test_audio_manager_initialization(self, mock_pygame):
        """Test AudioManager initialization."""
        manager = AudioManager()
        assert manager.master_volume == 1.0
        assert manager.effects_volume == 1.0
        assert manager.music_volume == 1.0
        assert manager.voice_volume == 1.0
        assert isinstance(manager.sounds, dict)  # Changed from sound_effects to sounds
        assert isinstance(manager.active_sounds, dict)  # Changed from active_channels

    def test_audio_manager_pygame_not_available(self):
        """Test AudioManager when pygame is not available."""
        with patch('src.audio.manager.pygame') as mock_pg:
            mock_pg.mixer.init.side_effect = pygame.error("Mixer not available")
            mock_pg.error = pygame.error
            
            with pytest.raises(pygame.error):
                AudioManager()

    def test_load_sound(self, audio_manager):
        """Test loading a sound effect."""
        sound = audio_manager.load_sound("test_sound", "/test.wav")
        assert sound.name == "test_sound"
        assert sound.file_path == "/test.wav"
        assert "test_sound" in audio_manager.sounds

    def test_load_music(self, audio_manager):
        """Test loading a music track."""
        track = audio_manager.load_music("test_music", "/music.mp3")
        assert track.name == "test_music"
        assert track.file_path == "/music.mp3"
        assert "test_music" in audio_manager.music_tracks

    def test_play_sound_success(self, audio_manager, mock_pygame):
        """Test successful sound playing."""
        # Add a test sound effect
        audio_manager.load_sound("test", "/test.wav")
        
        with patch('os.path.exists', return_value=True):
            mock_sound = MagicMock()
            mock_pygame.mixer.Sound.return_value = mock_sound
            mock_sound.play.return_value = MagicMock()
            
            audio_manager.play_sound("test", "system")
            mock_sound.set_volume.assert_called()
            mock_sound.play.assert_called()

    def test_play_sound_not_found(self, audio_manager):
        """Test playing non-existent sound."""
        with patch('src.audio.manager.logger') as mock_logger:
            audio_manager.play_sound("nonexistent", "system")
            mock_logger.warning.assert_called_with("Sound not found: nonexistent")

    def test_stop_sound(self, audio_manager):
        """Test stopping a sound."""
        mock_channel = MagicMock()
        audio_manager.active_sounds["test"] = {"channel": mock_channel}
        
        audio_manager.stop_sound("test")
        mock_channel.stop.assert_called_once()

    def test_stop_all_sounds(self, audio_manager, mock_pygame):
        """Test stopping all sounds."""
        mock_channel1 = MagicMock()
        mock_channel2 = MagicMock()
        audio_manager.active_sounds = {
            "sound1": {"channel": mock_channel1}, 
            "sound2": {"channel": mock_channel2}
        }
        
        audio_manager.stop_all_sounds()
        mock_channel1.stop.assert_called_once()
        mock_channel2.stop.assert_called_once()
        mock_pygame.mixer.stop.assert_called_once()

    def test_set_master_volume(self, audio_manager):
        """Test setting master volume."""
        audio_manager.set_master_volume(0.5)
        assert audio_manager.master_volume == 0.5

    def test_set_master_volume_clamp(self, audio_manager):
        """Test master volume is clamped to valid range."""
        audio_manager.set_master_volume(-0.5)
        assert audio_manager.master_volume == 0.0
        
        audio_manager.set_master_volume(1.5)
        assert audio_manager.master_volume == 1.0

    def test_set_effects_volume(self, audio_manager):
        """Test setting effects volume."""
        audio_manager.set_effects_volume(0.3)
        assert audio_manager.effects_volume == 0.3

    def test_play_corruption_sound(self, audio_manager):
        """Test playing corruption sound effect."""
        result = audio_manager.play_corruption_sound(intensity=0.5)
        # Should return None as method executes procedural sound generation
        assert result is None

    def test_cleanup(self, audio_manager, mock_pygame):
        """Test audio manager cleanup."""
        audio_manager.cleanup()
        mock_pygame.mixer.quit.assert_called_once()

    def test_procedural_sound_generation(self, audio_manager):
        """Test procedural sound generation methods."""
        # Test that procedural methods exist and can be called
        audio_manager.play_corruption_sound(0.5)
        audio_manager.play_glitch_sound(0.7)
        audio_manager.play_horror_sound(0.3)

    def test_volume_controls(self, audio_manager):
        """Test various volume control methods."""
        audio_manager.set_master_volume(0.8)
        audio_manager.set_effects_volume(0.6)
        audio_manager.set_music_volume(0.4)
        audio_manager.set_voice_volume(0.9)
        
        assert audio_manager.master_volume == 0.8
        assert audio_manager.effects_volume == 0.6
        assert audio_manager.music_volume == 0.4
        assert audio_manager.voice_volume == 0.9

    def test_category_management(self, audio_manager):
        """Test sound category management."""
        # Test that categories are properly initialized
        assert "corruption" in audio_manager.categories
        assert "horror" in audio_manager.categories
        assert "ambient" in audio_manager.categories
        assert "system" in audio_manager.categories


def mock_open_json(data):
    """Helper function to mock file opening with JSON data."""
    return mock_open(read_data=json.dumps(data))
