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

    def create_binaural_effect(self, base_frequency: float, beat_frequency: float, 
                              duration: float = 10.0, intensity: float = 0.5) -> None:
        """Create binaural beats for psychological horror effects."""
        try:
            sample_rate = 44100
            t = np.linspace(0, duration, int(sample_rate * duration))
            
            # Create left and right channels with frequency difference
            left_freq = base_frequency
            right_freq = base_frequency + beat_frequency
            
            # Generate sine waves
            left_channel = np.sin(2 * np.pi * left_freq * t) * intensity
            right_channel = np.sin(2 * np.pi * right_freq * t) * intensity
            
            # Create stereo array
            stereo_wave = np.column_stack((left_channel, right_channel))
            
            # Normalize and convert to int16
            stereo_wave = stereo_wave / np.max(np.abs(stereo_wave))
            stereo_wave = (stereo_wave * 32767).astype(np.int16)
            
            # Create and play sound
            sound = pygame.sndarray.make_sound(stereo_wave)
            sound.set_volume(intensity * self.effects_volume * self.master_volume)
            channel = sound.play(-1)  # Loop indefinitely
            
            # Store in active sounds
            self.active_sounds["binaural_effect"] = {
                "sound": sound,
                "channel": channel,
                "category": "horror"
            }
            
            logger.info(f"Created binaural effect: {base_frequency}Hz with {beat_frequency}Hz beat")
            
        except Exception as e:
            logger.error(f"Error creating binaural effect: {e}")

    def play_spatial_sound(self, sound_name: str, x: float, y: float, 
                          distance: float = 1.0, category: str = "effects") -> None:
        """Play a sound with spatial positioning (simulated binaural)."""
        if sound_name not in self.sounds:
            logger.warning(f"Spatial sound not found: {sound_name}")
            return
            
        try:
            sound = self.sounds[sound_name]
            
            # Calculate stereo panning based on x position
            # x = -1 (left), x = 0 (center), x = 1 (right)
            pan = max(-1.0, min(1.0, x))
            
            # Calculate volume based on distance
            distance_volume = max(0.1, 1.0 / (1.0 + distance))
            
            # Create left and right volumes
            if pan < 0:  # Sound is to the left
                left_volume = distance_volume
                right_volume = distance_volume * (1.0 + pan)
            else:  # Sound is to the right
                left_volume = distance_volume * (1.0 - pan)
                right_volume = distance_volume
            
            # Apply master volume
            left_volume *= self.master_volume * self.effects_volume
            right_volume *= self.master_volume * self.effects_volume
            
            # Load and play sound with spatial effect
            pygame_sound = pygame.mixer.Sound(sound.file_path)
            
            # Set average volume (pygame doesn't support per-channel volume directly)
            avg_volume = (left_volume + right_volume) / 2
            pygame_sound.set_volume(avg_volume)
            
            channel = pygame_sound.play()
            
            # Store in active sounds
            self.active_sounds[f"{sound_name}_spatial"] = {
                "sound": pygame_sound,
                "channel": channel,
                "category": category,
                "spatial": True,
                "position": (x, y, distance)
            }
            
        except Exception as e:
            logger.error(f"Error playing spatial sound {sound_name}: {e}")

    def apply_horror_audio_filter(self, sound_name: str, corruption_level: float) -> None:
        """Apply horror-specific audio filtering based on corruption level."""
        if sound_name not in self.active_sounds:
            return
            
        try:
            # Adjust volume based on corruption
            sound_data = self.active_sounds[sound_name]
            base_volume = sound_data.get("base_volume", 1.0)
            
            # Higher corruption = more erratic volume
            if corruption_level > 0.7:
                # Highly corrupted: erratic, disturbing volume changes
                volume_modifier = 0.5 + np.random.random() * corruption_level
            elif corruption_level > 0.4:
                # Moderately corrupted: subtle volume fluctuations
                volume_modifier = 0.8 + np.random.random() * 0.4
            else:
                # Low corruption: minimal effects
                volume_modifier = 0.9 + np.random.random() * 0.2
                
            new_volume = base_volume * volume_modifier * self.effects_volume * self.master_volume
            sound_data["sound"].set_volume(min(1.0, new_volume))
            
        except Exception as e:
            logger.error(f"Error applying horror filter to {sound_name}: {e}")

    def trigger_entity_audio_signature(self, entity_name: str, intensity: float = 0.7) -> None:
        """Trigger audio signature for specific entities."""
        entity_sounds = {
            "dr_voss": {"frequency": 440, "modulation": "warped"},
            "aetherial_scourge": {"frequency": 220, "modulation": "chaotic"},
            "sentinel": {"frequency": 880, "modulation": "mechanical"},
            "collective": {"frequency": 330, "modulation": "harmonic"},
            "prodigy": {"frequency": 660, "modulation": "innocent"},
            "lazarus": {"frequency": 110, "modulation": "deep"},
            "echo": {"frequency": 550, "modulation": "reverb"}
        }
        
        if entity_name not in entity_sounds:
            return
            
        try:
            params = entity_sounds[entity_name]
            base_freq = params["frequency"]
            modulation = params["modulation"]
            
            sample_rate = 44100
            duration = 2.0
            t = np.linspace(0, duration, int(sample_rate * duration))
            
            # Generate base tone
            wave = np.sin(2 * np.pi * base_freq * t)
            
            # Apply entity-specific modulation
            if modulation == "warped":
                wave = wave * np.sin(t * 10) * intensity
            elif modulation == "chaotic":
                noise = np.random.normal(0, 0.3, len(t))
                wave = wave + noise * intensity
            elif modulation == "mechanical":
                square_wave = np.sign(np.sin(2 * np.pi * base_freq * t))
                wave = (wave + square_wave * 0.3) * intensity
            elif modulation == "harmonic":
                harmonic = np.sin(2 * np.pi * base_freq * 2 * t) * 0.5
                wave = (wave + harmonic) * intensity
            elif modulation == "innocent":
                wave = wave * np.exp(-t * 0.1) * intensity
            elif modulation == "deep":
                wave = wave * (1 + np.sin(t * 2)) * intensity
            elif modulation == "reverb":
                echo_delay = int(sample_rate * 0.1)
                if len(wave) > echo_delay:
                    wave[echo_delay:] += wave[:-echo_delay] * 0.3
                wave = wave * intensity
            
            # Normalize and convert
            wave = wave / np.max(np.abs(wave))
            wave = (wave * 32767).astype(np.int16)
            
            # Create and play sound
            sound = pygame.sndarray.make_sound(wave)
            sound.set_volume(intensity * self.effects_volume * self.master_volume)
            channel = sound.play()
            
            # Store in active sounds
            self.active_sounds[f"entity_{entity_name}"] = {
                "sound": sound,
                "channel": channel,
                "category": "entity"
            }
            
            logger.info(f"Triggered audio signature for entity: {entity_name}")
            
        except Exception as e:
            logger.error(f"Error triggering entity audio signature for {entity_name}: {e}")

    def create_ambient_horror_loop(self, corruption_level: float) -> None:
        """Create continuous ambient horror audio based on corruption level."""
        try:
            sample_rate = 44100
            duration = 30.0  # 30-second loop
            t = np.linspace(0, duration, int(sample_rate * duration))
            
            # Base ambient frequency
            base_freq = 40 + corruption_level * 60  # 40-100 Hz range
            
            # Create base ambient drone
            wave = np.sin(2 * np.pi * base_freq * t)
            
            # Add corruption-specific effects
            if corruption_level > 0.8:
                # High corruption: chaotic, disturbing
                noise = np.random.normal(0, 0.4, len(t))
                wave = wave + noise
                # Add sudden spikes
                spike_points = np.random.choice(len(t), int(len(t) * 0.05), replace=False)
                wave[spike_points] *= 3
            elif corruption_level > 0.5:
                # Medium corruption: unsettling harmonics
                harmonic = np.sin(2 * np.pi * base_freq * 1.618 * t) * 0.3  # Golden ratio
                wave = wave + harmonic
                # Add subtle noise
                noise = np.random.normal(0, 0.2, len(t))
                wave = wave + noise
            elif corruption_level > 0.2:
                # Low corruption: subtle distortion
                distortion = np.sin(2 * np.pi * base_freq * 0.5 * t) * 0.1
                wave = wave + distortion
            
            # Apply envelope for smooth looping
            fade_samples = int(sample_rate * 1.0)  # 1-second fade
            wave[:fade_samples] *= np.linspace(0, 1, fade_samples)
            wave[-fade_samples:] *= np.linspace(1, 0, fade_samples)
            
            # Normalize and convert
            wave = wave / np.max(np.abs(wave))
            wave = (wave * 16383).astype(np.int16)  # Lower volume for ambient
            
            # Create and play looping sound
            sound = pygame.sndarray.make_sound(wave)
            volume = 0.3 * corruption_level * self.effects_volume * self.master_volume
            sound.set_volume(volume)
            channel = sound.play(-1)  # Loop indefinitely
            
            # Store in active sounds
            self.active_sounds["ambient_horror"] = {
                "sound": sound,
                "channel": channel,
                "category": "ambient",
                "corruption_level": corruption_level
            }
            
            logger.info(f"Created ambient horror loop with corruption level: {corruption_level}")
            
        except Exception as e:
            logger.error(f"Error creating ambient horror loop: {e}")

    def stop_binaural_effects(self) -> None:
        """Stop all binaural and ambient effects."""
        effects_to_stop = ["binaural_effect", "ambient_horror"]
        for effect_name in effects_to_stop:
            if effect_name in self.active_sounds:
                sound_data = self.active_sounds[effect_name]
                if sound_data["channel"]:
                    sound_data["channel"].stop()
                del self.active_sounds[effect_name]

