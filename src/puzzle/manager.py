"""Puzzle manager for Cyberscape: Digital Dread.

This module manages game puzzles, including:
- Puzzle state tracking
- Puzzle validation
- Hint system
- Progress tracking
"""

import logging
import os
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

# Updated import for LLM handler (relative import)
from ..core.llm import LLMHandler

logger = logging.getLogger(__name__)

@dataclass
class PuzzleState:
    """Represents the state of a puzzle."""
    puzzle_id: str
    is_active: bool = False
    is_completed: bool = False
    progress: float = 0.0
    hints_used: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    attempts: int = 0
    is_corrupted: bool = False
    corruption_level: float = 0.0

    def __post_init__(self):
        if self.hints_used is None:
            self.hints_used = []
        if self.start_time is None:
            self.start_time = datetime.now()

    def to_dict(self) -> dict:
        return {
            "puzzle_id": self.puzzle_id,
            "is_active": self.is_active,
            "is_completed": self.is_completed,
            "progress": self.progress,
            "hints_used": self.hints_used,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "completion_time": self.completion_time.isoformat() if self.completion_time else None,
            "attempts": self.attempts,
            "is_corrupted": self.is_corrupted,
            "corruption_level": self.corruption_level
        }

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            puzzle_id=d["puzzle_id"],
            is_active=d["is_active"],
            is_completed=d["is_completed"],
            progress=d["progress"],
            hints_used=d["hints_used"],
            start_time=datetime.fromisoformat(d["start_time"]) if d["start_time"] else None,
            completion_time=datetime.fromisoformat(d["completion_time"]) if d["completion_time"] else None,
            attempts=d["attempts"],
            is_corrupted=d.get("is_corrupted", False),
            corruption_level=d.get("corruption_level", 0.0)
        )

class Puzzle:
    """
    Base class for all puzzles in the game.
    """
    def __init__(self, puzzle_id: str, name: str, description: str, manager, difficulty: int = 1):
        self.puzzle_id = puzzle_id
        self.name = name
        self.description = description
        self.manager = manager # Store the manager instance
        self.difficulty = difficulty
        self.solved = False
        self.attempts = 0
        # --- AI GENERATED: Add missing attributes for compatibility ---
        self.is_corrupted: bool = False
        self.corruption_level: float = 0.0
        self.hints: list = []
        self.rewards: list = []
        # ------------------------------------------------------------

    def get_display_text(self) -> str:
        """
        Returns the text to display to the player when presenting the puzzle.
        This should be overridden by subclasses.
        """
        return f"{self.name}\n\n{self.description}"

    def attempt_solution(self, player_input: str, terminal) -> Tuple[bool, str]:
        """
        Processes the player's attempt to solve the puzzle.
        Returns a tuple: (is_solved, feedback_message).
        This must be overridden by subclasses.
        """
        self.attempts += 1
        # Default implementation, should be overridden
        return False, "Solution attempt logic not implemented for this puzzle type."

    def on_solve(self, terminal) -> str:
        """
        Called when the puzzle is successfully solved.
        Returns a message to display to the player.
        """
        self.solved = True
        logging.debug(f"Puzzle '{self.name}' solved!")

        # Trigger corruption effect on the last line
        if terminal and hasattr(terminal, 'effect_manager'):
            terminal.effect_manager.start_character_corruption_effect(line_index=-1, duration_ms=750, intensity=0.3)
            # Trigger audio glitch effect
            terminal.effect_manager.start_audio_glitch_effect(duration_ms=300, glitch_type="distortion", intensity=0.3)

        return f"Puzzle '{self.name}' solved!"

    def get_hint(self) -> str:
        """
        Provides a hint for the puzzle.
        This can be overridden by subclasses.
        """
        return "No hints available for this puzzle."

class AlgorithmPuzzle(Puzzle):
    """
    Base class for algorithm-based puzzles.
    """
    def __init__(self, puzzle_id: str, name: str, description: str, manager, difficulty: int = 1):
        super().__init__(puzzle_id, name, description, manager, difficulty)
        self.category = "Algorithm"

class SequenceCompletionPuzzle(AlgorithmPuzzle):
    """
    A puzzle where the player must complete a sequence of numbers or characters.
    Example: 2, 4, 6, 8, ?
    """
    def __init__(self, puzzle_id: str, name: str, description: str, manager,
                 sequence_prompt: List[Any], solution: List[Any],
                 difficulty: int = 1):
        super().__init__(puzzle_id, name, description, manager, difficulty)
        self.sequence_prompt = sequence_prompt # e.g., [2, 4, "6", 8, "?"] or "A B C ?"
        self.solution = solution # e.g., [10] or ["D"]

    def get_display_text(self) -> str:
        prompt_str = " ".join(map(str, self.sequence_prompt))
        return f"{self.name}\n\n{self.description}\n\nSequence: {prompt_str}"

    def attempt_solution(self, player_input: str, terminal) -> Tuple[bool, str]:
        self.attempts += 1
        # Assuming player_input is a string, potentially comma-separated for multiple values
        try:
            # Convert player input to the same type as solution elements for comparison
            # This is a simple approach; more robust parsing might be needed.
            if isinstance(self.solution[0], int):
                attempted_values = [int(x.strip()) for x in player_input.split(',')]
            elif isinstance(self.solution[0], float):
                attempted_values = [float(x.strip()) for x in player_input.split(',')]
            else: # Assume string
                attempted_values = [x.strip() for x in player_input.split(',')]

            if attempted_values == self.solution:
                self.solved = True
                logging.debug(f"Sequence puzzle '{self.name}' solved!")
                return True, self.on_solve(terminal)
            else:
                return False, "Incorrect sequence. Try again."
        except ValueError:
            return False, "Invalid input format. Please provide the correct type of value(s)."
        except Exception:
            return False, "Error processing your input. Please check the format."

