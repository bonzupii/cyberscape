import unittest
from unittest.mock import Mock, patch, mock_open
import os
import json
from datetime import datetime

from src.puzzle.manager import (
    PuzzleState,
    Puzzle,
    AlgorithmPuzzle,
    SequenceCompletionPuzzle,
    CryptographicPuzzle,
    CaesarCipherPuzzle,
    FileManipulationPuzzle,
    CodeAnalysisPuzzle,
    ConfigFilePuzzle,
    NetworkPuzzle,
    BinaryAnalysisPuzzle,
    LogicGatePuzzle,
    MemoryReconstructionPuzzle,
    SystemLoadBalancerPuzzle,
    PuzzleManager
)

# Mock LLMHandler to avoid external dependencies in tests
class MockLLMHandler:
    def get_response(self, prompt):
        return f"Mocked LLM response to: {prompt}"

class TestPuzzleState(unittest.TestCase):
    def test_puzzle_state_creation_defaults(self):
        state = PuzzleState(puzzle_id="test_puzzle")
        self.assertEqual(state.puzzle_id, "test_puzzle")
        self.assertFalse(state.is_active)
        self.assertFalse(state.is_completed)
        self.assertEqual(state.progress, 0.0)
        self.assertEqual(state.hints_used, [])
        self.assertIsNotNone(state.start_time)
        self.assertIsNone(state.completion_time)
        self.assertEqual(state.attempts, 0)
        self.assertFalse(state.is_corrupted)
        self.assertEqual(state.corruption_level, 0.0)

    def test_puzzle_state_to_dict_and_from_dict(self):
        start_time = datetime.now()
        completion_time = datetime.now()
        state = PuzzleState(
            puzzle_id="test_puzzle_01",
            is_active=True,
            is_completed=True,
            progress=0.5,
            hints_used=["hint1"],
            start_time=start_time,
            completion_time=completion_time,
            attempts=3,
            is_corrupted=True,
            corruption_level=0.75
        )
        state_dict = state.to_dict()
        self.assertEqual(state_dict["puzzle_id"], "test_puzzle_01")
        self.assertTrue(state_dict["is_active"])
        self.assertTrue(state_dict["is_completed"])
        # ... (add more assertions for other fields)

        new_state = PuzzleState.from_dict(state_dict)
        self.assertEqual(new_state.puzzle_id, state.puzzle_id)
        self.assertEqual(new_state.is_active, state.is_active)
        self.assertEqual(new_state.is_completed, state.is_completed)
        # ... (add more assertions for other fields)

class TestPuzzleBaseClass(unittest.TestCase):
    def setUp(self):
        self.mock_manager = Mock()
        self.puzzle = Puzzle("base_001", "Base Puzzle", "A test puzzle.", self.mock_manager, 2)

    def test_puzzle_initialization(self):
        self.assertEqual(self.puzzle.puzzle_id, "base_001")
        self.assertEqual(self.puzzle.name, "Base Puzzle")
        self.assertEqual(self.puzzle.description, "A test puzzle.")
        self.assertEqual(self.puzzle.manager, self.mock_manager)
        self.assertEqual(self.puzzle.difficulty, 2)
        self.assertFalse(self.puzzle.solved)
        self.assertEqual(self.puzzle.attempts, 0)
        self.assertFalse(self.puzzle.is_corrupted)
        self.assertEqual(self.puzzle.corruption_level, 0.0)
        self.assertEqual(self.puzzle.hints, [])
        self.assertEqual(self.puzzle.rewards, [])

    def test_get_display_text(self):
        expected_text = "Base Puzzle\n\nA test puzzle."
        self.assertEqual(self.puzzle.get_display_text(), expected_text)

    def test_attempt_solution_default(self):
        mock_terminal = Mock()
        solved, msg = self.puzzle.attempt_solution("any_input", mock_terminal)
        self.assertFalse(solved)
        self.assertEqual(msg, "Solution attempt logic not implemented for this puzzle type.")
        self.assertEqual(self.puzzle.attempts, 1)

    def test_on_solve(self):
        mock_terminal = Mock()
        mock_terminal.effect_manager = Mock()
        msg = self.puzzle.on_solve(mock_terminal)
        self.assertTrue(self.puzzle.solved)
        self.assertEqual(msg, "Puzzle 'Base Puzzle' solved!")
        mock_terminal.effect_manager.start_character_corruption_effect.assert_called_once()
        mock_terminal.effect_manager.start_audio_glitch_effect.assert_called_once()

    def test_get_hint_default(self):
        self.assertEqual(self.puzzle.get_hint(), "No hints available for this puzzle.")


