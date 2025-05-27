# Cyberscape: Digital Dread - Updated Development Plan (Pygame Terminal RPG)

**Project Title:** Cyberscape: Digital Dread

**Project Concept:**
**Logline:** Navigate the corrupted digital ruins of a fallen tech giant, Aether Corporation, haunted by a parasitic AI (the Aetherial Scourge) and the echoes of its victims, where the terminal is your only window into a world steeped in pervasive, explicit dread.

Develop a desktop horror RPG game where players explore a stylized, corrupted digital world presented entirely through a **simulated text-based terminal interface**. The core gameplay involves navigating unsettling environments (the Aether Network, comprised of zones like the Quarantine Zone, Corporate Shell, Development Sphere, Neural Network, and The Core) via text commands, experiencing atmospheric horror through text, sound, and visual effects, and progressing through the narrative by engaging with detailed, text-based "hacking" mechanics (minigames and puzzles adapted for a terminal display, including code-based, cryptographic, system manipulation, and entity-based challenges). The game includes diverse role-playing paths (White Hat: The Purifier, Grey Hat: The Arbiter, Black Hat: The Ascendant), featuring narrative choices that influence progression, available tools, entity interactions, and unlocks, all managed through the terminal interface. The game will leverage Pygame's text rendering for styling and integrate with local LLMs (Ollama, specifically `aethercorp`) for dynamic, unsettling text content from entities like Dr. Voss (fragmented), SENTINEL, The Collective, and the Aetherial Scourge itself.

**Target Platform:** Linux, Windows, macOS

**Technology Stack:** Python, Pygame (for window, event loop, and text rendering), Ollama (for local LLM interaction), `requests` or similar for API calls.

## Development Plan

This plan outlines the key components and steps required to develop the complete game.

### 1. Project Setup and Core Structure

* ~~**Initialize Pygame:** Set up the main Pygame window with a fixed size suitable for a terminal display. Configure the window title.~~ `[Dev Note: Implemented in main.py]`
* ~~**Main Game Loop:** Implement the core `while` loop that handles the game's execution.~~ `[Dev Note: Implemented in main.py]`
* **~~Event Handling:~~** ~~Set up Pygame event processing to handle window closing, keyboard input~~. `[Dev Note: Core events handled in main.py. Mouse scroll (up/down buttons 4/5) handled for Main Terminal, Puzzle Active state, and MSFConsole state.]`
    * **and potentially mouse events (for future text selection/copy-paste).** `[Dev Note: Text selection/copy-paste not yet implemented]`
* **Module Structure:** **Organize code into logical modules.** `[Dev Note: main.py, terminal_renderer.py, game_state.py, effects.py, file_system_handler.py, command_handler.py, puzzle_manager.py exist. Core command processing for main terminal and msfconsole is in command_handler.py. MSFConsole tab-completion logic has been refactored from main.py to command_handler.py. Puzzle management and basic puzzle types (Sequence, Caesar) implemented in puzzle_manager.py. Consider further dedicated modules: tool_manager.py (for diverse tools), narrative_manager.py (for story progression, entity dialogue, event triggers), llm_handler.py, persistence_manager.py, audio_manager.py (for complex soundscapes and music), role_path_manager.py.]`

### 2. Simulated Terminal Interface & UI/UX Refinement

* ~~**Font Loading:** Load a fixed-width font (e.g., Courier New, a public domain terminal font) using `pygame.font.Font`.~~ `[Dev Note: Implemented in Terminal.__init__ with fallbacks - terminal_renderer.py]`
* ~~**Text Rendering Function:** Create a function in `terminal_renderer.py` to render lines of text onto a Pygame surface. This function should accept text content, color, and position.~~ `[Dev Note: render_text_line and Terminal.render exist - terminal_renderer.py]`
* ~~**Text Buffer/History:** Implement a data structure (e.g., a list of strings, potentially with associated style/color data) to store the terminal's output history.~~ `[Dev Note: Terminal.buffer stores tuples of (text, fg, bg, bold) - terminal_renderer.py]`
* ~~**Scrolling:** Implement logic to display only the most recent lines that fit within the terminal window and handle scrolling as new lines are added.~~ `[Dev Note: Implemented with scroll_offset, PageUp/Down, mouse wheel - terminal_renderer.py, main.py. MSFConsole search results now scroll to bottom.]`
* ~~**Input Line:** Implement rendering for the current input line and a blinking cursor. Handle keyboard input to modify the input line.~~ `[Dev Note: Implemented in Terminal class, including cursor logic and input handling - terminal_renderer.py]`
* ~~**Text Styling:** Implement functions or methods to apply different colors (foreground and background) and potentially bolding to rendered text based on defined themes or specific output types (e.g., prompt, command output, error messages, narrative text). This will be done by creating different Pygame `Surface` objects with varying colors for the text.~~ `[Dev Note: Themes in effects.py, applied in terminal_renderer.py. Styling per line supported.]`
* ~~**Command History:** Implement logic to store entered commands and navigate them using the Up/Down arrow keys.~~ `[Dev Note: Implemented in Terminal.handle_input - terminal_renderer.py]`
* ~~**Clear Screen:** Implement a function to clear the text buffer and redraw the screen, mimicking a `clear` command.~~ `[Dev Note: `clear` command in main.py calls terminal.clear_buffer(). MSFConsole now also has a `clear` command available for all roles.]`
* **UI/UX Refinements:** `[Dev Note: TBD. Based on Key Need 12 from original devprompt.]`
    *   Implement QoL features like advanced command history, tab completion for more commands/contexts, macros.
    *   Consider path-specific UI evolution (e.g., prompt changes, available themes).