class CryptographicPuzzle(Puzzle):
    """
    Base class for cryptographic puzzles.
    """
    def __init__(self, puzzle_id: str, name: str, description: str, manager, difficulty: int = 1):
        super().__init__(puzzle_id, name, description, manager, difficulty)
        self.category = "Cryptographic"

class CaesarCipherPuzzle(CryptographicPuzzle):
    """
    A puzzle where the player must decrypt a Caesar cipher.
    """
    def __init__(self, puzzle_id: str, name: str, description: str, manager,
                 ciphertext: str, shift: int, difficulty: int = 1):
        super().__init__(puzzle_id, name, description, manager, difficulty)
        self.ciphertext = ciphertext
        self.shift = shift
        self.plaintext = self._decrypt(ciphertext, shift)

    def _decrypt(self, ciphertext: str, shift: int) -> str:
        result = []
        for char in ciphertext:
            if 'a' <= char <= 'z':
                s = ord(char) - shift
                if s < ord('a'):
                    s += 26
                result.append(chr(s))
            elif 'A' <= char <= 'Z':
                s = ord(char) - shift
                if s < ord('A'):
                    s += 26
                result.append(chr(s))
            else:
                result.append(char)
        return "".join(result)

    def get_display_text(self) -> str:
        return f"{self.name}\n\n{self.description}\n\nCiphertext: {self.ciphertext}"

    def attempt_solution(self, player_input: str, terminal) -> Tuple[bool, str]:
        self.attempts += 1
        if player_input.strip().lower() == self.plaintext.lower():
            self.solved = True
            # Use the passed terminal or manager's terminal if needed for output
            return True, self.on_solve(terminal)
        else:
            # Use the passed terminal or manager's terminal if needed for output
            return False, "Incorrect decryption. Try again."

    def get_hint(self) -> str:
        if self.difficulty <= 2:\
            return f"Hint: It's a type of substitution cipher. The shift is {self.shift}."
        return "Hint: It's a type of substitution cipher."

class FileManipulationPuzzle(Puzzle):
    """
    A puzzle where the player must find information in one file to unlock another.
    """
    def __init__(self, puzzle_id: str, name: str, description: str, manager,
                 target_file: str, required_content: str, success_message: str,
                 difficulty: int = 1):
        super().__init__(puzzle_id, name, description, manager, difficulty)
        self.category = "File Manipulation"
        self.target_file = target_file # Path to the file the player needs to interact with
        self.required_content = required_content # The specific string the player needs to find/input
        self.success_message = success_message # Message upon successful completion

    def get_display_text(self) -> str:
        return f"{self.name}\n\n{self.description}\n\nYour task is to find the key information and provide it here."

    def attempt_solution(self, player_input: str, terminal=None) -> Tuple[bool, str]:
        self.attempts += 1
        # Check if terminal and fs_handler are available
        if terminal is None or not hasattr(terminal, 'fs_handler'):
            return False, "Error: File system access unavailable for this puzzle."

        # In a more complex version, this could involve checking file content directly
        # via the file_system_handler, but for this puzzle type, the player
        # is expected to find the info and type it in.
        if terminal is None or not hasattr(terminal, 'fs_handler'):
            return False, "Error: Terminal instance not available."

        file_content = terminal.fs_handler.get_item_content(self.target_file)
        if file_content is None:
            return False, f"Error: Could not read file '{self.target_file}'."

        # Check if the player's input matches the required content
        if file_content.strip() == self.required_content:
            self.solved = True
            logging.debug(f"File manipulation puzzle '{self.name}' solved!")
            return True, self.on_solve(terminal)
        else:
            return False, "Incorrect input. The key information is not what you provided."

    def on_solve(self, terminal) -> str:
        self.solved = True
        # Use the passed terminal or manager\'s terminal if needed for output
        return f"Puzzle \'{self.name}\' solved!\\n{self.success_message}"

    def get_hint(self) -> str:
        if self.difficulty <= 2:
            return f"Hint: Look for clues in the file '{self.target_file}'."
        return "Hint: Examine the files in the system for relevant information."