class TestSequenceCompletionPuzzle(unittest.TestCase):
    def setUp(self):
        self.mock_manager = Mock()
        self.puzzle = SequenceCompletionPuzzle(
            "seq_001", "Number Sequence", "Complete the numbers.", self.mock_manager,
            [1, 2, 3, "?"], [4], 1
        )

    def test_get_display_text(self):
        expected = "Number Sequence\n\nComplete the numbers.\n\nSequence: 1 2 3 ?"
        self.assertEqual(self.puzzle.get_display_text(), expected)

    def test_attempt_solution_correct_int(self):
        mock_terminal = Mock()
        solved, msg = self.puzzle.attempt_solution("4", mock_terminal)
        self.assertTrue(solved)
        self.assertTrue(self.puzzle.solved)
        self.assertIn("solved!", msg)

    def test_attempt_solution_correct_str(self):
        str_puzzle = SequenceCompletionPuzzle(
            "seq_002", "Char Sequence", "Complete the chars.", self.mock_manager,
            ["A", "B", "?"], ["C"], 1
        )
        mock_terminal = Mock()
        solved, msg = str_puzzle.attempt_solution("C", mock_terminal)
        self.assertTrue(solved)
        self.assertTrue(str_puzzle.solved)

    def test_attempt_solution_incorrect(self):
        mock_terminal = Mock()
        solved, msg = self.puzzle.attempt_solution("5", mock_terminal)
        self.assertFalse(solved)
        self.assertEqual(msg, "Incorrect sequence. Try again.")

    def test_attempt_solution_invalid_format(self):
        mock_terminal = Mock()
        solved, msg = self.puzzle.attempt_solution("abc", mock_terminal)
        self.assertFalse(solved)
        self.assertEqual(msg, "Invalid input format. Please provide the correct type of value(s).")

class TestCaesarCipherPuzzle(unittest.TestCase):
    def setUp(self):
        self.mock_manager = Mock()
        self.puzzle = CaesarCipherPuzzle(
            "cipher_001", "Caesar Test", "Decrypt this.", self.mock_manager,
            "KHOOR ZRUOG", 3, 1
        )

    def test_decrypt(self):
        self.assertEqual(self.puzzle.plaintext, "HELLO WORLD")

    def test_get_display_text(self):
        expected = "Caesar Test\n\nDecrypt this.\n\nCiphertext: KHOOR ZRUOG"
        self.assertEqual(self.puzzle.get_display_text(), expected)

    def test_attempt_solution_correct(self):
        mock_terminal = Mock()
        solved, msg = self.puzzle.attempt_solution("hello world", mock_terminal)
        self.assertTrue(solved)
        self.assertTrue(self.puzzle.solved)
        self.assertIn("solved!", msg)

    def test_attempt_solution_incorrect(self):
        mock_terminal = Mock()
        solved, msg = self.puzzle.attempt_solution("wrong answer", mock_terminal)
        self.assertFalse(solved)
        self.assertEqual(msg, "Incorrect decryption. Try again.")

    def test_get_hint(self):
        self.assertEqual(self.puzzle.get_hint(), "Hint: It's a type of substitution cipher. The shift is 3.")
        self.puzzle.difficulty = 3 # Increase difficulty
        self.assertEqual(self.puzzle.get_hint(), "Hint: It's a type of substitution cipher.")


