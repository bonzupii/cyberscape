class FileSystemHandler:
    def __init__(self, initial_username="hacker"):
        self.username = initial_username
        self.current_path_list = ["~"]  # Initial path
        self.file_system = {
            "~": {  # Home directory
                "documents": {
                    "project_alpha": {
                        "notes.txt": "Project Alpha: Initial thoughts and plans.\n- Secure the mainframe.\n- Bypass firewall.",
                        "source_code.c": "// Placeholder C code\n#include <stdio.h>\nint main() { printf(\"Hello, Alpha!\\n\"); return 0; }"
                    },
                    "personal_journal.txt": "Day 42: The simulation feels more real every day. Or is it?",
                    "work_report.docx": "[DOCX content - not plain text]"
                },
                "downloads": {
                    "tool_v1.2.zip": "[ZIP archive data]",
                    "important_data.csv": "ID,Value1,Value2\n1,100,200\n2,150,250"
                },
                "scripts": {
                    "exploit.py": "print('Executing exploit... Access granted.')",
                    "scan.sh": "#!/bin/bash\necho 'Scanning network...'\nfor i in {1..5}; do echo \"Host 192.168.1.$i found\"; sleep 0.5; done",
                    "backup_script.py": "#!/usr/bin/env python\nprint('backing up files...')"
                },
                "pictures": {
                    "old_photo.jpg": "[JPEG data]"
                },
                ".config": {  # Hidden directory
                    "app_settings.ini": "[Settings]\nresolution=1920x1080\nuser_token=xxxx-xxxx-xxxx"
                },
                "notes.txt": "Remember to check the server logs.\nPasswords might be weak.\nFind the backdoor in /var/www.",
                ".bash_history": "ls -la\ncd scripts\n./exploit.py\ncat ~/notes.txt"
            },
            "root": {
                "bin": {
                    "sh": "[shell binary]",
                    "bash": "[bash binary]",
                    "ls": "[ls binary]",
                    "cat": "[cat binary]"
                },
                "etc": {
                    "passwd": "root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\nhacker:x:1000:1000:Hacker,,,:/home/hacker:/bin/bash",
                    "shadow": "[ACCESS DENIED - Permission Denied]",
                    "hosts": "127.0.0.1 localhost\n::1 localhost"
                },
                "var": {
                    "log": {
                        "auth.log": "May 10 06:00:00 kali sshd[1234]: Accepted publickey for hacker from 10.0.2.2 port 22 ssh2\nMay 10 06:05:17 kali sudo: hacker : TTY=pts/0 ; PWD=/home/hacker ; USER=root ; COMMAND=/usr/bin/apt update",
                        "syslog": "May 10 06:00:00 kali systemd[1]: Starting Daily apt download activities...\nMay 10 06:15:00 kali kernel: [   42.133700] usb 1-1: new high-speed USB device number 2 using xhci_hcd"
                    },
                    "www": {
                        "html": {
                            "index.html": "<html><body><h1>It works!</h1><p>This is the default web page for this server.</p></body></html>"
                        }
                    }
                },
                "tmp": {
                    "tempfile.tmp": "Temporary data..."
                },
                "usr": {
                    "local": {
                        "bin": {
                            "custom_tool": "[custom tool binary]"
                        }
                    }
                }
            }
        }
        self.corrupted_items = set() # Stores tuples of resolved path lists

        # Pre-mark some files as corrupted for demonstration
        # Note: _resolve_path_str_to_list uses self.current_path_list, which is "~" initially.
        # So, these paths are effectively relative to "~" if not absolute.
        initial_corrupted_files = [
            "~/documents/personal_journal.txt",
            "~/scripts/exploit.py",
            "/var/log/auth.log"
        ]
        initial_corrupted_dirs = [
            "~/documents/project_alpha", # Mark this directory as corrupted
            "/" # Mark the root directory as corrupted for testing
        ]

        for item_path_str in initial_corrupted_files:
            resolved_path_list = self._resolve_path_str_to_list(item_path_str)
            node = self._get_node_at_path(resolved_path_list)
            if resolved_path_list and isinstance(node, str): # Files are strings
                self.corrupted_items.add(tuple(resolved_path_list))
            # else:
                # print(f"Warning: Could not mark file '{item_path_str}' as corrupted during init (not a file or not found).") # Keep for debug
 
        for item_path_str in initial_corrupted_dirs:
            resolved_path_list = self._resolve_path_str_to_list(item_path_str)
            node = self._get_node_at_path(resolved_path_list)
            if resolved_path_list and isinstance(node, dict): # Directories are dicts
                self.corrupted_items.add(tuple(resolved_path_list))
            # else:
                # print(f"Warning: Could not mark directory '{item_path_str}' as corrupted during init (not a dir or not found).") # Keep for debug
 
    def get_current_path_str(self):
        """Returns the current path as a string, e.g., '~/documents' or '/var/log'."""
        if self.current_path_list == ["~"]:
            return "~"
        elif self.current_path_list == ["root"]:
            return "/"
        elif self.current_path_list[0] == "~":
            return "~/" + "/".join(self.current_path_list[1:])
        elif self.current_path_list[0] == "root":
            return "/" + "/".join(self.current_path_list[1:])
        return "/".join(self.current_path_list) # Should not happen with current logic

    def get_current_directory_node(self):
        """Returns the actual node (dictionary) of the current directory."""
        return self._get_node_at_path(self.current_path_list)

    def get_node_by_path_str(self, path_str: str):
        """Resolves a string path and returns the node at that path."""
        resolved_path_list = self._resolve_path_str_to_list(path_str)
        return self._get_node_at_path(resolved_path_list)

    def _get_node_at_path(self, path_list):
        """Helper to get the node in file_system dict from a path list."""
        current_node = self.file_system
        try:
            if not path_list:
                return None

            if path_list == ["~"]:
                return current_node["~"]
            elif path_list[0] == "~":
                current_node = current_node["~"]
                for part in path_list[1:]:
                    current_node = current_node[part]
                return current_node
            elif path_list == ["root"]:
                return current_node["root"]
            elif path_list[0] == "root":
                current_node = current_node["root"]
                for part in path_list[1:]:
                    current_node = current_node[part]
                return current_node
            else:
                # This case implies a malformed path_list not starting with '~' or 'root'
                return None
        except (KeyError, TypeError):
            return None

    def _resolve_path_str_to_list(self, path_str):
        """
        Converts a string path into the internal list representation.
        """
        stripped_path = path_str.strip()
        if not stripped_path:
            return list(self.current_path_list) # Return a copy of the current path

        if len(stripped_path) > 1 and stripped_path.endswith('/'):
            stripped_path = stripped_path[:-1]

        if stripped_path == "/":
            return ["root"]
        if stripped_path == "~":
            return ["~"]
        if stripped_path.startswith("/"):
            # For absolute paths like "/foo/bar", components will be ["foo", "bar"]
            # We prepend "root" to make it ["root", "foo", "bar"]
            # If stripped_path is just "/", split("/") gives ['', '']. Filtered gives []. Prepending "root" gives ["root"]. Correct.
            # If stripped_path is "/foo", split("/") gives ['', 'foo']. Filtered gives ['foo']. Prepending "root" gives ["root", "foo"]. Correct.
            # If stripped_path is "/foo/bar", split("/") gives ['', 'foo', 'bar']. Filtered gives ['foo', 'bar']. Prepending "root" gives ["root", "foo", "bar"]. Correct.
            components = [p for p in stripped_path.split('/')[1:] if p] # Skip the first empty component from leading '/' and filter others
            return ["root"] + components
        elif stripped_path.startswith("~/"):
            # For paths like "~/foo/bar", components will be ["foo", "bar"]
            # We prepend "~" to make it ["~", "foo", "bar"]
            components = [p for p in stripped_path[2:].split("/") if p]
            return ["~"] + components
        else:  # Relative path
            components = [p for p in stripped_path.split("/") if p]
            if not components: # e.g. path_str was "." or "" relative to current path
                return list(self.current_path_list) # Return a copy

            # Handle '..' components
            resolved_components = list(self.current_path_list)
            for component in components:
                if component == ".":
                    continue
                elif component == "..":
                    if len(resolved_components) > 1: # Can't go above ~ or root
                        resolved_components.pop()
                    # If at ~ or root, '..' does nothing more to the list path itself
                else:
                    resolved_components.append(component)
            return resolved_components


    def execute_cd(self, target_dir_name):
        """
        Executes the 'cd' command logic.
        Updates self.current_path_list.
        Returns: (bool: success, str: message_or_new_path_str)
        """
        if not target_dir_name:
            target_dir_name = "~"

        potential_path_list = []
        if target_dir_name == "~":
            potential_path_list = ["~"]
        elif target_dir_name == "/":
            potential_path_list = ["root"]
        # ".." is now handled by _resolve_path_str_to_list when it's part of a larger path
        # or as a standalone relative path.
        # Let's ensure "cd .." directly works as expected by resolving it.
        elif target_dir_name == "..":
            if len(self.current_path_list) > 1:
                potential_path_list = self.current_path_list[:-1]
            else: # Already at '~' or 'root'
                potential_path_list = list(self.current_path_list) # No change, but valid
        else:
            potential_path_list = self._resolve_path_str_to_list(target_dir_name)

        if not potential_path_list: # Should not happen if _resolve_path_str_to_list is robust
             return False, f"cd: invalid path resolution for: {target_dir_name}"

        node_at_potential_path = self._get_node_at_path(potential_path_list)

        if node_at_potential_path is None:
            return False, f"cd: no such file or directory: {target_dir_name}"
        elif not isinstance(node_at_potential_path, dict):
            return False, f"cd: not a directory: {target_dir_name}"
        else:
            self.current_path_list = potential_path_list
            return True, self.get_current_path_str()

    def execute_mkdir(self, dir_name):
        """
        Executes the 'mkdir' command logic.
        Returns: (bool: success, str: message)
        """
        if not dir_name:
            return False, "mkdir: missing operand"
        if "/" in dir_name or "\\" in dir_name or ".." in dir_name or "." == dir_name : # Basic validation
            return False, f"mkdir: invalid directory name: {dir_name}"

        # Resolve path to parent directory where new dir will be created
        # For mkdir, dir_name is relative to current_path_list
        parent_dir_node = self._get_node_at_path(self.current_path_list)

        if not isinstance(parent_dir_node, dict):
            # This implies current_path_list is somehow pointing to a file, which shouldn't happen.
            return False, f"mkdir: error accessing current directory structure."

        if dir_name in parent_dir_node:
            return False, f"mkdir: cannot create directory ‘{dir_name}’: File exists"
        else:
            parent_dir_node[dir_name] = {}
            return True, f"Directory '{dir_name}' created." # Optional success message

    def execute_touch(self, file_name):
        """
        Executes the 'touch' command logic.
        Returns: (bool: success, str: message)
        """
        if not file_name:
            return False, "touch: missing file operand"
        if "/" in file_name or "\\" in file_name or ".." in file_name or "." == file_name: # Basic validation
            return False, f"touch: invalid file name: {file_name}"

        parent_dir_node = self._get_node_at_path(self.current_path_list)

        if not isinstance(parent_dir_node, dict):
            return False, "touch: error accessing current directory structure."

        if file_name in parent_dir_node and isinstance(parent_dir_node[file_name], dict):
            return False, f"touch: cannot touch ‘{file_name}’: Is a directory"
        else:  # Create or update (just create/overwrite with empty string for now)
            parent_dir_node[file_name] = "" # Mark as empty file content
            return True, f"File '{file_name}' touched." # Optional

    def list_items(self, path_str="."):
        """
        Lists items in the specified directory path string.
        Returns a list of item names (strings), or None if path is invalid.
        Appends '/' to directory names.
        """
        target_path_list = self._resolve_path_str_to_list(path_str)
        dir_node = self._get_node_at_path(target_path_list)

        if isinstance(dir_node, dict):
            items = []
            for name, value in sorted(dir_node.items()):
                if isinstance(value, dict): # Directory
                    items.append(name + "/")
                else: # File
                    items.append(name)
            return items
        return None

    def get_item_content(self, item_path_str):
        """
        Gets the content of a file.
        Returns content string or None if not a file or not found.
        """
        target_path_list = self._resolve_path_str_to_list(item_path_str)
        item_node = self._get_node_at_path(target_path_list)

        if item_node is not None and isinstance(item_node, str):
            return item_node
        elif isinstance(item_node, dict):
            return None # It's a directory
        return None # Not found or other type

    def get_corrupted_file_count_in_dir(self, dir_path_str):
        """Counts the number of corrupted files directly within the given directory path."""
        dir_path_list = self._resolve_path_str_to_list(dir_path_str)
        dir_node = self._get_node_at_path(dir_path_list)

        if not isinstance(dir_node, dict):
            return 0 # Not a directory or doesn't exist

        corrupted_count = 0
        for item_name, item_value in dir_node.items():
            if isinstance(item_value, str): # It's a file
                # Construct the full path list for this item to check against self.corrupted_items
                item_full_path_list = dir_path_list + [item_name]
                if tuple(item_full_path_list) in self.corrupted_items:
                    corrupted_count += 1
        return corrupted_count

    def mark_item_corrupted(self, item_path_str, corrupted_status=True):
        """Marks or unmarks an item as corrupted."""
        resolved_path_list = self._resolve_path_str_to_list(item_path_str)
        if not resolved_path_list:
            return False, f"Cannot mark corruption: Invalid path '{item_path_str}'"

        node = self._get_node_at_path(resolved_path_list)
        if node is None:
            return False, f"Cannot mark corruption: Item '{item_path_str}' not found."
        # Allow marking both files (str) and directories (dict) as corrupted
        # if isinstance(node, dict):
        #     return False, f"Cannot mark corruption: Item '{item_path_str}' is a directory." # Old check, removing

        path_tuple = tuple(resolved_path_list)
        if corrupted_status:
            self.corrupted_items.add(path_tuple)
            return True, f"Item '{item_path_str}' marked as corrupted."
        else:
            if path_tuple in self.corrupted_items:
                self.corrupted_items.remove(path_tuple)
            return True, f"Item '{item_path_str}' unmarked as corrupted."

    def is_item_corrupted(self, item_path_str):
        """Checks if an item is marked as corrupted."""
        resolved_path_list = self._resolve_path_str_to_list(item_path_str)
        if not resolved_path_list:
            return False
        return tuple(resolved_path_list) in self.corrupted_items

    def remove_item(self, item_path_str, recursive=False):
        """
        Removes a file or directory.
        Returns: (bool: success, str: message)
        """
        if not item_path_str: # Handles empty string
            return False, "rm: missing operand"
        
        # Check for invalid targets like ".", "..", "/", "~" directly based on user input string
        # before resolving, as resolving "." or ".." might change them relative to current path.
        if item_path_str == "." or item_path_str == "..":
            return False, f"rm: cannot remove '{item_path_str}': Invalid argument"
        if item_path_str == "/" or item_path_str == "~":
             return False, f"rm: cannot remove '{item_path_str}': Operation not permitted"


        target_path_list = self._resolve_path_str_to_list(item_path_str)
        
        # After resolution, check if the path points to something that shouldn't be removed
        # (e.g. if item_path_str was complex but resolved to ~ or /)
        if not target_path_list : # Should be caught by initial check if item_path_str is empty
            return False, f"rm: invalid path resolution for: {item_path_str}"

        if target_path_list == ["~"] or target_path_list == ["root"]:
            # This catches cases where item_path_str might be like "~/." or "/."
            # which resolve to ["~"] or ["root"] respectively.
            return False, f"rm: cannot remove '{item_path_str}' (resolved to root or home): Operation not permitted"
        
        # Ensure there's an item name to remove (path list shouldn't be just ["~"] or ["root"] at this point)
        if len(target_path_list) <= 1:
             return False, f"rm: invalid path for removal: {item_path_str}"


        item_name = target_path_list[-1]
        parent_path_list = target_path_list[:-1]

        if not parent_path_list: # Should not happen if we prevent removing ~ or root
            return False, f"rm: cannot determine parent directory for '{item_path_str}'"

        parent_node = self._get_node_at_path(parent_path_list)

        if not isinstance(parent_node, dict):
            return False, f"rm: cannot access parent path for '{item_path_str}'"
        
        if item_name not in parent_node:
            return False, f"rm: cannot remove '{item_path_str}': No such file or directory"

        item_to_remove = parent_node[item_name]

        if isinstance(item_to_remove, dict): # It's a directory
            if not recursive and item_to_remove: # Directory is not empty and not recursive
                return False, f"rm: cannot remove '{item_path_str}': Directory not empty (use -r for recursive)"
            # If recursive or empty, proceed to delete
            del parent_node[item_name]
            return True, f"Removed '{item_path_str}'"
        else: # It's a file
            del parent_node[item_name]
            # Also remove from corrupted_items if it was there
            path_tuple_to_check = tuple(target_path_list)
            if path_tuple_to_check in self.corrupted_items:
                self.corrupted_items.remove(path_tuple_to_check)
            return True, f"Removed '{item_path_str}'"

    def move_item(self, src_path_str, dest_path_str):
        """
        Moves or renames a file or directory.
        Returns: (bool: success, str: message)
        """
        if not src_path_str or not dest_path_str:
            return False, "mv: missing source or destination operand"

        src_path_list = self._resolve_path_str_to_list(src_path_str)
        if not src_path_list or len(src_path_list) <=1: # Cannot move ~ or root
            if src_path_list == ["~"] or src_path_list == ["root"]:
                return False, f"mv: cannot move '{src_path_str}': Operation not permitted"
            return False, f"mv: invalid source path: {src_path_str}"
        
        src_item_name = src_path_list[-1]
        src_parent_path_list = src_path_list[:-1]
        src_parent_node = self._get_node_at_path(src_parent_path_list)

        if not isinstance(src_parent_node, dict) or src_item_name not in src_parent_node:
            return False, f"mv: cannot stat '{src_path_str}': No such file or directory"
        
        item_to_move = src_parent_node[src_item_name]

        # Resolve destination
        dest_path_list = self._resolve_path_str_to_list(dest_path_str)
        if not dest_path_list:
             return False, f"mv: invalid destination path: {dest_path_str}"

        dest_item_name = dest_path_list[-1]
        dest_parent_path_list = dest_path_list[:-1]

        # Special case: if dest_path_str ends with '/' or is an existing directory,
        # the intention is to move src_item_name *into* dest_path_list.
        # The _resolve_path_str_to_list might have stripped the trailing slash.
        # We need to check if the original dest_path_str pointed to an existing directory.
        
        potential_dest_dir_node = self._get_node_at_path(dest_path_list)
        
        final_dest_parent_node = None
        final_dest_item_name = ""

        if potential_dest_dir_node is not None and isinstance(potential_dest_dir_node, dict):
            # Case 1: Destination is an existing directory. Move source into it.
            final_dest_parent_node = potential_dest_dir_node
            final_dest_item_name = src_item_name # Item keeps its original name inside the new directory
        else:
            # Case 2: Destination is a new name (or overwrite file) in an existing directory.
            # The parent of the destination must exist.
            if not dest_parent_path_list: # e.g. trying to mv to ~/newfile, parent is ~
                 # This can happen if dest_path_list was like ['~', 'newfile'] -> parent is ['~']
                 # Or ['root', 'newfile'] -> parent is ['root']
                 # Or ['~'] if dest_path_str was just "newfile" and current path is /
                 # This needs careful handling. If dest_parent_path_list is empty, it implies
                 # the destination is in the root of the filesystem structure ('~' or 'root').
                 # This should be okay if dest_path_list correctly identified the target parent.
                 # Let's assume _resolve_path_str_to_list correctly forms dest_path_list.
                 # If dest_path_list is ['~', 'file'], parent is ['~'].
                 # If dest_path_list is ['file'] (relative to current path), then dest_parent_path_list
                 # will be the current path.
                 # This block might be redundant if _get_node_at_path(dest_parent_path_list) handles it.
                 pass


            final_dest_parent_node = self._get_node_at_path(dest_parent_path_list)
            final_dest_item_name = dest_item_name
        
        if not isinstance(final_dest_parent_node, dict):
            return False, f"mv: target '{dest_path_str}' is not a directory or its parent path is invalid"

        # Check for overwriting
        if final_dest_item_name in final_dest_parent_node:
            existing_dest_item = final_dest_parent_node[final_dest_item_name]
            # Prevent overwriting directory with file and vice-versa
            if isinstance(item_to_move, dict) and not isinstance(existing_dest_item, dict): # Moving dir onto file
                return False, f"mv: cannot overwrite non-directory '{final_dest_item_name}' with directory '{src_item_name}'"
            if not isinstance(item_to_move, dict) and isinstance(existing_dest_item, dict): # Moving file onto dir
                return False, f"mv: cannot overwrite directory '{final_dest_item_name}' with non-directory '{src_item_name}'"
            # Allow overwriting file with file.
            # Prevent overwriting non-empty directory with directory.
            if isinstance(item_to_move, dict) and isinstance(existing_dest_item, dict) and existing_dest_item: # Both are dirs, dest is non-empty
                 return False, f"mv: cannot overwrite non-empty directory '{final_dest_item_name}'"
            # If both are dirs and dest is empty, overwrite is allowed.
            # If both are files, overwrite is allowed.


        # Perform the move
        final_dest_parent_node[final_dest_item_name] = item_to_move
        
        # Delete from source, only if not moving to itself (renaming in same directory)
        if not (src_parent_node is final_dest_parent_node and src_item_name == final_dest_item_name):
            # Check if source was corrupted before deleting
            src_path_tuple = tuple(src_path_list)
            was_corrupted = src_path_tuple in self.corrupted_items
            
            del src_parent_node[src_item_name]
            if was_corrupted:
                self.corrupted_items.remove(src_path_tuple)
                # Determine the actual final path of the moved item for corruption tracking
                # `potential_dest_dir_node` was captured *before* the item was placed at the destination.
                # `dest_path_list` is the resolved path of `dest_path_str`.
                # `src_item_name` is the original name of the item being moved.
                actual_final_path_list_for_corruption = []
                if potential_dest_dir_node is not None and isinstance(potential_dest_dir_node, dict):
                    # Case 1: Destination (dest_path_list) was an existing directory.
                    # The item (src_item_name) is moved into it.
                    actual_final_path_list_for_corruption = dest_path_list + [src_item_name]
                else:
                    # Case 2: Destination was a new name (file or directory).
                    # The final path of the item is dest_path_list.
                    actual_final_path_list_for_corruption = dest_path_list
                
                if actual_final_path_list_for_corruption: # Ensure path is valid before adding
                    self.corrupted_items.add(tuple(actual_final_path_list_for_corruption))

            
        return True, f"Moved '{src_path_str}' to '{dest_path_str}'"