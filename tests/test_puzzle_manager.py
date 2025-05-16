import pytest
from puzzle_manager import Puzzle, AlgorithmPuzzle, SequenceCompletionPuzzle, CaesarCipherPuzzle, PuzzleManager

# --- Test Fixtures ---

@pytest.fixture
def sequence_puzzle_numbers():
    return SequenceCompletionPuzzle(
        puzzle_id="SEQ_NUM",
        name="Numerical Sequence",
        description="Complete the number sequence.",
        sequence_prompt=[1, 2, 3, "?"],
        solution=[4],
        difficulty=1
    )

@pytest.fixture
def sequence_puzzle_strings():
    return SequenceCompletionPuzzle(
        puzzle_id="SEQ_STR",
        name="Alphabetical Sequence",
        description="Complete the letter sequence.",
        sequence_prompt=["A", "B", "C", "?"],
        solution=["D"],
        difficulty=1
    )

@pytest.fixture
def sequence_puzzle_multi_solution():
    return SequenceCompletionPuzzle(
        puzzle_id="SEQ_MULTI",
        name="Multi-part Sequence",
        description="Complete the multi-part sequence.",
        sequence_prompt=[10, 20, "?", 40, "?"],
        solution=[30, 50],
        difficulty=2
    )

# --- Tests for SequenceCompletionPuzzle ---

def test_sequence_puzzle_creation(sequence_puzzle_numbers):
    assert sequence_puzzle_numbers.puzzle_id == "SEQ_NUM"
    assert sequence_puzzle_numbers.name == "Numerical Sequence"
    assert sequence_puzzle_numbers.category == "Algorithm"
    assert not sequence_puzzle_numbers.solved
    assert sequence_puzzle_numbers.attempts == 0

def test_sequence_puzzle_get_display_text(sequence_puzzle_numbers):
    expected_text = "Numerical Sequence\n\nComplete the number sequence.\n\nSequence: 1 2 3 ?"
    assert sequence_puzzle_numbers.get_display_text() == expected_text

def test_sequence_puzzle_attempt_solution_correct_number(sequence_puzzle_numbers):
    solved, feedback = sequence_puzzle_numbers.attempt_solution("4")
    assert solved
    assert sequence_puzzle_numbers.solved
    assert "solved" in feedback.lower()
    assert sequence_puzzle_numbers.attempts == 1

def test_sequence_puzzle_attempt_solution_correct_string(sequence_puzzle_strings):
    solved, feedback = sequence_puzzle_strings.attempt_solution("D")
    assert solved
    assert sequence_puzzle_strings.solved
    assert "solved" in feedback.lower()

def test_sequence_puzzle_attempt_solution_incorrect_number(sequence_puzzle_numbers):
    solved, feedback = sequence_puzzle_numbers.attempt_solution("5")
    assert not solved
    assert not sequence_puzzle_numbers.solved
    assert "incorrect" in feedback.lower()
    assert sequence_puzzle_numbers.attempts == 1

def test_sequence_puzzle_attempt_solution_incorrect_string(sequence_puzzle_strings):
    solved, feedback = sequence_puzzle_strings.attempt_solution("E")
    assert not solved
    assert not sequence_puzzle_strings.solved
    assert "incorrect" in feedback.lower()

def test_sequence_puzzle_attempt_solution_invalid_format_number(sequence_puzzle_numbers):
    solved, feedback = sequence_puzzle_numbers.attempt_solution("abc")
    assert not solved
    assert "invalid input format" in feedback.lower()

def test_sequence_puzzle_attempt_solution_correct_multi_number(sequence_puzzle_multi_solution):
    solved, feedback = sequence_puzzle_multi_solution.attempt_solution("30,50")
    assert solved
    assert sequence_puzzle_multi_solution.solved
    assert "solved" in feedback.lower()

def test_sequence_puzzle_attempt_solution_correct_multi_number_with_spaces(sequence_puzzle_multi_solution):
    solved, feedback = sequence_puzzle_multi_solution.attempt_solution("30, 50")
    assert solved
    assert sequence_puzzle_multi_solution.solved

def test_sequence_puzzle_attempt_solution_incorrect_multi_number_order(sequence_puzzle_multi_solution):
    solved, feedback = sequence_puzzle_multi_solution.attempt_solution("50,30")
    assert not solved
    assert "incorrect" in feedback.lower()

def test_sequence_puzzle_attempt_solution_incorrect_multi_number_partial(sequence_puzzle_multi_solution):
    solved, feedback = sequence_puzzle_multi_solution.attempt_solution("30")
    assert not solved # Expects both parts
    assert "incorrect" in feedback.lower()


