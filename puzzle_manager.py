import random
from typing import List, Any, Dict, Tuple

class Puzzle:
    """
    Base class for all puzzles and challenges in the game.
    """
    def __init__(self, puzzle_id: str, name: str, description: str, difficulty: int = 1):
        self.puzzle_id = puzzle_id
        self.name = name
        self.description = description
        self.difficulty = difficulty
        self.solved = False
        self.attempts = 0

    def get_display_text(self) -> str:
        """
        Returns the text to display to the player when presenting the puzzle.
        This should be overridden by subclasses.
        """
        return f"{self.name}\n\n{self.description}"

    def attempt_solution(self, player_input: Any) -> Tuple[bool, str]:
        """
        Processes the player's attempt to solve the puzzle.
        Returns a tuple: (is_solved, feedback_message).
        This must be overridden by subclasses.
        """
        self.attempts += 1
        # Default implementation, should be overridden
        return False, "Solution attempt logic not implemented for this puzzle type."

    def on_solve(self) -> str:
        """
        Called when the puzzle is successfully solved.
        Returns a message to display to the player.
        """
        self.solved = True
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
    def __init__(self, puzzle_id: str, name: str, description: str, difficulty: int = 1):
        super().__init__(puzzle_id, name, description, difficulty)
        self.category = "Algorithm"

class SequenceCompletionPuzzle(AlgorithmPuzzle):
    """
    A puzzle where the player must complete a sequence of numbers or characters.
    Example: 2, 4, 6, 8, ?
    """
    def __init__(self, puzzle_id: str, name: str, description: str,
                 sequence_prompt: List[Any], solution: List[Any],
                 difficulty: int = 1):
        super().__init__(puzzle_id, name, description, difficulty)
        self.sequence_prompt = sequence_prompt # e.g., [2, 4, "6", 8, "?"] or "A B C ?"
        self.solution = solution # e.g., [10] or ["D"]

    def get_display_text(self) -> str:
        prompt_str = " ".join(map(str, self.sequence_prompt))
        return f"{self.name}\n\n{self.description}\n\nSequence: {prompt_str}"

    def attempt_solution(self, player_input: str) -> Tuple[bool, str]:
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
                return True, self.on_solve()
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
    def __init__(self, puzzle_id: str, name: str, description: str, difficulty: int = 1):
        super().__init__(puzzle_id, name, description, difficulty)
        self.category = "Cryptographic"

class CaesarCipherPuzzle(CryptographicPuzzle):
    """
    A puzzle where the player must decrypt a Caesar cipher.
    """
    def __init__(self, puzzle_id: str, name: str, description: str,
                 ciphertext: str, shift: int, difficulty: int = 1):
        super().__init__(puzzle_id, name, description, difficulty)
        self.ciphertext = ciphertext
        self.shift = shift
        self.plaintext = self._decrypt(ciphertext, shift)

    def _decrypt(self, text: str, shift: int) -> str:
        result = []
        for char in text:
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

    def attempt_solution(self, player_input: str) -> Tuple[bool, str]:
        self.attempts += 1
        if player_input.strip().lower() == self.plaintext.lower():
            self.solved = True
            return True, self.on_solve()
        else:
            return False, "Incorrect decryption. Try again."

    def get_hint(self) -> str:
        if self.difficulty <= 2:
            return f"Hint: It's a type of substitution cipher. The shift is {self.shift}."
        return "Hint: It's a type of substitution cipher."


class PuzzleManager:
    """
    Manages the puzzles in the game.
    """
    def __init__(self):
        self.puzzles: Dict[str, Puzzle] = {}
        self.active_puzzle: Puzzle | None = None
        self._load_default_puzzles()

    def _load_default_puzzles(self):
        """Loads a set of predefined puzzles for testing/initial gameplay."""
        seq_puzzle = SequenceCompletionPuzzle(
            puzzle_id="SEQ001",
            name="Simple Number Sequence",
            description="Complete the following number sequence.",
            sequence_prompt=[2, 4, 6, 8, "?"],
            solution=[10],
            difficulty=1
        )
        self.load_puzzle(seq_puzzle)

        caesar_puzzle = CaesarCipherPuzzle(
            puzzle_id="CRYP001",
            name="Encrypted Message",
            description="Decrypt the following message. It seems to be shifted.",
            ciphertext="Khoor Zruog", # Hello World shifted by 3
            shift=3,
            difficulty=1
        )
        self.load_puzzle(caesar_puzzle)


    def load_puzzle(self, puzzle: Puzzle):
        """Loads a single puzzle into the manager."""
        if puzzle.puzzle_id in self.puzzles:
            # In a real game, this might log a warning or raise an error
            # For now, we'll allow overwriting for simplicity during development
            pass
        self.puzzles[puzzle.puzzle_id] = puzzle

    def get_puzzle(self, puzzle_id: str) -> Puzzle | None:
        """Retrieves a puzzle by its ID."""
        return self.puzzles.get(puzzle_id)

    def start_puzzle(self, puzzle_id: str) -> str:
        """
        Sets a puzzle as active and returns its display text.
        In a real game, this would also involve changing game state.
        """
        puzzle = self.get_puzzle(puzzle_id)
        if puzzle:
            self.active_puzzle = puzzle
            self.active_puzzle.solved = False # Reset solved state
            self.active_puzzle.attempts = 0
            return self.active_puzzle.get_display_text()
        return f"Error: Puzzle with ID '{puzzle_id}' not found."

    def attempt_active_puzzle(self, player_input: Any) -> Tuple[bool, str]:
        """
        Attempts to solve the currently active puzzle.
        """
        if self.active_puzzle:
            if self.active_puzzle.solved:
                return True, "This puzzle has already been solved."
            solved, feedback = self.active_puzzle.attempt_solution(player_input)
            if solved:
                self.active_puzzle = None # Clear active puzzle once solved
            return solved, feedback
        return False, "No active puzzle to attempt."

    def get_active_puzzle_hint(self) -> str:
        if self.active_puzzle and not self.active_puzzle.solved:
            return self.active_puzzle.get_hint()
        elif self.active_puzzle and self.active_puzzle.solved:
            return "This puzzle is already solved."
        return "No active puzzle."

# Example Usage (for testing, would be removed or moved)
if __name__ == "__main__":
    manager = PuzzleManager() # Puzzles are now loaded in __init__

    print("--- Testing Sequence Puzzle ---")
    print(manager.start_puzzle("SEQ001"))
    solved, feedback = manager.attempt_active_puzzle("12") # Incorrect
    print(f"Attempt 1 (Incorrect): Solved: {solved}, Feedback: {feedback}")
    if not solved and manager.active_puzzle:
        print(f"Hint: {manager.get_active_puzzle_hint()}")

    solved, feedback = manager.attempt_active_puzzle("10") # Correct
    print(f"Attempt 2 (Correct): Solved: {solved}, Feedback: {feedback}")
    print("-" * 30)

    print("\n--- Testing Caesar Cipher Puzzle ---")
    print(manager.start_puzzle("CRYP001"))
    solved, feedback = manager.attempt_active_puzzle("Invalid Answer") # Incorrect
    print(f"Attempt 1 (Incorrect): Solved: {solved}, Feedback: {feedback}")
    if not solved and manager.active_puzzle:
        print(f"Hint: {manager.get_active_puzzle_hint()}")

    solved, feedback = manager.attempt_active_puzzle("Hello World") # Correct
    print(f"Attempt 2 (Correct): Solved: {solved}, Feedback: {feedback}")
    print("-" * 30)

    print(f"\nAvailable puzzles: {list(manager.puzzles.keys())}")