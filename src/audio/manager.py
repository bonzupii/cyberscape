"""Audio manager for Cyberscape: Digital Dread.

This module manages all audio effects and music in the game, including:
- Corruption sounds
- Horror effects
- Ambient music
- Character voices
- System sounds
"""

import pygame
import numpy as np
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass

# Stub for GameStateManager to resolve diagnostics
class GameStateManager:
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SoundEffect:
    """Represents a sound effect with its properties."""

    def __init__(
        self,
        name: str,
        file_path: str = "",
        volume: float = 1.0,
        pitch: float = 1.0,
        loop: bool = False,
        category: str = "system"
    ) -> None:
        # Type checks to ensure correct types
        self.name: str = str(name) if name is not None else ""
        self.file_path: str = str(file_path) if file_path is not None else ""
        self.volume: float = float(volume) if volume is not None else 1.0
        self.pitch: float = float(pitch) if pitch is not None else 1.0
        self.loop: bool = bool(loop)
        self.category: str = str(category) if category is not None else "system"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.file_path,
            "volume": self.volume,
            "pitch": self.pitch,
            "loop": self.loop,
            "category": self.category
        }

    @classmethod
    def from_dict(cls, d: dict):
        name = d.get("name") or ""
        file_path = d.get("path") or ""
        return cls(
            name=str(name),
            file_path=str(file_path),
            volume=d.get("volume", 1.0),
            pitch=d.get("pitch", 1.0),
            loop=d.get("loop", False),
            category=d.get("category", "system")
        )

class MusicTrack:
    """Represents a music track with its properties."""

    def __init__(
        self,
        name: str,
        file_path: str = "",
        volume: float = 1.0,
        fade_time: int = 1000,
        loop: bool = True
    ) -> None:
        # Type checks to ensure correct types
        self.name: str = str(name) if name is not None else ""
        self.file_path: str = str(file_path) if file_path is not None else ""
        self.volume: float = float(volume) if volume is not None else 1.0
        self.fade_time: int = int(fade_time) if fade_time is not None else 1000
        self.loop: bool = bool(loop)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.file_path,
            "volume": self.volume,
            "fade_time": self.fade_time,
            "loop": self.loop
        }

    @classmethod
    def from_dict(cls, d: dict):
        name = d.get("name") or ""
        file_path = d.get("path") or ""
        return cls(
            name=str(name),
            file_path=str(file_path),
            volume=d.get("volume", 1.0),
            fade_time=d.get("fade_time", 1000),
            loop=d.get("loop", True)
        )

