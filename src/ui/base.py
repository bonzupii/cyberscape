"""Base classes for UI components."""

from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any
import pygame
from dataclasses import dataclass, field
from ..core.base import BaseManager

@dataclass
class UIComponent(BaseManager):
    """Base class for all UI components.
    
    This class provides common functionality for:
    - Surface management
    - Rendering
    - Position and size
    - Theme support
    """
    
    position: Tuple[int, int] = (0, 0)
    size: Tuple[int, int] = (0, 0)
    visible: bool = True
    surface: Optional[pygame.Surface] = field(default=None)
    theme: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize the UI component after dataclass initialization."""
        super().__post_init__()
        self.surface = None
        self.theme = {}
    
    def _initialize(self) -> None:
        """Initialize the UI component's surface."""
        if self.size[0] > 0 and self.size[1] > 0:
            self.surface = pygame.Surface(self.size, pygame.SRCALPHA)
            self.logger.debug(f"Created surface of size {self.size}")
    
    def _cleanup(self) -> None:
        """Clean up the UI component's surface."""
        if self.surface:
            self.surface = None
            self.logger.debug("Surface cleaned up")
    
    def set_position(self, x: int, y: int) -> None:
        """Set the component's position.
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        self.position = (x, y)
        self.logger.debug(f"Position set to {self.position}")
    
    def set_size(self, width: int, height: int) -> None:
        """Set the component's size.
        
        Args:
            width: Width in pixels
            height: Height in pixels
        """
        self.size = (width, height)
        if self.surface:
            self.surface = pygame.Surface(self.size, pygame.SRCALPHA)
        self.logger.debug(f"Size set to {self.size}")
    
    def set_theme(self, theme: Dict[str, Any]) -> None:
        """Set the component's theme.
        
        Args:
            theme: Theme dictionary
        """
        self.theme = theme
        self.logger.debug("Theme updated")
    
    def show(self) -> None:
        """Make the component visible."""
        self.visible = True
        self.logger.debug("Component shown")
    
    def hide(self) -> None:
        """Make the component invisible."""
        self.visible = False
        self.logger.debug("Component hidden")
    
    def render(self, target: pygame.Surface) -> None:
        """Render the component to the target surface.
        
        Args:
            target: Surface to render to
        """
        if not self.visible or not self.surface:
            return
            
        self._render()
        target.blit(self.surface, self.position)
    
    @abstractmethod
    def _render(self) -> None:
        """Render the component's content to its surface.
        
        This method should be implemented by subclasses to perform
        their specific rendering tasks.
        """
        pass
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle a pygame event.
        
        Args:
            event: The pygame event to handle
            
        Returns:
            bool: True if the event was handled
        """
        if not self.visible:
            return False
        return self._handle_event(event)
    
    @abstractmethod
    def _handle_event(self, event: pygame.event.Event) -> bool:
        """Handle a pygame event.
        
        This method should be implemented by subclasses to perform
        their specific event handling.
        
        Args:
            event: The pygame event to handle
            
        Returns:
            bool: True if the event was handled
        """
        return False 