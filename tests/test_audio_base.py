"""Tests for src/audio/base.py"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.audio.base import AudioComponent


class TestAudioComponent:
    """Test cases for AudioComponent class."""

    @pytest.fixture
    def mock_pygame(self):
        """Mock pygame for testing."""
        with patch('src.audio.base.pygame') as mock_pg:
            mock_pg.mixer.set_num_channels.return_value = None
            mock_pg.mixer.Sound.return_value = MagicMock()
            mock_pg.mixer.Channel.return_value = MagicMock()
            yield mock_pg

    def test_audio_component_initialization(self, mock_pygame):
        """Test AudioComponent initialization with default values."""
        component = AudioComponent()
        assert component.max_channels == 8
        assert component.volume == 1.0
        assert isinstance(component.sounds, dict)
        assert isinstance(component.channels, list)
        assert len(component.sounds) == 0
        assert len(component.channels) == 0

    def test_audio_component_custom_channels(self, mock_pygame):
        """Test AudioComponent with custom max_channels."""
        component = AudioComponent(max_channels=16)
        assert component.max_channels == 16
        mock_pygame.mixer.set_num_channels.assert_called_with(16)

    def test_audio_component_post_init(self, mock_pygame):
        """Test __post_init__ method."""
        component = AudioComponent()
        # Should initialize empty containers
        assert component.sounds == {}
        assert component.channels == []

    def test_audio_component_initialize(self, mock_pygame):
        """Test _initialize method."""
        component = AudioComponent(max_channels=12)
        component._initialize()
        mock_pygame.mixer.set_num_channels.assert_called_with(12)

    def test_audio_component_inheritance(self, mock_pygame):
        """Test that AudioComponent inherits from BaseManager."""
        component = AudioComponent()
        # Should have BaseManager methods
        assert hasattr(component, '_initialize')
        assert hasattr(component, 'max_channels')
        assert hasattr(component, 'sounds')
        assert hasattr(component, 'channels')
        assert hasattr(component, 'volume')

    def test_audio_component_field_defaults(self, mock_pygame):
        """Test that field defaults are properly set."""
        component1 = AudioComponent()
        component2 = AudioComponent()
        
        # Each instance should have its own dict/list instances
        assert component1.sounds is not component2.sounds
        assert component1.channels is not component2.channels
        
        # But they should be equal (both empty)
        assert component1.sounds == component2.sounds == {}
        assert component1.channels == component2.channels == []

    def test_audio_component_volume_setting(self, mock_pygame):
        """Test setting custom volume."""
        component = AudioComponent(volume=0.5)
        assert component.volume == 0.5

    @patch('src.audio.base.pygame', None)
    def test_audio_component_no_pygame(self):
        """Test AudioComponent when pygame is not available."""
        # Should still initialize without errors
        component = AudioComponent()
        assert component.max_channels == 8
        assert component.volume == 1.0
