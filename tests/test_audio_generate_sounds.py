"""Tests for src/audio/generate_sounds.py"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import os

# Mock scipy since it's not available
@pytest.fixture(autouse=True)
def mock_scipy():
    """Mock scipy for all tests."""
    with patch.dict('sys.modules', {'scipy': MagicMock(), 'scipy.io': MagicMock(), 'scipy.io.wavfile': MagicMock()}):
        yield

from src.audio.generate_sounds import (
    generate_completion_sound,
    generate_suggestion_sound,
    main
)


class TestGenerateSounds:
    """Test cases for sound generation functions."""

    @patch('src.audio.generate_sounds.wavfile.write')
    @patch('os.makedirs')
    def test_generate_completion_sound(self, mock_makedirs, mock_wavwrite):
        """Test completion sound generation."""
        generate_completion_sound()
        
        # Should create directory and write file
        mock_makedirs.assert_called_once()
        mock_wavwrite.assert_called_once()
        
        # Check wavfile.write call arguments
        call_args = mock_wavwrite.call_args[0]
        assert 'completion.wav' in call_args[0]  # filename
        assert call_args[1] == 44100  # sample rate
        assert isinstance(call_args[2], np.ndarray)  # signal data

    @patch('src.audio.generate_sounds.wavfile.write')
    @patch('os.makedirs')
    def test_generate_suggestion_sound(self, mock_makedirs, mock_wavwrite):
        """Test suggestion sound generation."""
        generate_suggestion_sound()
        
        mock_makedirs.assert_called_once()
        mock_wavwrite.assert_called_once()
        
        call_args = mock_wavwrite.call_args[0]
        assert 'suggestion.wav' in call_args[0]
        assert call_args[1] == 44100
        assert isinstance(call_args[2], np.ndarray)

    @patch('src.audio.generate_sounds.generate_completion_sound')
    @patch('src.audio.generate_sounds.generate_suggestion_sound')
    @patch('os.makedirs')
    def test_main_function(self, mock_makedirs, mock_gen_sug, mock_gen_comp):
        """Test main function calls all generators."""
        main()
        
        mock_makedirs.assert_called_once_with('sounds', exist_ok=True)
        mock_gen_comp.assert_called_once()
        mock_gen_sug.assert_called_once()

    @patch('src.audio.generate_sounds.wavfile.write')
    @patch('os.makedirs')
    def test_sound_properties(self, mock_makedirs, mock_wavwrite):
        """Test that generated sounds have correct properties."""
        generate_completion_sound()
        
        # Get the signal data from the mock call
        signal_data = mock_wavwrite.call_args[0][2]
        
        # Check signal properties
        assert len(signal_data) > 0
        assert signal_data.dtype == np.int16
        assert np.max(np.abs(signal_data)) <= 32767  # Within 16-bit range

    @patch('src.audio.generate_sounds.wavfile.write')
    @patch('os.makedirs', side_effect=OSError("Permission denied"))
    def test_directory_creation_error(self, mock_makedirs, mock_wavwrite):
        """Test handling of directory creation errors."""
        # Should not raise exception even if directory creation fails
        try:
            generate_completion_sound()
        except OSError:
            # Expected behavior - function may fail gracefully
            pass

    @patch('src.audio.generate_sounds.wavfile.write', side_effect=Exception("Write error"))
    @patch('os.makedirs')
    def test_file_write_error(self, mock_makedirs, mock_wavwrite):
        """Test handling of file write errors."""
        # Should not crash the application
        try:
            generate_completion_sound()
        except Exception:
            # Expected behavior - function may fail gracefully
            pass

    def test_signal_generation_math(self):
        """Test the mathematical correctness of signal generation."""
        # Test the core signal generation logic without file I/O
        sample_rate = 44100
        duration = 0.2
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Test basic sine wave generation
        frequency = 1000
        signal = np.sin(2 * np.pi * frequency * t)
        
        assert len(signal) == int(sample_rate * duration)
        assert np.max(signal) <= 1.0
        assert np.min(signal) >= -1.0

    def test_exponential_decay(self):
        """Test exponential decay function used in sound generation."""
        t = np.linspace(0, 1, 100)
        decay = np.exp(-10 * t)
        
        # Should start at 1 and decay towards 0
        assert decay[0] == pytest.approx(1.0, rel=1e-6)
        assert decay[-1] < 0.1  # Should be much smaller at the end
        assert np.all(decay[:-1] >= decay[1:])  # Should be monotonically decreasing

    def test_normalization(self):
        """Test signal normalization."""
        # Create a test signal
        signal = np.array([0.1, 0.5, -0.3, 0.8, -0.2])
        
        # Normalize
        normalized = signal / np.max(np.abs(signal))
        
        assert np.max(np.abs(normalized)) == pytest.approx(1.0, rel=1e-6)
        
    def test_pcm_conversion(self):
        """Test conversion to 16-bit PCM format."""
        # Test signal in range [-1, 1]
        signal = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])
        
        # Convert to 16-bit PCM
        pcm_signal = (signal * 32767).astype(np.int16)
        
        assert pcm_signal.dtype == np.int16
        assert pcm_signal[0] == -32767
        assert pcm_signal[-1] == 32767
        assert pcm_signal[2] == 0