def test_sequence_puzzle_on_solve(sequence_puzzle_numbers):
    sequence_puzzle_numbers.solved = True # Manually set for testing on_solve directly if needed
    feedback = sequence_puzzle_numbers.on_solve()
    assert "Puzzle 'Numerical Sequence' solved!" == feedback

def test_sequence_puzzle_get_hint(sequence_puzzle_numbers):
    # SequenceCompletionPuzzle uses the base Puzzle class hint
    assert "No hints available for this puzzle." in sequence_puzzle_numbers.get_hint()

# --- Test for SequenceCompletionPuzzle.get_hint() ---
def test_sequence_completion_puzzle_get_hint(sequence_puzzle_numbers):
    """Test that SequenceCompletionPuzzle uses the default hint."""
    assert sequence_puzzle_numbers.get_hint() == "No hints available for this puzzle."


# --- Test Fixtures for Base Puzzle ---

@pytest.fixture
def base_puzzle():
    return Puzzle(
        puzzle_id="BASE001",
        name="Base Puzzle Test",
        description="This is a test description for the base puzzle.",
        difficulty=1
    )

# --- Tests for Base Puzzle ---

def test_puzzle_get_display_text(base_puzzle):
    expected_text = "Base Puzzle Test\n\nThis is a test description for the base puzzle."
    assert base_puzzle.get_display_text() == expected_text

# --- Test Fixtures for CaesarCipherPuzzle ---

@pytest.fixture
def caesar_puzzle_simple():
    return CaesarCipherPuzzle(
        puzzle_id="CAESAR001",
        name="Simple Caesar Cipher",
        description="Decrypt this message.",
        ciphertext="Khoor Zruog", # Hello World
        shift=3,
        difficulty=1
    )

@pytest.fixture
def caesar_puzzle_punctuation():
    return CaesarCipherPuzzle(
        puzzle_id="CAESAR002",
        name="Caesar with Punctuation",
        description="Decrypt this, mind the punctuation.",
        ciphertext="Qeb Nrfzh Yoltk Clu...", # Corrected: "The Quick Brown Fox..." encrypted with shift=23
        shift=23,
        difficulty=2
    )

# --- Tests for CaesarCipherPuzzle ---

def test_caesar_puzzle_creation(caesar_puzzle_simple):
    assert caesar_puzzle_simple.puzzle_id == "CAESAR001"
    assert caesar_puzzle_simple.name == "Simple Caesar Cipher"
    assert caesar_puzzle_simple.category == "Cryptographic"
    assert not caesar_puzzle_simple.solved
    assert caesar_puzzle_simple.plaintext == "Hello World"

def test_caesar_puzzle_get_display_text(caesar_puzzle_simple):
    expected_text = "Simple Caesar Cipher\n\nDecrypt this message.\n\nCiphertext: Khoor Zruog"
    assert caesar_puzzle_simple.get_display_text() == expected_text

def test_caesar_puzzle_attempt_solution_correct(caesar_puzzle_simple):
    solved, feedback = caesar_puzzle_simple.attempt_solution("Hello World")
    assert solved
    assert caesar_puzzle_simple.solved
    assert "solved" in feedback.lower()

def test_caesar_puzzle_attempt_solution_correct_case_insensitive(caesar_puzzle_simple):
    solved, feedback = caesar_puzzle_simple.attempt_solution("hello world")
    assert solved
    assert "solved" in feedback.lower()

def test_caesar_puzzle_attempt_solution_incorrect(caesar_puzzle_simple):
    solved, feedback = caesar_puzzle_simple.attempt_solution("Goodbye World")
    assert not solved
    assert not caesar_puzzle_simple.solved
    assert "incorrect" in feedback.lower()

def test_caesar_puzzle_attempt_solution_punctuation_correct(caesar_puzzle_punctuation):
    solved, feedback = caesar_puzzle_punctuation.attempt_solution("The Quick Brown Fox...")
    assert solved
    assert "solved" in feedback.lower()

def test_caesar_puzzle_get_hint_easy(caesar_puzzle_simple):
    hint = caesar_puzzle_simple.get_hint()
    assert "shift is 3" in hint

def test_caesar_puzzle_get_hint_harder(caesar_puzzle_punctuation):
    # Difficulty 2 should still give the shift
    hint = caesar_puzzle_punctuation.get_hint()
    assert f"shift is {caesar_puzzle_punctuation.shift}" in hint

    # Test difficulty where shift might be hidden
    caesar_puzzle_punctuation.difficulty = 3
    hint_hard = caesar_puzzle_punctuation.get_hint()
    assert f"shift is {caesar_puzzle_punctuation.shift}" not in hint_hard # Assuming hint changes for difficulty 3+
    assert "substitution cipher" in hint_hard

