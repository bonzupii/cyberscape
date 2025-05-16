import shlex
from typing import List, Optional, Tuple, Callable, Dict, Any
from game_state import STATE_MSFCONSOLE, STATE_PUZZLE_ACTIVE # Import state constants

# Forward declarations to avoid circular imports if needed later
# class GameStateManager: pass
# class FileSystemHandler: pass
# class Terminal: pass

class CompletionHandler:
    """Handles context-aware tab autocompletion."""

    def __init__(self, game_state_manager, file_system_handler, command_configs):
        """
        Initializes the CompletionHandler.

        Args:
            game_state_manager: An instance of GameStateManager.
            file_system_handler: An instance of FileSystemHandler.
            command_configs: A dictionary containing command configurations
                             (e.g., {'main': MAIN_COMMAND_HANDLERS, 'msf': MSF_COMMAND_HANDLERS}).
        """
        self.game_state_manager = game_state_manager
        self.file_system_handler = file_system_handler
        self.command_configs = command_configs
        # Potential cache for completions if needed for performance
        self._completion_cache: Dict[str, List[str]] = {}
        self._last_input_line: str = ""
        self._last_suggestions: List[str] = []
        self._suggestion_index: int = -1

    def get_suggestions(self, input_line: str, cursor_pos: int) -> Tuple[List[str], Optional[str]]:
        """
        Gets completion suggestions based on the current input line and cursor position.

        Args:
            input_line: The current text in the input buffer.
            cursor_pos: The current position of the cursor.

        Returns:
            A tuple containing:
            - A list of suggestion strings.
            - A string representing the common prefix of all suggestions, if any.
        """
        # Basic parsing - might need refinement based on context
        try:
            # Use shlex to handle quotes, but only parse up to the cursor
            # This is tricky, as shlex expects complete tokens.
            # A simpler approach for now: split by space.
            # TODO: Improve parsing for robustness (e.g., handle quoted paths)
            text_before_cursor = input_line[:cursor_pos]
            parts = text_before_cursor.split()
            current_word = ""
            if text_before_cursor.endswith(" ") or not parts:
                 is_completing_command = len(parts) == 0
                 is_completing_argument = len(parts) > 0
            else:
                 current_word = parts[-1]
                 is_completing_command = len(parts) == 1
                 is_completing_argument = len(parts) > 1


            command_context = self._get_command_context()

            if is_completing_command:
                suggestions = self._suggest_commands(current_word, command_context)
            elif is_completing_argument:
                command = parts[0]
                suggestions = self._suggest_arguments(command, current_word, parts, command_context)
            else: # Should not happen with current logic, but default to empty
                 suggestions = []

            # Calculate common prefix
            common_prefix = self._find_common_prefix(suggestions) if suggestions else None

            # Store for cycling through suggestions
            self._last_suggestions = sorted(suggestions) # Always update with current suggestions
            if input_line != self._last_input_line:
                self._last_input_line = input_line
                self._suggestion_index = -1 # Reset index if input line fundamentally changed
            # If input line is same, _suggestion_index is preserved for cycling.

            return self._last_suggestions, common_prefix

        except Exception as e:
            # Log error appropriately in a real scenario
            print(f"Error during completion suggestion: {e}")
            return [], None

    def cycle_suggestion(self) -> Optional[str]:
         """Cycles through the last generated suggestions."""
         if not self._last_suggestions:
             return None

         self._suggestion_index = (self._suggestion_index + 1) % len(self._last_suggestions)
         return self._last_suggestions[self._suggestion_index]


    def _get_command_context(self) -> str:
        """Determines the current command context (e.g., 'main', 'msf')."""
        # Example: Check game state
        current_state = self.game_state_manager.get_state()
        if current_state == STATE_MSFCONSOLE: # Use imported constant
            return 'msf'
        elif current_state == STATE_PUZZLE_ACTIVE: # Use imported constant
            return 'puzzle' # Or a more specific context key if needed
        else:
            return 'main' # Default to main terminal

    def _suggest_commands(self, prefix: str, context: str) -> List[str]:
        """Suggests commands based on the prefix and context."""
        available_commands = self.command_configs.get(context, {}).keys()
        return [cmd for cmd in available_commands if cmd.startswith(prefix)]

    def _suggest_arguments(self, command: str, prefix: str, all_parts: List[str], context: str) -> List[str]:
        """Suggests arguments for a given command based on the prefix."""
        # --- File/Directory Completion ---
        file_op_commands = {'cd', 'ls', 'cat', 'rm', 'mv', 'touch', 'mkdir', 'scan', 'parse', 'restore', 'edit', 'patch', 'compile', 'decrypt'} # Add more as needed
        if command in file_op_commands:
            # Determine the path prefix being typed
            path_prefix = prefix
            base_dir = self.file_system_handler.get_current_directory_node()

            # Handle relative paths potentially starting from parent directories
            if '/' in prefix:
                 dir_part, file_part = prefix.rsplit('/', 1)
                 # Use the new public method that accepts a string path
                 target_dir_node = self.file_system_handler.get_node_by_path_str(dir_part)
                 if target_dir_node and isinstance(target_dir_node, dict):
                      base_dir = target_dir_node # Update base directory for suggestion
                      path_prefix = file_part # Suggest based on the part after the last '/'
                 else:
                      return [] # Invalid directory part
            else:
                 target_dir_node = base_dir # Suggest from current directory

            suggestions = []
            if isinstance(target_dir_node, dict):
                for item_name, item_value in target_dir_node.items():
                    if item_name.startswith(path_prefix):
                        # Add '/' suffix to directories for easier navigation
                        suffix = "/" if isinstance(item_value, dict) else ""
                        # Reconstruct full path suggestion if needed (relative to original prefix)
                        if '/' in prefix:
                             suggestions.append(f"{dir_part}/{item_name}{suffix}")
                        else:
                             suggestions.append(f"{item_name}{suffix}")
            return suggestions


        # --- Specific Command Argument Completion ---
        if command == 'theme' and context == 'main':
            # Assuming themes are defined elsewhere, e.g., in effects.py
            # This needs access to the actual theme names
            # Placeholder: Replace with actual theme loading
            available_themes = ['default', 'corrupted_kali', 'digital_nightmare', 'amber', 'green'] # Example themes
            return [th for th in available_themes if th.startswith(prefix)]

        if command == 'help' and context == 'main':
             # Suggest other commands
             return self._suggest_commands(prefix, context)

        if command == 'help' and context == 'msf':
             # Suggest MSF commands or topics
             msf_commands = self.command_configs.get('msf', {}).keys()
             # Add specific help topics if defined
             help_topics = ['search', 'use', 'info', 'set', 'run', 'back', 'exit', 'help', 'clear']
             combined = list(msf_commands) + help_topics
             return sorted(list(set(cmd for cmd in combined if cmd.startswith(prefix))))


        if command == 'use' and context == 'msf':
            # Placeholder: Needs logic to get available modules/exploits
            # This might involve querying a specific part of the game state or config
            available_modules = ['exploit/example_exploit', 'auxiliary/scanner/example_scan'] # Example
            return [mod for mod in available_modules if mod.startswith(prefix)]

        # Add more command-specific argument suggestions here...
        # e.g., 'kill' could suggest process IDs from game_state_manager
        # e.g., 'start_puzzle' could suggest puzzle IDs from puzzle_manager

        return [] # Default to no suggestions for unknown arguments

    def _find_common_prefix(self, suggestions: List[str]) -> Optional[str]:
        """Finds the longest common starting prefix among a list of strings."""
        if not suggestions:
            return None
        if len(suggestions) == 1:
             # If only one suggestion, the prefix is the suggestion itself
             # unless it's a directory, then keep the prefix before the last '/'
             s = suggestions[0]
             if s.endswith('/'):
                  return s # Return the full directory path with '/'
             else:
                  # For files or commands, return the full suggestion
                  # This might need adjustment based on desired behavior
                  return s


        shortest = min(suggestions, key=len)
        for i, char in enumerate(shortest):
            for other in suggestions:
                if other[i] != char:
                    # If the common prefix ends exactly at a '/', return it including '/'
                    if i > 0 and shortest[i-1] == '/':
                         return shortest[:i]
                    # Otherwise, return the prefix up to the differing character
                    # If the prefix contains '/', return up to the last '/'
                    prefix_candidate = shortest[:i]
                    # if not prefix_candidate: # If the common prefix is empty, it's just ""
                    #     return None # Reverting this: "" is preferred over None if suggestions were not empty
                    if '/' in prefix_candidate:
                         return prefix_candidate.rsplit('/', 1)[0] + '/'
                    else:
                         return prefix_candidate # Return common part for commands/files in root, or ""

        # If all suggestions are identical up to the length of the shortest one
        # Check if the shortest is a directory path
        if shortest.endswith('/'):
             return shortest
        else:
             # If it's potentially a file or command, return the common prefix
             # If '/' is present, return up to the last '/' to suggest directory contents
             if '/' in shortest:
                  prefix_candidate = shortest.rsplit('/', 1)[0] + '/'
                  return prefix_candidate # shortest ensures prefix_candidate won't be empty if shortest wasn't
             else:
                  return shortest # All suggestions are identical or start the same way