class BinauraAudioProcessor:
    """Handles binaural audio effects and 3D spatial audio."""
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.head_size = 0.17  # Average head diameter in meters
        self.speed_of_sound = 343  # m/s
        self.panning_cache = {}
        
    def create_binaural_beat(self, frequency1: float, frequency2: float, duration: float) -> np.ndarray:
        """Create binaural beats for psychological effects."""
        time_array = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Left ear frequency
        left_wave = np.sin(2 * np.pi * frequency1 * time_array)
        # Right ear frequency (slightly different for binaural effect)
        right_wave = np.sin(2 * np.pi * frequency2 * time_array)
        
        # Combine into stereo
        stereo_array = np.column_stack((left_wave, right_wave))
        return (stereo_array * 0.5).astype(np.float32)
    
    def apply_3d_positioning(self, audio: np.ndarray, x: float, y: float, z: float) -> np.ndarray:
        """Apply 3D spatial positioning to audio."""
        # Calculate distance
        distance = np.sqrt(x**2 + y**2 + z**2)
        if distance == 0:
            return audio
        
        # Calculate time delay for each ear (simplified HRTF)
        angle = np.arctan2(y, x)  # Azimuth angle
        
        # ITD (Interaural Time Difference)
        sin_angle = np.sin(angle)
        delay_samples = int((self.head_size / self.speed_of_sound) * sin_angle * self.sample_rate)
        
        # ILD (Interaural Level Difference) - simplified
        left_gain = 1.0 - max(0, sin_angle) * 0.3
        right_gain = 1.0 + min(0, sin_angle) * 0.3
        
        # Distance attenuation
        distance_factor = 1.0 / (1.0 + distance)
        
        if len(audio.shape) == 1:
            # Mono to stereo conversion with positioning
            left_channel = audio * left_gain * distance_factor
            right_channel = audio * right_gain * distance_factor
            
            # Apply delay
            if delay_samples > 0:
                left_channel = np.concatenate([np.zeros(delay_samples), left_channel])
                right_channel = np.concatenate([right_channel, np.zeros(delay_samples)])
            elif delay_samples < 0:
                right_channel = np.concatenate([np.zeros(-delay_samples), right_channel])
                left_channel = np.concatenate([left_channel, np.zeros(-delay_samples)])
            
            # Ensure both channels are same length
            min_length = min(len(left_channel), len(right_channel))
            return np.column_stack((left_channel[:min_length], right_channel[:min_length]))
        
        return audio
    
    def apply_horror_filter(self, audio: np.ndarray, corruption_level: float) -> np.ndarray:
        """Apply horror-themed audio filters based on corruption level."""
        if corruption_level <= 0:
            return audio
        
        # Low-pass filter for muffled effect
        if corruption_level > 0.3:
            cutoff_freq = 5000 * (1.0 - corruption_level * 0.5)
            # Simple low-pass filter approximation
            filtered = self._simple_lowpass(audio, cutoff_freq)
        else:
            filtered = audio
        
        # Add noise and distortion
        if corruption_level > 0.5:
            noise_level = corruption_level * 0.1
            noise = np.random.normal(0, noise_level, audio.shape)
            filtered = filtered + noise
        
        # Bit crushing effect for digital corruption
        if corruption_level > 0.7:
            bit_depth = max(4, int(16 * (1.0 - corruption_level)))
            scale = 2 ** (bit_depth - 1)
            filtered = np.round(filtered * scale) / scale
        
        return np.clip(filtered, -1.0, 1.0).astype(np.float32)
    
    def _simple_lowpass(self, audio: np.ndarray, cutoff_freq: float) -> np.ndarray:
        """Simple low-pass filter implementation."""
        # This is a simplified approach - a real implementation would use scipy
        alpha = cutoff_freq / (cutoff_freq + self.sample_rate / (2 * np.pi))
        
        if len(audio.shape) == 1:
            filtered = np.zeros_like(audio)
            filtered[0] = audio[0]
            for i in range(1, len(audio)):
                filtered[i] = alpha * audio[i] + (1 - alpha) * filtered[i-1]
        else:
            # Stereo
            filtered = np.zeros_like(audio)
            filtered[0] = audio[0]
            for i in range(1, len(audio)):
                filtered[i] = alpha * audio[i] + (1 - alpha) * filtered[i-1]
        
        return filtered