# --- Test for CaesarCipherPuzzle._decrypt() ---
def test_caesar_cipher_puzzle_decrypt():
    """Test the decryption logic for the Caesar cipher puzzle."""
    # Test with a simple case
    assert CaesarCipherPuzzle._decrypt(None, "Khoor Zruog", 3) == "Hello World"
    # Test with a different shift
    assert CaesarCipherPuzzle._decrypt(None, "Wklv lv d whvw", 3) == "This is a test"
    # Test with wrapping around the alphabet
    assert CaesarCipherPuzzle._decrypt(None, "Ebiil Tloia", 23) == "Hello World" # Shift 23 is same as -3
    # Test with punctuation and spaces
    assert CaesarCipherPuzzle._decrypt(None, "Qeb Nrfzh Yoltk Clu...", 23) == "The Quick Brown Fox..."
    # Test with zero shift
    assert CaesarCipherPuzzle._decrypt(None, "NoChange", 0) == "NoChange"


# --- Test Fixtures for PuzzleManager ---

@pytest.fixture
def puzzle_manager_with_puzzles(sequence_puzzle_numbers, caesar_puzzle_simple):
    manager = PuzzleManager()
    # PuzzleManager's __init__ now loads default puzzles, so we can either
    # clear them for isolated testing or use the ones it loads.
    # For this test, let's clear and add specific ones for more control.
    manager.puzzles = {} # Clear default loaded puzzles
    manager.load_puzzle(sequence_puzzle_numbers)
    manager.load_puzzle(caesar_puzzle_simple)
    return manager

@pytest.fixture
def empty_puzzle_manager():
    manager = PuzzleManager()
    manager.puzzles = {} # Ensure it's empty
    return manager

# --- Tests for PuzzleManager ---

def test_puzzle_manager_creation(empty_puzzle_manager):
    # Test if the _load_default_puzzles was called (or ensure it's empty if we clear it)
    # The fixture empty_puzzle_manager already clears it.
    # If we didn't clear, we'd check for "SEQ001" and "CRYP001"
    assert not empty_puzzle_manager.puzzles
    assert empty_puzzle_manager.active_puzzle is None

def test_puzzle_manager_load_default_puzzles():
    manager = PuzzleManager() # This will call _load_default_puzzles
    assert "SEQ001" in manager.puzzles
    assert "CRYP001" in manager.puzzles
    assert isinstance(manager.puzzles["SEQ001"], SequenceCompletionPuzzle)
    assert isinstance(manager.puzzles["CRYP001"], CaesarCipherPuzzle)


def test_puzzle_manager_load_puzzle(empty_puzzle_manager, sequence_puzzle_strings):
    assert not empty_puzzle_manager.get_puzzle("SEQ_STR")
    empty_puzzle_manager.load_puzzle(sequence_puzzle_strings)
    assert empty_puzzle_manager.get_puzzle("SEQ_STR") == sequence_puzzle_strings

def test_puzzle_manager_get_puzzle_exists(puzzle_manager_with_puzzles):
    puzzle = puzzle_manager_with_puzzles.get_puzzle("SEQ_NUM")
    assert puzzle is not None
    assert puzzle.puzzle_id == "SEQ_NUM"

def test_puzzle_manager_get_puzzle_not_exists(puzzle_manager_with_puzzles):
    assert puzzle_manager_with_puzzles.get_puzzle("NONEXISTENT") is None

def test_puzzle_manager_start_puzzle_success(puzzle_manager_with_puzzles):
    display_text = puzzle_manager_with_puzzles.start_puzzle("CAESAR001")
    assert puzzle_manager_with_puzzles.active_puzzle is not None
    assert puzzle_manager_with_puzzles.active_puzzle.puzzle_id == "CAESAR001"
    assert "Simple Caesar Cipher" in display_text
    assert puzzle_manager_with_puzzles.active_puzzle.solved is False # Ensure reset
    assert puzzle_manager_with_puzzles.active_puzzle.attempts == 0 # Ensure reset

def test_puzzle_manager_start_puzzle_not_found(puzzle_manager_with_puzzles):
    display_text = puzzle_manager_with_puzzles.start_puzzle("NONEXISTENT")
    assert puzzle_manager_with_puzzles.active_puzzle is None
    assert "Error: Puzzle with ID 'NONEXISTENT' not found." == display_text

def test_puzzle_manager_attempt_active_puzzle_correct(puzzle_manager_with_puzzles):
    puzzle_manager_with_puzzles.start_puzzle("SEQ_NUM")
    solved, feedback = puzzle_manager_with_puzzles.attempt_active_puzzle("4")
    assert solved
    assert "solved" in feedback.lower()
    assert puzzle_manager_with_puzzles.active_puzzle is None # Should be cleared after solve