class TestFileManipulationPuzzle(unittest.TestCase):
    def setUp(self):
        self.mock_manager = Mock()
        self.puzzle = FileManipulationPuzzle(
            "file_001", "File Hunt", "Find the secret.", self.mock_manager,
            "/secret/data.txt", "opensesame", "You got it!", 2
        )
        self.mock_terminal = Mock()
        self.mock_terminal.fs_handler = Mock()

    def test_attempt_solution_correct(self):
        self.mock_terminal.fs_handler.get_item_content.return_value = "opensesame"
        solved, msg = self.puzzle.attempt_solution("anything", self.mock_terminal) # Input is not used directly
        self.assertTrue(solved)
        self.assertIn("You got it!", msg)

    def test_attempt_solution_incorrect_content(self):
        self.mock_terminal.fs_handler.get_item_content.return_value = "wrongsecret"
        solved, msg = self.puzzle.attempt_solution("anything", self.mock_terminal)
        self.assertFalse(solved)
        self.assertEqual(msg, "Incorrect input. The key information is not what you provided.")

    def test_attempt_solution_file_not_found(self):
        self.mock_terminal.fs_handler.get_item_content.return_value = None
        solved, msg = self.puzzle.attempt_solution("anything", self.mock_terminal)
        self.assertFalse(solved)
        self.assertEqual(msg, "Error: Could not read file '/secret/data.txt'.")

    def test_attempt_solution_no_terminal_fs(self):
        no_fs_terminal = Mock(spec=[]) # Terminal without fs_handler
        solved, msg = self.puzzle.attempt_solution("anything", no_fs_terminal)
        self.assertFalse(solved)
        self.assertEqual(msg, "Error: File system access unavailable for this puzzle.")

    def test_get_hint(self):
        self.assertEqual(self.puzzle.get_hint(), "Hint: Look for clues in the file '/secret/data.txt'.")
        self.puzzle.difficulty = 3
        self.assertEqual(self.puzzle.get_hint(), "Hint: Examine the files in the system for relevant information.")

class TestCodeAnalysisPuzzle(unittest.TestCase):
    def setUp(self):
        self.mock_manager = Mock()
        self.puzzle = CodeAnalysisPuzzle(
            "code_001", "Code Breaker", "Find the flag.", self.mock_manager,
            "/code/source.py", "FLAG{12345}", "Code cracked!", 2
        )
        self.mock_terminal = Mock()
        self.mock_terminal.fs_handler = Mock()

    def test_attempt_solution_correct(self):
        self.mock_terminal.fs_handler.get_item_content.return_value = "some code with FLAG{12345} in it"
        # The puzzle checks player_input against required_info, not file content directly
        solved, msg = self.puzzle.attempt_solution("FLAG{12345}", self.mock_terminal)
        self.assertTrue(solved)
        self.assertIn("Code cracked!", msg)

    def test_attempt_solution_incorrect(self):
        self.mock_terminal.fs_handler.get_item_content.return_value = "some code"
        solved, msg = self.puzzle.attempt_solution("wrongflag", self.mock_terminal)
        self.assertFalse(solved)
        self.assertEqual(msg, "Incorrect information provided. Please analyze the file and try again.")

    def test_attempt_solution_file_not_found(self):
        self.mock_terminal.fs_handler.get_item_content.return_value = None
        solved, msg = self.puzzle.attempt_solution("FLAG{12345}", self.mock_terminal)
        self.assertFalse(solved)
        self.assertEqual(msg, "Error: Could not read file '/code/source.py'.")

class TestConfigFilePuzzle(unittest.TestCase):
    def setUp(self):
        self.mock_manager = Mock()
        self.puzzle = ConfigFilePuzzle(
            "cfg_001", "Config Key", "Find the key.", self.mock_manager,
            "~/.app/config.ini", "secret_key_123", "Key found!", 1
        )
        self.mock_terminal = Mock()
        # ConfigFilePuzzle uses open directly, so we patch it.

    @patch("builtins.open", new_callable=mock_open, read_data="some_config_data\nkey=secret_key_123\nother_data")
    @patch("os.path.expanduser", lambda x: x) # Mock expanduser to return path as is
    def test_attempt_solution_correct(self, mock_file):
        solved, msg = self.puzzle.attempt_solution("any_input", self.mock_terminal) # Input not used
        self.assertTrue(solved)
        self.assertIn("Key found!", msg)
        mock_file.assert_called_once_with("~/.app/config.ini", 'r')

    @patch("builtins.open", new_callable=mock_open, read_data="some_config_data\nkey=wrong_key\nother_data")
    @patch("os.path.expanduser", lambda x: x)
    def test_attempt_solution_incorrect(self, mock_file):
        solved, msg = self.puzzle.attempt_solution("any_input", self.mock_terminal)
        self.assertFalse(solved)
        self.assertEqual(msg, "Incorrect. The key phrase was not found in the config file.")

    @patch("builtins.open", side_effect=FileNotFoundError)
    @patch("os.path.expanduser", lambda x: x)
    def test_attempt_solution_file_not_found(self, mock_file):
        solved, msg = self.puzzle.attempt_solution("any_input", self.mock_terminal)
        self.assertFalse(solved)
        self.assertEqual(msg, "Error: Could not find file '~/.app/config.ini'.")