class CodeAnalysisPuzzle(Puzzle):
   """
   A puzzle where the player must analyze code in a file and provide a specific piece of information.
   """
   def __init__(self, puzzle_id: str, name: str, description: str, manager,
                 target_file: str, required_info: str, success_message: str,
                 difficulty: int = 1):
       super().__init__(puzzle_id, name, description, manager, difficulty)
       self.category = "Code Analysis"
       self.success_message = success_message
       self.target_file = target_file  # Path to the file containing the code
       self.required_info = required_info  # The specific information the player needs to find
       self.success_message = success_message

   def get_display_text(self) -> str:
       return f"{self.name}\n\n{self.description}\n\nAnalyze the code in '{self.target_file}' and provide the required information."

   def attempt_solution(self, player_input: str, terminal) -> Tuple[bool, str]:
       self.attempts += 1
       if terminal is None or not hasattr(terminal, 'fs_handler'):
           return False, "Error: File system access unavailable for this puzzle."

       file_content = terminal.fs_handler.get_item_content(self.target_file)
       if file_content is None:
           return False, f"Error: Could not read file '{self.target_file}'."

       if player_input.strip() == self.required_info:
           self.solved = True
           logging.debug(f"Code analysis puzzle '{self.name}' solved!")
           return True, self.on_solve(terminal)
       else:
           return False, "Incorrect information provided. Please analyze the file and try again."

   def on_solve(self, terminal) -> str:
       self.solved = True
       # If this puzzle needed to print something to the terminal on solve,
       # it would use terminal.add_line(...) or self.manager._terminal.add_line(...)
       # Using the passed terminal for consistency with base class
       return f"Puzzle \'{self.name}\' solved!\\n{self.success_message}"

   def get_hint(self) -> str:
       return f"Hint: Focus on the key functionalities and variables within the code in '{self.target_file}'."


class ConfigFilePuzzle(Puzzle):
    """
    A puzzle that requires reading a config file and checking for a specific key phrase.
    """
    def __init__(self, puzzle_id: str, name: str, description: str, manager,
                 config_file_path: str, key_phrase: str, success_message: str,
                 difficulty: int = 1):
        super().__init__(puzzle_id, name, description, manager, difficulty)
        self.config_file_path = config_file_path
        self.key_phrase = key_phrase
        self.success_message = success_message
        self.key_phrase = key_phrase
        self.success_message = success_message

    def get_display_text(self) -> str:
        return f"{self.name}\n\n{self.description}\n\nCheck the config file for the key phrase."

    def attempt_solution(self, player_input: str, terminal=None) -> Tuple[bool, str]:
        self.attempts += 1
        if terminal is None or not hasattr(terminal, 'fs_handler'):
            return False, "Error: File system access unavailable for this puzzle."

        # Construct the full path to the config file
        full_path = os.path.expanduser(self.config_file_path)

        try:
            with open(full_path, 'r') as file:
                file_content = file.read()
        except FileNotFoundError:
            return False, f"Error: Could not find file '{self.config_file_path}'."
        except Exception as e:
            return False, f"Error reading file '{self.config_file_path}': {e}"

        if self.key_phrase in file_content:
            self.solved = True
            logging.debug(f"Config file puzzle '{self.name}' solved!")
            return True, self.on_solve(terminal)
        else:
            return False, "Incorrect. The key phrase was not found in the config file."

    def on_solve(self, terminal) -> str:
         self.solved = True
         # If this puzzle needed to print something to the terminal on solve,
         # it would use terminal.add_line(...) or self.manager._terminal.add_line(...)
         # Using the passed terminal for consistency with base class
         return f"Puzzle \'{self.name}\' solved!\\n{self.success_message}"

    def get_hint(self) -> str:
        return f"Hint: The key phrase is hidden within the \'{self.config_file_path}\' file."

class NetworkPuzzle(Puzzle):
    """
    A puzzle where the player must navigate a network topology to find a path.
    """
    def __init__(self, puzzle_id: str, name: str, description: str, manager,
                 network_map: Dict[str, List[str]], start_node: str, target_node: str,
                 success_message: str, difficulty: int = 1):
        super().__init__(puzzle_id, name, description, manager, difficulty)
        self.category = "Network"
        self.network_map = network_map
        self.start_node = start_node
        self.target_node = target_node
        self.success_message = success_message # Ensure success_message is initialized
        self.current_path = []

    def get_display_text(self) -> str:
        network_str = "\nNetwork Topology:\n"
        for node, connections in self.network_map.items():
            network_str += f"{node} -> {', '.join(connections)}\n"
        return f"{self.name}\n\n{self.description}\n{network_str}\nFind a path from {self.start_node} to {self.target_node}."

    def attempt_solution(self, player_input: str, terminal) -> Tuple[bool, str]:
        self.attempts += 1
        path = [node.strip() for node in player_input.split("->")]

        # Validate path
        if not path or path[0] != self.start_node or path[-1] != self.target_node: # Added check for empty path
            return False, "Path must start and end at the specified nodes."

        # Check if each step is valid
        for i in range(len(path) - 1):
            current = path[i]
            next_node = path[i + 1]
            if next_node not in self.network_map.get(current, []):
                return False, f"Invalid connection: {current} -> {next_node}"

        self.solved = True
        return True, self.on_solve(terminal)

    def on_solve(self, terminal) -> str:
        self.solved = True
        return f"Puzzle '{self.name}' solved!\n{self.success_message}"

class BinaryAnalysisPuzzle(Puzzle):
    """
    A puzzle where the player must analyze binary data to find patterns or extract information.
    """
    def __init__(self, puzzle_id: str, name: str, description: str, manager,
                 binary_data: str, pattern: str, success_message: str,
                 difficulty: int = 1):
        super().__init__(puzzle_id, name, description, manager, difficulty)
        self.category = "Binary Analysis"
        self.binary_data = binary_data
        self.pattern = pattern
        self.success_message = success_message # Ensure success_message is initialized

    def get_display_text(self) -> str:
        return f"{self.name}\n\n{self.description}\n\nBinary Data:\n{self.binary_data}"

    def attempt_solution(self, player_input: str, terminal) -> Tuple[bool, str]:
        self.attempts += 1
        if player_input.strip() == self.pattern:
            self.solved = True
            return True, self.on_solve(terminal)
        return False, "Incorrect pattern. Analyze the binary data more carefully."

    def on_solve(self, terminal) -> str:
        self.solved = True
        return f"Puzzle '{self.name}' solved!\n{self.success_message}"