def test_puzzle_manager_attempt_active_puzzle_incorrect(puzzle_manager_with_puzzles):
    puzzle_manager_with_puzzles.start_puzzle("SEQ_NUM")
    solved, feedback = puzzle_manager_with_puzzles.attempt_active_puzzle("5")
    assert not solved
    assert "incorrect" in feedback.lower()
    assert puzzle_manager_with_puzzles.active_puzzle is not None # Should remain active

def test_puzzle_manager_attempt_active_puzzle_no_active_puzzle(puzzle_manager_with_puzzles):
    solved, feedback = puzzle_manager_with_puzzles.attempt_active_puzzle("anything")
    assert not solved
    assert "No active puzzle to attempt." == feedback

def test_puzzle_manager_attempt_active_puzzle_already_solved(puzzle_manager_with_puzzles):
    puzzle_manager_with_puzzles.start_puzzle("SEQ_NUM")
    puzzle_manager_with_puzzles.attempt_active_puzzle("4") # Solve it
    assert puzzle_manager_with_puzzles.active_puzzle is None # It's cleared
    
    # To test the "already solved" message, we need to set an active puzzle that is already solved
    # This scenario is a bit artificial as PuzzleManager clears active_puzzle on solve.
    # Let's manually set one for this test case.
    seq_puzzle = puzzle_manager_with_puzzles.get_puzzle("SEQ_NUM")
    seq_puzzle.solved = True # Manually mark as solved
    puzzle_manager_with_puzzles.active_puzzle = seq_puzzle # Reactivate it (artificially)
    
    solved, feedback = puzzle_manager_with_puzzles.attempt_active_puzzle("4")
    assert solved # It's already solved, so attempt returns True
    assert "This puzzle has already been solved." == feedback


def test_puzzle_manager_get_active_puzzle_hint_active(puzzle_manager_with_puzzles):
    puzzle_manager_with_puzzles.start_puzzle("CAESAR001")
    hint = puzzle_manager_with_puzzles.get_active_puzzle_hint()
    assert "shift is 3" in hint

def test_puzzle_manager_get_active_puzzle_hint_none_active(puzzle_manager_with_puzzles):
    hint = puzzle_manager_with_puzzles.get_active_puzzle_hint()
    assert "No active puzzle." == hint

def test_puzzle_manager_get_active_puzzle_hint_already_solved(puzzle_manager_with_puzzles):
    puzzle_manager_with_puzzles.start_puzzle("CAESAR001")
    puzzle_manager_with_puzzles.attempt_active_puzzle("Hello World") # Solve it
    # Active puzzle is cleared. To test the "already solved" hint message,
    # we need to manually set an active puzzle that is solved.
    caesar_puzzle = puzzle_manager_with_puzzles.get_puzzle("CAESAR001")
    caesar_puzzle.solved = True # Ensure it's marked solved
    puzzle_manager_with_puzzles.active_puzzle = caesar_puzzle # Manually set it as active

    hint = puzzle_manager_with_puzzles.get_active_puzzle_hint()
    assert "This puzzle is already solved." == hint

def test_puzzle_manager_overwrite_puzzle_warning(capsys, empty_puzzle_manager, sequence_puzzle_numbers):
    # This test relies on the print statement in load_puzzle, which is for dev feedback.
    # In a real application, this might be a log or an exception.
    # For now, we'll check stdout if PuzzleManager still prints.
    # Note: PuzzleManager in puzzle_manager.py was updated to pass on overwrite.
    # So this test might not capture output unless print is re-added or logging is used.
    
    # The current PuzzleManager._load_default_puzzles() loads "SEQ001" and "CRYP001".
    # Let's use a manager that has these defaults.
    manager_with_defaults = PuzzleManager()
    
    new_seq_puzzle = SequenceCompletionPuzzle(
        puzzle_id="SEQ001", # Same ID as a default puzzle
        name="Overwriting Sequence",
        description="This should overwrite.",
        sequence_prompt=[9, 8, "?"],
        solution=[7],
        difficulty=3
    )
    manager_with_defaults.load_puzzle(new_seq_puzzle) # Attempt to overwrite
    
    # If PuzzleManager had a print warning for overwriting, we'd check capsys.readouterr().out
    # Since it's now 'pass', we just check that the puzzle was indeed overwritten.
    retrieved_puzzle = manager_with_defaults.get_puzzle("SEQ001")
    assert retrieved_puzzle is not None
    assert retrieved_puzzle.name == "Overwriting Sequence"