class CorruptionAudioEffects:
    """Specialized audio effects for corruption system."""
    
    def __init__(self, binaural_processor: BinauraAudioProcessor):
        self.binaural = binaural_processor
        self.whisper_voices = []
        self.phantom_sounds = []
        self.digital_artifacts = []
        
    def create_whisper_effect(self, text: str, corruption_level: float) -> np.ndarray:
        """Create whispering voice effects (simulated)."""
        # This would ideally use TTS, but for now we'll create atmospheric sounds
        duration = len(text) * 0.1  # 100ms per character
        base_freq = 150 + (corruption_level * 50)  # Vary frequency with corruption
        
        time_array = np.linspace(0, duration, int(self.binaural.sample_rate * duration))
        
        # Create whisper-like sound with multiple frequencies
        whisper = np.zeros_like(time_array)
        for i, harmonic in enumerate([1, 1.5, 2.1, 3.2]):
            freq = base_freq * harmonic
            amplitude = 0.3 / (i + 1)  # Decreasing amplitude for harmonics
            whisper += amplitude * np.sin(2 * np.pi * freq * time_array)
        
        # Apply envelope for whisper effect
        envelope = np.exp(-time_array * 2) * np.sin(np.pi * time_array / duration)
        whisper *= envelope
        
        # Add noise for breath effect
        noise = np.random.normal(0, 0.05, len(whisper))
        whisper += noise
        
        # Apply random panning for unsettling effect
        x = np.random.uniform(-1, 1)
        y = np.random.uniform(-1, 1)
        return self.binaural.apply_3d_positioning(whisper, x, y, 0.5)
    
    def create_digital_scream(self, intensity: float) -> np.ndarray:
        """Create digitally corrupted scream effect."""
        duration = 1.0 + (intensity * 2.0)  # Longer scream at higher intensity
        time_array = np.linspace(0, duration, int(self.binaural.sample_rate * duration))
        
        # Base frequency sweep for scream
        freq_start = 200
        freq_end = 800 + (intensity * 400)
        frequency = np.linspace(freq_start, freq_end, len(time_array))
        
        # Create frequency-modulated tone
        phase = np.cumsum(2 * np.pi * frequency / self.binaural.sample_rate)
        scream = np.sin(phase)
        
        # Apply dramatic envelope
        attack_time = 0.1
        decay_time = duration - attack_time
        attack_samples = int(attack_time * self.binaural.sample_rate)
        
        envelope = np.ones_like(scream)
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        envelope[attack_samples:] = np.exp(-np.linspace(0, 5, len(envelope) - attack_samples))
        
        scream *= envelope
        
        # Apply heavy corruption
        scream = self.binaural.apply_horror_filter(scream, intensity)
        
        # Random stereo positioning for disorientation
        return self.binaural.apply_3d_positioning(scream, 0, 0, 1.0)
    
    def create_system_glitch(self, duration: float, corruption_level: float) -> np.ndarray:
        """Create system glitch/error sounds."""
        time_array = np.linspace(0, duration, int(self.binaural.sample_rate * duration))
        
        # Digital noise base
        noise = np.random.uniform(-1, 1, len(time_array))
        
        # Add periodic glitch pulses
        pulse_freq = 10 + (corruption_level * 20)
        pulses = np.sin(2 * np.pi * pulse_freq * time_array)
        pulses = np.where(pulses > 0.7, 1, 0)  # Square wave effect
        
        # Combine noise with pulses
        glitch = noise * 0.3 + pulses * 0.7
        
        # Apply bit crushing
        bit_depth = max(2, int(8 * (1.0 - corruption_level)))
        scale = 2 ** (bit_depth - 1)
        glitch = np.round(glitch * scale) / scale
        
        # Random stereo effects
        left_delay = np.random.randint(0, int(0.01 * self.binaural.sample_rate))
        right_delay = np.random.randint(0, int(0.01 * self.binaural.sample_rate))
        
        left_channel = np.concatenate([np.zeros(left_delay), glitch])
        right_channel = np.concatenate([np.zeros(right_delay), glitch])
        
        max_length = max(len(left_channel), len(right_channel))
        left_channel = np.pad(left_channel, (0, max_length - len(left_channel)))
        right_channel = np.pad(right_channel, (0, max_length - len(right_channel)))
        
        return np.column_stack((left_channel, right_channel)).astype(np.float32)