class LogicGatePuzzle(Puzzle):
    """
    A puzzle where the player must solve a logic gate circuit.
    """
    def __init__(self, puzzle_id: str, name: str, description: str, manager,
                 circuit: Dict[str, List[str]], inputs: Dict[str, bool],
                 expected_output: bool, success_message: str,
                 difficulty: int = 1):
        super().__init__(puzzle_id, name, description, manager, difficulty)
        self.category = "Logic"
        self.circuit = circuit
        self.inputs = inputs
        self.expected_output = expected_output
        self.success_message = success_message # Ensure success_message is initialized

    def get_display_text(self) -> str:
        circuit_str = "\nCircuit:\n"
        for gate, connections in self.circuit.items():
            circuit_str += f"{gate}: {', '.join(connections)}\n"
        inputs_str = "\nInputs:\n"
        for input_name, value in self.inputs.items():
            inputs_str += f"{input_name}: {value}\n"
        return f"{self.name}\n\n{self.description}\n{circuit_str}{inputs_str}"

    def attempt_solution(self, player_input: str, terminal) -> Tuple[bool, str]:
        self.attempts += 1
        try:
            result = bool(int(player_input.strip())) # Assuming 0 or 1
            if result == self.expected_output:
                self.solved = True
                return True, self.on_solve(terminal)
            return False, "Incorrect output. Check your logic."
        except ValueError:
            return False, "Please provide a valid boolean value (0 or 1)."

class MemoryReconstructionPuzzle(Puzzle):
    """
    Puzzle where the player must reorder corrupted log snippets to reconstruct an entity's memory.
    """
    def __init__(self, puzzle_id: str, name: str, description: str, manager,
                 snippets: list, correct_order: list, max_attempts: int = 5, difficulty: int = 2):
        super().__init__(puzzle_id, name, description, manager, difficulty)
        self.category = "Memory Reconstruction"
        self.snippets = snippets  # List of (snippet_id, text)
        self.correct_order = correct_order  # List of snippet_ids in correct order
        self.max_attempts = max_attempts
        self.failed_attempts = 0
        self.horror_triggered = False

    def get_display_text(self) -> str:
        display = f"{self.name}\n\n{self.description}\n\nCorrupted Log Snippets (IDs):\n"
        for sid, text in self.snippets:
            display += f"[{sid}] {text}\n"
        display += "\nEnter the correct order of IDs, separated by commas (e.g., 3,1,2,4)."
        return display

    def attempt_solution(self, player_input: str, terminal) -> tuple:
        self.attempts += 1
        try:
            order = [int(x.strip()) for x in player_input.split(",")]
        except Exception:
            return False, "Invalid input format. Please enter IDs separated by commas."
        if order == self.correct_order:
            self.solved = True
            return True, self.on_solve(terminal)
        else:
            self.failed_attempts += 1
            if self.failed_attempts >= self.max_attempts and not self.horror_triggered:
                self.trigger_horror_event(terminal)
                self.horror_triggered = True
            return False, self.get_failure_message(terminal)

    def get_failure_message(self, terminal):
        # Optionally use LLM for dynamic taunt
        try:
            llm = LLMHandler()
            return llm.get_response("A digital voice whispers: 'You are lost in the fragments...'")
        except Exception:
            return "The fragments seem to shift and whisper. Try again."

    def trigger_horror_event(self, terminal):
        if terminal and hasattr(terminal, 'effect_manager'):
            terminal.effect_manager.start_glitch_overlay(1200, 0.7)
            terminal.effect_manager.start_screen_shake_effect(800, 10)
        if terminal:
            terminal.add_line("A cold digital presence brushes against your mind...", style_key='error')

    def get_hint(self) -> str:
        return "Hint: Look for temporal clues or recurring phrases in the snippets."

    def on_solve(self, terminal) -> str:
        self.solved = True
        # Return a more specific success message for this puzzle type
        return "Memory successfully reconstructed! The entity\'s memory stabilizes."


