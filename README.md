# Cyberscape: Digital Dread

A terminal-based horror RPG that combines classic text adventure gameplay with modern horror elements and AI-driven narrative experiences.

## Overview

Cyberscape: Digital Dread is a unique horror game that takes place entirely within a terminal interface. Players navigate through a corrupted digital landscape, solving puzzles, uncovering mysteries, and facing the malevolent Aetherial Scourge that threatens to consume the digital realm.

## Features

- **Terminal-Based Interface**: Authentic terminal experience with ASCII art and text-based interactions
- **Dynamic Horror Elements**: Corruption effects, glitch mechanics, and psychological horror
- **AI-Driven Narrative**: LLM-powered storytelling that adapts to player choices
- **Multiple Roles**: Play as White Hat, Grey Hat, or Black Hat hacker
- **Complex Puzzles**: System-based puzzles that integrate with the game's narrative
- **Immersive Audio**: Dynamic sound effects and ambient audio
- **Corruption System**: Progressive corruption mechanics that affect gameplay and narrative

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/cyberscape.git
cd cyberscape
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the game:
```bash
python src/main.py
```

## Project Structure

```
cyberscape/
├── assets/                 # Game assets (images, fonts, etc.)
├── config/                 # Configuration files
│   ├── game/              # Game-specific configs
│   └── llm/               # LLM integration configs
├── data/                  # Game data files
│   ├── audio/            # Audio data
│   ├── logs/             # Game logs
│   ├── personal/         # Player-specific data
│   ├── puzzles/          # Puzzle data
│   ├── security/         # Security-related data
│   └── system/           # System configuration files
├── docs/                  # Documentation
│   ├── design/           # Game design docs
│   ├── story/            # Story and narrative docs
│   └── technical/        # Technical documentation
├── saves/                # Game save files
├── sounds/               # Sound effects and music
├── src/                  # Source code
│   ├── audio/           # Audio system
│   ├── core/            # Core game systems
│   ├── puzzle/          # Puzzle system
│   ├── story/           # Story and narrative system
│   ├── ui/              # User interface
│   └── utils/           # Utility functions
├── tests/               # Test files
```

## Development

### Prerequisites

- Python 3.8+
- Pygame
- OpenAI API key (for LLM features)

### Running Tests

```bash
pytest
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- See [attributions.md](attributions.md) for credits and acknowledgments 