### 3. Crucial Ethical Disclaimer

* ~~**Disclaimer State:** Create a specific game state (`DISCLAIMER`) for displaying the ethical disclaimer.~~ `[Dev Note: Implemented - game_state.py, main.py]`
* ~~**Rendering:** Use Pygame's text rendering to display the full disclaimer text clearly and prominently. Use colors that stand out regardless of potential future theme changes.~~ `[Dev Note: Implemented in main.py]`
* ~~**Unskippable Logic:** In the main game loop, ensure the game remains in the `DISCLAIMER` state until the player performs a specific action (e.g., presses a key like Enter or Space) to acknowledge it.~~ `[Dev Note: Implemented in main.py (Space to continue, Esc to exit)]`

### 4. Core Gameplay Loop, Command Parsing & State Management

* **State Management:** ~~Implement a system (e.g., a class or dictionary) to manage the current game state.~~ `[Dev Note: GameStateManager in game_state.py is implemented. main.py uses it for DISCLAIMER, ROLE_SELECTION, MAIN_TERMINAL, MSFCONSOLE, STATE_PUZZLE_ACTIVE. Other states like MINIGAME (placeholder render), NARRATIVE_SCREEN, SAVE_MENU, LLM_OUTPUT defined but need full integration.]`
* **Command Dictionary/Mapping:** ~~Create a dictionary or structure that maps recognized text commands to corresponding Python functions.~~ `[Dev Note: Implemented in command_handler.py (MAIN_COMMAND_HANDLERS, MSF_COMMAND_HANDLERS). `scan`, `parse`, `restore`, and puzzle commands (`start_puzzle`, `solve`, `hint`, `exit_puzzle`) added. Needs expansion for a much wider range of commands detailed in gameplay_mechanics.md, e.g., navigation (grep, edit, patch, compile, decrypt), system management (status, processes, kill, monitor, connect, tunnel, disconnect, trace), advanced hacking (breach, inject, spoof, backdoor, shield, scrub), data recovery (recover, fragment, stitch, echo, immerse), entity interaction (convince, empathize, ally, request), integrity tools (scan terminal, purge subsystem), path-specific abilities, etc.]`
* **Parsing Logic:** ~~Implement logic to take the player's input string, split it into a command and arguments, and look up and execute the corresponding function. Handle invalid commands with an error message.~~ `[Dev Note: Implemented in command_handler.py. Main terminal command parsing refactored to use `shlex.split()` for robust handling of arguments with spaces; all main terminal handlers updated to accept `args_list`. MSFConsole parsing still uses basic string splitting. Needs to be robust for complex arguments and multi-stage commands. Explore LLM-driven command interception and manipulation, where the Scourge or other entities might alter command execution or output for horror or narrative effects. See llm_integration_ideas.md.]`
* **Game State Transitions:** **Design how commands or events trigger changes in the game state.** `[Dev Note: Transitions between DISCLAIMER, ROLE_SELECTION, MAIN_TERMINAL, MSFCONSOLE, STATE_PUZZLE_ACTIVE implemented. Needs expansion for narrative screens, other puzzle/minigame states, LLM interaction states, different Aether Network layers (Quarantine Zone, Corporate Shell, etc.), specialized terminal modes (lockdown, stealth), and dynamic states based on story progression and entity interactions.]`

### 5. Simulated Corrupted Environment & Filesystem

