"""Base classes for story components."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from ..core.base import BaseManager

@dataclass
class StoryComponent(BaseManager):
    """Base class for all story components.
    
    This class provides common functionality for:
    - Narrative state management
    - Branch tracking
    - Event handling
    - Progress tracking
    """
    
    current_branch: str = "main"
    branches: Dict[str, List[str]] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    flags: Dict[str, bool] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize the story component after dataclass initialization."""
        super().__post_init__()
        self.branches = {}
        self.events = []
        self.flags = {}
        self.variables = {}
    
    def _initialize(self) -> None:
        """Initialize the story's state."""
        self.current_branch = "main"
        self.events.clear()
        self.flags.clear()
        self.variables.clear()
        self._initialize_story()
        self.logger.debug("Story initialized")
    
    def _cleanup(self) -> None:
        """Clean up the story's state."""
        self._cleanup_story()
        self.logger.debug("Story cleaned up")
    
    def add_branch(self, name: str, events: List[str]) -> None:
        """Add a new story branch.
        
        Args:
            name: Name of the branch
            events: List of events in the branch
        """
        self.branches[name] = events
        self.logger.debug(f"Added branch: {name}")
    
    def switch_branch(self, name: str) -> bool:
        """Switch to a different story branch.
        
        Args:
            name: Name of the branch to switch to
            
        Returns:
            bool: True if branch switch was successful
        """
        if name not in self.branches:
            self.logger.error(f"Branch not found: {name}")
            return False
            
        self.current_branch = name
        self.logger.info(f"Switched to branch: {name}")
        return True
    
    def add_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Add a story event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        event = {
            "type": event_type,
            "data": data,
            "branch": self.current_branch,
            "timestamp": self.get_state("current_time", 0.0)
        }
        self.events.append(event)
        self.logger.debug(f"Added event: {event_type}")
    
    def set_flag(self, name: str, value: bool = True) -> None:
        """Set a story flag.
        
        Args:
            name: Name of the flag
            value: Flag value
        """
        self.flags[name] = value
        self.logger.debug(f"Set flag {name} to {value}")
    
    def get_flag(self, name: str) -> bool:
        """Get a story flag's value.
        
        Args:
            name: Name of the flag
            
        Returns:
            bool: Flag value
        """
        return self.flags.get(name, False)
    
    def set_variable(self, name: str, value: Any) -> None:
        """Set a story variable.
        
        Args:
            name: Name of the variable
            value: Variable value
        """
        self.variables[name] = value
        self.logger.debug(f"Set variable {name} to {value}")
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a story variable's value.
        
        Args:
            name: Name of the variable
            default: Default value if variable not found
            
        Returns:
            Any: Variable value
        """
        return self.variables.get(name, default)
    
    def get_current_events(self) -> List[Dict[str, Any]]:
        """Get events in the current branch.
        
        Returns:
            List[Dict[str, Any]]: List of events
        """
        return [
            event for event in self.events
            if event["branch"] == self.current_branch
        ]
    
    def get_progress(self) -> float:
        """Get the story's progress.
        
        Returns:
            float: Progress from 0.0 to 1.0
        """
        return self._calculate_progress()
    
    @abstractmethod
    def _initialize_story(self) -> None:
        """Initialize the story's specific state.
        
        This method should be implemented by subclasses to perform
        their specific initialization tasks.
        """
        pass
    
    @abstractmethod
    def _cleanup_story(self) -> None:
        """Clean up the story's specific state.
        
        This method should be implemented by subclasses to perform
        their specific cleanup tasks.
        """
        pass
    
    @abstractmethod
    def _calculate_progress(self) -> float:
        """Calculate the story's progress.
        
        This method should be implemented by subclasses to perform
        their specific progress calculation.
        
        Returns:
            float: Progress from 0.0 to 1.0
        """
        return 0.0 