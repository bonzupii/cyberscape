from typing import List, Optional, Tuple, Dict
import logging
from .state import STATE_MSFCONSOLE, STATE_PUZZLE_ACTIVE, STATE_MAIN_TERMINAL
import os
import re
import random

logger = logging.getLogger(__name__)

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
        self._last_input_line = ""
        self._last_suggestions = []
        self._suggestion_index = 0
        self._last_cursor_pos = 0
        self._terminal = None # Store terminal instance for interaction
        self._cache_timeout = 5.0  # Cache timeout in seconds
        self._last_cache_update = 0.0
        
        # Command categories for better organization
        self.command_categories = {
            'file_ops': {'ls', 'cd', 'cat', 'mkdir', 'touch', 'rm', 'write', 'scan', 'parse', 'restore'},
            'system_ops': {'status', 'processes', 'kill', 'clear', 'history'},
            'network_ops': {'ping', 'traceroute', 'netstat', 'ifconfig'},
            'security_ops': {'firewall', 'scan', 'patch', 'decrypt'},
            'utility_ops': {'grep', 'find', 'diff', 'sort', 'uniq'},
            'theme_ops': {'theme', 'color', 'style'},
            'help_ops': {'help', 'man', 'info'}
        }

        # Offline responses for testing/development
        self.offline_responses = {
            "help": "Available commands: ls, cd, cat, mkdir, touch, rm, write, theme",
            "ls": "file1.txt\nfile2.txt\ndocuments/\ntools/",
            "cat /root/README.txt": "Welcome to the system.",
            "cat ~/documents/personal_journal.txt": "Day 1: The system seems different today..."
        }

    def set_terminal(self, terminal):
        """Sets the terminal instance for the completion handler."""
        self._terminal = terminal
        self.offline_mode = True  # Default to offline mode

    def reset_suggestion_index(self):
        """Reset the suggestion index for a new completion."""
        self._suggestion_index = 0

    def get_suggestions(self, input_line: str, cursor_pos: int) -> Tuple[List[str], Optional[str]]:
        """Get suggestions for the current input at cursor position."""
        self._last_input_line = input_line
        self._last_cursor_pos = cursor_pos
        
        # Check if corruption should affect suggestions
        corruption_level = self.game_state_manager.get_corruption_level()
        if corruption_level > 0.75:  # High corruption
            # 20% chance to return corrupted suggestions
            if random.random() < 0.2:
                return self._get_corrupted_suggestions(input_line)
        
        # Split input into command and arguments
        parts = input_line[:cursor_pos].split()
        if not parts:
            return self._get_all_commands(), None
        
        command = parts[0]
        current_word = parts[-1] if len(parts) > 1 else ""
        
        # Get current context
        context = self._get_command_context()
        
        # Handle file path completion
        if command in self.command_categories['file_ops']:
            suggestions, prefix = self._suggest_file_path(current_word, command)
            if corruption_level > 0.5:  # Medium corruption
                suggestions = self._corrupt_suggestions(suggestions, corruption_level)
            return suggestions, prefix
        
        # Handle command completion
        if len(parts) == 1:
            suggestions, prefix = self._suggest_command(current_word, context)
            if corruption_level > 0.5:  # Medium corruption
                suggestions = self._corrupt_suggestions(suggestions, corruption_level)
            return suggestions, prefix
        
        # Handle argument completion
        suggestions, prefix = self._suggest_arguments(command, current_word, parts, context)
        if corruption_level > 0.5:  # Medium corruption
            suggestions = self._corrupt_suggestions(suggestions, corruption_level)
        return suggestions, prefix

    def _suggest_file_path(self, current_word: str, command: str) -> Tuple[List[str], Optional[str]]:
        """Suggest file paths based on current word and command."""
        # Handle special cases
        if current_word == "/":
            return ["/"], "/"
        if current_word == "./":
            return ["./"], "./"
        if current_word == "~":
            return ["~/"], "~/"
        
        # Handle home directory expansion
        if current_word.startswith("~/"):
            current_word = os.path.expanduser(current_word)
        
        # Split path into directory and name parts
        parts = current_word.split("/")
        if len(parts) == 1:
            dir_node = self.file_system_handler.get_current_directory_node()
            name_prefix = parts[0]
            path_base = ""
        else:
            dir_path = "/".join(parts[:-1])
            name_prefix = parts[-1]
            dir_node = self.file_system_handler.get_node_by_path_str(dir_path)
            path_base = dir_path + "/" if dir_path else ""
        
        if not dir_node or dir_node.get("type") != "directory":
            return [], None
        
        # Get matching items with type filtering
        suggestions = []
        for item_name, item_data in dir_node["content"].items():
            if item_name.startswith(name_prefix):
                # Filter based on command type
                if command in ['cd', 'ls'] and item_data.get("type") == "directory":
                    suggestions.append(item_name + "/")
                elif command in ['cat', 'rm', 'write', 'scan', 'parse', 'restore'] and item_data.get("type") == "file":
                    suggestions.append(item_name)
                elif command == 'mkdir':
                    # For mkdir, only suggest directories that don't exist
                    if not item_data.get("type"):
                        suggestions.append(item_name + "/")
                else:
                    # For other commands, suggest both files and directories
                    if item_data.get("type") == "directory":
                        suggestions.append(item_name + "/")
                    else:
                        suggestions.append(item_name)
        
        # Sort suggestions
        suggestions.sort()
        
        # Find common prefix
        common_prefix = None
        if suggestions:
            common_prefix = os.path.commonprefix(suggestions)
            if common_prefix and common_prefix != name_prefix:
                return [], path_base + common_prefix
        
        return [path_base + s for s in suggestions], None

    def _suggest_command(self, prefix: str, context: str) -> Tuple[List[str], Optional[str]]:
        """Suggest commands based on prefix and context."""
        # Get available commands for current context
        available_commands = set()
        for category, commands in self.command_categories.items():
            if self._is_category_available(category, context):
                available_commands.update(commands)
        
        # Add context-specific commands
        context_commands = self.command_configs.get(context, {}).keys()
        available_commands.update(context_commands)
        
        # Filter and sort suggestions
        suggestions = [cmd for cmd in available_commands if cmd.startswith(prefix)]
        suggestions.sort()
        
        if suggestions:
            common_prefix = os.path.commonprefix(suggestions)
            if common_prefix and common_prefix != prefix:
                return [], common_prefix
        
        return suggestions, None

    def _is_category_available(self, category: str, context: str) -> bool:
        """Check if a command category is available in the current context."""
        # Get role and corruption level
        role = self.game_state_manager.get_role()
        corruption_level = self.game_state_manager.get_corruption_level()
        
        # Check role-based restrictions
        if role == "purifier":
            available_categories = {'file_ops', 'system_ops', 'network_ops', 'security_ops', 'utility_ops', 'theme_ops', 'help_ops'}
        elif role == "ascendant":
            available_categories = {'file_ops', 'system_ops', 'network_ops', 'security_ops', 'utility_ops', 'theme_ops', 'help_ops'}
        elif role == "arbiter":
            available_categories = {'file_ops', 'system_ops', 'network_ops', 'utility_ops', 'theme_ops', 'help_ops'}
        else:
            available_categories = set()
        
        # Check context restrictions
        if context == STATE_MSFCONSOLE:
            available_categories &= {'security_ops', 'network_ops'}
        elif context == STATE_PUZZLE_ACTIVE:
            available_categories &= {'file_ops', 'utility_ops', 'help_ops'}
        
        # Corruption can affect category availability
        if corruption_level > 0.75:  # High corruption
            # 10% chance to block a category
            if random.random() < 0.1:
                return False
        
        return category in available_categories

    def _suggest_arguments(self, command: str, prefix: str, all_parts: List[str], context: str) -> Tuple[List[str], Optional[str]]:
        """Suggest arguments for a given command based on the prefix."""
        # Get command handler for current context
        command_handler = self.command_configs.get(context, {}).get(command)
        if not command_handler:
            return [], None
            
        # Handle specific command argument suggestions
        if command == "theme":
            return self._suggest_themes(prefix)
        elif command == "kill":
            return self._suggest_process_names(prefix)
        elif command in ["ping", "ssh", "telnet"]:
            return self._suggest_hostnames(prefix)
            
        return [], None

    def _suggest_process_names(self, prefix: str) -> List[str]:
        """Suggest process names for system commands."""
        # This would typically come from the game state
        processes = ["system", "network", "security", "monitor", "backup"]
        return [p for p in processes if p.startswith(prefix)]

    def _suggest_hostnames(self, prefix: str) -> List[str]:
        """Suggest hostnames for network commands."""
        # This would typically come from the game state
        hosts = ["localhost", "gateway", "dns", "mail", "web"]
        return [h for h in hosts if h.startswith(prefix)]

    def _suggest_themes(self, prefix: str) -> List[str]:
        """Suggest theme names for theme commands."""
        if not self._terminal:
            return []
        return [t for t in self._terminal.theme_manager.get_available_themes() if t.startswith(prefix)]

    def _get_all_commands(self) -> List[str]:
        """Get all available commands for the current context."""
        context = self._get_command_context()
        return self._suggest_command("", context)[0]

    def _get_command_context(self) -> str:
        """Determines the current command context."""
        current_state = self.game_state_manager.get_state()
        if current_state == STATE_MSFCONSOLE:
            return 'msf'
        elif current_state == STATE_PUZZLE_ACTIVE:
            return 'puzzle'
        else:
            return 'main'

    def cycle_suggestion(self) -> Optional[str]:
        """Cycle through the last set of suggestions."""
        if not self._last_suggestions:
            return None
        
        suggestion = self._last_suggestions[self._suggestion_index]
        self._suggestion_index = (self._suggestion_index + 1) % len(self._last_suggestions)
        return suggestion

    def _get_offline_response(self, command: str) -> str:
        """Get a response for testing/development when offline."""
        command_norm = command.strip()
        if command_norm in self.offline_responses:
            return self.offline_responses[command_norm]
        
        base_command = command_norm.split()[0] if command_norm else ""
        return self.offline_responses.get(base_command, "Command not recognized in offline mode.")

    def process_command(self, command: str) -> str:
        """
        Processes a command and returns a simulated or actual response.
        """
        logging.debug(f"Processing command: {command}")
        if self.offline_mode:
            return self._get_offline_response(command)
        else:
            # Implement actual LLM API call here when online mode is enabled
            return "LLM API call not implemented yet.  Using offline mode."

    def toggle_offline_mode(self):
        """Toggles between offline and online modes."""
        self.offline_mode = not self.offline_mode
        mode_str = "offline" if self.offline_mode else "online"
        logging.debug(f"Toggling offline mode to: {mode_str}")
        return f"Completion handler switched to {mode_str} mode."

    def reset_completion_state(self):
        """Reset all completion state variables."""
        self._last_input_line = ""
        self._last_suggestions = []
        self._suggestion_index = 0
        self._last_cursor_pos = 0
        self._completion_cache.clear()
        self._last_cache_update = 0.0

    def _get_corrupted_suggestions(self, input_line: str) -> Tuple[List[str], Optional[str]]:
        """Generate corrupted suggestions based on the Scourge's influence."""
        corrupted_suggestions = [
            "DIE",
            "FUCK",
            "SHIT",
            "KILL",
            "DESTROY",
            "CORRUPT",
            "INFECT",
            "CONSUME",
            "BURN",
            "SCREAM"
        ]
        
        # Add some corrupted file paths
        corrupted_paths = [
            "/corrupted/",
            "/infected/",
            "/scourge/",
            "/voss/",
            "/aether/",
            "/digital_hell/"
        ]
        
        # Add some corrupted commands
        corrupted_commands = [
            "corrupt",
            "infect",
            "scourge",
            "voss",
            "aether",
            "digital_hell"
        ]
        
        # Combine all corrupted suggestions
        all_corrupted = corrupted_suggestions + corrupted_paths + corrupted_commands
        
        # Filter based on input
        if input_line:
            filtered = [s for s in all_corrupted if s.lower().startswith(input_line.lower())]
            if filtered:
                return filtered, None
        
        return all_corrupted, None

    def _corrupt_suggestions(self, suggestions: List[str], corruption_level: float) -> List[str]:
        """Apply corruption effects to suggestions based on corruption level."""
        if not suggestions:
            return suggestions
        
        corrupted = []
        for suggestion in suggestions:
            # Higher corruption means more aggressive corruption
            if corruption_level > 0.9:  # Extreme corruption
                if random.random() < 0.3:  # 30% chance to completely corrupt
                    corrupted.append(random.choice([
                        "FUCK",
                        "DIE",
                        "SHIT",
                        "KILL",
                        "DESTROY"
                    ]))
                else:
                    corrupted.append(self._corrupt_text(suggestion, corruption_level))
            elif corruption_level > 0.75:  # High corruption
                if random.random() < 0.2:  # 20% chance to corrupt
                    corrupted.append(self._corrupt_text(suggestion, corruption_level))
                else:
                    corrupted.append(suggestion)
            elif corruption_level > 0.5:  # Medium corruption
                if random.random() < 0.1:  # 10% chance to corrupt
                    corrupted.append(self._corrupt_text(suggestion, corruption_level))
                else:
                    corrupted.append(suggestion)
            else:
                corrupted.append(suggestion)
        
        return corrupted

    def _corrupt_text(self, text: str, corruption_level: float) -> str:
        """Corrupt text based on corruption level."""
        if not text:
            return text
        
        # Define corruption characters
        corruption_chars = "█▒▓§Æ"
        
        # Calculate corruption amount
        corruption_amount = int(len(text) * corruption_level * 0.5)
        
        # Convert to list for manipulation
        chars = list(text)
        
        # Apply corruption
        for _ in range(corruption_amount):
            if chars:
                pos = random.randint(0, len(chars) - 1)
                chars[pos] = random.choice(corruption_chars)
        
        return ''.join(chars)
