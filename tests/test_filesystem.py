"""
Comprehensive tests for the new FileSystemHandler implementation.
"""

import pytest
from unittest.mock import patch
from src.core.filesystem import FileSystemHandler, DirectoryNode, FileNode


class TestNewFileSystemHandler:
    """Test cases for the new FileSystemHandler implementation."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.fs = FileSystemHandler()
    
    def test_initialization(self):
        """Test filesystem initialization."""
        assert self.fs.username == "hacker"
        assert self.fs.hostname == "system"
        assert self.fs.home_path == "/home/hacker"
        assert self.fs.get_current_path_str() == "/home/hacker"
        assert isinstance(self.fs.root, DirectoryNode)
        assert isinstance(self.fs.current_directory, DirectoryNode)
    
    def test_initial_filesystem_structure(self):
        """Test that the initial filesystem structure is created correctly."""
        # Check root directories exist
        root_items = self.fs.list_items("/")
        root_names = [name for name, _ in root_items]
        
        expected_dirs = ["bin", "etc", "var", "home", "tmp", "system"]
        for expected_dir in expected_dirs:
            assert expected_dir in root_names
        
        # Check home directory exists
        home_items = self.fs.list_items("/home")
        home_names = [name for name, _ in home_items]
        assert "hacker" in home_names
        
        # Check user home directory structure
        user_home_items = self.fs.list_items("/home/hacker")
        user_home_names = [name for name, _ in user_home_items]
        assert "documents" in user_home_names
        assert "tools" in user_home_names
        assert "welcome.txt" in user_home_names
    
    def test_path_resolution_absolute(self):
        """Test absolute path resolution."""
        # Test root path
        assert self.fs._resolve_path("/") == "/"
        
        # Test simple absolute path
        assert self.fs._resolve_path("/bin") == "/bin"
        
        # Test nested absolute path
        assert self.fs._resolve_path("/home/hacker/documents") == "/home/hacker/documents"
        
        # Test path with . and ..
        assert self.fs._resolve_path("/home/hacker/../hacker") == "/home/hacker"
        assert self.fs._resolve_path("/home/hacker/.") == "/home/hacker"
    
    def test_path_resolution_relative(self):
        """Test relative path resolution."""
        # Start in home directory
        assert self.fs.get_current_path_str() == "/home/hacker"
        
        # Test relative paths
        assert self.fs._resolve_path("documents") == "/home/hacker/documents"
        assert self.fs._resolve_path("./documents") == "/home/hacker/documents"
        assert self.fs._resolve_path("../other") == "/home/other"
        assert self.fs._resolve_path("..") == "/home"
        
        # Change directory and test again
        self.fs.execute_cd("/bin")
        assert self.fs._resolve_path("../etc") == "/etc"
        assert self.fs._resolve_path(".") == "/bin"
    
    def test_path_resolution_home(self):
        """Test home directory path resolution."""
        # Test home shortcut
        assert self.fs._resolve_path("~") == "/home/hacker"
        assert self.fs._resolve_path("~/documents") == "/home/hacker/documents"
        assert self.fs._resolve_path("~/documents/file.txt") == "/home/hacker/documents/file.txt"
        
        # Test from different directory
        self.fs.execute_cd("/")
        assert self.fs._resolve_path("~") == "/home/hacker"
        assert self.fs._resolve_path("~/tools") == "/home/hacker/tools"
    
    def test_get_node_at_path(self):
        """Test node retrieval at various paths."""
        # Test root
        root_node = self.fs._get_node_at_path("/")
        assert isinstance(root_node, DirectoryNode)
        assert root_node == self.fs.root
        
        # Test directory
        bin_node = self.fs._get_node_at_path("/bin")
        assert isinstance(bin_node, DirectoryNode)
        assert bin_node.name == "bin"
        
        # Test file
        readme_node = self.fs._get_node_at_path("/README.txt")
        assert isinstance(readme_node, FileNode)
        assert readme_node.name == "README.txt"
        
        # Test non-existent path
        nonexistent = self.fs._get_node_at_path("/nonexistent")
        assert nonexistent is None
        
        # Test trying to traverse through a file
        invalid = self.fs._get_node_at_path("/README.txt/invalid")
        assert invalid is None
    
    def test_current_path_list_property(self):
        """Test the current_path_list property for backward compatibility."""
        # Test root
        self.fs.current_directory = self.fs.root
        assert self.fs.current_path_list == []
        
        # Test home directory
        self.fs._change_to_home()
        assert self.fs.current_path_list == ["~"]
        
        # Test regular directory
        self.fs.execute_cd("/bin")
        assert self.fs.current_path_list == ["bin"]
        
        # Test nested directory
        self.fs.execute_cd("/home/hacker/documents")
        assert self.fs.current_path_list == ["home", "hacker", "documents"]
    
    def test_current_path_list_setter(self):
        """Test setting current path via the list property."""
        # Set to root
        self.fs.current_path_list = []
        assert self.fs.current_directory == self.fs.root
        
        # Set to home
        self.fs.current_path_list = ["~"]
        assert self.fs.get_current_path_str() == "/home/hacker"
        
        # Set to specific path
        self.fs.current_path_list = ["bin"]
        assert self.fs.get_current_path_str() == "/bin"
    
    def test_execute_cd_success(self):
        """Test successful directory changes."""
        # Test absolute path
        success, message = self.fs.execute_cd("/bin")
        assert success is True
        assert "Changed directory to /bin" in message
        assert self.fs.get_current_path_str() == "/bin"
        
        # Test relative path
        success, message = self.fs.execute_cd("../etc")
        assert success is True
        assert self.fs.get_current_path_str() == "/etc"
        
        # Test home directory
        success, message = self.fs.execute_cd("~")
        assert success is True
        assert self.fs.get_current_path_str() == "/home/hacker"
        
        # Test current and parent directory
        success, message = self.fs.execute_cd("documents")
        assert success is True
        assert self.fs.get_current_path_str() == "/home/hacker/documents"
        
        success, message = self.fs.execute_cd("..")
        assert success is True
        assert self.fs.get_current_path_str() == "/home/hacker"
    
    def test_execute_cd_failure(self):
        """Test cd command failure cases."""
        # Test missing operand
        success, message = self.fs.execute_cd("")
        assert success is False
        assert "missing directory operand" in message
        
        # Test non-existent directory
        success, message = self.fs.execute_cd("/nonexistent")
        assert success is False
        assert "no such directory" in message
        
        # Test trying to cd to a file
        success, message = self.fs.execute_cd("/README.txt")
        assert success is False
        assert "no such directory" in message
    
    def test_list_items_directories(self):
        """Test listing directory contents."""
        # Test root directory
        items = self.fs.list_items("/")
        assert isinstance(items, list)
        
        # Check that directories and files are properly categorized
        item_dict = {name: item_type for name, item_type in items}
        assert item_dict["bin"] == "directory"
        assert item_dict["etc"] == "directory"
        assert item_dict["README.txt"] == "file"
        
        # Test empty directory
        self.fs.execute_mkdir("/empty_test")
        empty_items = self.fs.list_items("/empty_test")
        assert empty_items == []
        
        # Test non-existent directory
        invalid_items = self.fs.list_items("/nonexistent")
        assert invalid_items == []
        
        # Test current directory (None parameter)
        self.fs.execute_cd("/home/hacker")
        current_items = self.fs.list_items(None)
        current_names = [name for name, _ in current_items]
        assert "documents" in current_names
        assert "tools" in current_names
    
    def test_write_and_read_files(self):
        """Test file creation and reading."""
        # Test creating a new file
        success, message = self.fs.write_file_content("/test_file.txt", "Hello, World!")
        assert success is True
        assert "Successfully wrote to /test_file.txt" in message
        
        # Test reading the file
        content = self.fs.get_item_content("/test_file.txt")
        assert content == "Hello, World!"
        
        # Test overwriting existing file
        success, message = self.fs.write_file_content("/test_file.txt", "Updated content")
        assert success is True
        
        content = self.fs.get_item_content("/test_file.txt")
        assert content == "Updated content"
        
        # Test creating file in subdirectory
        success, message = self.fs.write_file_content("/home/hacker/documents/note.txt", "My note")
        assert success is True
        
        content = self.fs.get_item_content("/home/hacker/documents/note.txt")
        assert content == "My note"
    
    def test_write_file_errors(self):
        """Test file writing error cases."""
        # Test empty path
        success, message = self.fs.write_file_content("", "content")
        assert success is False
        assert "missing file operand" in message
        
        # Test writing to root
        success, message = self.fs.write_file_content("/", "content")
        assert success is False
        assert "cannot write to root directory" in message
        
        # Test writing to non-existent parent directory
        success, message = self.fs.write_file_content("/nonexistent/file.txt", "content")
        assert success is False
        assert "parent directory does not exist" in message
    
    def test_get_item_content_errors(self):
        """Test file reading error cases."""
        # Test non-existent file
        content = self.fs.get_item_content("/nonexistent.txt")
        assert content is None
        
        # Test trying to read a directory
        content = self.fs.get_item_content("/bin")
        assert content is None
        
        # Test invalid path
        content = self.fs.get_item_content("/nonexistent/file.txt")
        assert content is None
    
    def test_execute_mkdir(self):
        """Test directory creation."""
        # Test creating a new directory
        success, message = self.fs.execute_mkdir("/new_directory")
        assert success is True
        assert "Successfully created directory /new_directory" in message
        
        # Verify directory was created
        items = self.fs.list_items("/")
        item_names = [name for name, _ in items]
        assert "new_directory" in item_names
        
        # Test creating nested directory
        success, message = self.fs.execute_mkdir("/new_directory/subdirectory")
        assert success is True
        
        # Verify nested directory
        nested_items = self.fs.list_items("/new_directory")
        nested_names = [name for name, _ in nested_items]
        assert "subdirectory" in nested_names
        
        # Test relative path
        self.fs.execute_cd("/home/hacker")
        success, message = self.fs.execute_mkdir("new_folder")
        assert success is True
        assert self.fs.get_item_content("/home/hacker/new_folder") is None  # Directory, not file
        
        user_items = self.fs.list_items("/home/hacker")
        user_names = [name for name, _ in user_items]
        assert "new_folder" in user_names
    
    def test_execute_mkdir_errors(self):
        """Test mkdir error cases."""
        # Test empty path
        success, message = self.fs.execute_mkdir("")
        assert success is False
        assert "missing directory operand" in message
        
        # Test creating root
        success, message = self.fs.execute_mkdir("/")
        assert success is False
        assert "cannot create root directory" in message
        
        # Test directory already exists
        success, message = self.fs.execute_mkdir("/bin")
        assert success is False
        assert "directory already exists" in message
        
        # Test file with same name exists
        self.fs.write_file_content("/test_conflict.txt", "content")
        success, message = self.fs.execute_mkdir("/test_conflict.txt")
        assert success is False
        assert "directory already exists" in message
        
        # Test parent doesn't exist
        success, message = self.fs.execute_mkdir("/nonexistent/newdir")
        assert success is False
        assert "parent directory does not exist" in message
    
    def test_remove_files(self):
        """Test file removal."""
        # Create a test file
        self.fs.write_file_content("/test_remove.txt", "to be removed")
        assert self.fs.get_item_content("/test_remove.txt") == "to be removed"
        
        # Remove the file
        success, message = self.fs.remove_item("/test_remove.txt")
        assert success is True
        assert "Successfully removed /test_remove.txt" in message
        
        # Verify file is gone
        content = self.fs.get_item_content("/test_remove.txt")
        assert content is None
        
        # Remove from list
        items = self.fs.list_items("/")
        item_names = [name for name, _ in items]
        assert "test_remove.txt" not in item_names
    
    def test_remove_directories(self):
        """Test directory removal."""
        # Create a test directory
        self.fs.execute_mkdir("/test_remove_dir")
        
        # Remove empty directory
        success, message = self.fs.remove_item("/test_remove_dir")
        assert success is True
        assert "Successfully removed /test_remove_dir" in message
        
        # Verify directory is gone
        items = self.fs.list_items("/")
        item_names = [name for name, _ in items]
        assert "test_remove_dir" not in item_names
    
    def test_remove_non_empty_directory(self):
        """Test removing non-empty directory."""
        # Create directory with content
        self.fs.execute_mkdir("/test_non_empty")
        self.fs.write_file_content("/test_non_empty/file.txt", "content")
        
        # Try to remove without recursive flag
        success, message = self.fs.remove_item("/test_non_empty")
        assert success is False
        assert "Directory not empty" in message
        
        # Remove with recursive flag
        success, message = self.fs.remove_item("/test_non_empty", recursive=True)
        assert success is True
        
        # Verify directory is gone
        items = self.fs.list_items("/")
        item_names = [name for name, _ in items]
        assert "test_non_empty" not in item_names
    
    def test_remove_errors(self):
        """Test remove error cases."""
        # Test empty path
        success, message = self.fs.remove_item("")
        assert success is False
        assert "missing operand" in message
        
        # Test removing root
        success, message = self.fs.remove_item("/")
        assert success is False
        assert "cannot remove root directory" in message
        
        # Test removing home directory
        success, message = self.fs.remove_item("/home/hacker")
        assert success is False
        assert "cannot remove home directory" in message
        
        # Test removing non-existent item
        success, message = self.fs.remove_item("/nonexistent")
        assert success is False
        assert "No such file or directory" in message
    
    def test_file_corruption(self):
        """Test file corruption functionality."""
        # Create a corrupted file
        success, message = self.fs.write_file_content("/corrupted.txt", "original content", corrupted=True)
        assert success is True
        
        # Read the corrupted file
        content = self.fs.get_item_content("/corrupted.txt")
        assert content != "original content"  # Should be corrupted
        assert len(content) == len("original content")  # Length preserved
        
        # Check that corruption is tracked
        assert "/corrupted.txt" in self.fs.corrupted_items
    
    def test_corruption_function(self):
        """Test the corruption function directly."""
        original = "This is a test file with some content."
        
        # Test with specific corruption level
        with patch('random.randint', return_value=0), patch('random.choice', return_value='X'):
            corrupted = self.fs._corrupt_content(original, 0.2)
            # Should have some X characters
            assert 'X' in corrupted
            assert len(corrupted) == len(original)
        
        # Test with zero corruption
        no_corruption = self.fs._corrupt_content(original, 0.0)
        assert no_corruption == original
    
    def test_state_persistence(self):
        """Test getting and restoring filesystem state."""
        # Make some changes to the filesystem
        self.fs.execute_mkdir("/state_test")
        self.fs.write_file_content("/state_test/file1.txt", "content1")
        self.fs.write_file_content("/state_test/corrupted.txt", "corrupted content", corrupted=True)
        self.fs.execute_cd("/state_test")
        
        # Get state
        state = self.fs.get_state()
        assert isinstance(state, dict)
        assert "root" in state
        assert "current_path" in state
        assert "corrupted_items" in state
        assert state["current_path"] == "/state_test"
        assert "/state_test/corrupted.txt" in state["corrupted_items"]
        
        # Create a new filesystem and restore state
        new_fs = FileSystemHandler()
        new_fs.restore_state(state)
        
        # Verify state was restored
        assert new_fs.get_current_path_str() == "/state_test"
        assert new_fs.get_item_content("/state_test/file1.txt") == "content1"
        assert "/state_test/corrupted.txt" in new_fs.corrupted_items
        
        # Check that corrupted file is still corrupted
        corrupted_content = new_fs.get_item_content("/state_test/corrupted.txt")
        assert corrupted_content != "corrupted content"
    
    def test_set_role(self):
        """Test role-based filesystem modifications."""
        # Test setting purifier role
        self.fs.set_role("purifier")
        
        # Check that role-specific directories were created
        items = self.fs.list_items("/")
        item_names = [name for name, _ in items]
        assert "secure" in item_names
        assert "audit" in item_names
        assert "backup" in item_names
        
        # Check that role-specific files were created
        secure_items = self.fs.list_items("/secure")
        secure_names = [name for name, _ in secure_items]
        assert any("security_logs" in name for name in secure_names)
        
        # Test setting different role
        self.fs.set_role("ascendant")
        
        items = self.fs.list_items("/")
        item_names = [name for name, _ in items]
        assert "hidden" in item_names
        assert "backdoors" in item_names
        assert "malware" in item_names
    
    def test_cleanup(self):
        """Test filesystem cleanup."""
        # Add some corrupted items and locked files
        self.fs.corrupted_items.add("/test/path")
        self.fs.locked_files.add("/locked/file")
        
        # Call cleanup
        self.fs.cleanup()
        
        # Verify cleanup
        assert len(self.fs.corrupted_items) == 0
        assert len(self.fs.locked_files) == 0
    
    def test_edge_cases(self):
        """Test various edge cases."""
        # Test very long paths
        long_path = "/a" * 100
        success, _ = self.fs.execute_mkdir(long_path)
        # Should handle gracefully (may succeed or fail depending on implementation)
        
        # Test special characters in filenames
        success, _ = self.fs.write_file_content("/special-file_name.txt", "content")
        assert success is True
        
        content = self.fs.get_item_content("/special-file_name.txt")
        assert content == "content"
        
        # Test empty file content
        success, _ = self.fs.write_file_content("/empty.txt", "")
        assert success is True
        
        content = self.fs.get_item_content("/empty.txt")
        assert content == ""
    
    def test_permissions_tracking(self):
        """Test that file and directory permissions are tracked."""
        # Check default permissions
        self.fs.write_file_content("/test_perms.txt", "content")
        file_node = self.fs._get_node_at_path("/test_perms.txt")
        assert isinstance(file_node, FileNode)
        assert file_node.permissions == "rw-r--r--"
        
        self.fs.execute_mkdir("/test_perms_dir")
        dir_node = self.fs._get_node_at_path("/test_perms_dir")
        assert isinstance(dir_node, DirectoryNode)
        assert dir_node.permissions == "rwxr-xr-x"
    
    def test_timestamps(self):
        """Test that timestamps are tracked and updated."""
        # Create a file and check timestamps
        self.fs.write_file_content("/timestamp_test.txt", "original")
        file_node = self.fs._get_node_at_path("/timestamp_test.txt")
        
        assert isinstance(file_node, FileNode)
        original_created = file_node.created_at
        original_modified = file_node.modified_at
        
        # Update the file and check that modified time changes
        import time
        time.sleep(0.01)  # Small delay to ensure timestamp difference
        
        self.fs.write_file_content("/timestamp_test.txt", "updated")
        updated_file_node = self.fs._get_node_at_path("/timestamp_test.txt")
        
        assert updated_file_node.created_at == original_created  # Created time unchanged
        assert updated_file_node.modified_at > original_modified  # Modified time updated


class TestFileNode:
    """Test cases for FileNode class."""
    
    def test_file_node_creation(self):
        """Test FileNode creation and basic properties."""
        file_node = FileNode("test.txt", "test content")
        
        assert file_node.name == "test.txt"
        assert file_node.content == "test content"
        assert file_node.size == len("test content")
        assert file_node.is_corrupted is False
        assert file_node.corruption_level == 0.0
        assert file_node.permissions == "rw-r--r--"
        assert isinstance(file_node.created_at, type(file_node.modified_at))
    
    def test_file_node_serialization(self):
        """Test FileNode to_dict and from_dict methods."""
        file_node = FileNode("test.txt", "test content", is_corrupted=True, corruption_level=0.3)
        
        # Test to_dict
        file_dict = file_node.to_dict()
        assert isinstance(file_dict, dict)
        assert file_dict["name"] == "test.txt"
        assert file_dict["content"] == "test content"
        assert file_dict["is_corrupted"] is True
        assert file_dict["corruption_level"] == 0.3
        
        # Test from_dict
        restored_node = FileNode.from_dict(file_dict)
        assert restored_node.name == file_node.name
        assert restored_node.content == file_node.content
        assert restored_node.is_corrupted == file_node.is_corrupted
        assert restored_node.corruption_level == file_node.corruption_level


class TestDirectoryNode:
    """Test cases for DirectoryNode class."""
    
    def test_directory_node_creation(self):
        """Test DirectoryNode creation and basic properties."""
        dir_node = DirectoryNode("testdir")
        
        assert dir_node.name == "testdir"
        assert dir_node.permissions == "rwxr-xr-x"
        assert isinstance(dir_node.files, dict)
        assert isinstance(dir_node.directories, dict)
        assert len(dir_node.files) == 0
        assert len(dir_node.directories) == 0
        assert dir_node.parent is None
    
    def test_directory_node_with_parent(self):
        """Test DirectoryNode creation with parent relationship."""
        parent_node = DirectoryNode("parent")
        child_node = DirectoryNode("child", parent=parent_node)
        
        assert child_node.parent == parent_node
        assert child_node.name == "child"
    
    def test_directory_node_serialization(self):
        """Test DirectoryNode to_dict and from_dict methods."""
        dir_node = DirectoryNode("testdir")
        
        # Add some content
        dir_node.files["test.txt"] = FileNode("test.txt", "content")
        dir_node.directories["subdir"] = DirectoryNode("subdir", parent=dir_node)
        
        # Test to_dict
        dir_dict = dir_node.to_dict()
        assert isinstance(dir_dict, dict)
        assert dir_dict["name"] == "testdir"
        assert "files" in dir_dict
        assert "directories" in dir_dict
        assert "test.txt" in dir_dict["files"]
        assert "subdir" in dir_dict["directories"]
        
        # Test from_dict
        restored_node = DirectoryNode.from_dict(dir_dict)
        assert restored_node.name == dir_node.name
        assert "test.txt" in restored_node.files
        assert "subdir" in restored_node.directories
        assert isinstance(restored_node.files["test.txt"], FileNode)
        assert isinstance(restored_node.directories["subdir"], DirectoryNode)
        assert restored_node.directories["subdir"].parent == restored_node