class AudioManager:
    """Manages all audio playback and effects in the game."""

    # Default volume levels from README
    DEFAULT_VOLUMES = {
        "system": 0.6,
        "corruption": 0.8,
        "horror": 0.7,
        "ambient": 0.5,
        "character": 0.9,
        "effects": 0.4,
        "entity": 0.7,
        "puzzle": 0.6,
        "layer": 0.5,
        "music": 0.7
    }

    def __init__(self, game_state: Optional[GameStateManager] = None):
        self.game_state = game_state

        # For test compatibility
        self.sounds = {}
        self.music_tracks = {}
        self.current_music = None
        self.volume = 1.0
        self.master_volume = 1.0
        self.effects_volume = 1.0
        self.music_volume = 1.0
        self.voice_volume = 1.0
        self.active_sounds = {}
        self.procedural_params = {
            "glitch": {"frequency": 440, "duration": 0.1},
            "corruption": {"frequency": 220, "duration": 0.2},
            "horror": {"frequency": 110, "duration": 0.3}
        }

        # Initialize pygame mixer
        try:
            pygame.mixer.init()
            pygame.mixer.set_num_channels(32)  # Support multiple simultaneous sounds
            logger.info("Pygame mixer initialized successfully")
        except pygame.error as e:
            logger.error(f"Failed to initialize pygame mixer: {e}")
            raise

        # Sound categories
        self.categories = {
            "corruption": [],
            "horror": [],
            "ambient": [],
            "system": [],
            "entity": [],
            "character": [],
            "voice": [],
            "puzzle": [],
            "layer": [],
            "music": []
        }

    def load_sound(self, name: str, file_path: str) -> SoundEffect:
        """Load a sound effect from file."""
        sound: SoundEffect = SoundEffect(name, file_path)
        self.sounds[name] = sound
        return sound

    def load_music(self, name: str, file_path: str) -> MusicTrack:
        """Load a music track from file."""
        track = MusicTrack(name, file_path)
        self.music_tracks[name] = track
        return track

    def play_sound(self, sound_name: str, category: str, volume: Optional[float] = None) -> None:
        """Play a sound effect."""
        if sound_name not in self.sounds:
            logger.warning(f"Sound not found: {sound_name}")
            return

        sound = self.sounds[sound_name]
        # Ensure volume is a float and not None
        if volume is None or not isinstance(volume, (float, int)):
            volume = sound.volume * self.master_volume * self.effects_volume
        else:
            volume = float(volume)

        try:
            pygame_sound = pygame.mixer.Sound(sound.file_path)
            safe_volume = float(volume) if volume is not None else 1.0
            pygame_sound.set_volume(safe_volume)
            channel = pygame_sound.play()
            self.active_sounds[sound_name] = {
                "sound": pygame_sound,
                "channel": channel,
                "category": category
            }
        except Exception as e:
            logger.error(f"Error playing sound {sound_name}: {e}")

    def stop_sound(self, sound_name: str) -> None:
        """Stop a playing sound effect."""
        if sound_name in self.active_sounds:
            sound_data = self.active_sounds[sound_name]
            if sound_data["channel"] is not None:
                sound_data["channel"].stop()
            del self.active_sounds[sound_name]

    def stop_all_sounds(self) -> None:
        """Stop all playing sounds."""
        pygame.mixer.stop()
        self.active_sounds.clear()

    def play_corruption_sound(self, intensity: float) -> None:
        """Play a corruption sound effect based on intensity."""
        if not self.game_state:
            return

        # Select appropriate sound based on intensity
        if intensity < 0.3:
            sound_name = "corruption_minor"
        elif intensity < 0.7:
            sound_name = "corruption_moderate"
        else:
            sound_name = "corruption_severe"

        volume = self.DEFAULT_VOLUMES["corruption"] * intensity
        self.play_sound(sound_name, "corruption", volume)

    def play_horror_sound(self, intensity: float) -> None:
        """Play a horror sound effect based on intensity."""
        if not self.game_state:
            return

        # Select appropriate sound based on intensity
        if intensity < 0.3:
            sound_name = "horror_ambient"
        elif intensity < 0.7:
            sound_name = "horror_creepy"
        else:
            sound_name = "horror_jumpscare"

        volume = self.DEFAULT_VOLUMES["horror"] * intensity
        self.play_sound(sound_name, "horror", volume)

    def play_glitch_sound(self, intensity: float) -> None:
        """Play a glitch sound effect based on intensity."""
        if not self.game_state:
            return

        # Select appropriate sound based on intensity
        if intensity < 0.3:
            sound_name = "glitch_minor"
        elif intensity < 0.7:
            sound_name = "glitch_moderate"
        else:
            sound_name = "glitch_severe"

        volume = self.DEFAULT_VOLUMES["system"] * intensity
        self.play_sound(sound_name, "system", volume)

    def play_sound_effect(self, effect: SoundEffect) -> None:
        """Play a sound effect object."""
        self.play_sound(effect.name, effect.category, effect.volume)

    def play_music_track(self, track: MusicTrack) -> None:
        """Play a music track with fade transition."""
        if track.name in self.music_tracks:
            try:
                pygame.mixer.music.load(track.file_path)
                pygame.mixer.music.set_volume(track.volume * self.master_volume * self.music_volume)
                pygame.mixer.music.play(fade_ms=track.fade_time)
                self.current_music = track.name
            except Exception as e:
                logger.error(f"Error playing music track {track.name}: {e}")

    def set_master_volume(self, volume: float) -> None:
        """Set the master volume level."""
        self.master_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.master_volume * self.music_volume)

    def set_music_volume(self, volume: float) -> None:
        """Set the music volume level."""
        self.music_volume = max(0.0, min(1.0, volume))
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.set_volume(self.master_volume * self.music_volume)

    def set_effects_volume(self, volume: float) -> None:
        """Set the sound effects volume level."""
        self.effects_volume = max(0.0, min(1.0, volume))

    def set_voice_volume(self, volume: float) -> None:
        """Set the voice volume level."""
        self.voice_volume = max(0.0, min(1.0, volume))

    def cleanup(self) -> None:
        """Clean up audio resources."""
        for sound_data in self.active_sounds.values():
            if sound_data["sound"] is not None:
                sound_data["sound"].stop()
        self.stop_all_sounds()
        pygame.mixer.quit()

    def _generate_procedural_sound(self, sound_type: str, intensity: float) -> None:
        """Generate and play a procedural sound effect."""
        try:
            params = self.procedural_params.get(sound_type, {})
            if not params:
                return

            # Generate sound parameters
            frequency = params["frequency"] * (1 + intensity)
            duration = params["duration"] * (1 + intensity)
            sample_rate = 44100
            t = np.linspace(0, duration, int(sample_rate * duration))

            # Generate base waveform
            if sound_type == "glitch":
                wave = np.sin(2 * np.pi * frequency * t)
                # Add glitch effects
                noise = np.random.normal(0, intensity, len(t))
                wave = wave + noise * intensity
            elif sound_type == "corruption":
                wave = np.sin(2 * np.pi * frequency * t)
                # Add corruption effects
                wave = wave * (1 + np.random.normal(0, intensity, len(t)))
            else:  # horror
                wave = np.sin(2 * np.pi * frequency * t)
                # Add horror effects
                wave = wave * np.exp(-t * intensity)

            # Normalize and convert to int16
            wave = wave / np.max(np.abs(wave))
            wave = (wave * 32767).astype(np.int16)

            # Create sound object
            sound = pygame.sndarray.make_sound(wave)
            sound.set_volume(intensity * self.effects_volume * self.master_volume)
            channel = sound.play()

            # Store in active sounds
            sound_name = f"{sound_type}_procedural"
            self.active_sounds[sound_name] = {
                "sound": sound,
                "channel": channel,
                "category": sound_type
            }

        except Exception as e:
            logger.error(f"Error generating procedural sound {sound_type}: {e}")
