# ✅ Cyberscape Dev Checklist

## 🧠 Game States
- [ ] All defined states exist in `game_state.py`.
- [ ] `main.py` switches into and out of each state without error.

## 🎮 Commands
- [ ] Each new command is registered in `command_handler.py`.
- [ ] Role-specific commands validate against current role.
- [ ] Errors (invalid commands, permission issues) are styled and rendered with `effects`.

## 💾 File System
- [ ] Files can be corrupted, scanned, parsed, and restored via commands.
- [ ] `cat` command reflects corruption visually using glitch effects.
- [ ] Hidden data triggers horror or narrative hooks.

## 👁️ Terminal Effects
- [ ] Cursor trail (if active) renders glitch symbols with decay.
- [ ] Flicker, screen tear, and overlays work under load.
- [ ] Prompt corruption is visually clear and reverts safely.

## 🎧 Audio
- [ ] Sounds are routed through `audio_manager.py`.
- [ ] Corrupted files trigger specific ambient or distortion tracks.
- [ ] No overlapping playback bugs.

## 🧩 Puzzles
- [ ] All puzzle types have:
  - [ ] Solvability logic
  - [ ] `start_puzzle`, `solve`, `hint`, `exit` integration
  - [ ] Optional LLM-enhanced hint generation

## 🧠 LLM Systems
- [ ] LLM responses are generated with context.
- [ ] Horror prompts use correct entity voice.
- [ ] Prompt injection vulnerability is guarded (e.g., no raw echoing of player input).

## 💾 Save/Load
- [ ] Game state, path, inventory, and terminal buffer are saved.
- [ ] Loading a save reconstructs correct state and view.
- [ ] Optional: NG+ markers persist after final events.

## 🧪 Tests
- [ ] Tests exist for:
  - [ ] Game state transitions
  - [ ] Commands
  - [ ] Role logic
  - [ ] Puzzles
  - [ ] LLM horror generation
- [ ] All `unittest` and `pytest` suites pass.

## 🧠 Game States
- [ ] All defined states exist in `game_state.py`:
  - [ ] `STATE_MAIN_TERMINAL`: Default interactive state
  - [ ] `STATE_MSFCONSOLE`: Metasploit-like interface
  - [ ] `STATE_PUZZLE_ACTIVE`: Active puzzle solving
  - [ ] `STATE_DISCLAIMER`: Initial warning screen
  - [ ] `STATE_CORRUPTION`: High corruption takeover
  - [ ] `STATE_STORY`: Narrative sequence
- [ ] `main.py` switches into and out of each state without error
- [ ] State transitions preserve terminal buffer and effects
- [ ] Corruption level affects available states
- [ ] Role restrictions are enforced per state

## 🎮 Commands
- [ ] Each new command is registered in `command_handler.py`:
  - [ ] Basic terminal commands (`clear`, `help`, etc.)
  - [ ] File system commands (`ls`, `cd`, `cat`, etc.)
  - [ ] System commands (`status`, `processes`, etc.)
  - [ ] Puzzle commands (`start_puzzle`, `solve`, etc.)
  - [ ] Story commands (`talk`, `story`, `choose`)
- [ ] Role-specific commands validate against current role:
  - [ ] `ROLE_PURIFIER`: Defensive/analysis tools
  - [ ] `ROLE_ARBITER`: Mixed ethical tools
  - [ ] `ROLE_ASCENDANT`: Offensive/exploitation tools
- [ ] Errors are styled and rendered with `effects`:
  - [ ] Permission denied messages
  - [ ] Invalid command syntax
  - [ ] System errors
  - [ ] Corruption warnings

## 💾 File System
- [ ] Files can be corrupted, scanned, parsed, and restored:
  - [ ] `corrupt` command with intensity levels
  - [ ] `scan` for hidden data
  - [ ] `parse` for structured analysis
  - [ ] `restore` with corruption resistance
- [ ] `cat` command reflects corruption visually:
  - [ ] Glitch characters from `CORRUPTION_CHARS`
  - [ ] Color distortion effects
  - [ ] Text scrambling
  - [ ] Progressive corruption levels
- [ ] Hidden data triggers:
  - [ ] Horror narrative elements
  - [ ] System log entries
  - [ ] Character dialogue
  - [ ] Puzzle clues

## 👁️ Terminal Effects
- [ ] Cursor trail renders glitch symbols:
  - [ ] Decay over time
  - [ ] Corruption-based intensity
  - [ ] Color variations
- [ ] Screen effects:
  - [ ] Flicker with timing control
  - [ ] Screen tear with direction
  - [ ] Overlays with transparency
  - [ ] Performance optimization
- [ ] Prompt corruption:
  - [ ] Visual glitches
  - [ ] Safe reversion logic
  - [ ] Corruption level indicators

## 🎧 Audio
- [ ] Sounds routed through `audio_manager.py`:
  - [ ] Command execution sounds
  - [ ] System alerts
  - [ ] Ambient background
  - [ ] Horror triggers
- [ ] Corrupted file audio:
  - [ ] Distortion effects
  - [ ] Frequency shifts
  - [ ] Volume modulation
- [ ] Playback management:
  - [ ] No overlapping bugs
  - [ ] Volume control
  - [ ] State-based muting

## 🧩 Puzzles
- [ ] Puzzle types:
  - [ ] Terminal-based challenges
  - [ ] File system puzzles
  - [ ] Network analysis
  - [ ] Code decryption
- [ ] Integration features:
  - [ ] `start_puzzle` initialization
  - [ ] `solve` validation
  - [ ] `hint` system
  - [ ] `exit` cleanup
- [ ] LLM-enhanced hints:
  - [ ] Context-aware suggestions
  - [ ] Progressive difficulty
  - [ ] Role-specific guidance

## 🧠 LLM Systems
- [ ] Context-aware responses:
  - [ ] Current game state
  - [ ] Player role
  - [ ] Corruption level
  - [ ] Story progress
- [ ] Entity voice consistency:
  - [ ] Aetherial Scourge
  - [ ] Dr. Voss
  - [ ] SENTINEL
  - [ ] Other NPCs
- [ ] Security measures:
  - [ ] Input sanitization
  - [ ] Response validation
  - [ ] Rate limiting
  - [ ] Error handling

## 💾 Save/Load
- [ ] State persistence:
  - [ ] Game state machine
  - [ ] Player path
  - [ ] Inventory
  - [ ] Terminal buffer
- [ ] Load functionality:
  - [ ] State reconstruction
  - [ ] View restoration
  - [ ] Effect reapplication
- [ ] NG+ features:
  - [ ] Corruption markers
  - [ ] Story flags
  - [ ] Unlocked content

## 🧪 Tests
- [ ] Game state tests:
  - [ ] State transitions
  - [ ] State persistence
  - [ ] Role restrictions
- [ ] Command tests:
  - [ ] Basic functionality
  - [ ] Error handling
  - [ ] Role permissions
- [ ] Role logic tests:
  - [ ] Command access
  - [ ] Story impact
  - [ ] Puzzle interaction
- [ ] Puzzle tests:
  - [ ] Solvability
  - [ ] Hint system
  - [ ] State management
- [ ] LLM tests:
  - [ ] Response generation
  - [ ] Context handling
  - [ ] Security measures
- [ ] Test framework:
  - [ ] `unittest` integration
  - [ ] `pytest` configuration
  - [ ] Mock objects
  - [ ] Coverage reporting