class SystemLoadBalancerPuzzle(Puzzle):
    """
    Puzzle where the player must allocate virtual CPU/memory to processes based on corrupted metrics.
    """
    def __init__(self, puzzle_id: str, name: str, description: str, manager,
                 processes: list, correct_alloc: dict, success_message: str, # Ensure success_message is here
                 max_attempts: int = 4, difficulty: int = 3):
        super().__init__(puzzle_id, name, description, manager, difficulty)
        self.category = "System Load Balancer"
        self.processes = processes
        self.correct_alloc = correct_alloc
        self.success_message = success_message # Assign to self.success_message
        self.max_attempts = max_attempts
        self.failed_attempts = 0
        self.horror_triggered = False

    def get_display_text(self) -> str:
        display = f"{self.name}\n\n{self.description}\n\nProcesses and (corrupted) metrics:\n"
        for proc in self.processes:
            cpu = self._glitch_metric(self.correct_alloc[proc][0])
            mem = self._glitch_metric(self.correct_alloc[proc][1])
            display += f"{proc}: CPU={cpu}%, MEM={mem}MB\n"
        display += "\nAllocate resources as: proc1:cpu,mem; proc2:cpu,mem ..."
        return display

    def _glitch_metric(self, value):
        import random
        if random.random() < 0.3:
            return "???"
        if random.random() < 0.2:
            return value + random.randint(-10, 10)
        return value

    def attempt_solution(self, player_input: str, terminal) -> tuple:
        self.attempts += 1
        try:
            allocs = {}
            for part in player_input.split(';'):
                proc, vals = part.strip().split(':')
                cpu, mem = [int(x) for x in vals.split(',')]
                allocs[proc.strip()] = (cpu, mem)
        except Exception:
            return False, "Invalid input format. Use proc:cpu,mem; ..."
        if allocs == self.correct_alloc:
            self.solved = True
            return True, self.on_solve(terminal)
        else:
            self.failed_attempts += 1
            if self.failed_attempts >= self.max_attempts and not self.horror_triggered:
                self.trigger_horror_event(terminal)
                self.horror_triggered = True
            return False, self.get_failure_message(terminal)

    def get_failure_message(self, terminal):
        try:
            llm = LLMHandler()
            return llm.get_response("A corrupted system process screams in binary static...")
        except Exception:
            return "The system groans under the strain. Try again."

    def trigger_horror_event(self, terminal):
        if terminal and hasattr(terminal, 'effect_manager'):
            terminal.effect_manager.start_glitch_overlay(1500, 0.8)
            terminal.effect_manager.start_screen_shake_effect(1000, 12)
        if terminal:
            terminal.add_line("A process crashes violently. The digital air grows colder...", style_key='error')

    def get_hint(self) -> str:
        return "Hint: Balance the highest CPU to the most critical process."

    def on_solve(self, terminal) -> str:
        self.solved = True
        return f"Puzzle '{self.name}' solved!\n{self.success_message}"