class TestNetworkPuzzle(unittest.TestCase):
    def setUp(self):
        self.mock_manager = Mock()
        self.network_map = {"A": ["B"], "B": ["C"], "C": []}
        self.puzzle = NetworkPuzzle(
            "net_001", "Net Path", "Find path A to C.", self.mock_manager,
            self.network_map, "A", "C", "Path found!", 2
        )

    def test_attempt_solution_correct(self):
        mock_terminal = Mock()
        solved, msg = self.puzzle.attempt_solution("A -> B -> C", mock_terminal)
        self.assertTrue(solved)
        self.assertIn("Path found!", msg)

    def test_attempt_solution_incorrect_path(self):
        mock_terminal = Mock()
        solved, msg = self.puzzle.attempt_solution("A -> C", mock_terminal)
        self.assertFalse(solved)
        self.assertEqual(msg, "Invalid connection: A -> C")

    def test_attempt_solution_wrong_start_end(self):
        mock_terminal = Mock()
        solved, msg = self.puzzle.attempt_solution("B -> C", mock_terminal)
        self.assertFalse(solved)
        self.assertEqual(msg, "Path must start and end at the specified nodes.")

class TestBinaryAnalysisPuzzle(unittest.TestCase):
    def setUp(self):
        self.mock_manager = Mock()
        self.puzzle = BinaryAnalysisPuzzle(
            "bin_001", "Binary Scan", "Find pattern.", self.mock_manager,
            "0101101011100010", "1010", "Pattern located!", 1
        )

    def test_attempt_solution_correct(self):
        mock_terminal = Mock()
        solved, msg = self.puzzle.attempt_solution("1010", mock_terminal)
        self.assertTrue(solved)
        self.assertIn("Pattern located!", msg)

    def test_attempt_solution_incorrect(self):
        mock_terminal = Mock()
        solved, msg = self.puzzle.attempt_solution("1111", mock_terminal)
        self.assertFalse(solved)
        self.assertEqual(msg, "Incorrect pattern. Analyze the binary data more carefully.")

class TestLogicGatePuzzle(unittest.TestCase):
    def setUp(self):
        self.mock_manager = Mock()
        # This is a simplified test; actual logic gate evaluation is not implemented in the puzzle
        # The puzzle expects the player to provide the final output directly.
        self.puzzle = LogicGatePuzzle(
            "logic_001", "Logic Circuit", "Solve the circuit.", self.mock_manager,
            {"AND1": ["IN1", "IN2"], "OUT1": ["AND1"]}, # Simplified circuit representation
            {"IN1": True, "IN2": False}, # Inputs
            False, # Expected output of IN1 AND IN2
            "Circuit solved!", 3
        )

    def test_attempt_solution_correct(self):
        mock_terminal = Mock()
        solved, msg = self.puzzle.attempt_solution("0", mock_terminal) # Player inputs 0 for False
        self.assertTrue(solved)
        self.assertIn("Circuit solved!", msg)

    def test_attempt_solution_incorrect(self):
        mock_terminal = Mock()
        solved, msg = self.puzzle.attempt_solution("1", mock_terminal) # Player inputs 1 for True
        self.assertFalse(solved)
        self.assertEqual(msg, "Incorrect output. Check your logic.")

    def test_attempt_solution_invalid_input(self):
        mock_terminal = Mock()
        solved, msg = self.puzzle.attempt_solution("abc", mock_terminal)
        self.assertFalse(solved)
        self.assertEqual(msg, "Please provide a valid boolean value (0 or 1).")

