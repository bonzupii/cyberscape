"""Base classes for puzzle components."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
import logging
from ..core.base import BaseManager

@dataclass
class PuzzleComponent(BaseManager):
    """Base class for all puzzle components.
    
    This class provides common functionality for:
    - Puzzle state management
    - Hint system
    - Progress tracking
    - Solution validation
    """
    
    difficulty: int = 1
    hints: List[str] = field(default_factory=list)
    current_hint_index: int = 0
    solved: bool = False
    attempts: int = 0
    max_attempts: int = 3
    time_limit: Optional[float] = None
    start_time: Optional[float] = None
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger(__name__))
    
    def __post_init__(self):
        """Initialize the puzzle component after dataclass initialization."""
        super().__post_init__()
        self.hints = []
        self.current_hint_index = 0
        self.solved = False
        self.attempts = 0
        self.start_time = None
        self.logger.debug("Puzzle component initialized")
    
    def _initialize(self) -> None:
        """Initialize the puzzle's state."""
        try:
            self.solved = False
            self.attempts = 0
            self.current_hint_index = 0
            self.start_time = None
            self._initialize_puzzle()
            self.logger.debug("Puzzle initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize puzzle: {e}")
            raise
    
    def _cleanup(self) -> None:
        """Clean up the puzzle's state."""
        try:
            self.solved = False
            self.attempts = 0
            self.current_hint_index = 0
            self.start_time = None
            self._cleanup_puzzle()
            self.logger.debug("Puzzle cleaned up successfully")
        except Exception as e:
            self.logger.error(f"Failed to clean up puzzle: {e}")
            raise
    
    def start(self) -> bool:
        """Start the puzzle.
        
        Returns:
            bool: True if puzzle started successfully
        """
        try:
            if self.solved:
                self.logger.warning("Attempted to start already solved puzzle")
                return False
                
            self._initialize()
            self.start_time = self.get_state("current_time", 0.0)
            self.logger.info("Puzzle started successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start puzzle: {e}")
            return False
    
    def get_hint(self) -> Optional[str]:
        """Get the next hint for the puzzle.
        
        Returns:
            Optional[str]: The next hint, or None if no more hints
        """
        try:
            if not self.hints or self.current_hint_index >= len(self.hints):
                self.logger.debug("No more hints available")
                return None
                
            hint = self.hints[self.current_hint_index]
            self.current_hint_index += 1
            self.logger.debug(f"Hint {self.current_hint_index} provided")
            return hint
        except Exception as e:
            self.logger.error(f"Failed to get hint: {e}")
            return None
    
    def check_solution(self, solution: Any) -> Tuple[bool, str]:
        """Check if a solution is correct.
        
        Args:
            solution: The solution to check
            
        Returns:
            Tuple[bool, str]: (is_correct, message)
        """
        try:
            if self.solved:
                self.logger.warning("Attempted to check solution for already solved puzzle")
                return False, "Puzzle already solved"
                
            if self.attempts >= self.max_attempts:
                self.logger.warning("Maximum attempts reached")
                return False, "Maximum attempts reached"
                
            if self.time_limit and self.start_time:
                current_time = self.get_state("current_time", 0.0)
                if current_time - self.start_time > self.time_limit:
                    self.logger.warning("Time limit exceeded")
                    return False, "Time limit exceeded"
            
            self.attempts += 1
            is_correct, message = self._validate_solution(solution)
            
            if is_correct:
                self.solved = True
                self.logger.info("Puzzle solved successfully")
            else:
                self.logger.debug(f"Solution attempt {self.attempts} failed: {message}")
                
            return is_correct, message
        except Exception as e:
            self.logger.error(f"Failed to check solution: {e}")
            return False, f"Error checking solution: {str(e)}"
    
    def get_progress(self) -> float:
        """Get the puzzle's progress.
        
        Returns:
            float: Progress from 0.0 to 1.0
        """
        try:
            return self._calculate_progress()
        except Exception as e:
            self.logger.error(f"Failed to calculate progress: {e}")
            return 0.0
    
    def is_solved(self) -> bool:
        """Check if the puzzle is solved.
        
        Returns:
            bool: True if puzzle is solved
        """
        return self.solved
    
    def get_remaining_attempts(self) -> int:
        """Get the number of remaining attempts.
        
        Returns:
            int: Number of remaining attempts
        """
        return max(0, self.max_attempts - self.attempts)
    
    def get_remaining_time(self) -> Optional[float]:
        """Get the remaining time for the puzzle.
        
        Returns:
            Optional[float]: Remaining time in seconds, or None if no time limit
        """
        if not self.time_limit or not self.start_time:
            return None
            
        current_time = self.get_state("current_time", 0.0)
        remaining = self.time_limit - (current_time - self.start_time)
        return max(0.0, remaining)
    
    @abstractmethod
    def _initialize_puzzle(self) -> None:
        """Initialize the puzzle's specific state.
        
        This method should be implemented by subclasses to perform
        their specific initialization tasks.
        """
        pass
    
    @abstractmethod
    def _cleanup_puzzle(self) -> None:
        """Clean up the puzzle's specific state.
        
        This method should be implemented by subclasses to perform
        their specific cleanup tasks.
        """
        pass
    
    @abstractmethod
    def _validate_solution(self, solution: Any) -> Tuple[bool, str]:
        """Validate a solution to the puzzle.
        
        This method should be implemented by subclasses to perform
        their specific solution validation.
        
        Args:
            solution: The solution to validate
            
        Returns:
            Tuple[bool, str]: (is_correct, message)
        """
        return False, "Not implemented"
    
    @abstractmethod
    def _calculate_progress(self) -> float:
        """Calculate the puzzle's progress.
        
        This method should be implemented by subclasses to perform
        their specific progress calculation.
        
        Returns:
            float: Progress from 0.0 to 1.0
        """
        return 0.0 