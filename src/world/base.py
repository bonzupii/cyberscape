"""Base classes for world management in Cyberscape: Digital Dread."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class WorldComponent(ABC):
    """Base class for world-related components."""
    
    def __init__(self, component_id: str):
        self.component_id = component_id
        self.is_active = True
        self.metadata = {}
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the world component."""
        pass
    
    @abstractmethod
    def update(self, delta_time: float) -> None:
        """Update the component state."""
        pass
    
    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """Get the current component state."""
        pass
    
    @abstractmethod
    def set_state(self, state: Dict[str, Any]) -> None:
        """Set the component state."""
        pass
    
    def activate(self) -> None:
        """Activate the component."""
        self.is_active = True
    
    def deactivate(self) -> None:
        """Deactivate the component."""
        self.is_active = False

@dataclass
class NavigationPath:
    """Represents a path between world locations."""
    source_id: str
    target_id: str
    path_type: str  # "direct", "hidden", "conditional"
    requirements: List[str]
    difficulty: int = 1
    is_bidirectional: bool = True
    corruption_effect: float = 0.0

class LocationManager(WorldComponent):
    """Base class for managing locations within the world."""
    
    def __init__(self):
        super().__init__("location_manager")
        self.locations = {}
        self.navigation_paths = {}
        self.current_location = None
    
    def add_location(self, location_id: str, location_data: Dict[str, Any]) -> bool:
        """Add a new location to the manager."""
        if location_id in self.locations:
            return False
        
        self.locations[location_id] = location_data
        return True
    
    def get_location(self, location_id: str) -> Optional[Dict[str, Any]]:
        """Get location data by ID."""
        return self.locations.get(location_id)
    
    def add_navigation_path(self, path: NavigationPath) -> None:
        """Add a navigation path between locations."""
        path_key = f"{path.source_id}->{path.target_id}"
        self.navigation_paths[path_key] = path
        
        if path.is_bidirectional:
            reverse_path_key = f"{path.target_id}->{path.source_id}"
            reverse_path = NavigationPath(
                source_id=path.target_id,
                target_id=path.source_id,
                path_type=path.path_type,
                requirements=path.requirements,
                difficulty=path.difficulty,
                is_bidirectional=False,  # Prevent infinite recursion
                corruption_effect=path.corruption_effect
            )
            self.navigation_paths[reverse_path_key] = reverse_path
    
    def get_available_paths(self, from_location: str) -> List[NavigationPath]:
        """Get available navigation paths from a location."""
        available_paths = []
        
        for path_key, path in self.navigation_paths.items():
            if path.source_id == from_location:
                available_paths.append(path)
        
        return available_paths
    
    def initialize(self) -> bool:
        """Initialize the location manager."""
        return True
    
    def update(self, delta_time: float) -> None:
        """Update location state."""
        pass
    
    def get_state(self) -> Dict[str, Any]:
        """Get the current state."""
        return {
            "locations": self.locations,
            "navigation_paths": {k: {
                "source_id": v.source_id,
                "target_id": v.target_id,
                "path_type": v.path_type,
                "requirements": v.requirements,
                "difficulty": v.difficulty,
                "is_bidirectional": v.is_bidirectional,
                "corruption_effect": v.corruption_effect
            } for k, v in self.navigation_paths.items()},
            "current_location": self.current_location
        }
    
    def set_state(self, state: Dict[str, Any]) -> None:
        """Set the state from saved data."""
        self.locations = state.get("locations", {})
        self.current_location = state.get("current_location")
        
        # Reconstruct navigation paths
        self.navigation_paths = {}
        for path_key, path_data in state.get("navigation_paths", {}).items():
            path = NavigationPath(
                source_id=path_data["source_id"],
                target_id=path_data["target_id"],
                path_type=path_data["path_type"],
                requirements=path_data["requirements"],
                difficulty=path_data["difficulty"],
                is_bidirectional=path_data["is_bidirectional"],
                corruption_effect=path_data["corruption_effect"]
            )
            self.navigation_paths[path_key] = path