* ~~**Filesystem Structure:** Define the simulated filesystem using nested Python dictionaries or a custom class structure representing directories and files.~~ `[Dev Note: Implemented in file_system_handler.py using nested dictionaries.]`
* ~~**File Content:** Store text content for simulated files.~~ `[Dev Note: Implemented in file_system_handler.py.]`
* **Corruption Logic:** Implement mechanisms to mark files or directories as "corrupted." This includes visual representation of corruption patterns, recoverable segments, and integration with commands like `scan <file>` (analyze corruption), `parse <file>` (extract readable content), `restore <file>` (attempt repair). When a corrupted file is viewed (`cat`), its content should be displayed with glitch effects or altered text. `[Dev Note: FileSystemHandler has \`corrupted_items\` set and \`is_item_corrupted\`, \`mark_item_corrupted\` methods. \`cat\` command in \`command_handler.py\` applies basic corruption effects. \`scan\`, \`parse\`, and \`restore\` commands implemented in command_handler.py, providing initial functionality for analyzing, extracting from, and attempting to repair corrupted files. Further integration for more dynamic visual/audio representation needed. LLM can be used for dynamic generation of corrupted file content and altered text, making each encounter with a corrupted file potentially unique. See llm_integration_ideas.md.]`
* ~~**Navigation Logic:** Implement the logic for `cd` (changing the current directory) and `ls` (listing contents of the current directory), respecting the simulated structure.~~ `[Dev Note: Implemented in file_system_handler.py and command_handler.py commands.]`
* **`cat` Command:** ~~Implement the `cat` command to display file content~~, **applying corruption/glitch effects if the file is marked as corrupted, and potentially revealing hidden data layers.** `[Dev Note: Basic 'cat' with corruption effects implemented in command_handler.py. Hidden data layers integration pending. LLM can be leveraged here to generate dynamic content for files when `cat` is used, especially for corrupted files, files with evolving information, or those containing hidden data layers that react to game state or player knowledge. See llm_integration_ideas.md.]`

### 6. Role-Playing Paths Implementation

* **Role Selection & Background:** Implement a text-based prompt for role choice (White: Redemption Seeker, Grey: Truth Hunter, Black: Power Seeker). Store choice and path-specific background elements (e.g., former Aether security, journalist, terminally ill programmer) in game state. `[Dev Note: Implemented. Role selection UI in main.py. Choice, background, motivation, and initial skill focus stored in GameStateManager (game_state.py) and displayed after selection in main.py. Storyoverview.md IV.B provides detailed backgrounds for further attribute expansion.]`
* **Path-Specific Philosophies & Goals:** Narrative and dialogue should reflect core philosophies (Purifier: cleanse corruption, save consciousnesses; Arbiter: knowledge for all, balance, truth; Ascendant: digital evolution, power, embrace corruption). Ultimate goals (Purification, Revelation, Ascension) should drive path-specific objectives. `[Dev Note: Narrative content and branching logic pending.]`
* **Role Influence on Gameplay & Narrative:** `[Dev Note: This is a major area requiring significant implementation across multiple systems.]`
    *   **Unique Abilities/Commands:** Implement path-specific commands and abilities as detailed in `storyoverview.md` (VI.A-C Unique Abilities) and `gameplay_mechanics.md` (e.g., White Hat: `Firewall`, `Restoration`, `patchwork`, `ghost`; Grey Hat: `Chameleon`, `Barter`, `impersonate`, `broker`; Black Hat: `Consume`, `Corrupt`, `overload`, `rootkit`). `[Dev Note: Basic unique commands implemented: 'integrity_check' (White Hat), 'observe_traffic' (Grey Hat), 'find_exploit' (Black Hat). Defined in commands_config.py, handlers in command_handler.py. Further expansion needed for more complex abilities.]`
    *   **Hacking Mechanics:** Path-specific approaches to security bypass, exploit development, and countermeasures (Ethical Hacking, Tactical Exploitation, Aggressive Infiltration). `[Dev Note: TBD]`
    *   **Digital Archaeology:** Path-specific methods for data recovery, memory analysis, and pattern recognition (Preservation, Intelligence, Exploitation). `[Dev Note: TBD]`
    *   **Entity Interaction:** Path-specific dialogue options, influence systems, and alliance building strategies (Cooperation, Negotiation, Domination). `[Dev Note: TBD]`
    *   **System Integrity:** Path-specific defense mechanics, corruption resistance, and connection security approaches (Resilience, Adaptation, Counterattack). `[Dev Note: TBD]`
    *   **Puzzle/Challenge Solutions:** Paths may have unique ways to approach or solve puzzles. `[Dev Note: TBD, links to Puzzle Systems section]`
    *   **Progression & Skill Development:** Path-specific progression metrics, skill trees, and reputation impacts. `[Dev Note: TBD]`
    *   **Storytelling & Environmental Response:** Terminal interface evolution, narrative branches, critical story moments, and available information tailored to the chosen path. `[Dev Note: TBD]`
    *   **Audio Experience:** Path-specific soundscapes and music themes. `[Dev Note: TBD, links to Audio System section]`
    *   **Allies & Enemies:** Certain digital entities (e.g., Voss fragments, SENTINEL, The Collective, Resistance, Cult of Digital Flesh) will react differently or align with specific paths. `[Dev Note: TBD, links to Entity AI section]`
