# --- Player Roles ---
ROLE_NONE = None # Default before selection
ROLE_PURIFIER = "PURIFIER"
ROLE_ARBITER = "ARBITER"
ROLE_ASCENDANT = "ASCENDANT"

# --- Role-Based Command Access ---
COMMAND_ACCESS = {
    ROLE_PURIFIER: {
        "allowed_main": [
            "help", "clear", "ls", "cd", "pwd", "cat", "grep", "scan", "parse",
            "restore", "status", "processes", "kill", "quit", "exit", "theme", "type", "burst", "sequence", "corrupt", "flicker", "colorchange", "overlay", "jiggle", "screenres", "fullscreen", "windowed", "whoami", "hostname", "uname", "head", "tail", "mkdir", "touch", "echo",
            "convince", "empathize", "ally", "rusty"
        ],
        "allowed_msf": ["help", "clear", "search", "use", "info", "show", "set", "back", "exit", "sessions"],
        "allowed_puzzle": ["help", "solve", "hint", "exit_puzzle", "theme", "quit", "exit"],
        "help_text_main": {
            "help": "  help              - Show this help message",
            "clear": "  clear             - Clear the terminal screen",
            "ls": "  ls                - List directory contents",
            "cd": "  cd <dir>          - Change directory",
            "pwd": "  pwd               - Print working directory",
            "cat": "  cat <file>        - Display file content",
            "grep": "  grep <pattern> <file> - Search for PATTERN in FILE",
            "scan": "  scan <file>       - Analyze a file for corruption",
            "parse": "  parse <file>      - Attempt to extract readable data from a file",
            "restore": "  restore <file>    - Attempt to repair a corrupted file",
            "status": "  status            - Display system status overview",
            "processes": "  processes         - List running simulated processes",
            "kill": "  kill <pid>        - Terminate a simulated process",
            "quit": "  quit              - Exit the game",
            "exit": "  exit              - Exit the game (alias for quit)",
            "theme": "  theme <name>      - Change terminal theme",
            "type": "  type <text>       - Simulate typing the given text",
            "burst": "  burst <text>      - Instantly display the given text",
            "sequence": "  sequence          - Demonstrate a sequence of typing and delays",
            "corrupt": "  corrupt <off> [dur] [int] [rate] - Corrupt line",
            "flicker": "  flicker <off> [dur] [rate] [key] - Flicker line",
            "colorchange": "  colorchange <off> <dur> [fg] [bg] - Temp change line color",
            "overlay": "  overlay [dur] [num] [key] [rate] - Show text overlay",
            "jiggle": "  jiggle <off> [dur] [int] [rate] - Jiggle line",
            "screenres": "  screenres <W>x<H> - Change screen resolution",
            "fullscreen": "  fullscreen        - Switch to fullscreen mode",
            "windowed": "  windowed          - Switch to windowed mode",
            "whoami": "  whoami            - Print current username",
            "hostname": "  hostname          - Print hostname",
            "uname": "  uname [-a]        - Print system information",
            "head": "  head [-n N] <file>- Show first N lines",
            "tail": "  tail [-n N] <file>- Show last N lines",
            "mkdir": "  mkdir <dirname>   - Create a new directory",
            "touch": "  touch <filename>  - Create/update file",
            "echo": "  echo [text]       - Print text",
            "convince": "  convince <entity> <message> - Attempt to convince an entity through reasoning",
            "empathize": "  empathize <entity> <message> - Connect with an entity through shared understanding",
            "ally": "  ally <entity> <message> - Offer cooperation to an entity",
            "rusty": "  rusty <message>   - Interact with the Rusty assistant"
        },
        "help_text_puzzle": {
            "help": "  help              - Show puzzle mode help",
            "solve": "  solve <answer>    - Attempt to solve the active puzzle",
            "hint": "  hint              - Get a hint for the active puzzle",
            "exit_puzzle": "  exit_puzzle       - Leave the current puzzle",
            "theme": "  theme <name>      - Change terminal theme",
            "quit": "  quit              - Exit the game",
            "exit": "  exit              - Exit the game (alias for quit)"
        },
        "help_text_msf": {
            "help": "  help             - Show this help",
            "clear": "  clear            - Clear the msfconsole screen",
            "search": "  search <keyword> - Search for modules",
            "use": "  use <module>     - Select a module",
            "info": "  info [module]    - Display information about a module",
            "show": "  show             - Show options for the current module",
            "set": "  set <opt> <val>  - Set an option",
            "back": "  back             - Return to the main terminal",
            "exit": "  exit             - Exit msfconsole",
            "sessions": "  sessions [-l]    - List active sessions"
        }
    },
    ROLE_ARBITER: {
        "allowed_main": [
            "help", "clear", "ls", "cd", "pwd", "cat", "grep", "scan", "parse",
            "restore", "status", "processes", "kill", "quit", "exit", "theme", "type", "burst", "sequence", "corrupt", "flicker", "colorchange", "overlay", "jiggle", "screenres", "fullscreen", "windowed", "whoami", "hostname", "uname", "head", "tail", "mkdir", "touch", "echo", "rm", "mv", "msfconsole",
            "convince", "empathize", "pressure", "deceive", "ally", "rusty"
        ],
        "allowed_msf": ["help", "clear", "search", "use", "info", "show", "set", "run", "exploit", "back", "exit", "sessions"],
        "allowed_puzzle": ["help", "solve", "hint", "exit_puzzle", "theme", "quit", "exit"],
        "help_text_main": {
            "grep": "  grep <pattern> <file> - Search for PATTERN in FILE",
            "scan": "  scan <file>       - Analyze a file for corruption",
            "parse": "  parse <file>      - Attempt to extract readable data from a file",
            "restore": "  restore <file>    - Attempt to repair a corrupted file",
            "write": "  write <file> <content> - Writes content to a file",
            "observe_traffic": "  observe_traffic   - Monitors network traffic for anomalies",
            "start_puzzle": "  start_puzzle <id> - Activate a puzzle challenge",
            "analyze_log": "  analyze_log <pattern> - Analyzes the project_eternal.log file for a specific pattern",
            "help": "  help              - Show this help message",
            "clear": "  clear             - Clear the terminal screen",
            "theme": "  theme <name>      - Change terminal theme",
            "type": "  type <text>       - Simulate typing the given text",
            "burst": "  burst <text>      - Instantly display the given text",
            "sequence": "  sequence          - Demonstrate a sequence of typing and delays",
            "corrupt": "  corrupt <off> [dur] [int] [rate] - Corrupt line",
            "flicker": "  flicker <off> [dur] [rate] [key] - Flicker line",
            "colorchange": "  colorchange <off> <dur> [fg] [bg] - Temp change line color",
            "overlay": "  overlay [dur] [num] [key] [rate] - Show text overlay",
            "jiggle": "  jiggle <off> [dur] [int] [rate] - Jiggle line",
            "screenres": "  screenres <W>x<H> - Change screen resolution",
            "fullscreen": "  fullscreen        - Switch to fullscreen mode",
            "windowed": "  windowed          - Switch to windowed mode",
            "pwd": "  pwd               - Print working directory",
            "ls": "  ls                - List directory contents",
            "cd": "  cd <dir>          - Change directory",
            "cat": "  cat <file>        - Display file content",
            "mkdir": "  mkdir <dirname>   - Create a new directory",
            "touch": "  touch <filename>  - Create/update file",
            "echo": "  echo [text]       - Print text",
            "whoami": "  whoami            - Print current username",
            "hostname": "  hostname          - Print hostname",
            "uname": "  uname [-a]        - Print system information",
            "head": "  head [-n N] <file>- Show first N lines",
            "tail": "  tail [-n N] <file>- Show last N lines",
            "rm": "  rm <file/dir>     - Remove a file or directory",
            "mv": "  mv <src> <dest>   - Move/rename a file or directory",
            "status": "  status            - Display system status overview",
            "processes": "  processes         - List running simulated processes",
            "kill": "  kill <pid>        - Terminate a simulated process",
            "msfconsole": "  msfconsole        - Start the Metasploit console",
            "quit": "  quit              - Exit the game",
            "exit": "  exit              - Exit the game (alias for quit)",
            "talk": "talk <character_id> [message] - Interact with characters in the system",
            "story": "story - Show current story context and available choices",
            "choose": "choose <choice_id> - Make a story choice",
            "convince": "  convince <entity> <message> - Attempt to convince an entity through reasoning",
            "empathize": "  empathize <entity> <message> - Connect with an entity through shared understanding",
            "pressure": "  pressure <entity> <message> - Apply strategic pressure to an entity",
            "deceive": "  deceive <entity> <message> - Attempt to mislead an entity for strategic advantage",
            "ally": "  ally <entity> <message> - Offer cooperation to an entity",
            "rusty": "  rusty <message>   - Interact with the Rusty assistant"
        },
        "help_text_puzzle": {
            "solve": "  solve <answer>    - Attempt to solve the active puzzle",
            "hint": "  hint              - Get a hint for the active puzzle",
            "exit_puzzle": "  exit_puzzle       - Leave the current puzzle",
            "help": "  help              - Show puzzle mode help",
            "theme": "  theme <name>      - Change terminal theme",
            "quit": "  quit              - Exit the game",
            "exit": "  exit              - Exit the game (alias for quit)"
        },
        "help_text_msf": {
            "clear": "  clear            - Clear the msfconsole screen",
            "help": "  help             - Show this help",
            "search": "  search <keyword> - Search for modules",
            "use": "  use <module>     - Select a module",
            "info": "  info [module]    - Display information about a module",
            "show": "  show             - Show options for the current module",
            "set": "  set <opt> <val>  - Set an option",
            "run": "  run / exploit    - Execute the current module",
            "exploit": "  run / exploit    - Execute the current module (alias for run)",
            "sessions": "  sessions [-l]    - List active sessions",
            "back": "  back             - Return to the main terminal",
            "exit": "  exit             - Exit msfconsole"
        }
    },
    ROLE_ASCENDANT: {  # Same as Grey Hat for now, can diverge later
        "allowed_main": [
            "help", "clear", "ls", "cd", "pwd", "cat", "grep", "scan", "parse",
            "restore", "status", "processes", "kill", "quit", "exit", "theme", "type", "burst", "sequence", "corrupt", "flicker", "colorchange", "overlay", "jiggle", "screenres", "fullscreen", "windowed", "whoami", "hostname", "uname", "head", "tail", "mkdir", "touch", "echo", "rm", "mv",
            "threaten", "fragment", "enslave", "consume", "rusty"
        ],
        "allowed_msf": ["help", "clear", "search", "use", "info", "show", "set", "run", "exploit", "back", "exit", "sessions"],
        "allowed_puzzle": ["help", "solve", "hint", "exit_puzzle", "theme", "quit", "exit"],
        "help_text_main": { # Black Hat sees all standard commands
            "grep": "  grep <pattern> <file> - Search for PATTERN in FILE",
            "scan": "  scan <file>       - Analyze a file for corruption",
            "parse": "  parse <file>      - Attempt to extract readable data from a file",
            "restore": "  restore <file>    - Attempt to repair a corrupted file",
            "write": "  write <file> <content> - Writes content to a file",
            "find_exploit": "  find_exploit      - Searches for known vulnerabilities in the current system",
            "start_puzzle": "  start_puzzle <id> - Activate a puzzle challenge",
            "analyze_log": "  analyze_log <pattern> - Analyzes the project_eternal.log file for a specific pattern",
            "help": "  help              - Show this help message",
            "clear": "  clear             - Clear the terminal screen",
            "theme": "  theme <name>      - Change terminal theme",
            "type": "  type <text>       - Simulate typing the given text",
            "burst": "  burst <text>      - Instantly display the given text",
            "sequence": "  sequence          - Demonstrate a sequence of typing and delays",
            "corrupt": "  corrupt <off> [dur] [int] [rate] - Corrupt line",
            "flicker": "  flicker <off> [dur] [rate] [key] - Flicker line",
            "colorchange": "  colorchange <off> <dur> [fg] [bg] - Temp change line color",
            "overlay": "  overlay [dur] [num] [key] [rate] - Show text overlay",
            "jiggle": "  jiggle <off> [dur] [int] [rate] - Jiggle line",
            "screenres": "  screenres <W>x<H> - Change screen resolution",
            "fullscreen": "  fullscreen        - Switch to fullscreen mode",
            "windowed": "  windowed          - Switch to windowed mode",
            "pwd": "  pwd               - Print working directory",
            "ls": "  ls                - List directory contents",
            "cd": "  cd <dir>          - Change directory",
            "cat": "  cat <file>        - Display file content",
            "mkdir": "  mkdir <dirname>   - Create a new directory",
            "touch": "  touch <filename>  - Create/update file",
            "echo": "  echo [text]       - Print text",
            "whoami": "  whoami            - Print current username",
            "hostname": "  hostname          - Print hostname",
            "uname": "  uname [-a]        - Print system information",
            "head": "  head [-n N] <file>- Show first N lines",
            "tail": "  tail [-n N] <file>- Show last N lines",
            "rm": "  rm <file/dir>     - Remove a file or directory",
            "mv": "  mv <src> <dest>   - Move/rename a file or directory",
            "status": "  status            - Display system status overview",
            "processes": "  processes         - List running simulated processes",
            "kill": "  kill <pid>        - Terminate a simulated process",
            "msfconsole": "  msfconsole        - Start the Metasploit console",
            "quit": "  quit              - Exit the game",
            "exit": "  exit              - Exit the game (alias for quit)",
            "talk": "talk <character_id> [message] - Interact with characters in the system",
            "story": "story - Show current story context and available choices",
            "choose": "choose <choice_id> - Make a story choice",
            "threaten": "  threaten <entity> <message> - Intimidate an entity to force compliance",
            "fragment": "  fragment <entity> <message> - Attempt to break an entity's coherence",
            "enslave": "  enslave <entity> <message> - Subjugate an entity to your will",
            "consume": "  consume <entity> <message> - Absorb an entity's essence or knowledge",
            "rusty": "  rusty <message>   - Interact with the Rusty assistant"
        },
        "help_text_puzzle": {
            "solve": "  solve <answer>    - Attempt to solve the active puzzle",
            "hint": "  hint              - Get a hint for the active puzzle",
            "exit_puzzle": "  exit_puzzle       - Leave the current puzzle",
            "help": "  help              - Show puzzle mode help",
            "theme": "  theme <name>      - Change terminal theme",
            "quit": "  quit              - Exit the game",
            "exit": "  exit              - Exit the game (alias for quit)"
        },
        "help_text_msf": { # Black Hat sees all msf commands
            "clear": "  clear            - Clear the msfconsole screen",
            "help": "  help             - Show this help",
            "search": "  search <keyword> - Search for modules",
            "use": "  use <module>     - Select a module",
            "info": "  info [module]    - Display information about a module",
            "show": "  show             - Show options for the current module",
            "set": "  set <opt> <val>  - Set an option",
            "run": "  run / exploit    - Execute the current module",
            "exploit": "  run / exploit    - Execute the current module (alias for run)",
            "sessions": "  sessions [-l]    - List active sessions",
            "back": "  back             - Return to the main terminal",
            "exit": "  exit             - Exit msfconsole"
        }
    }
}

# Export role commands data for test compatibility
ROLE_COMMANDS = {
    "purifier": COMMAND_ACCESS[ROLE_PURIFIER]["allowed_main"],
    "arbiter": COMMAND_ACCESS[ROLE_ARBITER]["allowed_main"],
    "ascendant": COMMAND_ACCESS[ROLE_ASCENDANT]["allowed_main"]
}

# Export command help data for test compatibility
COMMAND_HELP = {}
for role_data in COMMAND_ACCESS.values():
    if "help_text_main" in role_data:
        for cmd, help_text in role_data["help_text_main"].items():
            COMMAND_HELP[cmd] = help_text