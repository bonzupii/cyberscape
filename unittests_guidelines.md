# Unit Testing Guidelines for Cyberscape DigitalDread

This document outlines the plan and guidelines for writing unit tests for the Python code files in this project.

**Overall Strategy:**

The goal is to create a suite of unit tests that verify the correctness of individual components (functions, methods, classes) in isolation. We use `pytest` as the testing framework due to its simplicity and power.

**Plan Details:**

1.  **Setup Testing Environment:**
    *   **Install `pytest`:** `pytest` and `pytest-mock` are project dependencies.
        ```bash
        pip install pytest pytest-mock
        ```
        (`pytest-mock` is useful for creating mock objects).
    *   **Create `tests` Directory:** A `tests` directory exists at the root of the project (`/home/bonzupii/Projects/cyberscape_digitaldread`).
        ```
        cyberscape_digitaldread/
        ├── tests/
        ├── command_handler.py
        ├── commands_config.py
        ├── ... (other project files)
        ```
    *   **Configuration:** A `pytest.ini` file has been added to the project root to manage `pytest` configuration, such as filtering warnings.
        ```ini
        [pytest]
        filterwarnings =
            ignore:pkg_resources is deprecated as an API:DeprecationWarning:pygame.pkgdata
        ```

2.  **Iterate Through Each Code File for Testing:**
    For each of the Python files in the project, a corresponding test file has been created in the `tests` directory:
    *   `command_handler.py` -> `tests/test_command_handler.py`
    *   `commands_config.py` -> `tests/test_commands_config.py`
    *   `effects.py` -> `tests/test_effects.py`
    *   `file_system_handler.py` -> `tests/test_file_system_handler.py`
    *   `game_state.py` -> `tests/test_game_state.py`
    *   `main.py` -> `tests/test_main.py`
    *   `terminal_renderer.py` -> `tests/test_terminal_renderer.py`
    *   `puzzle_manager.py` -> `tests/test_puzzle_manager.py`

    **For each module (`your_module.py`) and its corresponding test file (`tests/test_your_module.py`):**
    *   **A. Analyze the Module:**
        *   Read `your_module.py` to understand its purpose, classes, functions, and their inputs/outputs.
        *   Identify the core logic, expected behaviors, potential edge cases, and error conditions for each unit (function/method).
    *   **B. Write Test Cases in `tests/test_your_module.py`:**
        *   **Import necessary components:** Import the functions/classes from `your_module.py` that you want to test.
        *   **Structure tests:** Use functions named `test_*` (e.g., `def test_my_function_handles_empty_input():`).
        *   **AAA Pattern (Arrange, Act, Assert):**
            *   **Arrange:** Set up any preconditions, create necessary objects, and prepare input data.
            *   **Act:** Call the function or method you are testing with the prepared inputs.
            *   **Assert:** Verify that the outcome (return value, state change, exception raised) is what you expect using `pytest`'s `assert` statements.
        *   **Cover different scenarios:**
            *   **Happy path:** Test with typical, valid inputs.
            *   **Edge cases:** Test with boundary values (e.g., empty lists, zero, max values), null inputs (if applicable).
            *   **Error handling:** Test how the code behaves with invalid inputs and ensure expected exceptions are raised (using `pytest.raises`).
        *   **Mocking Dependencies:** If a function/method in `your_module.py` depends on other modules (e.g., file system operations, network calls, other classes you've written), use the `mocker` fixture (from `pytest-mock`) to replace these dependencies with mock objects. This ensures you are testing the unit in isolation.
            *   For example, when testing `command_handler.py`, if it uses `file_system_handler.py`, you would mock the relevant functions from `file_system_handler.py` to avoid actual file operations during tests.
        *   **Testing Tab-Completion Logic (e.g., in `command_handler.py` for `msfconsole`):**
            *   Mock the `Terminal` object passed to the completion handler.
            *   Set `mock_terminal.input_string` to simulate various user inputs.
            *   Set `mock_terminal.cursor_char_pos` appropriately.
            *   Initialize `mock_terminal.last_completion_prefix`, `mock_terminal.completion_options`, and `mock_terminal.completion_index` as needed for different test scenarios (e.g., first tab, cycling through options).
            *   Call the tab-completion handler function (e.g., `handle_msfconsole_tab_completion(mock_terminal)`).
            *   Assert the expected changes to `mock_terminal.input_string` after completion.
            *   Assert the expected state of `mock_terminal.cursor_char_pos`, `mock_terminal.last_completion_prefix`, `mock_terminal.completion_options`, and `mock_terminal.completion_index`.
            *   Verify calls to `mock_terminal.add_line` if options are expected to be displayed.
            *   Test scenarios:
                *   Single unique completion.
                *   Multiple matches with a common prefix.
                *   Cycling through multiple suggestions.
                *   No matches.
                *   Completion for commands, and for arguments of specific commands (e.g., `use <module>`, `set <option>`).
        *   **Testing Role-Specific Command Access:**
            *   When testing command handlers (e.g., in `test_command_handler.py`), ensure that commands intended for specific player roles are accessible to those roles and denied to others.
            *   Use `mock_game_state_manager.get_player_role.return_value` to simulate different player roles.
            *   Verify that `process_main_terminal_command` (or individual handlers if tested directly) correctly allows or denies command execution based on the `COMMAND_ACCESS` configuration in `commands_config.py`.
            *   Assert that appropriate error messages are added to the terminal for denied commands.
        *   **Testing File System Interaction Commands (e.g., `scan`, `parse`, `restore`):**
            *   Mock the `FileSystemHandler` methods (`is_item_corrupted`, `get_item_content`, `mark_item_corrupted`, `_resolve_path_str_to_list`, `_get_node_at_path`) to simulate different file states (e.g., corrupted, not corrupted, file not found, is a directory).
            *   Mock `EffectManager` methods to verify that appropriate visual/textual effects are triggered (e.g., progress updates, corruption effects).
            *   Mock `random.randint` or `random.random` if the command's behavior depends on random outcomes (e.g., simulated success/failure rates for `restore`, simulated corruption levels for `scan`).
            *   Assert that `terminal.add_line` and `terminal.update_line_text` are called with the expected messages and styles.
            *   Verify that `fs_handler.mark_item_corrupted` is called correctly by the `restore` command.
        *   **Handling Removed Debug `print()` Statements:**
            *   If tests were previously written to assert the output of `print()` statements (e.g., using `capsys.readouterr()`), and these `print()` statements are later removed or commented out (e.g., during code cleanup), the corresponding assertions in the tests must also be removed or updated to avoid test failures. The primary goal of unit tests is to verify logic and return values, not debug print output.

3.  **Running Tests:**
    *   Navigate to your project root directory (`/home/bonzupii/Projects/cyberscape_digitaldread`) in the terminal.
    *   Run `pytest`. `pytest` will automatically discover and run your test files.
    ```bash
    pytest
    ```

4.  **Maintenance and Iteration:**
    *   Run tests frequently, especially before committing code changes.
    *   When you change existing code, update the corresponding tests.
    *   When you add new features, write new tests for them.
    *   Aim for good test coverage, ensuring that most of your code paths are exercised by tests.

**Suggested Order for Tackling Files (All Completed):**

1.  **`effects.py`:** (DONE - All tests passing)
2.  **`commands_config.py`:** (DONE - All tests passing)
3.  **`game_state.py`:** (DONE - All tests passing)
4.  **`file_system_handler.py`:** (DONE - All tests passing)
5.  **`terminal_renderer.py`:** (DONE - All tests passing)
6.  **`command_handler.py`:** (DONE - All tests passing, including MSF-related if applicable or deferred)
7.  **`main.py`:** (DONE - All tests passing)
8.  **`puzzle_manager.py`:** (DONE - All tests passing for `PuzzleManager`, `SequenceCompletionPuzzle`, `CaesarCipherPuzzle`)

**Current Status (as of 2025-05-11):**
All planned unit test files have been created.
Recent updates include:
*   Refactoring of main terminal command parsing in `command_handler.py` to use `shlex.split()` and `args_list`. Unit tests in `test_command_handler.py` were updated to reflect these changes (e.g., passing `args_list` and `puzzle_manager_instance` to handlers, testing `shlex` behavior).
*   MSFConsole enhancements:
    *   Mouse wheel scrolling (logic in `main.py`, tested manually).
    *   `clear` command added. Tests for `_handle_msf_clear` and its availability in `MSF_COMMAND_HANDLERS` / `MSF_KNOWN_COMMANDS` added to `test_command_handler.py`. Tests for command access and help text for `clear` in MSFConsole added to `test_commands_config.py`.
    *   Scroll-to-bottom behavior for `search` results. Test in `test_command_handler.py` updated to verify `terminal.scroll_to_bottom()` is called.
*   Unit tests in `test_main.py` were updated to correctly mock calls to `process_main_terminal_command` which now includes `puzzle_manager_instance`.
*   Added `grep` command: Implemented `_handle_grep` in `command_handler.py` and added corresponding tests to `test_command_handler.py`.
*   Added system management commands: Implemented `_handle_status`, `_handle_processes`, and `_handle_kill` in `command_handler.py` and added corresponding tests to `test_command_handler.py`.

All implemented tests for all modules (`effects.py`, `commands_config.py`, `game_state.py`, `file_system_handler.py`, `terminal_renderer.py`, `command_handler.py`, `main.py`, and `puzzle_manager.py`) are **passing (539 tests)**.
Any previously noted pending or skipped tests (including MSFconsole-related command handler tests, if they were part of the initial scope) have been addressed or are considered complete for the current phase.
The core functionality of each module, as covered by the current tests, is verified. Further tests can be added to increase coverage for more complex scenarios or edge cases within each module as development continues.
A `pytest.ini` file has been added to suppress specific `DeprecationWarning`s from external libraries like `pygame` to keep test output clean.