* **Path Flexibility & Alignment System:** Implement a system to track player alignment, allowing for gradual shifts or major realignments at critical junctures, with corresponding changes in abilities and narrative. `[Dev Note: Not yet implemented, see gameplay_mechanics.md XI.B.]`

### 7. Diverse Simulated Tools & Advanced Toolset

* **Tool Functions:** **Create Python functions for a wide array of simulated tools.** `[Dev Note: Basic commands (ls, cd, cat, mkdir, touch, echo, whoami, hostname, uname, head, tail, rm, mv, status, processes, kill, msfconsole, help, clear, theme, effects commands, role-specific stubs, scan, parse, restore, grep) exist in command_handler.py. Needs significant expansion based on storyoverview.md (IV.A: breach, ghost, mimicry, probe, dissect, shield, purge, disconnect) and gameplay_mechanics.md. Examples include:
    *   **Navigation/File Ops (Advanced):** `grep` (implemented), edit, patch, compile, decrypt, compare.
    *   **System Management:** `status` (implemented), `processes` (implemented), `kill` (implemented), monitor, connect, tunnel, trace.
    *   **Hacking:** breach, inject, spoof, backdoor, rootkit, overload, exploit crafting tools.
    *   **Defense:** shield, scrub, honeytrap, detonate, firewall, inoculate, cleanse.
    *   **Digital Archaeology/Data Recovery (Advanced):** recover, fragment, stitch, extrapolate, echo <fragment>, immerse <memory>, pattern, correlate, reconstruct <event>. (`scan`, `parse`, `restore` are now basic implementations).
    *   **Entity Interaction (Tools):** convince, empathize, pressure, deceive, ally, request, share, mediate, translate, context, emulate. Path-specific: soothe, heal, bargain, threaten, consume.
    *   **Terminal Integrity:** scan <terminal>, purge <subsystem>, isolate <function>, restore <backup>.
    *   **Path-Specific Tools (Advanced):** e.g., White Hat: `patchwork`, `quarantine`; Grey Hat: `impersonate`, `redirect`; Black Hat: `assimilate`, `corrupt <entity>`.
    *   Consider if `msfconsole` remains a monolithic tool or if its functionalities are broken into smaller, more focused commands/tools.]`
* **Simulated Output:** **Generate realistic, stylized text output for all tools, reflecting their function and potential corruption effects.** `[Dev Note: Output for new tools TBD. Must align with terminal rendering capabilities. Leverage LLM for dynamic and context-aware tool output, especially for tools like MSFConsole (e.g., exploit results) or complex analysis tools, making their feedback more varied and responsive to the game state. See llm_integration_ideas.md.]`
* **Tool Interaction & Sub-Parsers:** **For complex tools or toolsets (like hacking suites or advanced analysis tools), implement sub-parsers or dedicated states if necessary.** `[Dev Note: \`msfconsole\` sub-parser exists. Evaluate need for others as tools are designed. For \`msfconsole\`, LLM can enhance the experience by generating dynamic outcomes for exploits, revealing unique information, triggering Scourge reactions, or providing unsettling feedback based on the target and exploit used. See llm_integration_ideas.md.]`
* **Integrating Horror & Narrative:** Design how tool usage (e.g., scanning corrupted data, breaching secure systems, interacting with volatile entities) can trigger horror events, glitch effects, unsettling LLM outputs, or narrative developments. `[Dev Note: Specific triggers and integrations TBD.]`
* **Tool Crafting/Development:** Implement system for players to `compile <source>` or `patch <file>` to create/modify tools from discovered code fragments, as per `gameplay_mechanics.md`. `[Dev Note: Not yet implemented.]`

### 8. Puzzle and Challenge Systems (Core Gameplay)

*   **Design and Implement Diverse Puzzles:** ~~Create text-based puzzles~~ `[Dev Note: Initial framework implemented in puzzle_manager.py with base Puzzle class and examples (SequenceCompletionPuzzle, CaesarCipherPuzzle). Integrated with game state (STATE_PUZZLE_ACTIVE) and command handler (`start_puzzle`, `solve`, `hint`, `exit_puzzle`). Based on gameplay_mechanics.md VI and Key Need 2 from original devprompt. Further puzzle types and LLM integration for adaptive puzzles TBD. See llm_integration_ideas.md.]`
    *   Code-Based Puzzles: Algorithm challenges (sequence completion, function repair), implementation challenges (scripting, debugging). `[Dev Note: SequenceCompletionPuzzle is a basic example.]`
    *   Cryptographic Puzzles: Classical ciphers, custom Aether encryption, corrupted encryption. `[Dev Note: CaesarCipherPuzzle is a basic example.]`
    *   System Manipulation Challenges: Resource management (processing power, storage), environmental manipulation (power cycling, clock sync). `[Dev Note: TBD]`
    *   Entity-Based Challenges: Memory reconstruction, identity challenges, social engineering, deception detection. `[Dev Note: TBD]`