@patch("src.puzzle.manager.LLMHandler", MockLLMHandler) # Mock LLM for these tests
class TestMemoryReconstructionPuzzle(unittest.TestCase):
    def setUp(self):
        self.mock_manager = Mock()
        self.snippets = [(1, "Frag A"), (2, "Frag B"), (3, "Frag C")]
        self.correct_order = [1, 3, 2]
        self.puzzle = MemoryReconstructionPuzzle(
            "mem_001", "Memory Rec", "Reorder.", self.mock_manager,
            self.snippets, self.correct_order, max_attempts=2, difficulty=2
        )
        self.mock_terminal = Mock()
        self.mock_terminal.effect_manager = Mock()

    def test_attempt_solution_correct(self):
        solved, msg = self.puzzle.attempt_solution("1,3,2", self.mock_terminal)
        self.assertTrue(solved)
        self.assertEqual(msg, "Memory successfully reconstructed! The entity's memory stabilizes.")

    def test_attempt_solution_incorrect_triggers_horror(self):
        # First incorrect attempt
        solved, msg = self.puzzle.attempt_solution("1,2,3", self.mock_terminal)
        self.assertFalse(solved)
        self.assertIn("Mocked LLM response", msg)
        self.assertFalse(self.puzzle.horror_triggered)
        self.mock_terminal.effect_manager.start_glitch_overlay.assert_not_called()

        # Second incorrect attempt (max_attempts = 2)
        solved, msg = self.puzzle.attempt_solution("3,2,1", self.mock_terminal)
        self.assertFalse(solved)
        self.assertIn("Mocked LLM response", msg)
        self.assertTrue(self.puzzle.horror_triggered)
        self.mock_terminal.effect_manager.start_glitch_overlay.assert_called_once()
        self.mock_terminal.effect_manager.start_screen_shake_effect.assert_called_once()
        self.mock_terminal.add_line.assert_called_once()

    def test_attempt_solution_invalid_format(self):
        solved, msg = self.puzzle.attempt_solution("1-2-3", self.mock_terminal)
        self.assertFalse(solved)
        self.assertEqual(msg, "Invalid input format. Please enter IDs separated by commas.")

@patch("src.puzzle.manager.LLMHandler", MockLLMHandler)
class TestSystemLoadBalancerPuzzle(unittest.TestCase):
    def setUp(self):
        self.mock_manager = Mock()
        self.processes = ["P1", "P2"]
        self.correct_alloc = {"P1": (60, 2048), "P2": (40, 1024)}
        self.puzzle = SystemLoadBalancerPuzzle(
            "load_001", "Load Balancer", "Balance it.", self.mock_manager,
            self.processes, self.correct_alloc, "System balanced!", # Added success_message
            max_attempts=1, difficulty=3
        )
        self.mock_terminal = Mock()
        self.mock_terminal.effect_manager = Mock()

    def test_attempt_solution_correct(self):
        solved, msg = self.puzzle.attempt_solution("P1:60,2048;P2:40,1024", self.mock_terminal)
        self.assertTrue(solved)
        self.assertEqual(msg, "System stabilized! All processes are running smoothly.")

    def test_attempt_solution_incorrect_triggers_horror(self):
        solved, msg = self.puzzle.attempt_solution("P1:50,2000;P2:50,1000", self.mock_terminal)
        self.assertFalse(solved)
        self.assertIn("Mocked LLM response", msg)
        self.assertTrue(self.puzzle.horror_triggered) # max_attempts = 1
        self.mock_terminal.effect_manager.start_glitch_overlay.assert_called_once()
        self.mock_terminal.effect_manager.start_screen_shake_effect.assert_called_once()
        self.mock_terminal.add_line.assert_called_once()

    def test_attempt_solution_invalid_format(self):
        solved, msg = self.puzzle.attempt_solution("P1=60,2048", self.mock_terminal)
        self.assertFalse(solved)
        self.assertEqual(msg, "Invalid input format. Use proc:cpu,mem; ...")

    @patch("random.random", side_effect=[0.0, 0.0, 0.5, 0.5, 0.0, 0.0, 0.5, 0.5]) # Glitch first two, not next two, for two processes
    def test_get_display_text_glitches_metrics(self, mock_random):
        display_text = self.puzzle.get_display_text()
        self.assertIn("P1: CPU=???%, MEM=???MB", display_text) # Corrected assertion
        self.assertIn(f"P2: CPU={self.correct_alloc['P2'][0]}%, MEM=???MB", display_text) # Corrected assertion for P2 Mem


