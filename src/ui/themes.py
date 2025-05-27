"""Theme management module for the Cyberscape game."""

import pygame
from typing import Dict, Any, Tuple

# --- Color Definitions ---
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GREY_LIGHT = (200, 200, 200)
COLOR_GREY_DARK = (50, 50, 50)
COLOR_RED_BRIGHT = (255, 0, 0)
COLOR_RED_DARK = (150, 0, 0)
COLOR_GREEN_BRIGHT = (0, 255, 0)
COLOR_GREEN_DARK = (0, 150, 0)
COLOR_BLUE_BRIGHT = (0, 0, 255)
COLOR_BLUE_CYAN = (0, 255, 255)
COLOR_YELLOW_BRIGHT = (255, 255, 0)
COLOR_MAGENTA_BRIGHT = (255, 0, 255)

# --- Theme Definitions ---
THEMES: Dict[str, Dict[str, Any]] = {
    "default": {
        "default_fg": COLOR_GREY_LIGHT,
        "default_bg": COLOR_BLACK,
        "prompt": COLOR_GREEN_BRIGHT,
        "error": COLOR_RED_BRIGHT,
        "success": COLOR_GREEN_BRIGHT,
        "highlight": COLOR_BLUE_CYAN,
        "llm_response": (150, 200, 255),  # Light blue for LLM responses
        "cursor_bg": COLOR_WHITE,
        "cursor_fg": COLOR_BLACK,
        "matrix": COLOR_GREEN_BRIGHT,
        "corruption": COLOR_RED_BRIGHT,
        "entity": COLOR_BLUE_CYAN,
        "system": COLOR_YELLOW_BRIGHT,
        "name": "Default Terminal"
    },
    "purifier": {
        "default_fg": (200, 255, 200),  # Light green
        "default_bg": (10, 20, 10),     # Very dark green
        "prompt": (100, 255, 100),      # Bright green
        "error": (255, 100, 100),       # Soft red
        "success": (100, 255, 100),     # Bright green
        "highlight": (150, 255, 150),   # Light green
        "llm_response": (150, 200, 255),
        "cursor_bg": (100, 255, 100),
        "cursor_fg": (10, 20, 10),
        "matrix": (100, 255, 100),
        "corruption": (255, 100, 100),
        "entity": (150, 255, 150),
        "system": (200, 255, 200),
        "name": "The Purifier Terminal"
    },
    "arbiter": {
        "default_fg": (200, 200, 255),  # Light blue
        "default_bg": (20, 20, 40),     # Dark blue
        "prompt": (150, 150, 255),      # Medium blue
        "error": (255, 150, 100),       # Orange
        "success": (100, 255, 200),     # Cyan
        "highlight": (200, 200, 255),   # Light blue
        "llm_response": (150, 200, 255),
        "cursor_bg": (150, 150, 255),
        "cursor_fg": (20, 20, 40),
        "matrix": (150, 150, 255),
        "corruption": (255, 150, 100),
        "entity": (200, 200, 255),
        "system": (150, 150, 255),
        "name": "The Arbiter Terminal"
    },
    "ascendant": {
        "default_fg": (255, 100, 100),  # Red
        "default_bg": (20, 0, 0),       # Dark red
        "prompt": (255, 50, 50),        # Bright red
        "error": (255, 200, 0),         # Yellow
        "success": (255, 50, 50),       # Bright red
        "highlight": (255, 100, 100),   # Red
        "llm_response": (150, 200, 255),
        "cursor_bg": (255, 50, 50),
        "cursor_fg": (20, 0, 0),
        "matrix": (255, 50, 50),
        "corruption": (255, 200, 0),
        "entity": (255, 100, 100),
        "system": (255, 50, 50),
        "name": "The Ascendant Terminal"
    },
    "corrupted_kali": {
        "default_fg": (180, 220, 180),  # Muted green
        "default_bg": (10, 20, 10),     # Very dark green/black
        "prompt": (100, 255, 100),      # Brighter green
        "error": (255, 80, 80),         # Glitchy red
        "success": (80, 220, 80),       # Muted success green
        "highlight": (220, 80, 220),    # Corrupted magenta
        "llm_response": (150, 200, 255),
        "cursor_bg": (100, 255, 100),
        "cursor_fg": (10, 20, 10),
        "matrix": (100, 255, 100),
        "corruption": (255, 80, 80),
        "entity": (220, 80, 220),
        "system": (180, 220, 180),
        "name": "Corrupted Kali"
    },
    "digital_nightmare": {
        "default_fg": (150, 0, 0),      # Dark blood red
        "default_bg": (10, 0, 0),       # Near black with red tint
        "prompt": (200, 50, 50),        # Menacing red
        "error": (255, 150, 0),         # Unsettling orange/yellow
        "success": (100, 0, 0),         # Barely visible success
        "highlight": (255, 0, 255),     # Harsh magenta
        "llm_response": (150, 200, 255),
        "cursor_bg": (200, 50, 50),
        "cursor_fg": (10, 0, 0),
        "matrix": (200, 50, 50),
        "corruption": (255, 150, 0),
        "entity": (255, 0, 255),
        "system": (150, 0, 0),
        "name": "Digital Nightmare"
    },
    "classic_dos": {
        "default_fg": COLOR_GREY_LIGHT,
        "default_bg": (0, 0, 128),      # Dark Blue
        "prompt": COLOR_WHITE,
        "error": COLOR_YELLOW_BRIGHT,
        "success": COLOR_GREEN_BRIGHT,
        "highlight": COLOR_WHITE,
        "llm_response": (150, 200, 255),
        "cursor_bg": COLOR_WHITE,
        "cursor_fg": (0, 0, 128),
        "matrix": COLOR_GREEN_BRIGHT,
        "corruption": COLOR_YELLOW_BRIGHT,
        "entity": COLOR_WHITE,
        "system": COLOR_GREY_LIGHT,
        "name": "Classic DOS"
    }
}

class ThemeManager:
    """Singleton class to manage the current theme and path."""
    _current_theme_name = "default"
    _current_path = "default"

    @classmethod
    def get_current_theme(cls) -> Dict[str, Any]:
        """Get the current theme dictionary.

        Returns:
            Dict[str, Any]: The current theme dictionary, or default theme if none set
        """
        return THEMES.get(cls._current_theme_name, THEMES["default"])

    @classmethod
    def set_theme(cls, theme_name: str) -> bool:
        """Set the current theme by name.

        Args:
            theme_name: Name of the theme to set

        Returns:
            bool: True if theme was set successfully, False if theme doesn't exist
        """
        if theme_name in THEMES:
            cls._current_theme_name = theme_name
            return True
        return False

    @classmethod
    def set_path_theme(cls, path: str) -> bool:
        """Set theme based on the current path.

        Args:
            path: Current path to determine theme from

        Returns:
            bool: True if theme was set successfully, False otherwise
        """
        cls._current_path = path
        theme_mapping = {
            "purifier": "default",
            "arbiter": "cyberpunk",
            "ascendant": "digital_nightmare",
            "classic_dos": "classic_dos",
            "corrupted_kali": "corrupted_kali",
            "digital_nightmare": "digital_nightmare"
        }
        theme_name = theme_mapping.get(path, "default")
        return cls.set_theme(theme_name)

    @classmethod
    def get_current_path(cls) -> str:
        """Get the current path.

        Returns:
            str: The current path
        """
        return cls._current_path

def get_theme_color(color_key: str, default_color: Tuple[int, int, int] = COLOR_WHITE) -> Tuple[int, int, int]:
    """Get a color from the current theme."""
    return ThemeManager.get_current_theme().get(color_key, default_color) 