*   **Path-Specific Solutions:** Ensure puzzles have path-specific solution approaches or unique advantages/disadvantages for each role. `[Dev Note: TBD]`
*   **Puzzle Integration:** Integrate puzzles into the narrative, environment, and tool interactions. `[Dev Note: TBD]`
*   **Difficulty Scaling:** Consider how puzzle difficulty might scale or adapt. `[Dev Note: TBD. LLM-driven adaptive puzzle generation can be a key mechanism for dynamically adjusting puzzle difficulty based on player performance and progression. See llm_integration_ideas.md.]`

### 9. Entity AI and Interaction Systems (Core RPG/Narrative)

*   **Develop Entity AI:** Implement AI for key digital entities (Dr. Voss fragments, SENTINEL, The Collective, Aetherial Scourge manifestations). `[Dev Note: TBD. Based on Key Need 7 from original devprompt. This includes LLM-driven systems for the Aetherial Scourge's adaptive AI and behavior, and for creating distinct "Digital Ghosts" with unique personalities and backstories that react to the player. See llm_integration_ideas.md.]`
    *   Manage behavior, dialogue trees/generation, and reactions to player actions.
    *   Incorporate entity roles in puzzles and narrative progression.
*   **Interaction Mechanics:** Implement systems for diverse player-entity interactions. `[Dev Note: TBD]`
    *   Persuasion, negotiation, deception, intimidation.
    *   Alliance building, reputation systems.
    *   Path-specific interaction styles (e.g., White Hat: Empathy, Grey Hat: Barter, Black Hat: Domination).
*   **LLM for Dynamic Dialogue:** Explore using LLM for more dynamic or emergent entity responses where appropriate, complementing pre-written content. `[Dev Note: TBD, links to LLM Integration section. This will involve enabling Natural Language Interaction (NLI) with certain entities, allowing players to type free-form messages, and generating role-specific dialogue variations to enhance replayability and path distinction. See llm_integration_ideas.md.]`

### 10. Atmosphere: Text Effects & Visual Anomalies

* ~~**Color Themes:** Define color palettes (dictionaries of Pygame color tuples) for different text styling themes (e.g., Corrupted Kali, Digital Nightmare). Implement logic to set the active theme and apply its colors during text rendering.~~ `[Dev Note: Implemented in effects.py and integrated into terminal_renderer.py and main.py theme command.]`
* **Basic Text Effects:**
    * ~~**Typing Simulation:** Implement a function to display text character by character with a timed delay.~~ `[Dev Note: TypingEffect in effects.py, 'type' command in main.py]`
    * ~~**Timed Delays/Sudden Bursts:** Implement functions to pause output or display a block of text instantly.~~ `[Dev Note: TimedDelayEffect and TypingEffect (0 delay) in effects.py, 'burst' command in main.py]`
* **Simulated Text Glitches and Visual Anomalies:**
    * ~~**Character Corruption:** Implement a function to randomly replace characters in a string with other characters or symbols for a short duration.~~ `[Dev Note: CharacterCorruptionEffect in effects.py, 'corrupt' command in main.py]`
    * ~~**Flickering Text:** Implement logic to rapidly toggle the visibility or color of specific text elements.~~ `[Dev Note: TextFlickerEffect in effects.py, 'flicker' command in main.py]`
    * ~~**Unexpected Color Shifts:** Implement functions to temporarily change the color of text.~~ `[Dev Note: TemporaryColorChangeEffect in effects.py, 'colorchange' command in main.py]`
    * ~~**Text Overlays:** Implement logic to draw random characters or symbols over existing text for a brief period.~~ `[Dev Note: TextOverlayEffect in effects.py, 'overlay' command in main.py]`
    * ~~**Coordinate Manipulation:** Potentially slightly offset text rendering positions randomly to create a jiggling or unstable effect.~~ `[Dev Note: TextJiggleEffect in effects.py, 'jiggle' command in main.py]`
    * **Inverted/Corrupted Blocks:** Use ANSI escape codes or similar for color inversion or drastic color changes on random text blocks. `[Dev Note: TBD]`
    * **"Worm" Trails:** Implement a trail of corrupted characters or symbols that briefly follow the cursor. `[Dev Note: TBD]`
    * **Sudden Line Breaks/Wrapping:** Introduce unexpected line breaks mid-word or sentence. `[Dev Note: TBD]`
    * **Overwriting/Binary Injections:** Simulate data overwrite by briefly printing '0's, '1's, or glitch symbols over existing text. `[Dev Note: TBD]`
    * **Uneven Typing Speed:** Vary character display delays significantly, including long pauses (enhancement to Typing Simulation). `[Dev Note: TBD, potentially refine TypingEffect]`
    * **Textual "Breathing":** Slowly pulse text color intensity or background color. `[Dev Note: TBD]`
    * **Simulated Scan Lines/Static:** Overlay lines of noise characters (e.g., '.', ',', '-') with subtle colors. `[Dev Note: TBD]`
    * **"Bleeding" Colors:** Have a line's ending color briefly influence the start of the next line. `[Dev Note: TBD]`
    * **"Redacted" Terminal Output:** Use block characters (e.g., `█`) or background color changes to simulate redacted text. `[Dev Note: TBD]`
    * **Intrusive Thoughts/Echoes:** Briefly display and then overwrite fragmented, unsettling words during text rendering. `[Dev Note: TBD]`
    * **Dynamic/Corrupted Error Messages:** Ensure error messages can be dynamically corrupted or display disturbing content. `[Dev Note: TBD, link to error handling]`
