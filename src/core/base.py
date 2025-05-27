"""Base classes for core game components."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging
from dataclasses import dataclass, field

@dataclass
class BaseManager(ABC):
    """Base class for all manager components in the game.
    
    This class provides common functionality for:
    - Logging
    - State management
    - Error handling
    - Resource cleanup
    """
    
    name: str
    logger: logging.Logger = field(init=False)
    _state: Dict[str, Any] = field(default_factory=dict)
    _is_initialized: bool = field(default=False)
    
    def __post_init__(self):
        """Initialize the manager after dataclass initialization."""
        self.logger = logging.getLogger(f"cyberscape.{self.name}")
        self._state = {}
        self._is_initialized = False
    
    def initialize(self) -> bool:
        """Initialize the manager.
        
        Returns:
            bool: True if initialization was successful
        """
        if self._is_initialized:
            self.logger.warning(f"{self.name} already initialized")
            return True
            
        try:
            self._initialize()
            self._is_initialized = True
            self.logger.info(f"{self.name} initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.name}: {e}")
            return False
    
    def cleanup(self) -> None:
        """Clean up resources used by the manager."""
        if not self._is_initialized:
            return
            
        try:
            self._cleanup()
            self._is_initialized = False
            self.logger.info(f"{self.name} cleaned up successfully")
        except Exception as e:
            self.logger.error(f"Error during {self.name} cleanup: {e}")
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get a value from the manager's state.
        
        Args:
            key: The state key to retrieve
            default: Default value if key doesn't exist
            
        Returns:
            The state value or default if not found
        """
        return self._state.get(key, default)
    
    def set_state(self, key: str, value: Any) -> None:
        """Set a value in the manager's state.
        
        Args:
            key: The state key to set
            value: The value to set
        """
        self._state[key] = value
        self.logger.debug(f"State updated: {key}={value}")
    
    def clear_state(self) -> None:
        """Clear all state values."""
        self._state.clear()
        self.logger.debug("State cleared")
    
    @abstractmethod
    def _initialize(self) -> None:
        """Initialize the manager's resources.
        
        This method should be implemented by subclasses to perform
        their specific initialization tasks.
        """
        pass
    
    @abstractmethod
    def _cleanup(self) -> None:
        """Clean up the manager's resources.
        
        This method should be implemented by subclasses to perform
        their specific cleanup tasks.
        """
        pass
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup() 