class PuzzleManager:
    def __init__(self):
        """Initialize the puzzle manager."""
        self.puzzles = {}
        self.active_puzzle = None
        self.terminal = None
        self.current_difficulty = 1
        self.solved_puzzles = set()
        self.puzzle_data = {}
        self._load_puzzle_data()
        self._load_default_puzzles()
        logging.info("Puzzle manager initialized")

    def _load_puzzle_data(self) -> None:
        """Load puzzle data from files."""
        try:
            puzzle_dir = "data/puzzles"
            if not os.path.exists(puzzle_dir):
                os.makedirs(puzzle_dir)
                logging.warning(f"Created missing puzzle directory: {puzzle_dir}")
                return

            for filename in os.listdir(puzzle_dir):
                if filename.endswith(".json"):
                    puzzle_id = filename[:-5]  # Remove .json extension
                    try:
                        with open(os.path.join(puzzle_dir, filename), 'r') as f:
                            puzzle_data = json.load(f)
                            self.puzzle_data[puzzle_id] = puzzle_data
                            self._create_puzzle_from_data(puzzle_data)
                    except json.JSONDecodeError as e:
                        logging.error(f"Error parsing puzzle file {filename}: {e}")
                    except Exception as e:
                        logging.error(f"Error loading puzzle file {filename}: {e}")

            logging.info(f"Loaded {len(self.puzzle_data)} puzzle data files")
        except Exception as e:
            logging.error(f"Error loading puzzle data: {e}")

    def _create_puzzle_from_data(self, puzzle_data: dict) -> None:
        """Create a puzzle instance from puzzle data."""
        try:
            puzzle_type = puzzle_data.get("type")
            puzzle_id = puzzle_data.get("puzzle_id")
            name = puzzle_data.get("name")
            description = puzzle_data.get("description")
            difficulty = puzzle_data.get("difficulty", 1)
            solution_data = puzzle_data.get("solution", {})

            # --- AI GENERATED: Type checks for required fields ---
            if not isinstance(puzzle_id, str) or not puzzle_id:
                puzzle_id = "unknown_puzzle_id"
            if not isinstance(name, str) or not name:
                name = "Unknown Puzzle"
            if not isinstance(description, str) or not description:
                description = "No description provided."
            if not isinstance(puzzle_type, str) or not puzzle_type:
                puzzle_type = "unknown"
            # ----------------------------------------------------

            # Skip schema validation file which has type "object"
            if puzzle_type == "object":
                return
                
            puzzle = self._instantiate_puzzle_by_type(
                puzzle_type, puzzle_id, name, description, difficulty, solution_data
            )
            if puzzle is None:
                logging.error(f"Unknown puzzle type: {puzzle_type}")
                return

            # Set corruption effects if specified
            corruption_effects = puzzle_data.get("corruption_effects", {})
            if corruption_effects:
                puzzle.is_corrupted = any([
                    corruption_effects.get("visual_corruption", False),
                    corruption_effects.get("audio_corruption", False),
                    corruption_effects.get("text_corruption", False)
                ])
                puzzle.corruption_level = corruption_effects.get("corruption_level", 0.0)

            # Set hints if specified
            hints = puzzle_data.get("hints", [])
            if hints:
                puzzle.hints = hints

            # Store rewards
            rewards = puzzle_data.get("rewards", {})
            if rewards:
                puzzle.rewards = rewards

            self.puzzles[puzzle_id] = puzzle
        except Exception as e:
            logging.error(f"Error loading puzzle data: {e}")

    def _instantiate_puzzle_by_type(
        self, puzzle_type: str, puzzle_id: str, name: str, description: str, difficulty: int, solution_data: dict
    ):
        """Helper to instantiate puzzles by type, reducing cyclomatic complexity."""
        if puzzle_type == "sequence":
            return SequenceCompletionPuzzle(
                puzzle_id=puzzle_id,
                name=name,
                description=description,
                manager=self,
                sequence_prompt=solution_data.get("sequence_prompt", []),
                solution=solution_data.get("solution", []),
                difficulty=difficulty
            )
        elif puzzle_type == "cipher":
            return CaesarCipherPuzzle(
                puzzle_id=puzzle_id,
                name=name,
                description=description,
                manager=self,
                ciphertext=solution_data.get("ciphertext", ""),
                shift=solution_data.get("shift", 0),
                difficulty=difficulty
            )
        elif puzzle_type == "file_manipulation":
            return FileManipulationPuzzle(
                puzzle_id=puzzle_id,
                name=name,
                description=description,
                manager=self,
                target_file=solution_data.get("target_file", ""),
                required_content=solution_data.get("required_content", ""),
                success_message=solution_data.get("success_message", ""),
                difficulty=difficulty
            )
        elif puzzle_type == "code_analysis":
            return CodeAnalysisPuzzle(
                puzzle_id=puzzle_id,
                name=name,
                description=description,
                manager=self,
                target_file=solution_data.get("target_file", ""),
                required_info=solution_data.get("required_info", ""),
                success_message=solution_data.get("success_message", ""),
                difficulty=difficulty
            )
        elif puzzle_type == "network":
            return NetworkPuzzle(
                puzzle_id=puzzle_id,
                name=name,
                description=description,
                manager=self,
                network_map=solution_data.get("network_map", {}),
                start_node=solution_data.get("start_node", ""),
                target_node=solution_data.get("target_node", ""),
                success_message=solution_data.get("success_message", ""),
                difficulty=difficulty
            )
        elif puzzle_type == "memory_reconstruction":
            return MemoryReconstructionPuzzle(
                puzzle_id=puzzle_id,
                name=name,
                description=description,
                manager=self,
                snippets=solution_data.get("snippets", []),
                correct_order=solution_data.get("correct_order", []),
                max_attempts=solution_data.get("max_attempts", 5),
                difficulty=difficulty
            )
        elif puzzle_type == "system_load_balancer":
            return SystemLoadBalancerPuzzle(
                puzzle_id=puzzle_id,
                name=name,
                description=description,
                manager=self,
                processes=solution_data.get("processes", []),
                correct_alloc=solution_data.get("correct_alloc", {}),
                max_attempts=solution_data.get("max_attempts", 4),
                difficulty=difficulty
            )
        elif puzzle_type == "binary_analysis":
            return BinaryAnalysisPuzzle(
                puzzle_id=puzzle_id,
                name=name,
                description=description,
                manager=self,
                binary_data=solution_data.get("binary_data", ""),
                pattern=solution_data.get("pattern", ""),
                success_message=solution_data.get("success_message", ""),
                difficulty=difficulty
            )
        elif puzzle_type == "config_file":
            return ConfigFilePuzzle(
                puzzle_id=puzzle_id,
                name=name,
                description=description,
                manager=self,
                config_file_path=solution_data.get("config_file_path", ""),
                key_phrase=solution_data.get("key_phrase", ""),
                success_message=solution_data.get("success_message", ""),
                difficulty=difficulty
            )
        else:
            return None

    def _load_default_puzzles(self):
        """Load default puzzles into the manager."""
        try:
            # Sequence Completion Puzzles
            self.load_puzzle(SequenceCompletionPuzzle(
                puzzle_id="seq_1",
                name="Number Sequence",
                description="Complete the sequence: 2, 4, 6, 8, ?",
                manager=self,
                sequence_prompt=[2, 4, 6, 8, "?"],
                solution=[10],
                difficulty=1
            ))

            # Caesar Cipher Puzzles
            self.load_puzzle(CaesarCipherPuzzle(
                puzzle_id="cipher_1",
                name="Simple Substitution",
                description="Decrypt the following message using a Caesar cipher:",
                manager=self,
                ciphertext="KHOOR ZRUOG",
                shift=3,
                difficulty=1
            ))

            # File Manipulation Puzzles
            self.load_puzzle(FileManipulationPuzzle(
                puzzle_id="file_1",
                name="Hidden Message",
                description="Find the hidden message in the system files.",
                manager=self,
                target_file="/etc/messages/hidden.txt",
                required_content="ACCESS GRANTED",
                success_message="You found the hidden message!",
                difficulty=2
            ))

            # Code Analysis Puzzles
            self.load_puzzle(CodeAnalysisPuzzle(
                puzzle_id="code_1",
                name="Debug the Code",
                description="Find the bug in the following code:",
                manager=self,
                target_file="/var/log/debug.log",
                required_info="MISSING_SEMICOLON",
                success_message="You found the bug!",
                difficulty=2
            ))

            # Network Puzzles
            self.load_puzzle(NetworkPuzzle(
                puzzle_id="net_1",
                name="Network Path",
                description="Find the shortest path through the network:",
                manager=self,
                network_map={
                    "A": ["B", "C"],
                    "B": ["A", "D", "E"],
                    "C": ["A", "F"],
                    "D": ["B", "G"],
                    "E": ["B", "G"],
                    "F": ["C", "G"],
                    "G": ["D", "E", "F"]
                },
                start_node="A",
                target_node="G",
                success_message="You found the optimal path!",
                difficulty=2
            ))

            # Memory Reconstruction Puzzles
            self.load_puzzle(MemoryReconstructionPuzzle(
                puzzle_id="mem_1",
                name="Memory Fragments",
                description="Reconstruct the corrupted memory fragments:",
                manager=self,
                snippets=[
                    "The system is",
                    "corrupted beyond",
                    "repair. The",
                    "Aetherial Scourge",
                    "has taken",
                    "control."
                ],
                correct_order=[0, 1, 2, 3, 4, 5],
                max_attempts=5,
                difficulty=3
            ))

            # System Load Balancer Puzzles
            self.load_puzzle(SystemLoadBalancerPuzzle(
                puzzle_id="load_1",
                name="System Load",
                description="Balance the system load across available resources:",
                manager=self,
                processes=[
                    {"id": "P1", "load": 30},
                    {"id": "P2", "load": 45},
                    {"id": "P3", "load": 25}
                ],
                correct_alloc={
                    "P1": "CPU1",
                    "P2": "CPU2",
                    "P3": "CPU3"
                },
                success_message="System resources balanced effectively!", # Added success_message
                max_attempts=4,
                difficulty=3
            ))

            # --- Alias default puzzles to legacy/test IDs ---
            # Map: test_id -> real_id
            alias_map = {
                "SEQ001": "seq_1",
                "CRYP001": "cipher_1",
                "FILE001": "file_1",
                "CODE001": "code_1",
                "NET001": "net_1",
                "MEMREC001": "mem_1",
                "LOADBAL001": "load_1"
            }
            for alias, real in alias_map.items():
                if real in self.puzzles:
                    self.puzzles[alias] = self.puzzles[real]

            logging.info(f"Loaded {len(self.puzzles)} default puzzles (with aliases)")
        except Exception as e:
            logging.error(f"Error loading default puzzles: {e}")

    def load_puzzle(self, puzzle: Puzzle):
        """Load a puzzle into the manager."""
        if not isinstance(puzzle, Puzzle):
            raise ValueError("Invalid puzzle object")
        if puzzle.puzzle_id in self.puzzles:
            logging.warning(f"Overwriting existing puzzle: {puzzle.puzzle_id}")
        self.puzzles[puzzle.puzzle_id] = puzzle
        logging.debug(f"Loaded puzzle: {puzzle.puzzle_id}")

    def get_puzzle(self, puzzle_id: str) -> Puzzle | None:
        """Get a puzzle by ID."""
        return self.puzzles.get(puzzle_id)

    def start_puzzle(self, puzzle_id: str) -> str:
        """Start a puzzle by ID."""
        puzzle = self.get_puzzle(puzzle_id)
        if not puzzle:
            return f"Error: Puzzle '{puzzle_id}' not found"
        if puzzle.solved:
            return f"Error: Puzzle '{puzzle_id}' already solved"
        if puzzle.difficulty > self.current_difficulty:
            return f"Error: Puzzle '{puzzle_id}' requires higher difficulty level"
        self.active_puzzle = puzzle
        return puzzle.get_display_text()

    def attempt_active_puzzle(self, player_input: Any, terminal) -> Tuple[bool, str]:
        """Attempt to solve the active puzzle."""
        if not self.active_puzzle:
            return False, "No active puzzle"
        if not self.terminal:
            self.terminal = terminal
        return self.active_puzzle.attempt_solution(player_input, terminal)

    def get_active_puzzle_hint(self) -> str:
        """Get a hint for the active puzzle."""
        if not self.active_puzzle:
            return "No active puzzle"
        return self.active_puzzle.get_hint()

    def get_next_puzzle(self) -> str:
        """Get the next available puzzle."""
        available_puzzles = [
            p for p in self.puzzles.values()
            if not p.solved and p.difficulty <= self.current_difficulty
        ]
        if not available_puzzles:
            return "No more puzzles available at current difficulty"
        return available_puzzles[0].puzzle_id

    def advance_difficulty(self):
        """Advance to the next difficulty level."""
        self.current_difficulty += 1
        logging.info(f"Advanced to difficulty level {self.current_difficulty}")

    def on_puzzle_solve(self, puzzle_id: str):
        """Handle puzzle completion."""
        puzzle = self.get_puzzle(puzzle_id)
        if not puzzle:
            return

        puzzle.solved = True
        self.solved_puzzles.add(puzzle_id)
        self.active_puzzle = None
        logging.info(f"Puzzle '{puzzle_id}' solved")

        self._show_puzzle_complete_message(puzzle)
        self._handle_puzzle_rewards(puzzle)

        # Check if all puzzles at current difficulty are solved
        current_difficulty_puzzles = [
            p for p in self.puzzles.values()
            if p.difficulty == self.current_difficulty
        ]
        if all(p.solved for p in current_difficulty_puzzles):
            self.advance_difficulty()

    def _show_puzzle_complete_message(self, puzzle):
        if self.terminal:
            self.terminal.add_line("")
            self.terminal.add_line("PUZZLE COMPLETE", style_key='success')
            self.terminal.add_line(f"'{puzzle.name}' has been solved!", style_key='success')
            self.terminal.add_line("")
            if hasattr(self.terminal, 'effect_manager'):
                self.terminal.effect_manager.start_glitch_overlay(800, 0.3)
                self.terminal.effect_manager.trigger_success_effect()

    def _handle_puzzle_rewards(self, puzzle):
        if not hasattr(puzzle, 'rewards'):
            return
        rewards = puzzle.rewards
        if not rewards or not self.terminal:
            return
        self.terminal.add_line("REWARDS:", style_key='highlight')

        # Reduce corruption if specified
        if isinstance(rewards, dict) and 'corruption_reduction' in rewards:
            reduction = rewards.get('corruption_reduction', 0)
            if hasattr(self.terminal, 'game_state_manager'):
                current_corruption = self.terminal.game_state_manager.get_corruption_level()
                new_corruption = max(0.0, current_corruption - reduction)
                self.terminal.game_state_manager.set_corruption_level(new_corruption)
                self.terminal.add_line(f"- System corruption reduced by {reduction*100:.1f}%", style_key='success')
                self.terminal.add_line(f"  New corruption level: {new_corruption*100:.1f}%", style_key='info')

        # Unlock files if specified
        if isinstance(rewards, dict) and 'unlock_files' in rewards:
            self.terminal.add_line("- Files unlocked:", style_key='success')
            for file_path in rewards.get('unlock_files', []):
                if hasattr(self.terminal, 'fs_handler'):
                    success = self.terminal.fs_handler.unlock_file(file_path)
                    if success:
                        self.terminal.add_line(f"  • {file_path}", style_key='info')

        # Trigger story events if specified
        if isinstance(rewards, dict) and 'story_events' in rewards:
            story_event_triggered = False
            for event in rewards.get('story_events', []):
                if hasattr(self.terminal, 'story_manager'):
                    self.terminal.story_manager.trigger_story_event("puzzle_reward", event)
                    story_event_triggered = True

            if story_event_triggered:
                self.terminal.add_line("- Story progression unlocked", style_key='success')

        self.terminal.add_line("")

    def set_terminal(self, terminal):
        """Set the terminal instance for the puzzle manager."""
        self.terminal = terminal

    def create_puzzle(self, puzzle_id, description, solution, hints=None):
        """Create and register a simple test puzzle for integration tests."""
        class TestPuzzle(Puzzle):
            def __init__(self, puzzle_id, description, solution, hints=None):
                super().__init__(puzzle_id, puzzle_id, description, self, 1)
                self.solution = solution
                self.hints = hints or []
            def attempt_solution(self, player_input, terminal):
                if player_input.strip() == self.solution:
                    self.solved = True
                    return True, self.on_solve(terminal)
                return False, "Incorrect."
            def get_hint(self):
                return self.hints[0] if self.hints else "No hints."
        puzzle = TestPuzzle(puzzle_id, description, solution, hints)
        self.puzzles[puzzle_id] = puzzle
        return puzzle

    def is_puzzle_solved(self, puzzle_id):
        puzzle = self.puzzles.get(puzzle_id)
        return puzzle.solved if puzzle else False