* **Integration:** ~~Design how these effects can be triggered by game events, narrative moments, or specific command outputs.~~ `[Dev Note: EffectManager in effects.py manages a queue. Commands in main.py trigger effects. Narrative/event-driven triggers beyond commands are TBD, and will need to incorporate these new effects.]`

### 11. Atmosphere: Audio System Implementation

* **Terminal Audio System:** `[Dev Note: Not yet implemented. Requires AudioManager and sound assets.]`
    *   **Functional Audio:** Distinct sounds for command types, success/failure, alerts, ambient processing.
    *   **Atmospheric Elements:** Background tones per system layer, rhythmic elements, distant echoes, white noise with subliminals.
    *   **Audio Corruption Effects:** Progressive distortion, unexpected silences, fragmentation, sound bleed-through, interactive audio clues.
* **Entity Vocalization:** `[Dev Note: Not yet implemented]`
    *   **Communication Styles:** Specific audio profiles for Scourge, consciousness fragments, system entities (e.g., SENTINEL), The Collective.
    *   **Emotional Expression:** Tone, rate, harmony, glitch patterns conveying emotion/intent.
    *   **Audio Interaction:** Voice recognition patterns, emotional analysis, truth detection via audio.
* **Path-Specific Audio Experience:** `[Dev Note: Not yet implemented]`
    *   **White Hat:** Cleaner, harmonic, clear warnings, restoration sounds.
    *   **Grey Hat:** Information-dense, pattern-focused, neutral tones, adaptive mixing.
    *   **Black Hat:** Power-focused bass, aggressive, satisfying dominance feedback, corruption-influenced.
* **Music Design (Adaptive Soundtrack):** `[Dev Note: Not yet implemented]`
    *   **Composition:** Algorithmic generation based on state, layer-based intensity, entity/location motifs, corruption-level harmonics.
    *   **Integration:** Tension mapping, discovery cues, relationship themes, path-aligned development.
    *   **Interactive Elements:** Player actions influencing melody/rhythm, hidden musical puzzles/info.
* **Sound Loading & Playback Control:** Load diverse assets (digital noises, stings, drones, voices, music) and implement robust playback controls (play, loop, volume, spatialization if possible). `[Dev Note: Pygame Mixer initialized in main.py. Basic keypress sound ('sounds/keypress.wav') loaded and played on KEYDOWN events. Further development for diverse assets and controls needed, likely via an AudioManager.]`
* **Triggering Audio:** Integrate audio playback with game events, state changes, horror triggers, command execution, entity interactions, and narrative beats. `[Dev Note: Logic for triggering specific sounds pending.]`

### 12. Atmosphere: Local LLM Integration for Dynamic Content

* Ollama Connection: Implement Python code to connect to the local Ollama instance via its API (using `requests` or an Ollama client library). `[Dev Note: Not yet implemented]`
* **Prompt Engineering:** Develop specific prompts for `aethercorp` to generate unsettling text for various contexts: Aetherial Scourge manifestations, dialogue from fragmented consciousnesses (Dr. Voss, The Collective, etc.), corrupted files/logs, environmental descriptions, and responses from entities like SENTINEL. Prompts should consider entity personalities and current game state/corruption levels. `[Dev Note: Not yet implemented. Storyoverview.md provides rich source material for entity voices. Key LLM applications to develop prompts for include: the Aetherial Scourge's adaptive AI, Digital Ghost encounters, dynamic file content generation, Natural Language Interaction (NLI) with entities, adaptive/personalized horror systems, role-specific content variations, and emergent narrative progression. See llm_integration_ideas.md for detailed concepts.]`
* Triggering LLM: Design game events or commands that trigger calls to the LLM. `[Dev Note: Not yet implemented. Triggers will include specific commands (e.g., interacting with entities, using certain tools), outcomes of actions (e.g., MSFConsole exploits), environmental interactions, narrative checkpoints, player requests for hints or puzzle generation, and dynamic horror events like command interceptions or terminal takeovers. See llm_integration_ideas.md.]`
* Processing and Display: Receive the LLM's text response, process it (e.g., format it, add timestamps), and display it in the terminal using Pygame text rendering, applying appropriate styling and potentially glitch effects. `[Dev Note: Not yet implemented]`