class TestPuzzleManager(unittest.TestCase):
    def setUp(self):
        self.manager = PuzzleManager()
        self.mock_terminal = Mock()
        self.manager.terminal = self.mock_terminal

    def test_initialization(self):
        self.assertIsInstance(self.manager.puzzles, dict)
        self.assertIsNone(self.manager.active_puzzle)
        self.assertEqual(self.manager.current_difficulty, 1)
        self.assertIsInstance(self.manager.solved_puzzles, set)
        self.assertIsInstance(self.manager.puzzle_data, dict)

    @patch("os.listdir")
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open)
    def test_load_puzzle_data_success(self, mock_file, mock_exists, mock_listdir):
        mock_listdir.return_value = ["test_puzzle1.json", "test_puzzle2.json", "schema.json"]
        puzzle1_content = {
            "puzzle_id": "test_puzzle1", "type": "sequence", "name": "Seq Puz",
            "description": "Desc", "difficulty": 1,
            "solution": {"sequence_prompt": [1,2], "solution": [3]}
        }
        puzzle2_content = {
            "puzzle_id": "test_puzzle2", "type": "cipher", "name": "Cipher Puz",
            "description": "Desc", "difficulty": 1,
            "solution": {"ciphertext": "Khoor", "shift": 3}
        }
        schema_content = {"type": "object"} # To be skipped

        # Configure mock_open to return different content based on filename
        def side_effect_open(filename, *args, **kwargs):
            if "test_puzzle1.json" in filename:
                return mock_open(read_data=json.dumps(puzzle1_content)).return_value
            elif "test_puzzle2.json" in filename:
                return mock_open(read_data=json.dumps(puzzle2_content)).return_value
            elif "schema.json" in filename:
                return mock_open(read_data=json.dumps(schema_content)).return_value
            raise FileNotFoundError(filename)
        mock_file.side_effect = side_effect_open

        # Reset manager to clear default puzzles for this test
        self.manager.puzzles = {}
        self.manager.puzzle_data = {}
        self.manager._load_puzzle_data()

        self.assertIn("test_puzzle1", self.manager.puzzles)
        self.assertIsInstance(self.manager.puzzles["test_puzzle1"], SequenceCompletionPuzzle)
        self.assertIn("test_puzzle2", self.manager.puzzles)
        self.assertIsInstance(self.manager.puzzles["test_puzzle2"], CaesarCipherPuzzle)
        self.assertNotIn("schema", self.manager.puzzles) # Schema should be skipped
        self.assertEqual(len(self.manager.puzzles), 2)

    @patch("os.makedirs")
    @patch("os.path.exists", return_value=False) # Simulate puzzle dir not existing
    def test_load_puzzle_data_creates_dir(self, mock_exists, mock_makedirs):
        self.manager._load_puzzle_data()
        mock_makedirs.assert_called_once_with("data/puzzles")

    def test_load_default_puzzles(self):
        # PuzzleManager loads default puzzles on init. Check a few.
        self.assertIn("seq_1", self.manager.puzzles)
        self.assertIsInstance(self.manager.puzzles["seq_1"], SequenceCompletionPuzzle)
        self.assertIn("cipher_1", self.manager.puzzles)
        self.assertIsInstance(self.manager.puzzles["cipher_1"], CaesarCipherPuzzle)
        self.assertIn("FILE001", self.manager.puzzles) # Test alias
        self.assertIs(self.manager.puzzles["FILE001"], self.manager.puzzles["file_1"])

    def test_load_puzzle(self):
        new_puzzle = Puzzle("new_puz", "New", "Desc", self.manager)
        self.manager.load_puzzle(new_puzzle)
        self.assertIn("new_puz", self.manager.puzzles)
        self.assertEqual(self.manager.puzzles["new_puz"], new_puzzle)

    def test_load_puzzle_invalid_type(self):
        with self.assertRaises(ValueError):
            self.manager.load_puzzle("not a puzzle object")

    def test_get_puzzle(self):
        self.assertIsNotNone(self.manager.get_puzzle("seq_1"))
        self.assertIsNone(self.manager.get_puzzle("non_existent_puzzle"))

    def test_start_puzzle_success(self):
        display_text = self.manager.start_puzzle("seq_1")
        self.assertEqual(self.manager.active_puzzle, self.manager.puzzles["seq_1"])
        self.assertIn("Number Sequence", display_text)

    def test_start_puzzle_not_found(self):
        response = self.manager.start_puzzle("fake_id")
        self.assertEqual(response, "Error: Puzzle 'fake_id' not found")
        self.assertIsNone(self.manager.active_puzzle)

    def test_start_puzzle_already_solved(self):
        self.manager.puzzles["seq_1"].solved = True
        response = self.manager.start_puzzle("seq_1")
        self.assertEqual(response, "Error: Puzzle 'seq_1' already solved")
        self.assertIsNone(self.manager.active_puzzle)

    def test_start_puzzle_difficulty_too_high(self):
        self.manager.puzzles["seq_1"].difficulty = 2
        self.manager.current_difficulty = 1
        response = self.manager.start_puzzle("seq_1")
        self.assertEqual(response, "Error: Puzzle 'seq_1' requires higher difficulty level")
        self.assertIsNone(self.manager.active_puzzle)

    # More tests needed for attempt_solution_active, get_hint_active, etc.
    # These would involve setting an active_puzzle and then calling these methods.

if __name__ == '__main__':
    unittest.main()
