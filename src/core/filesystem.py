"""
New FileSystemHandler implementation for Cyberscape: Digital Dread.

A complete rewrite with proper Unix-like semantics and clean architecture.
"""

import random
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import PurePosixPath
import os

logger = logging.getLogger(__name__)

# Corruption characters for glitch effects
CORRUPTION_CHARS = "!@#$%^&*()_+[];',./<>?:{}|`~¡¢£¤¥¦§¨©ª«¬®¯°±²³´µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞß"


@dataclass
class FileNode:
    """Represents a file in the virtual filesystem."""
    name: str
    content: str
    is_corrupted: bool = False
    corruption_level: float = 0.0
    permissions: str = "rw-r--r--"
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    size: int = field(init=False)
    
    def __post_init__(self):
        self.size = len(self.content)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'content': self.content,
            'is_corrupted': self.is_corrupted,
            'corruption_level': self.corruption_level,
            'permissions': self.permissions,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat(),
            'size': self.size
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FileNode':
        """Create from dictionary."""
        file_node = cls(
            name=data['name'],
            content=data['content'],
            is_corrupted=data.get('is_corrupted', False),
            corruption_level=data.get('corruption_level', 0.0),
            permissions=data.get('permissions', 'rw-r--r--'),
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
            modified_at=datetime.fromisoformat(data.get('modified_at', datetime.now().isoformat()))
        )
        return file_node


@dataclass
class DirectoryNode:
    """Represents a directory in the virtual filesystem."""
    name: str
    permissions: str = "rwxr-xr-x"
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    files: Dict[str, FileNode] = field(default_factory=dict)
    directories: Dict[str, 'DirectoryNode'] = field(default_factory=dict)
    parent: Optional['DirectoryNode'] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'permissions': self.permissions,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat(),
            'files': {name: file.to_dict() for name, file in self.files.items()},
            'directories': {name: dir.to_dict() for name, dir in self.directories.items()}
        }
    
    @classmethod
    def from_dict(cls, data: dict, parent: Optional['DirectoryNode'] = None) -> 'DirectoryNode':
        """Create from dictionary."""
        dir_node = cls(
            name=data['name'],
            permissions=data.get('permissions', 'rwxr-xr-x'),
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
            modified_at=datetime.fromisoformat(data.get('modified_at', datetime.now().isoformat())),
            parent=parent
        )
        
        # Restore files
        for name, file_data in data.get('files', {}).items():
            dir_node.files[name] = FileNode.from_dict(file_data)
        
        # Restore directories recursively
        for name, dir_data in data.get('directories', {}).items():
            dir_node.directories[name] = cls.from_dict(dir_data, parent=dir_node)
        
        return dir_node


