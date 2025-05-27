# AI-generated: Procedural Border Effects System for Cyberscape
from typing import List, Protocol, Optional
from enum import Enum, auto
import random
import time

class BorderRegion(Enum):
    MAIN_OUTPUT = auto()
    RUSTY_PANEL = auto()
    COMMAND_BAR = auto()

class BorderStyle(Enum):
    CORRUPTED = auto()
    MECHANICAL = auto()
    DIGITAL = auto()

class BorderEffect(Protocol):
    def apply(self, border_grid: List[List[str]], corruption: float, frame: int) -> None:
        ...

class PulseEffect:
    """Pulses border brightness or thickness."""
    def apply(self, border_grid: List[List[str]], corruption: float, frame: int) -> None:
        pulse_phase = (frame // 8) % 2
        char_map = {'|': '║', '-': '═', '+': '╬'}
        for y, row in enumerate(border_grid):
            for x, char in enumerate(row):
                if char in char_map and pulse_phase == 1:
                    border_grid[y][x] = char_map[char]

class GlitchEffect:
    """Randomly replaces border segments with glitch symbols."""
    GLITCH_CHARS = ['@', '#', '░', '▒', '▓', '*', '§', 'Æ', ' ']

    def apply(self, border_grid: List[List[str]], corruption: float, frame: int) -> None:
        glitch_chance = min(0.02 + corruption * 0.15, 0.25)
        for y, row in enumerate(border_grid):
            for x, char in enumerate(row):
                if char.strip() and random.random() < glitch_chance:
                    border_grid[y][x] = random.choice(self.GLITCH_CHARS)

class DistortEffect:
    """Distorts border by shifting or bending segments."""
    def apply(self, border_grid: List[List[str]], corruption: float, frame: int) -> None:
        if corruption < 0.2:
            return
        for y, row in enumerate(border_grid):
            if random.random() < corruption * 0.1:
                row.reverse()

class ColorBleedEffect:
    """Placeholder for color bleed; actual color handled by renderer."""
    def apply(self, border_grid: List[List[str]], corruption: float, frame: int) -> None:
        # No-op for ASCII; renderer can interpret special markers if needed
        pass

class BorderEffectManager:
    """
    Generates and animates procedural borders for UI regions.
    Effects are layered and escalate with corruption.
    """
    def __init__(self):
        self.effects = {
            BorderRegion.MAIN_OUTPUT: [PulseEffect(), GlitchEffect(), DistortEffect()],
            BorderRegion.RUSTY_PANEL: [PulseEffect(), GlitchEffect()],
            BorderRegion.COMMAND_BAR: [PulseEffect(), GlitchEffect()],
        }
        self.styles = {
            BorderRegion.MAIN_OUTPUT: BorderStyle.CORRUPTED,
            BorderRegion.RUSTY_PANEL: BorderStyle.MECHANICAL,
            BorderRegion.COMMAND_BAR: BorderStyle.DIGITAL,
        }

    def generate_border(
        self,
        width: int,
        height: int,
        region: BorderRegion,
        corruption: float,
        frame: Optional[int] = None
    ) -> List[str]:
        """
        Generate a procedural border for the given region and corruption level.
        Returns a list of strings, each representing a row of the border.
        """
        if frame is None:
            frame = int(time.time() * 10)
        style = self.styles.get(region, BorderStyle.CORRUPTED)
        border_grid = self._base_border_grid(width, height, style)
        for effect in self.effects.get(region, []):
            effect.apply(border_grid, corruption, frame)
        return ["".join(row) for row in border_grid]

    def _base_border_grid(self, width: int, height: int, style: BorderStyle) -> List[List[str]]:
        """Create the base border grid for a region and style."""
        if style == BorderStyle.CORRUPTED:
            h, v, c = '-', '|', '+'
        elif style == BorderStyle.MECHANICAL:
            h, v, c = '=', '‖', '¤'
        elif style == BorderStyle.DIGITAL:
            h, v, c = '_', '‖', '*'
        else:
            h, v, c = '-', '|', '+'
        grid = []
        for y in range(height):
            row = []
            for x in range(width):
                if y == 0 and x == 0:
                    row.append(c)
                elif y == 0 and x == width - 1:
                    row.append(c)
                elif y == height - 1 and x == 0:
                    row.append(c)
                elif y == height - 1 and x == width - 1:
                    row.append(c)
                elif y == 0 or y == height - 1:
                    row.append(h)
                elif x == 0 or x == width - 1:
                    row.append(v)
                else:
                    row.append(' ')
            grid.append(row)
        return grid
