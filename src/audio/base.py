"""Base classes for audio components."""

import pygame
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from ..core.base import BaseManager

@dataclass
class AudioComponent(BaseManager):
    """Base class for all audio components.
    
    This class provides common functionality for:
    - Sound loading and management
    - Volume control
    - Playback state
    - Resource cleanup
    """
    max_channels: int = 8
    sounds: Dict[str, 'pygame.mixer.Sound'] = field(default_factory=dict)
    channels: List['pygame.mixer.Channel'] = field(default_factory=list)
    volume: float = 1.0

    def __post_init__(self) -> None:
        """Initialize the audio component after dataclass initialization."""
        super().__post_init__()
        self.sounds = {}
        self.channels = []
    
    def _initialize(self) -> None:
        """Initialize the audio component's channels."""
        pygame.mixer.set_num_channels(self.max_channels)
        self.channels = [pygame.mixer.Channel(i) for i in range(self.max_channels)]
        self.logger.debug(f"Initialized {self.max_channels} audio channels")
    
    def _cleanup(self) -> None:
        """Clean up the audio component's resources."""
        self.stop_all()
        self.sounds.clear()
        self.channels.clear()
        self.logger.debug("Audio resources cleaned up")
    
    def load_sound(self, name: str, path: str) -> bool:
        """Load a sound file.
        
        Args:
            name: Name to give the sound
            path: Path to the sound file
            
        Returns:
            bool: True if sound was loaded successfully
        """
        try:
            sound = pygame.mixer.Sound(path)
            self.sounds[name] = sound
            self.logger.debug(f"Loaded sound: {name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load sound {name}: {e}")
            return False
    
    def play_sound(self, name: str, loop: int = 0) -> Optional[pygame.mixer.Channel]:
        """Play a loaded sound.
        
        Args:
            name: Name of the sound to play
            loop: Number of times to loop (-1 for infinite)
            
        Returns:
            Optional[pygame.mixer.Channel]: The channel playing the sound, or None if failed
        """
        if name not in self.sounds:
            self.logger.error(f"Sound not found: {name}")
            return None
            
        # Find an available channel
        channel = next((c for c in self.channels if not c.get_busy()), None)
        if not channel:
            self.logger.warning("No available audio channels")
            return None
            
        try:
            channel.play(self.sounds[name], loops=loop)
            channel.set_volume(self.volume)
            self.logger.debug(f"Playing sound: {name}")
            return channel
        except Exception as e:
            self.logger.error(f"Failed to play sound {name}: {e}")
            return None
    
    def stop_sound(self, name: str) -> None:
        """Stop a playing sound.
        
        Args:
            name: Name of the sound to stop
        """
        if name not in self.sounds:
            return
            
        for channel in self.channels:
            if channel.get_sound() == self.sounds[name]:
                channel.stop()
                self.logger.debug(f"Stopped sound: {name}")
                break
    
    def stop_all(self) -> None:
        """Stop all playing sounds."""
        for channel in self.channels:
            channel.stop()
        self.logger.debug("Stopped all sounds")
    
    def set_volume(self, volume: float) -> None:
        """Set the volume for all sounds.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.volume = max(0.0, min(1.0, volume))
        for channel in self.channels:
            channel.set_volume(self.volume)
        self.logger.debug(f"Volume set to {self.volume}")
    
    def get_volume(self) -> float:
        """Get the current volume level.
        
        Returns:
            The current volume level.
        """
        return self.volume
    
    def is_playing(self, name: str) -> bool:
        """Check if a sound is currently playing.
        
        Args:
            name: Name of the sound to check
            
        Returns:
            bool: True if the sound is playing
        """
        if name not in self.sounds:
            return False
            
        return any(
            channel.get_busy() and channel.get_sound() == self.sounds[name]
            for channel in self.channels
        ) 