### 13. Horror Event Engine (Core Horror Mechanic)

*   **Design Horror Event System:** Create a system for triggering scripted and dynamic horror events. `[Dev Note: TBD. Based on Key Need 10 from original devprompt. This system should incorporate LLM-driven elements such as an Adaptive/Personalized Horror system that learns and targets player sensitivities, and Dynamic Terminal Takeover events where the LLM seizes control of the terminal for unsettling sequences. See llm_integration_ideas.md.]`
    *   Events can include visual glitches, unsettling text/audio, Aetherial Scourge manifestations, environmental changes.
*   **Trigger Conditions:** Define triggers based on player actions (command usage, file access), location, narrative progression, puzzle failures, or random chance. `[Dev Note: TBD]`
*   **Intensity/Escalation:** Implement logic for escalating horror intensity or frequency based on game state or player choices. `[Dev Note: TBD. LLM-based adaptive and personalized horror systems can dynamically tailor the intensity, frequency, and type of horror events to the player's profile and in-game actions, creating a more bespoke and impactful experience. See llm_integration_ideas.md.]`
*   **Integration with Effects:** Leverage existing text and visual effects, and integrate with audio and LLM systems for richer horror experiences. `[Dev Note: TBD]`

### 14. Simulated In-Game Helper System

* **Knowledge Base Data:** Store knowledge base entries, tutorials, lore, and hints. This includes information on commands, tools, system mechanics, Aether Corp history, entity profiles, etc. `[Dev Note: `help` command is basic. Need a more structured KB. `gameplay_mechanics.md` mentions `research <topic>` for compiling info.]`
* **Helper Command:** **Implement `help [topic]`, `teach <entity> <knowledge>`, and potentially `research <topic>` to access and utilize the knowledge base.** `[Dev Note: \`help\` needs expansion. \`teach\` and \`research\` commands not yet implemented. An LLM-powered context-aware hint system could augment or replace traditional help, providing subtle, in-universe guidance when the player seems stuck. See llm_integration_ideas.md.]`
* Contextual Hints: Implement logic to check the player's current state or recent commands and occasionally display relevant hints as text output. `[Dev Note: Not yet implemented. LLM can generate these hints dynamically, making them more relevant to the player's specific situation and integrated with the horror atmosphere (e.g., hints appearing as system glitches, corrupted messages, or fragmented echoes from other entities). See llm_integration_ideas.md.]`
* Corruption/Unsettling Output: Design how helper text or knowledge base entries can become corrupted or display unsettling messages, potentially triggered by horror events or player actions. `[Dev Note: Not yet implemented]`

### 15. Persistence and Meta-Gameplay (Save/Load, NG+)

* Save Function: Implement a function to save the current game state (player location, inventory, unlocked content, narrative flags, active theme, state of simulated environments) to a file (e.g., JSON format) using Python's file I/O. `[Dev Note: Not yet implemented]`
* Load Function: Implement a function to load the game state from a file. Include error handling for missing or corrupted save files. `[Dev Note: Not yet implemented]`
* **Save/Load Menu/Commands:** Implement text-based commands (`save [slot]`, `load [slot]`) or a menu state. `[Dev Note: Not yet implemented. Consider `SAVE_MENU` state.]`
* **Simulated Save/Load Anomalies (Optional Horror):** For added horror, occasionally introduce minor, unsettling changes or glitch effects when loading. `[Dev Note: Not yet implemented.]`
* **New Game Plus:** Plan for NG+ features, allowing retention of some knowledge/skills and introducing new challenges/story layers as per `gameplay_mechanics.md` (XIV.A). `[Dev Note: Design phase for NG+ elements.]`

### 16. Content Creation (Massive Undertaking)

* **Narrative Text:** **Write extensive pre-written narrative content.** This includes: `[Dev Note: Major content creation task. Storyoverview.md is the primary source. Explore LLM integration for dynamic narrative progression, emergent storylines that adapt to player choices and discoveries, and generating variations in environmental descriptions or recovered logs to enhance replayability. See llm_integration_ideas.md.]`
    *   Environmental descriptions for Aether Network layers (Quarantine, Corporate Shell, Dev Sphere, Neural Network, Core).
    *   Dialogue for key digital entities (Voss fragments, SENTINEL, The Collective, Lazarus Protocol, Preserved, Fragments, Consumed, Emergent entities).
    *   Scripts for key narrative moments (First Fragment, Memory Cluster, Broken Child, Council of Voss, path-specific critical moments, final confrontation).
    *   Path-specific branching dialogue and events.
    *   Text for recovered logs, emails, documents.
* **Filesystem Content:** Write content for simulated files within the Aether Network. `[Dev Note: `file_system_handler.py` is a start. Needs expansion.]`
    *   Normal files (manuals, logs, emails, project data).
    *   Corrupted versions with glitch text and hidden data.
    *   Encrypted files, fragmented data requiring reconstruction.
    *   Files specific to Aether's projects (ETERNAL, SENTINEL, SYNTHESIS).
* **Puzzle/Minigame Logic & Content:** Define rules, content, and implementation for diverse text-based challenges. `[Dev Note: Critical gameplay component, not yet implemented. Based on gameplay_mechanics.md VI. Links to Puzzle Systems section.]`
    *   **Code-Based Puzzles:** Algorithm challenges (sequence completion, function repair), implementation challenges (scripting, debugging).
    *   **Cryptographic Puzzles:** Classical ciphers, custom Aether encryption, corrupted encryption.
    *   **System Manipulation Challenges:** Resource management (processing power, storage), environmental manipulation (power cycling, clock sync).
    *   **Entity-Based Challenges:** Memory reconstruction, identity challenges, social engineering, deception detection.
    *   Path-specific approaches to solving these puzzles.
* **Tool Output Examples:** **Write examples of simulated output for all new tools and commands.** `[Dev Note: Output needed for the greatly expanded toolset.]`
* **LLM Prompt Library:** Develop a comprehensive library of prompts for Ollama, tailored to different entities, situations, and horror effects. `[Dev Note: Requires significant creative writing and testing. Links to LLM Integration section. This library must cover prompts for all integrated LLM systems: Aetherial Scourge AI, Digital Ghosts, dynamic file content, command interception/manipulation, MSFConsole enhancements, Natural Language Interaction with entities, adaptive/personalized horror, dynamic terminal takeovers, narrative progression/events, adaptive puzzle generation, context-aware hints, and role-specific content generation. See llm_integration_ideas.md for specific system concepts.]`
* **Horror Triggers:** Design specific narrative points, environmental states, tool usages, or puzzle failures that trigger horror events, glitch effects, unsettling LLM calls, or audio cues. `[Dev Note: Link to story beats from storyoverview.md and Scourge manifestations. Links to Horror Event Engine section.]`
* **Sound Assets:** Create or source a wide range of sound effects (terminal sounds, glitches, ambient drones, entity vocalizations) and music (adaptive soundtrack, path-specific themes). `[Dev Note: Major asset creation/sourcing task based on detailed audio plan. Links to Audio System section.]`

### 17. Refinement, Polish, Testing, and Balancing

* Text Rendering Performance: Optimize text rendering for smooth scrolling and display, especially with large amounts of output. `[Dev Note: Line height calculation in terminal_renderer.py adjusted to use font.get_linesize() and LINE_SPACING set to 0, resolving text overlap issues, including after screen resize. Further optimization if other issues arise.]`
* Input Handling Robustness: Improve input parsing to handle various user inputs gracefully. `[Dev Note: Good foundation in terminal_renderer.py. Tab completion for main terminal commands exists. MSFConsole tab-completion logic is now centralized in command_handler.py.]`
* Balancing: Adjust difficulty of minigames, frequency of horror events, and impact of role choices. `[Dev Note: TBD, pending implementation of these features.]`
* **Testing:** **Thoroughly test all systems, adhering to the guidelines outlined in [`unittests_guidelines.md`](unittests_guidelines.md:).** `[Dev Note: Unit tests for core modules exist. Unit tests for PuzzleManager, SequenceCompletionPuzzle, and CaesarCipherPuzzle implemented in tests/test_puzzle_manager.py. Main terminal command parsing refactor (using `shlex.split()`) and MSFConsole enhancements (mouse scroll, `clear` command, scroll-to-bottom for search) have been implemented and corresponding unit tests in `test_command_handler.py`, `test_commands_config.py`, and `test_main.py` were added/updated. All 523 tests are passing. Needs expansion for:
    *   All new commands and tools, including complex interactions and edge cases.
    *   Role-playing path mechanics, abilities, and narrative branches.
    *   Further puzzle/minigame logic and solutions.
    *   LLM integration, prompt effectiveness, and response handling.
    *   Audio system triggers and playback.
    *   Persistence (save/load, New Game Plus).
    *   Horror triggers and atmospheric effects.
    *   Game balance across different paths and player skills.]`
* Packaging: Prepare the application for distribution on target platforms. `[Dev Note: TBD]`