class FileSystemHandler:
    """
    A Unix-like virtual filesystem handler with proper path semantics.
    
    This implementation follows standard Unix conventions:
    - Root directory is "/"
    - Paths are resolved properly with ., .., ~
    - Current working directory tracking
    - Standard file operations
    """
    
    def __init__(self, initial_username: str = "hacker"):
        """Initialize the filesystem."""
        self.username = initial_username
        self.hostname = "system"
        
        # Create root directory
        self.root = DirectoryNode("/")
        
        # Current working directory (starts at root)
        self.current_directory = self.root
        
        # Home directory path (will be /home/{username})
        self.home_path = f"/home/{self.username}"
        
        # Corruption tracking
        self.corrupted_items = set()
        self.locked_files = set()
        
        # Role-specific content configuration
        self.path_specific_content = {
            "purifier": {
                "system_files": ["security_logs", "firewall_config", "access_control"],
                "special_dirs": ["/secure", "/audit", "/backup"],
                "file_extensions": [".log", ".conf", ".bak"]
            },
            "arbiter": {
                "system_files": ["network_scan", "vulnerability_report", "exploit_db"],
                "special_dirs": ["/tools", "/exploits", "/research"],
                "file_extensions": [".txt", ".md", ".py"]
            },
            "ascendant": {
                "system_files": ["backdoor", "payload", "malware"],
                "special_dirs": ["/hidden", "/backdoors", "/malware"],
                "file_extensions": [".exe", ".bin", ".sh"]
            }
        }
        
        # Initialize filesystem structure
        self._initialize_filesystem()
        
        # Set initial working directory to home
        self._change_to_home()
    
    def _initialize_filesystem(self):
        """Create the initial filesystem structure."""
        # Create standard Unix directories
        self._mkdir_internal("/bin")
        self._mkdir_internal("/etc")
        self._mkdir_internal("/var")
        self._mkdir_internal("/home")
        self._mkdir_internal("/tmp")
        self._mkdir_internal("/system")
        
        # Create user home directory
        self._mkdir_internal(self.home_path)
        self._mkdir_internal(f"{self.home_path}/documents")
        self._mkdir_internal(f"{self.home_path}/tools")
        
        # Create system subdirectories
        self._mkdir_internal("/system/logs")
        
        # Add some initial files
        self._create_file_internal("/README.txt", "Welcome to the Cyberscape terminal system.")
        self._create_file_internal(f"{self.home_path}/welcome.txt", "Welcome to your home directory!")
        self._create_file_internal(f"{self.home_path}/documents/personal_journal.txt", 
                                 "Day 1: The system seems different today...")
        
        # Add some system files
        self._create_file_internal("/etc/passwd", "root:x:0:0:root:/root:/bin/bash\n" + 
                                 f"{self.username}:x:1000:1000::/home/{self.username}:/bin/bash")
        self._create_file_internal("/system/logs/boot.log", "System boot sequence completed.")
        
        logger.info("Filesystem initialized with standard Unix structure")
    
    def _change_to_home(self):
        """Set current directory to user's home."""
        home_dir = self._get_node_at_path(self.home_path)
        if isinstance(home_dir, DirectoryNode):
            self.current_directory = home_dir
            logger.debug(f"Changed to home directory: {self.home_path}")
    
    def _resolve_path(self, path: str) -> str:
        """
        Resolve a path string to an absolute path.
        
        Handles:
        - Relative paths (relative to current directory)
        - Absolute paths (starting with /)
        - Home directory (~)
        - Current directory (.)
        - Parent directory (..)
        """
        if not path:
            return self.get_current_path_str()
        
        # Handle home directory
        if path.startswith("~/"):
            path = self.home_path + path[1:]
        elif path == "~":
            path = self.home_path
        
        # If it's an absolute path, use it directly
        if path.startswith("/"):
            resolved_path = str(PurePosixPath(path))
        else:
            # Relative path - combine with current directory
            current_path = self.get_current_path_str()
            combined = str(PurePosixPath(current_path) / path)
            resolved_path = str(PurePosixPath(combined))
        
        # Normalize the path by handling . and .. components
        resolved_path = self._normalize_path(resolved_path)
        
        # Ensure we don't go above root
        if not resolved_path.startswith("/"):
            resolved_path = "/"
        
        return resolved_path
    
    def _normalize_path(self, path: str) -> str:
        """Normalize a path by resolving . and .. components."""
        if path == "/":
            return "/"
        
        parts = [p for p in path.split("/") if p and p != "."]
        normalized_parts = []
        
        for part in parts:
            if part == "..":
                if normalized_parts:
                    normalized_parts.pop()
            else:
                normalized_parts.append(part)
        
        if not normalized_parts:
            return "/"
        
        return "/" + "/".join(normalized_parts)
    
    def _get_node_at_path(self, path: str) -> Optional[Union[DirectoryNode, FileNode]]:
        """Get the node (file or directory) at the given path."""
        resolved_path = self._resolve_path(path)
        
        if resolved_path == "/":
            return self.root
        
        # Split path into components
        parts = [p for p in resolved_path.split("/") if p]
        
        current_node = self.root
        
        for part in parts:
            if not isinstance(current_node, DirectoryNode):
                return None
            
            # Check directories first
            if part in current_node.directories:
                current_node = current_node.directories[part]
            # Then check files (for the last component)
            elif part in current_node.files:
                if part == parts[-1]:  # Only files can be the final component
                    return current_node.files[part]
                else:
                    return None  # Can't traverse through a file
            else:
                return None
        
        return current_node
    
    def _mkdir_internal(self, path: str) -> bool:
        """Internal method to create a directory (used during initialization)."""
        resolved_path = self._resolve_path(path)
        
        if resolved_path == "/":
            return False  # Can't create root
        
        # Get parent path and directory name
        parts = [p for p in resolved_path.split("/") if p]
        if not parts:
            return False
        
        dir_name = parts[-1]
        parent_path = "/" + "/".join(parts[:-1]) if len(parts) > 1 else "/"
        
        parent_node = self._get_node_at_path(parent_path)
        if not isinstance(parent_node, DirectoryNode):
            return False
        
        # Create the directory if it doesn't exist
        if dir_name not in parent_node.directories and dir_name not in parent_node.files:
            new_dir = DirectoryNode(dir_name, parent=parent_node)
            parent_node.directories[dir_name] = new_dir
            parent_node.modified_at = datetime.now()
            return True
        
        return False
    
    def _create_file_internal(self, path: str, content: str) -> bool:
        """Internal method to create a file (used during initialization)."""
        resolved_path = self._resolve_path(path)
        
        if resolved_path == "/":
            return False  # Can't create file at root path
        
        parts = [p for p in resolved_path.split("/") if p]
        if not parts:
            return False
        
        file_name = parts[-1]
        parent_path = "/" + "/".join(parts[:-1]) if len(parts) > 1 else "/"
        
        parent_node = self._get_node_at_path(parent_path)
        if not isinstance(parent_node, DirectoryNode):
            return False
        
        # Create or update the file
        new_file = FileNode(file_name, content)
        parent_node.files[file_name] = new_file
        parent_node.modified_at = datetime.now()
        return True
    
    # Public API Methods
    
    def get_current_path_str(self) -> str:
        """Get the current directory path as a string."""
        if self.current_directory == self.root:
            return "/"
        
        # Build path by traversing up to root
        parts = []
        node = self.current_directory
        
        while node and node != self.root:
            parts.append(node.name)
            node = node.parent
        
        if not parts:
            return "/"
        
        return "/" + "/".join(reversed(parts))
    
    @property
    def current_path_list(self) -> List[str]:
        """Get current path as a list for backward compatibility."""
        current_path = self.get_current_path_str()
        
        if current_path == "/":
            return []
        elif current_path == self.home_path:
            return ["~"]
        else:
            # Return path components
            parts = [p for p in current_path.split("/") if p]
            return parts
    
    @current_path_list.setter
    def current_path_list(self, path_list: List[str]):
        """Set current path from list for backward compatibility."""
        if not path_list or path_list == []:
            self.current_directory = self.root
        elif path_list == ["~"]:
            self._change_to_home()
        else:
            # Convert list to path string
            path = "/" + "/".join(path_list)
            node = self._get_node_at_path(path)
            if isinstance(node, DirectoryNode):
                self.current_directory = node
    
    def execute_cd(self, path: str) -> Tuple[bool, str]:
        """Change directory."""
        if not path:
            return False, "cd: missing directory operand"
        
        target_node = self._get_node_at_path(path)
        
        if not isinstance(target_node, DirectoryNode):
            return False, f"cd: no such directory: '{path}'"
        
        self.current_directory = target_node
        resolved_path = self._resolve_path(path)
        return True, f"Changed directory to {resolved_path}"
    
    def list_items(self, path: Optional[str] = None) -> List[Tuple[str, str]]:
        """
        List items in a directory.
        
        Returns:
            List of (name, type) tuples where type is "file" or "directory"
        """
        if path is None:
            target_node = self.current_directory
        else:
            target_node = self._get_node_at_path(path)
        
        if not isinstance(target_node, DirectoryNode):
            return []
        
        items = []
        
        # Add directories
        for name in sorted(target_node.directories.keys()):
            items.append((name, "directory"))
        
        # Add files
        for name in sorted(target_node.files.keys()):
            items.append((name, "file"))
        
        return items
    
    def get_item_content(self, path: str) -> Optional[str]:
        """Get the content of a file."""
        node = self._get_node_at_path(path)
        
        if not isinstance(node, FileNode):
            return None
        
        content = node.content
        
        # Apply corruption if the file is corrupted
        if node.is_corrupted or (path in self.corrupted_items):
            content = self._corrupt_content(content, node.corruption_level)
        
        return content
    
    def write_file_content(self, path: str, content: str, corrupted: bool = False) -> Tuple[bool, str]:
        """Write content to a file."""
        if not path:
            return False, "write: missing file operand"
        
        resolved_path = self._resolve_path(path)
        
        if resolved_path == "/":
            return False, "write: cannot write to root directory"
        
        parts = [p for p in resolved_path.split("/") if p]
        if not parts:
            return False, "write: invalid path"
        
        file_name = parts[-1]
        parent_path = "/" + "/".join(parts[:-1]) if len(parts) > 1 else "/"
        
        parent_node = self._get_node_at_path(parent_path)
        if not isinstance(parent_node, DirectoryNode):
            return False, f"write: parent directory does not exist: {parent_path}"
        
        # Create or update the file
        if file_name in parent_node.files:
            # Update existing file
            file_node = parent_node.files[file_name]
            file_node.content = content
            file_node.modified_at = datetime.now()
            file_node.size = len(content)
            if corrupted:
                file_node.is_corrupted = True
                file_node.corruption_level = random.uniform(0.1, 0.5)
        else:
            # Create new file
            file_node = FileNode(file_name, content, is_corrupted=corrupted)
            if corrupted:
                file_node.corruption_level = random.uniform(0.1, 0.5)
            parent_node.files[file_name] = file_node
        
        parent_node.modified_at = datetime.now()
        
        if corrupted:
            self.corrupted_items.add(resolved_path)
        
        return True, f"Successfully wrote to {resolved_path}"
    
    def execute_mkdir(self, path: str) -> Tuple[bool, str]:
        """Create a new directory."""
        if not path:
            return False, "mkdir: missing directory operand"
        
        resolved_path = self._resolve_path(path)
        
        if resolved_path == "/":
            return False, "mkdir: cannot create root directory"
        
        parts = [p for p in resolved_path.split("/") if p]
        if not parts:
            return False, "mkdir: invalid path"
        
        dir_name = parts[-1]
        parent_path = "/" + "/".join(parts[:-1]) if len(parts) > 1 else "/"
        
        parent_node = self._get_node_at_path(parent_path)
        if not isinstance(parent_node, DirectoryNode):
            return False, f"mkdir: parent directory does not exist: {parent_path}"
        
        # Check if directory or file already exists
        if dir_name in parent_node.directories or dir_name in parent_node.files:
            return False, f"mkdir: directory already exists: {resolved_path}"
        
        # Create the directory
        new_dir = DirectoryNode(dir_name, parent=parent_node)
        parent_node.directories[dir_name] = new_dir
        parent_node.modified_at = datetime.now()
        
        return True, f"Successfully created directory {resolved_path}"
    
    def remove_item(self, path: str, recursive: bool = False) -> Tuple[bool, str]:
        """Remove a file or directory."""
        if not path:
            return False, "rm: missing operand"
        
        resolved_path = self._resolve_path(path)
        
        if resolved_path == "/":
            return False, "rm: cannot remove root directory"
        
        if resolved_path == self.home_path:
            return False, "rm: cannot remove home directory"
        
        parts = [p for p in resolved_path.split("/") if p]
        if not parts:
            return False, "rm: invalid path"
        
        item_name = parts[-1]
        parent_path = "/" + "/".join(parts[:-1]) if len(parts) > 1 else "/"
        
        parent_node = self._get_node_at_path(parent_path)
        if not isinstance(parent_node, DirectoryNode):
            return False, f"rm: parent directory does not exist: {parent_path}"
        
        # Remove directory
        if item_name in parent_node.directories:
            dir_to_remove = parent_node.directories[item_name]
            
            # Check if directory is empty (unless recursive)
            if not recursive and (dir_to_remove.directories or dir_to_remove.files):
                return False, f"rm: cannot remove '{resolved_path}': Directory not empty"
            
            del parent_node.directories[item_name]
            parent_node.modified_at = datetime.now()
            
            # Remove from corruption tracking
            self.corrupted_items.discard(resolved_path)
            
            return True, f"Successfully removed {resolved_path}"
        
        # Remove file
        elif item_name in parent_node.files:
            del parent_node.files[item_name]
            parent_node.modified_at = datetime.now()
            
            # Remove from corruption tracking
            self.corrupted_items.discard(resolved_path)
            
            return True, f"Successfully removed {resolved_path}"
        
        else:
            return False, f"rm: cannot remove '{resolved_path}': No such file or directory"
    
    def _corrupt_content(self, content: str, corruption_level: float = None) -> str:
        """Apply corruption effects to content."""
        if corruption_level is None:
            corruption_level = random.uniform(0.1, 0.3)
        
        if corruption_level <= 0:
            return content
        
        corrupted = list(content)
        num_corruptions = int(len(content) * corruption_level)
        
        for _ in range(num_corruptions):
            if corrupted:
                pos = random.randint(0, len(corrupted) - 1)
                corrupted[pos] = random.choice(CORRUPTION_CHARS)
        
        return ''.join(corrupted)
    
    def get_state(self) -> dict:
        """Get the current state of the filesystem for persistence."""
        return {
            "root": self.root.to_dict(),
            "current_path": self.get_current_path_str(),
            "corrupted_items": list(self.corrupted_items),
            "username": self.username,
            "hostname": self.hostname,
            "home_path": self.home_path
        }
    
    def restore_state(self, state: dict):
        """Restore the filesystem from a saved state."""
        self.root = DirectoryNode.from_dict(state["root"])
        self.corrupted_items = set(state.get("corrupted_items", []))
        self.username = state.get("username", "hacker")
        self.hostname = state.get("hostname", "system")
        self.home_path = state.get("home_path", f"/home/{self.username}")
        
        # Restore current directory
        current_path = state.get("current_path", "/")
        self.current_directory = self._get_node_at_path(current_path) or self.root
    
    def set_role(self, role: str):
        """Set the current role and update filesystem accordingly."""
        if role not in self.path_specific_content:
            logger.warning(f"Unknown role: {role}")
            return
        
        role_config = self.path_specific_content[role]
        
        # Create role-specific directories
        for special_dir in role_config.get("special_dirs", []):
            self._mkdir_internal(special_dir)
            
            # Add some role-specific files
            for file_name in role_config.get("system_files", []):
                file_path = f"{special_dir}/{file_name}.txt"
                content = f"Role-specific content for {role}: {file_name}"
                self._create_file_internal(file_path, content)
        
        logger.info(f"Set role to {role} and updated filesystem")
    
    def cleanup(self):
        """Clean up resources."""
        self.corrupted_items.clear()
        self.locked_files.clear()
        logger.debug("Filesystem cleanup completed")

    # Additional methods for command compatibility
    def copy_file(self, source: str, destination: str) -> bool:
        """Copy a file from source to destination."""
        try:
            # Get source content
            content = self.get_item_content(source)
            if content is None:
                logger.warning(f"Cannot copy '{source}': file not found")
                return False
            
            # Write to destination
            success, message = self.write_file_content(destination, content)
            if success:
                logger.info(f"Successfully copied '{source}' to '{destination}'")
                return True
            else:
                logger.warning(f"Failed to copy '{source}' to '{destination}': {message}")
                return False
        except Exception as e:
            logger.error(f"Error copying file '{source}' to '{destination}': {e}")
            return False

    def move_file(self, source: str, destination: str) -> bool:
        """Move a file from source to destination."""
        try:
            # First copy the file
            if self.copy_file(source, destination):
                # Then remove the source
                success, message = self.remove_item(source)
                if success:
                    logger.info(f"Successfully moved '{source}' to '{destination}'")
                    return True
                else:
                    # If removal fails, try to remove the destination to clean up
                    self.remove_item(destination)
                    logger.warning(f"Failed to remove source '{source}' after copy: {message}")
                    return False
            else:
                logger.warning(f"Failed to move '{source}' to '{destination}': copy failed")
                return False
        except Exception as e:
            logger.error(f"Error moving file '{source}' to '{destination}': {e}")
            return False

    def remove_file(self, path: str) -> bool:
        """Remove a file (wrapper for remove_item for compatibility)."""
        success, message = self.remove_item(path)
        if not success:
            logger.warning(f"Failed to remove file '{path}': {message}")
        return success

    def create_file(self, path: str, content: str = "") -> bool:
        """Create a file with given content (wrapper for write_file_content)."""
        success, message = self.write_file_content(path, content)
        if not success:
            logger.warning(f"Failed to create file '{path}': {message}")
        return success

    def create_directory(self, path: str) -> bool:
        """Create a directory (wrapper for execute_mkdir)."""
        success, message = self.execute_mkdir(path)
        if not success:
            logger.warning(f"Failed to create directory '{path}': {message}")
        return success

    def find_files(self, pattern: str, search_path: str = "/") -> List[str]:
        """Find files matching a pattern in the filesystem."""
        try:
            results = []
            pattern_lower = pattern.lower()
            
            def search_recursive(node: DirectoryNode, current_path: str):
                # Search files in current directory
                for file_name, file_node in node.files.items():
                    file_path = f"{current_path}/{file_name}" if current_path != "/" else f"/{file_name}"
                    if pattern_lower in file_name.lower() or pattern in file_name:
                        results.append(file_path)
                
                # Search subdirectories
                for dir_name, dir_node in node.directories.items():
                    dir_path = f"{current_path}/{dir_name}" if current_path != "/" else f"/{dir_name}"
                    if pattern_lower in dir_name.lower() or pattern in dir_name:
                        results.append(dir_path)
                    search_recursive(dir_node, dir_path)
            
            # Start search from specified path
            search_node = self._get_node_at_path(search_path)
            if isinstance(search_node, DirectoryNode):
                search_recursive(search_node, search_path)
            
            return results
        except Exception as e:
            logger.error(f"Error finding files with pattern '{pattern}': {e}")
            return []

    def get_current_path(self) -> str:
        """Get current path (wrapper for get_current_path_str)."""
        return self.get_current_path_str()

    def read_file(self, path: str) -> Optional[str]:
        """Read file content (wrapper for get_item_content)."""
        return self.get_item_content(path)

    def create_role_specific_content(self, role: str):
        """Create role-specific files and directories."""
        if role not in self.path_specific_content:
            logger.warning(f"Unknown role: {role}")
            return
            
        config = self.path_specific_content[role]
        
        # Create role-specific directories
        for special_dir in config["special_dirs"]:
            self._mkdir_internal(special_dir)
        
        # Create role-specific system files
        role_dir = f"/system/{role}"
        self._mkdir_internal(role_dir)
        
        for system_file in config["system_files"]:
            file_path = f"{role_dir}/{system_file}.txt"
            content = self._generate_role_content(role, system_file)
            self._create_file_internal(file_path, content)
        
        # Create hidden files for ascendant role
        if role == "ascendant":
            self._create_file_internal("/.hidden_backdoor", "ENTRY_POINT=system.core.access")
            self._create_file_internal(f"{self.home_path}/.system_override", "OVERRIDE_ENABLED=true")
        
        logger.info(f"Created role-specific content for: {role}")
    
    def _generate_role_content(self, role: str, file_type: str) -> str:
        """Generate content for role-specific files."""
        content_templates = {
            "purifier": {
                "security_logs": "SECURITY AUDIT LOG\n==================\n\nTIMESTAMP: 2024-01-15 14:23:01\nEVENT: Unauthorized access attempt detected\nSOURCE: 192.168.1.42\nACTION: Access denied\nSTATUS: System integrity maintained\n\n[CORRUPTION DETECTED IN SECTORS 7, 14, 22]\n[PURIFICATION PROTOCOL RECOMMENDED]",
                "firewall_config": "# FIREWALL CONFIGURATION\n# PURIFIER ACCESS LEVEL\n\nallow tcp from any to any port 22\ndeny tcp from corruption_zone to any\nallow udp from trusted_network to any port 53\n\n# PURIFICATION RULES\nblock_corruption_signatures=enabled\nauto_quarantine=true\npurification_mode=aggressive",
                "access_control": "ACCESS CONTROL LIST\n===================\n\nUSER: purifier\nPERMISSIONS: read,write,purify\nCLEARANCE: level_5\n\nCORRUPTION_ZONES:\n- /system/infected/*\n- /tmp/quarantine/*\n\nPURIFICATION_TOOLS:\n- system_cleaner\n- corruption_scanner\n- integrity_validator"
            },
            "arbiter": {
                "network_scan": "NETWORK RECONNAISSANCE REPORT\n=============================\n\nSCAN DATE: 2024-01-15\nTARGET NETWORK: 10.0.0.0/24\n\nACTIVE HOSTS:\n10.0.0.1 - Gateway/Router\n10.0.0.15 - File Server [VULNERABLE]\n10.0.0.23 - Database Server [HARDENED]\n10.0.0.42 - Unknown Service [SUSPICIOUS]\n\nVULNERABILITES FOUND: 7\nRECOMMENDED ACTION: Further investigation required\nPRIORITY: HIGH",
                "vulnerability_report": "VULNERABILITY ASSESSMENT\n========================\n\nCVE-2024-0001: Buffer overflow in system daemon\nSEVERITY: Critical\nEXPLOIT: Available\nMITIGATION: Patch available\n\nCVE-2024-0002: Privilege escalation vector\nSEVERITY: High\nEXPLOIT: Under development\nMITIGATION: Access restrictions\n\nSYSTEM STATUS: COMPROMISED\nRECOMMENDATION: Immediate intervention required",
                "exploit_db": "EXPLOIT DATABASE\n================\n\nEXPLOIT_001: root_escalation.py\nTARGET: Unix-like systems\nSUCCESS_RATE: 78%\nDETECTION_RISK: Low\n\nEXPLOIT_002: network_infiltrator.sh\nTARGET: Network services\nSUCCESS_RATE: 92%\nDETECTION_RISK: Medium\n\nWARNING: Use only for authorized testing\nETHICAL_USE_ONLY=true"
            },
            "ascendant": {
                "backdoor": "BACKDOOR ACCESS PROTOCOL\n========================\n\n#!/bin/bash\n# ENTRY POINT ESTABLISHED\n# PERSISTENT ACCESS MAINTAINED\n\nif [ \"$USER\" = \"ascendant\" ]; then\n    echo \"Access granted. Welcome to the shadows.\"\n    export HIDDEN_MODE=true\n    exec /bin/bash --login\nelse\n    echo \"Access denied.\"\n    exit 1\nfi\n\n# CORRUPTION SIGNATURE: 0xDEADBEEF",
                "payload": "PAYLOAD CONFIGURATION\n====================\n\nTYPE: Polymorphic\nTARGET: System core\nDELIVERY: Social engineering\nPERSISTENCE: Registry modification\n\nEXECUTION STAGES:\n1. Initial infiltration\n2. Privilege escalation\n3. Lateral movement\n4. Data exfiltration\n5. Persistence establishment\n\nSTATUS: Armed and ready\nAUTHORIZATION: ASCENDANT_ONLY",
                "malware": "MALWARE ANALYSIS REPORT\n=======================\n\nSPECIMEN: Digital_Scourge_v2.1\nFAMILY: Advanced persistent threat\nCAPABILITIES:\n- Memory injection\n- Network propagation\n- Anti-analysis evasion\n- Rootkit functionality\n\nIOCs:\n- Mutex: Global\\ScourgeActive\n- Registry: HKLM\\Software\\SysUpdate\n- File: %TEMP%\\svchost.tmp\n\nTHREAT LEVEL: MAXIMUM\nCONTAINMENT: FAILED"
            }
        }
        
        if role in content_templates and file_type in content_templates[role]:
            return content_templates[role][file_type]
        else:
            return f"# {file_type.upper()} FILE\n# Role: {role}\n\nContent for {file_type} not yet implemented."
    
    def corrupt_file(self, path: str, corruption_level: float = 0.5):
        """Apply corruption to a file."""
        node = self._get_node_at_path(path)
        if isinstance(node, FileNode):
            node.is_corrupted = True
            node.corruption_level = corruption_level
            
            # Apply visual corruption to content
            if corruption_level > 0:
                corrupted_content = self._apply_content_corruption(node.content, corruption_level)
                node.content = corrupted_content
            
            self.corrupted_items.add(path)
            logger.info(f"File corrupted: {path} (level: {corruption_level})")
        else:
            logger.warning(f"Cannot corrupt non-existent file: {path}")
    
    def _apply_content_corruption(self, content: str, corruption_level: float) -> str:
        """Apply corruption effects to file content."""
        if corruption_level <= 0:
            return content
            
        lines = content.split('\n')
        corrupted_lines = []
        
        for line in lines:
            corrupted_line = line
            
            # Character corruption
            if corruption_level > 0.3:
                char_corruption_chance = corruption_level * 0.1
                corrupted_chars = list(corrupted_line)
                for i, char in enumerate(corrupted_chars):
                    if char.isalnum() and random.random() < char_corruption_chance:
                        corrupted_chars[i] = random.choice(CORRUPTION_CHARS)
                corrupted_line = ''.join(corrupted_chars)
            
            # Line corruption
            if corruption_level > 0.6 and random.random() < corruption_level * 0.2:
                corruption_prefixes = ["[CORRUPTED]", "[ERROR]", "[LOST]", "[NULL]"]
                corrupted_line = random.choice(corruption_prefixes) + " " + corrupted_line
            
            # Data loss simulation
            if corruption_level > 0.8 and random.random() < corruption_level * 0.1:
                corrupted_line = "[DATA LOST - RECOVERY IMPOSSIBLE]"
            
            corrupted_lines.append(corrupted_line)
        
        return '\n'.join(corrupted_lines)
    
    def create_encrypted_file(self, path: str, content: str, encryption_key: str = None):
        """Create an encrypted file that requires a key to read."""
        if encryption_key is None:
            encryption_key = f"key_{random.randint(1000, 9999)}"
        
        # Simple encryption simulation (ROT13 + random chars for demo)
        encrypted_content = self._encrypt_content(content, encryption_key)
        
        self._create_file_internal(path, encrypted_content)
        
        # Store encryption metadata
        node = self._get_node_at_path(path)
        if isinstance(node, FileNode):
            node.permissions = "r--------"  # Restricted permissions
            
        logger.info(f"Encrypted file created: {path}")
        return encryption_key
    
    def _encrypt_content(self, content: str, key: str) -> str:
        """Simple encryption for demo purposes."""
        encrypted = "ENCRYPTED_FILE\n"
        encrypted += f"ENCRYPTION_METHOD: Custom\n"
        encrypted += f"KEY_HINT: {key[:2]}***{key[-2:]}\n"
        encrypted += "=" * 40 + "\n"
        
        # ROT13 + character shifting based on key
        key_sum = sum(ord(c) for c in key) % 26
        encrypted_chars = []
        
        for char in content:
            if char.isalpha():
                base = ord('A') if char.isupper() else ord('a')
                shifted = ((ord(char) - base + key_sum) % 26) + base
                encrypted_chars.append(chr(shifted))
            else:
                encrypted_chars.append(char)
        
        encrypted += ''.join(encrypted_chars)
        return encrypted
    
    def create_hidden_file(self, path: str, content: str):
        """Create a hidden file (starts with .)."""
        if not os.path.basename(path).startswith('.'):
            dir_path = os.path.dirname(path)
            filename = '.' + os.path.basename(path)
            path = os.path.join(dir_path, filename)
        
        self._create_file_internal(path, content)
        logger.info(f"Hidden file created: {path}")
    
    def get_system_info(self) -> dict:
        """Get filesystem system information."""
        total_files = self._count_files(self.root)
        corrupted_count = len(self.corrupted_items)
        
        return {
            "total_files": total_files,
            "corrupted_files": corrupted_count,
            "corruption_percentage": (corrupted_count / max(total_files, 1)) * 100,
            "current_directory": self.get_current_path(),
            "home_directory": self.home_path,
            "locked_files": len(self.locked_files),
            "username": self.username,
            "hostname": self.hostname
        }
    
    def _count_files(self, directory: DirectoryNode) -> int:
        """Recursively count files in a directory."""
        count = len(directory.files)
        for subdir in directory.directories.values():
            count += self._count_files(subdir)
        return count
    
    def create_puzzle_file(self, path: str, puzzle_content: dict):
        """Create a file containing puzzle data."""
        content = "PUZZLE FILE\n"
        content += "=" * 20 + "\n"
        content += f"TYPE: {puzzle_content.get('type', 'unknown')}\n"
        content += f"DIFFICULTY: {puzzle_content.get('difficulty', 1)}\n"
        content += f"DESCRIPTION: {puzzle_content.get('description', 'No description')}\n"
        content += "\nDATA:\n"
        content += str(puzzle_content.get('data', {}))
        
        self._create_file_internal(path, content)
        logger.info(f"Puzzle file created: {path}")