# Example Usage (for testing, would be removed or moved)
class MockTerminal:
    """A simple mock terminal for testing purposes."""
    def display(self, text):
        print(text)
    def get_command(self, prompt):
        # This won't be called by the current test structure,
        # but adding it for completeness if needed later.
        return input(prompt)
    def get_fs_handler(self):
        # Return a mock file system handler if needed by puzzles
        # For now, return None or a simple object that doesn't crash
        return None # Or create a MockFileSystemHandler if necessary


if __name__ == "__main__":
    manager = PuzzleManager() # Puzzles are now loaded in __init__
    mock_terminal = MockTerminal()

    print("--- Testing Sequence Puzzle ---")
    print(manager.start_puzzle("SEQ002"))
    solved, feedback = manager.attempt_active_puzzle("30", mock_terminal) # Incorrect
    print(f"Attempt 1 (Incorrect): Solved: {solved}, Feedback: {feedback}")
    if not solved and manager.active_puzzle:
        print(f"Hint: {manager.get_active_puzzle_hint()}")

    solved, feedback = manager.attempt_active_puzzle("31", mock_terminal) # Correct
    print(f"Attempt 2 (Correct): Solved: {solved}, Feedback: {feedback}")
    print("-" * 30)

    print("\n--- Testing Caesar Cipher Puzzle ---")
    print(manager.start_puzzle("CRYP002"))
    solved, feedback = manager.attempt_active_puzzle("Wrong Answer", mock_terminal) # Incorrect
    print(f"Attempt 1 (Incorrect): Solved: {solved}, Feedback: {feedback}")
    if not solved and manager.active_puzzle:
        print(f"Hint: {manager.get_active_puzzle_hint()}")

    solved, feedback = manager.attempt_active_puzzle("This is a test", mock_terminal) # Correct
    print(f"Attempt 2 (Correct): Solved: {solved}, Feedback: {feedback}")
    print("-" * 30)

    # print("\n--- Testing File Manipulation Puzzle ---")
    print(manager.start_puzzle("FILE001"))
    solved, feedback = manager.attempt_active_puzzle("wrong key", mock_terminal) # Incorrect
    print(f"Attempt 1 (Incorrect): Solved: {solved}, Feedback: {feedback}")
    if not solved and manager.active_puzzle:
        print(f"Hint: {manager.get_active_puzzle_hint()}")

    solved, feedback = manager.attempt_active_puzzle("xxxx-xxxx-xxxx", mock_terminal) # Correct
    print(f"Attempt 2 (Correct): Solved: {solved}, Feedback: {feedback}")
    print("-" * 30)

    print(f"\nAvailable puzzles: {list(manager.puzzles.keys())}")
