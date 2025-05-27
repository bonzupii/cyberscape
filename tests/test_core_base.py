"""Tests for src/core/base.py"""

import pytest
import logging
from unittest.mock import Mock, patch
from src.core.base import BaseManager


class TestManager(BaseManager):
    """Test implementation of BaseManager for testing."""
    
    def __init__(self, name: str = "test"):
        self.name = name
        super().__post_init__()
    
    def _initialize(self) -> None:
        """Test implementation of _initialize."""
        pass
    
    def _cleanup(self) -> None:
        """Test implementation of cleanup."""
        pass


class TestBaseManager:
    """Test cases for BaseManager class."""

    def test_base_manager_initialization(self):
        """Test BaseManager initialization."""
        manager = TestManager("test_manager")
        assert manager.name == "test_manager"
        assert isinstance(manager.logger, logging.Logger)
        assert manager.logger.name == "cyberscape.test_manager"
        assert isinstance(manager._state, dict)
        assert len(manager._state) == 0
        assert manager._is_initialized is False

    def test_base_manager_state_management(self):
        """Test state management functionality."""
        manager = TestManager()
        
        # Test setting state
        manager.set_state("key1", "value1")
        assert manager.get_state("key1") == "value1"
        
        # Test getting non-existent state with default
        assert manager.get_state("nonexistent", "default") == "default"
        
        # Test getting non-existent state without default
        assert manager.get_state("nonexistent") is None

    def test_base_manager_initialize(self):
        """Test initialization process."""
        manager = TestManager()
        assert not manager._is_initialized
        
        result = manager.initialize()
        assert result is True
        assert manager._is_initialized is True
        
        # Second initialization should return False
        result = manager.initialize()
        assert result is False

    def test_base_manager_is_ready(self):
        """Test is_ready method."""
        manager = TestManager()
        assert not manager.is_ready()
        
        manager.initialize()
        assert manager.is_ready()

    def test_base_manager_error_handling(self):
        """Test error handling in BaseManager."""
        manager = TestManager()
        
        # Test handle_error method
        with patch.object(manager.logger, 'error') as mock_error:
            manager.handle_error("Test error", Exception("test"))
            mock_error.assert_called_once()

    def test_base_manager_logging(self):
        """Test logging functionality."""
        manager = TestManager("log_test")
        
        with patch.object(manager.logger, 'info') as mock_info:
            manager.logger.info("Test message")
            mock_info.assert_called_once_with("Test message")

    def test_base_manager_cleanup_method(self):
        """Test cleanup method in BaseManager."""
        manager = TestManager()
        manager.initialize()
        
        # Test cleanup
        manager.cleanup()
        assert manager._is_initialized is False

    def test_base_manager_abstract_methods(self):
        """Test that abstract methods are properly defined."""
        # Should not be able to instantiate BaseManager directly
        with pytest.raises(TypeError):
            BaseManager("test")
