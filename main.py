#!/usr/bin/env python3
"""
Cyberscape: Digital Dread - Unified Game Entry Point

This script combines the main entry logic and the core game loop into a single entry point.
"""

import sys
import logging
import random
import time
import math
from pathlib import Path

from src.core.effects import get_random_blip, corrupt_line

import pygame
import pygame.mixer

# --- Project Root Setup ---
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# --- Import Game Components ---
from src.core.commands import MainTerminalHandler
from src.core.effects import EffectManager
from src.core.filesystem import FileSystemHandler
from src.core.llm import LLMHandler
from src.core.knowledge_graph import KnowledgeGraph
from src.audio.manager import AudioManager
from src.core.persistence import PersistenceManager
from src.puzzle.manager import PuzzleManager
from src.story.manager import StoryManager
from src.ui.terminal import TerminalRenderer
from src.ui.terminal_integration import create_terminal_renderer
from src.world.manager import WorldManager

# --- Logging Setup ---
def setup_logging():
    log_dir = project_root / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_dir / "game.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

# --- Game Constants ---
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Cyberscape: Digital Dread"
FPS = 60

# --- Font Loading and Disclaimer/Role Selection Rendering ---
NEW_FONT_NAME = "OpenDyslexicMono-Regular.otf"
DISCLAIMER_FONT_SIZE_LARGE = 26
DISCLAIMER_FONT_SIZE_MEDIUM = 13
DISCLAIMER_FONT_SIZE_SMALL = 16

def load_monospace_font(size):
    font_to_load = None
    try:
        font_to_load = pygame.font.Font(NEW_FONT_NAME, size)
        return font_to_load
    except pygame.error:
        try:
            font_to_load = pygame.font.Font(None, size)
            return font_to_load
        except pygame.error as e_fallback:
            pygame.quit()
            raise RuntimeError(f"Failed to initialize any font for disclaimer (size {size}).") from e_fallback

SKULL_DETAILED_FRAME_CLOSED = r"""
     .----.
  .-"      "-.
 /            \
|              |
|,  .-.  .-.  ,|
| )(__/  \__)( |
|/     /\     \|
(_     ^^     _)
 \__|IIIIII|__/
  | \IIIIII/ |
  \          /
   `--------`

"""
#invisible character, might need it later, don't need right now: ‎
SKULL_DETAILED_FRAME_OPEN = r"""
     .----.
  .-"      "-.
 /            \
|              |
|,  .-.  .-.  ,|
| )(__/  \__)( |
|/     /\     \|
(_     ^^     _)
 \__|IIIIII|__/
  | |      | |
  | \IIIIII/ |
  \          /
   `--------`
"""

def render_text(surface, text, pos, color, font):
    if font is None:
        return
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, pos)

def render_disclaimer_screen(screen, corruption_level, disclaimer_mono_font_medium, disclaimer_mono_font_small, skull_open: bool = False, border_manager=None, corruption_anim_frame=0, border_anim_phase=0.0):
    # Fixed grid size
    GRID_COLS = 92
    GRID_ROWS = 28
    # Enforce sensible minimum window size
    min_width, min_height = 800, 400
    width = max(screen.get_width(), min_width)
    height = max(screen.get_height(), min_height)
    # Define small_window_mode and normal_font_size at the top so they're always available
    small_window_mode = (width < 600 or height < 400)
    normal_font_size = 10 if small_window_mode else 12
    cell_width = width / GRID_COLS
    cell_height = height / GRID_ROWS
    BLACK = (0, 0, 0)
    CORRUPTION_CHARS = "!@#$%^&*()_+[];',./<>?:{}|`~" + "¡¢£¤¥¦§¨©ª«¬®¯°±²³´µ¶·¸¹º»¼½¾¿" + "ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞß"
    screen.fill(BLACK)

    # --- Procedural Border: align to grid edges ---
    grid = [[" " for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
    # --- UTF-8/ASCII border at grid edges ---
    # Single line: ─ │ ┌ ┐ └ ┘
    # Double line: ═ ║ ╔ ╗ ╚ ╝
    for y in range(GRID_ROWS):
        for x in range(GRID_COLS):
            # Corners
            if y == 0 and x == 0:
                grid[y][x] = "┌"
            elif y == 0 and x == GRID_COLS - 1:
                grid[y][x] = "┐"
            elif y == GRID_ROWS - 1 and x == 0:
                grid[y][x] = "└"
            elif y == GRID_ROWS - 1 and x == GRID_COLS - 1:
                grid[y][x] = "┘"
            # Top/bottom edges
            elif y == 0 or y == GRID_ROWS - 1:
                grid[y][x] = "─"
            # Left/right edges
            elif x == 0 or x == GRID_COLS - 1:
                grid[y][x] = "│"

    # --- Skull as monospaced grid, centered in grid ---
    skull_font_path = "assets/fonts/OpenDyslexicMono-Regular.otf"
    try:
        skull_font = pygame.font.Font(skull_font_path, 12)
    except Exception:
        skull_font = pygame.font.SysFont('monospace', 12)
    skull_frame = SKULL_DETAILED_FRAME_OPEN if skull_open else SKULL_DETAILED_FRAME_CLOSED
    skull_lines = [line.rstrip('\n') for line in skull_frame.split('\n')]
    skull_grid_width = max(len(line) for line in skull_lines)
    skull_grid_height = len(skull_lines)
    skull_start_col = (GRID_COLS - skull_grid_width) // 2
    # Move skull up, leave at least 2 rows above, and 2 rows below before text
    skull_start_row = 2
    for row_idx, line in enumerate(skull_lines):
        for col_idx, ch in enumerate(line):
            if ch and not ch.isspace() and ch.isprintable():
                grid[skull_start_row + row_idx][skull_start_col + col_idx] = ("SKULL", ch)
    skull_end_row = skull_start_row + skull_grid_height - 1

    # --- Disclaimer text block, centered and wrapped in grid ---
    disclaimer_messages = [
        "This game is a work of fiction and intended for mature audiences.",
        "It explores themes of horror and hacking.",
        " ",
        "The activities depicted, if performed in real life, can have serious",
        "legal, ethical, and personal consequences.",
        " ",
        "This simulation does not endorse or encourage any illegal or unethical behavior.",
        "Always act responsibly and ethically online and offline.",
        " ",
        "Player discretion is strongly advised."
    ]
    corruption_level = 0.32  # Slightly reduced corruption for disclaimer text
    # Word wrap to grid width minus padding
    text_block_cols = GRID_COLS - 8
    wrapped_lines = []
    for line in disclaimer_messages:
        words = line.split()
        current_line = ""
        for word in words:
            test_line = (current_line + " " if current_line else "") + word
            if len(test_line) > text_block_cols:
                wrapped_lines.append(current_line)
                current_line = word
            else:
                current_line = test_line
        if current_line:
            wrapped_lines.append(current_line)
        if line.strip() == "":
            wrapped_lines.append("")
    # Center text block vertically below skull
    text_block_height = len(wrapped_lines)
    text_block_start_row = skull_start_row + skull_grid_height + 2

    # Intrusive/profane blips for corruption are now imported from effects.py

    # Improved text wrapping and vertical spacing
    # Only wrap to available width inside border
    text_block_cols = GRID_COLS - 6
    wrapped_lines = []
    for line in disclaimer_messages:
        words = line.split()
        current_line = ""
        for word in words:
            test_line = (current_line + " " if current_line else "") + word
            if len(test_line) > text_block_cols:
                wrapped_lines.append(current_line)
                current_line = word
            else:
                current_line = test_line
        if current_line:
            wrapped_lines.append(current_line)
        if line.strip() == "":
            wrapped_lines.append("")

    # Insert rare, fixed-length blips (never break line structure) and persist them for multiple frames
    # We'll use a global/static cache for blip state per line index and line content hash
    if not hasattr(render_disclaimer_screen, "blip_cache"):
        render_disclaimer_screen.blip_cache = {}
    blip_cache = render_disclaimer_screen.blip_cache
    BLIP_FRAMES = 48  # Number of frames a blip should persist (tweak for ~2x longer visibility)

    # Clear blip cache if line count or content changes
    current_hash = hash(tuple(wrapped_lines))
    if getattr(render_disclaimer_screen, "blip_cache_hash", None) != current_hash:
        blip_cache.clear()
        render_disclaimer_screen.blip_cache_hash = current_hash

    visible_lines = []
    for idx, wline in enumerate(wrapped_lines):
        blip = None
        line_hash = hash(wline)
        cache_entry = blip_cache.get(idx, None)
        # If a blip is cached, still within its lifetime, and for the same line content, reuse it
        if (
            cache_entry
            and corruption_anim_frame - cache_entry["frame"] < BLIP_FRAMES
            and cache_entry.get("line_hash") == line_hash
        ):
            start, length, blip_word = cache_entry["start"], cache_entry["length"], cache_entry["word"]
            wline = (
                wline[:start] +
                blip_word +
                wline[start + len(blip_word):]
            )
            blip = (start, len(blip_word))
        else:
            # Possibly insert a new blip
            if wline.strip() and random.random() < 0.10:
                blip_candidate = get_random_blip()
                if len(wline) >= len(blip_candidate):
                    max_start = len(wline) - len(blip_candidate)
                    start = random.randint(0, max_start)
                    wline = (
                        wline[:start] +
                        blip_candidate +
                        wline[start + len(blip_candidate):]
                    )
                    blip = (start, len(blip_candidate))
                    # Cache this blip with the current frame and line hash
                    blip_cache[idx] = {
                        "start": start,
                        "length": len(blip_candidate),
                        "word": blip_candidate,
                        "frame": corruption_anim_frame,
                        "line_hash": hash(wline)
                    }
                else:
                    # No blip inserted, clear cache for this line
                    if idx in blip_cache:
                        del blip_cache[idx]
            else:
                # No blip inserted, clear cache for this line
                if idx in blip_cache:
                    del blip_cache[idx]
        visible_lines.append((wline, blip))

    # Calculate available rows for text, leave at least 2 rows above and below
    min_spacing = 1
    max_text_lines = GRID_ROWS - (skull_end_row + 2 + 3)  # 2 after skull, 3 for prompt/border
    if len(visible_lines) + min_spacing * (len(visible_lines) - 1) > max_text_lines:
        # Reduce spacing if needed
        min_spacing = 0
    text_block_start_row = skull_end_row + 2
    grid_row = text_block_start_row

    for wline, blip in visible_lines:
        if grid_row >= GRID_ROWS - 3:
            break
        # Use centralized corruption logic from effects.py
        rng = random.Random(corruption_anim_frame + idx)
        corrupted_line = corrupt_line(wline, corruption_level, blip_range=blip, rng=rng)
        start_col = max(1, min((GRID_COLS - len(corrupted_line)) // 2, GRID_COLS - 2))
        for j, ch in enumerate(corrupted_line):
            grid_col = start_col + j
            if grid_col < 1 or grid_col >= GRID_COLS - 1:
                continue
            # Render blips in red, rest as normal
            if blip and blip[0] <= j < blip[0] + blip[1]:
                grid[grid_row][grid_col] = ("BLIP", ch)
            else:
                grid[grid_row][grid_col] = ("TEXT", ch)
        grid_row += 1 + min_spacing

    # --- Prompt at the bottom, centered ---
    prompt = "Press any key to continue..."
    prompt_row = GRID_ROWS - 3
    prompt_start_col = max(1, min((GRID_COLS - len(prompt)) // 2, GRID_COLS - 2))
    for j, ch in enumerate(prompt):
        grid_col = prompt_start_col + j
        if grid_col < 1 or grid_col >= GRID_COLS - 1:
            continue
        grid[prompt_row][grid_col] = ("PROMPT", ch)

    # --- Render the grid ---
    # Always render single line border, then overlay double line border with breathing effect
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            # For last column/row, align to window edge
            if col == GRID_COLS - 1:
                x = width - cell_width
            else:
                x = col * cell_width
            if row == GRID_ROWS - 1:
                y = height - cell_height
            else:
                y = row * cell_height
            cell = grid[row][col]
            # Draw single line border at edges
            border_ch = None
            if row == 0 and col == 0:
                border_ch = "┌"
            elif row == 0 and col == GRID_COLS - 1:
                border_ch = "┐"
            elif row == GRID_ROWS - 1 and col == 0:
                border_ch = "└"
            elif row == GRID_ROWS - 1 and col == GRID_COLS - 1:
                border_ch = "┘"
            elif row == 0 or row == GRID_ROWS - 1:
                border_ch = "─"
            elif col == 0 or col == GRID_COLS - 1:
                border_ch = "│"
            if border_ch:
                border_font_size = 9 if small_window_mode else 12
                surf = pygame.font.SysFont('monospace', border_font_size).render(border_ch, True, (120, 120, 120))
                # For last col/row, right/bottom align the character
                if col == GRID_COLS - 1:
                    surf_rect = surf.get_rect(right=x + cell_width, centery=y + cell_height / 2)
                elif row == GRID_ROWS - 1:
                    surf_rect = surf.get_rect(centerx=x + cell_width / 2, bottom=y + cell_height)
                else:
                    surf_rect = surf.get_rect(center=(x + cell_width / 2, y + cell_height / 2))
                screen.blit(surf, surf_rect)
            # Overlay double line border with breathing effect (faster)
            double_border_ch = None
            if row == 0 and col == 0:
                double_border_ch = "╔"
            elif row == 0 and col == GRID_COLS - 1:
                double_border_ch = "╗"
            elif row == GRID_ROWS - 1 and col == 0:
                double_border_ch = "╚"
            elif row == GRID_ROWS - 1 and col == GRID_COLS - 1:
                double_border_ch = "╝"
            elif row == 0 or row == GRID_ROWS - 1:
                double_border_ch = "═"
            elif col == 0 or col == GRID_COLS - 1:
                double_border_ch = "║"
            if double_border_ch:
                pulse = 0.5 + 0.5 * math.sin(time.time() * 2.5)
                overlay_alpha = int(180 * pulse)
                overlay_color = (200, 80, 80)
                overlay_font_size = 9 if small_window_mode else 12
                overlay_font = pygame.font.SysFont('monospace', overlay_font_size)
                overlay_surf = overlay_font.render(double_border_ch, True, overlay_color)
                overlay_surf.set_alpha(overlay_alpha)
                if col == GRID_COLS - 1:
                    overlay_rect = overlay_surf.get_rect(right=x + cell_width, centery=y + cell_height / 2)
                elif row == GRID_ROWS - 1:
                    overlay_rect = overlay_surf.get_rect(centerx=x + cell_width / 2, bottom=y + cell_height)
                else:
                    overlay_rect = overlay_surf.get_rect(center=(x + cell_width / 2, y + cell_height / 2))
                screen.blit(overlay_surf, overlay_rect)
            # Draw content
            if isinstance(cell, tuple):
                tag, ch = cell
                if tag == "SKULL":
                    # Use slightly smaller font size for skull if window is small
                    if small_window_mode:
                        skull_font_size = 10
                        skull_surf = pygame.font.SysFont('monospace', skull_font_size).render(ch, True, (200, 0, 0))
                    else:
                        skull_surf = skull_font.render(ch, True, (200, 0, 0))
                    surf = skull_surf
                elif tag == "TEXT":
                    color = (220, 220, 220)
                    surf = pygame.font.SysFont('monospace', normal_font_size).render(ch, True, color)
                elif tag == "PROMPT":
                    color = (255, 255, 255)
                    surf = pygame.font.SysFont('monospace', normal_font_size).render(ch, True, color)
                elif tag == "BLIP":
                    color = (255, 32, 32)
                    surf = pygame.font.SysFont('monospace', normal_font_size).render(ch, True, color)
                else:
                    surf = pygame.font.SysFont('monospace', normal_font_size).render(ch, True, (120, 120, 120))
                if col == GRID_COLS - 1:
                    surf_rect = surf.get_rect(right=x + cell_width, centery=y + cell_height / 2)
                elif row == GRID_ROWS - 1:
                    surf_rect = surf.get_rect(centerx=x + cell_width / 2, bottom=y + cell_height)
                else:
                    surf_rect = surf.get_rect(center=(x + cell_width / 2, y + cell_height / 2))
                screen.blit(surf, surf_rect)

def render_role_selection_screen(screen, border_manager=None, corruption_anim_frame=0, border_anim_phase=0.0):
    # Fixed grid size
    GRID_COLS = 92
    GRID_ROWS = 28
    width, height = screen.get_width(), screen.get_height()
    cell_width = width // GRID_COLS
    cell_height = height // GRID_ROWS
    BLACK = (0, 0, 0)
    screen.fill(BLACK)

    # --- Procedural Border: align to grid edges ---
    grid = [[" " for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
    # --- UTF-8/ASCII border at grid edges ---
    for y in range(GRID_ROWS):
        for x in range(GRID_COLS):
            # Corners
            if y == 0 and x == 0:
                grid[y][x] = "┌"
            elif y == 0 and x == GRID_COLS - 1:
                grid[y][x] = "┐"
            elif y == GRID_ROWS - 1 and x == 0:
                grid[y][x] = "└"
            elif y == GRID_ROWS - 1 and x == GRID_COLS - 1:
                grid[y][x] = "┘"
            # Top/bottom edges
            elif y == 0 or y == GRID_ROWS - 1:
                grid[y][x] = "─"
            # Left/right edges
            elif x == 0 or x == GRID_COLS - 1:
                grid[y][x] = "│"

    # --- Title ---
    title = "Select Your Role:"
    title_row = 3
    title_start_col = max(0, min((GRID_COLS - len(title)) // 2, GRID_COLS - 1))
    for j, ch in enumerate(title):
        grid_col = title_start_col + j
        if grid_col < 0 or grid_col >= GRID_COLS:
            continue
        grid[title_row][grid_col] = ("TITLE", ch)

    # --- Roles ---
    roles = [
        ("1. The Purifier", "Defender of systems, seeker of truth"),
        ("2. The Arbiter", "Balancer of chaos, wielder of knowledge"),
        ("3. The Ascendant", "Agent of entropy, master of corruption")
    ]
    role_block_start_row = 6
    for idx, (role, desc) in enumerate(roles):
        role_row = role_block_start_row + idx * 4
        role_start_col = max(0, min((GRID_COLS - len(role)) // 2, GRID_COLS - 1))
        for j, ch in enumerate(role):
            grid_col = role_start_col + j
            if grid_col < 0 or grid_col >= GRID_COLS:
                continue
            grid[role_row][grid_col] = ("ROLE", ch)
        # Wrap description if needed
        desc_lines = []
        desc_words = desc.split()
        desc_line = ""
        desc_block_cols = GRID_COLS - 12
        for word in desc_words:
            test_line = (desc_line + " " if desc_line else "") + word
            if len(test_line) > desc_block_cols:
                desc_lines.append(desc_line)
                desc_line = word
            else:
                desc_line = test_line
        if desc_line:
            desc_lines.append(desc_line)
        for d_idx, dline in enumerate(desc_lines):
            desc_row = role_row + 1 + d_idx
            desc_start_col = max(0, min((GRID_COLS - len(dline)) // 2, GRID_COLS - 1))
            for j, ch in enumerate(dline):
                grid_col = desc_start_col + j
                if grid_col < 0 or grid_col >= GRID_COLS:
                    continue
                grid[desc_row][grid_col] = ("DESC", ch)

    # --- Prompt at the bottom, centered ---
    prompt = "Press 1, 2, or 3 to select your role."
    prompt_row = GRID_ROWS - 3
    prompt_start_col = max(0, min((GRID_COLS - len(prompt)) // 2, GRID_COLS - 1))
    for j, ch in enumerate(prompt):
        grid_col = prompt_start_col + j
        if grid_col < 0 or grid_col >= GRID_COLS:
            continue
        grid[prompt_row][grid_col] = ("PROMPT", ch)

    # --- Render the grid ---
    # Always render single line border, then overlay double line border with breathing effect
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            # For last column/row, align to window edge
            if col == GRID_COLS - 1:
                x = width - cell_width
            else:
                x = col * cell_width
            if row == GRID_ROWS - 1:
                y = height - cell_height
            else:
                y = row * cell_height
            cell = grid[row][col]
            # Draw single line border at edges
            border_ch = None
            if row == 0 and col == 0:
                border_ch = "┌"
            elif row == 0 and col == GRID_COLS - 1:
                border_ch = "┐"
            elif row == GRID_ROWS - 1 and col == 0:
                border_ch = "└"
            elif row == GRID_ROWS - 1 and col == GRID_COLS - 1:
                border_ch = "┘"
            elif row == 0 or row == GRID_ROWS - 1:
                border_ch = "─"
            elif col == 0 or col == GRID_COLS - 1:
                border_ch = "│"
            if border_ch:
                surf = pygame.font.SysFont('monospace', 12).render(border_ch, True, (120, 120, 120))
                # For last col/row, right/bottom align the character
                if col == GRID_COLS - 1:
                    surf_rect = surf.get_rect(right=x + cell_width, centery=y + cell_height / 2)
                elif row == GRID_ROWS - 1:
                    surf_rect = surf.get_rect(centerx=x + cell_width / 2, bottom=y + cell_height)
                else:
                    surf_rect = surf.get_rect(center=(x + cell_width / 2, y + cell_height / 2))
                screen.blit(surf, surf_rect)
            # Overlay double line border with breathing effect (faster, decoupled)
            double_border_ch = None
            if row == 0 and col == 0:
                double_border_ch = "╔"
            elif row == 0 and col == GRID_COLS - 1:
                double_border_ch = "╗"
            elif row == GRID_ROWS - 1 and col == 0:
                double_border_ch = "╚"
            elif row == GRID_ROWS - 1 and col == GRID_COLS - 1:
                double_border_ch = "╝"
            elif row == 0 or row == GRID_ROWS - 1:
                double_border_ch = "═"
            elif col == 0 or col == GRID_COLS - 1:
                double_border_ch = "║"
            if double_border_ch:
                # Use border_anim_phase for border breathing
                pulse = 0.5 + 0.5 * math.sin(border_anim_phase * 2.5)
                overlay_alpha = int(180 * pulse)
                overlay_color = (200, 80, 80)
                overlay_font = pygame.font.SysFont('monospace', 12)
                overlay_surf = overlay_font.render(double_border_ch, True, overlay_color)
                overlay_surf.set_alpha(overlay_alpha)
                if col == GRID_COLS - 1:
                    overlay_rect = overlay_surf.get_rect(right=x + cell_width, centery=y + cell_height / 2)
                elif row == GRID_ROWS - 1:
                    overlay_rect = overlay_surf.get_rect(centerx=x + cell_width / 2, bottom=y + cell_height)
                else:
                    overlay_rect = overlay_surf.get_rect(center=(x + cell_width / 2, y + cell_height / 2))
                screen.blit(overlay_surf, overlay_rect)
            # Draw content
            if isinstance(cell, tuple):
                tag, ch = cell
                if tag == "TITLE":
                    surf = pygame.font.SysFont('monospace', 12).render(ch, True, (200, 200, 200))
                elif tag == "ROLE":
                    surf = pygame.font.SysFont('monospace', 12).render(ch, True, (220, 220, 220))
                elif tag == "DESC":
                    surf = pygame.font.SysFont('monospace', 12).render(ch, True, (150, 150, 150))
                elif tag == "PROMPT":
                    surf = pygame.font.SysFont('monospace', 12).render(ch, True, (255, 255, 255))
                else:
                    surf = pygame.font.SysFont('monospace', 12).render(ch, True, (120, 120, 120))
                if col == GRID_COLS - 1:
                    surf_rect = surf.get_rect(right=x + cell_width, centery=y + cell_height / 2)
                elif row == GRID_ROWS - 1:
                    surf_rect = surf.get_rect(centerx=x + cell_width / 2, bottom=y + cell_height)
                else:
                    surf_rect = surf.get_rect(center=(x + cell_width / 2, y + cell_height / 2))
                screen.blit(surf, surf_rect)
# --- Main Game Class ---
class Game:
    """Main game class that coordinates all game components"""
    def __init__(
        self,
        command_handler: MainTerminalHandler,
        effect_manager: EffectManager,
        file_system: FileSystemHandler,
        llm_handler: LLMHandler,
        audio_manager: AudioManager,
        persistence_manager: PersistenceManager,
        puzzle_manager: PuzzleManager,
        story_manager: StoryManager,
        terminal_renderer: TerminalRenderer,
        world_manager: WorldManager,
        game_state=None
    ):
        self.command_handler = command_handler
        self.effect_manager = effect_manager
        self.file_system = file_system
        self.llm_handler = llm_handler
        self.audio_manager = audio_manager
        self.persistence_manager = persistence_manager
        self.puzzle_manager = puzzle_manager
        self.story_manager = story_manager
        self.terminal_renderer = terminal_renderer
        self.world_manager = world_manager
        self.game_state = game_state

        self.running = False
        self.current_state = "disclaimer"
        self.corruption_level = 0.0
        self.current_zone = "mainframe"
        self.current_layer = 0

        self.disclaimer_acknowledged = False
        self.skull_anim_timer = 0.0
        self.skull_anim_state = False  # False = closed, True = open
        self.corruption_anim_timer = 0.0
        self.corruption_anim_frame = 0
        self.border_anim_timer = 0.0
        self.border_anim_phase = 0.0

        pygame.init()
        pygame.mixer.init()
        # Set sensible default and minimum window size
        min_width, min_height = 800, 400
        default_width, default_height = 1280, 720
        self.screen = pygame.display.set_mode((default_width, default_height), pygame.RESIZABLE)
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()

        # Set the terminal renderer's dimensions to match the window
        self.terminal_renderer.width = WINDOW_WIDTH
        self.terminal_renderer.height = WINDOW_HEIGHT

        logging.info("Game initialized successfully")

    def run(self):
        """Main game loop"""
        self.running = True
        logging.info("Starting main game loop")
        try:
            while self.running:
                self._handle_events()
                self._update()
                self._render()
                self.clock.tick(FPS)
        except Exception as e:
            logging.error(f"Error in main game loop: {e}", exc_info=True)
            self.running = False
        finally:
            self._cleanup()

    def _handle_events(self):
        """Handle all game events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.current_state == "disclaimer" and not self.disclaimer_acknowledged:
                    self.disclaimer_acknowledged = True
                    self.current_state = "role_selection"
                else:
                    self._handle_keydown(event)
            elif event.type == pygame.VIDEORESIZE:
                # Update the terminal renderer's dimensions when the window is resized
                self.terminal_renderer.width = event.w
                self.terminal_renderer.height = event.h

    def _handle_keydown(self, event):
        """Handle keyboard input"""
        if event.key == pygame.K_ESCAPE:
            self.running = False
        elif self.current_state == "role_selection":
            self._handle_role_selection_input(event)
        else:
            self.command_handler.handle_input(event)
    
    def _handle_role_selection_input(self, event):
        """Handle input during role selection"""
        if event.key == pygame.K_1:
            self._select_role("PURIFIER")
        elif event.key == pygame.K_2:
            self._select_role("ARBITER")
        elif event.key == pygame.K_3:
            self._select_role("ASCENDANT")
        # Also handle number row keys
        elif event.unicode == "1":
            self._select_role("PURIFIER")
        elif event.unicode == "2":
            self._select_role("ARBITER")
        elif event.unicode == "3":
            self._select_role("ASCENDANT")
    
    def _select_role(self, role):
        """Select a player role and transition to main terminal"""
        logging.info(f"Player selected role: {role}")
        
        # Set role in game state manager if available
        if hasattr(self.game_state, 'set_player_role'):
            success = self.game_state.set_player_role(role)
            if success:
                logging.info(f"Role set successfully in GameStateManager: {role}")
                # Transition to main terminal using GameStateManager
                if hasattr(self.game_state, 'change_state'):
                    from src.core.state import STATE_MAIN_TERMINAL
                    self.game_state.change_state(STATE_MAIN_TERMINAL)
                self.current_state = "main_terminal"
                
                # Add welcome message to terminal
                role_names = {
                    "PURIFIER": "The Purifier - Defender of Systems",
                    "ARBITER": "The Arbiter - Balancer of Chaos", 
                    "ASCENDANT": "The Ascendant - Agent of Entropy"
                }
                self.terminal_renderer.add_to_buffer(f"Role selected: {role_names.get(role, role)}")
                self.terminal_renderer.add_to_buffer("Welcome to the Aether Network.")
                self.terminal_renderer.add_to_buffer("Type 'help' to see available commands.")
            else:
                logging.error(f"Failed to set role: {role}")
        else:
            # Fallback for basic game state
            logging.warning("GameStateManager not available, using basic role selection")
            self.current_state = "main_terminal"
            self.terminal_renderer.add_to_buffer(f"Role selected: {role}")
            self.terminal_renderer.add_to_buffer("Welcome to the Aether Network.")
            self.terminal_renderer.add_to_buffer("Type 'help' to see available commands.")

    def _update(self):
        """Update game state"""
        # Animate skull on disclaimer screen
        if self.current_state == "disclaimer" and not self.disclaimer_acknowledged:
            self.skull_anim_timer += 1.0 / FPS
            # Toggle skull every 0.09 seconds (very fast)
            if self.skull_anim_timer >= 0.09:
                self.skull_anim_state = not self.skull_anim_state
                self.skull_anim_timer = 0.0

        # Update corruption animation frame for all states
        self.corruption_anim_timer += 1.0 / FPS
        if self.corruption_anim_timer >= 0.1:  # Update every 0.1 seconds
            self.corruption_anim_frame = (self.corruption_anim_frame + 1) % 10
            self.corruption_anim_timer = 0.0
            
        # Update border animation phase for breathing effect
        self.border_anim_timer += 1.0 / FPS
        self.border_anim_phase = self.border_anim_timer

        # The effect manager expects a delta time (dt), so we use a fixed timestep for now
        self.effect_manager.update(1.0 / FPS)
        
        # Update world manager
        if hasattr(self.world_manager, 'update'):
            self.world_manager.update(1.0 / FPS)
        
        # If audio_manager or story_manager have update methods, call them here as needed
        # (No update method in StoryManager or PuzzleManager per actual code)

    def _render(self):
        """Render the current game state"""
        # Render to the main pygame display surface
        if self.current_state == "disclaimer" and not self.disclaimer_acknowledged:
            # Use default pygame font for now
            disclaimer_mono_font_medium = pygame.font.SysFont('monospace', DISCLAIMER_FONT_SIZE_MEDIUM)
            disclaimer_mono_font_small = pygame.font.SysFont('monospace', DISCLAIMER_FONT_SIZE_SMALL)
            # Pass border manager for procedural border rendering
            render_disclaimer_screen(
                self.screen,
                self.corruption_level,
                disclaimer_mono_font_medium,
                disclaimer_mono_font_small,
                skull_open=self.skull_anim_state,
                border_manager=self.terminal_renderer.border_manager,
                corruption_anim_frame=self.corruption_anim_frame,
                border_anim_phase=self.border_anim_phase
            )
        elif self.current_state == "role_selection":
            render_role_selection_screen(
                self.screen,
                border_manager=self.terminal_renderer.border_manager,
                corruption_anim_frame=self.corruption_anim_frame,
                border_anim_phase=self.border_anim_phase
            )
        else:
            self.terminal_renderer.render(self.screen, self.effect_manager)
        pygame.display.flip()

    def _cleanup(self):
        """Clean up resources before exit"""
        logging.info("Cleaning up game resources...")
        # Save game state if possible
        if hasattr(self.persistence_manager, "save_game") and hasattr(self, "game_state"):
            self.persistence_manager.save_game(self.game_state)
        self.audio_manager.stop_all_sounds()
        pygame.quit()
        logging.info("Game cleanup complete")

    def change_state(self, new_state: str):
        logging.info(f"Changing game state from {self.current_state} to {new_state}")
        self.current_state = new_state
        if new_state == "main_menu":
            self._init_main_menu()
        elif new_state == "game":
            self._init_game()
        elif new_state == "puzzle":
            self._init_puzzle()

    def _init_main_menu(self):
        # Play menu music if available
        if hasattr(self.audio_manager, "music_tracks") and "menu" in self.audio_manager.music_tracks:
            self.audio_manager.play_music_track(self.audio_manager.music_tracks["menu"])
        # Theme management is handled by a theme manager if present

    def _init_game(self):
        # Play ambient music if available
        if hasattr(self.audio_manager, "music_tracks") and "ambient" in self.audio_manager.music_tracks:
            self.audio_manager.play_music_track(self.audio_manager.music_tracks["ambient"])
        # Theme management is handled by a theme manager if present

    def _init_puzzle(self):
        # Play puzzle music if available
        if hasattr(self.audio_manager, "music_tracks") and "puzzle" in self.audio_manager.music_tracks:
            self.audio_manager.play_music_track(self.audio_manager.music_tracks["puzzle"])
        # Theme management is handled by a theme manager if present

    def set_corruption_level(self, level: float):
        self.corruption_level = max(0.0, min(1.0, level))
        logging.info(f"Corruption level set to {self.corruption_level}")

    def change_zone(self, new_zone: str, new_layer: int = 0):
        logging.info(f"Changing zone from {self.current_zone} to {new_zone} (layer {new_layer})")
        self.current_zone = new_zone
        self.current_layer = new_layer
        # No set_zone method in AudioManager; removed
        # No set_zone method in EffectManager; remove this call

# --- Entry Point ---
def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        logger.info("Initializing game components...")

        # Create data directories if they don't exist
        for dir_name in ["saves", "data/logs", "data/personal"]:
            (project_root / dir_name).mkdir(parents=True, exist_ok=True)

        # Initialize managers
        audio_manager = AudioManager()
        file_system = FileSystemHandler()
        llm_handler = LLMHandler()
        knowledge_graph = KnowledgeGraph()
        persistence_manager = PersistenceManager()
        puzzle_manager = PuzzleManager()
        
        # Game state manager is required for EffectManager and StoryManager
        try:
            from src.core.state import GameStateManager
            game_state = GameStateManager()
        except ImportError:
            # Create a simple game state object with required attributes
            logger.warning("GameStateManager not found. Using SimpleNamespace as fallback.")
            from types import SimpleNamespace
            # Import the expected GameStateManager type for type compatibility
            try:
                from src.core.state import GameStateManager as GSMType
                class CompatibleGameState(SimpleNamespace, GSMType):
                    pass
                game_state = CompatibleGameState(role="purifier", corruption_level=0.0)
            except (ImportError, TypeError):
                # If we can't import the type or there's a type error, create a basic object
                logger.warning("Failed to create type-compatible game state. Basic functionality only.")
                game_state = SimpleNamespace(role="purifier", corruption_level=0.0)

            setattr(game_state, "is_takeover_active", lambda: False)

        # Initialize world manager
        world_manager = WorldManager(game_state)

        # Initialize enhanced terminal renderer
        terminal_renderer = create_terminal_renderer(
            enhanced=True,
            effect_manager=None,  # Will be set after effect_manager is created
            game_state_manager=game_state
        )
        
        # Initialize effect manager with terminal renderer
        effect_manager = EffectManager(game_state, audio_manager, terminal_renderer)
        
        # Update the terminal renderer with the effect manager
        terminal_renderer.effect_manager = effect_manager
        
        # Configure enhanced effects if using enhanced renderer
        if hasattr(terminal_renderer, '_effect_config'):
            from src.ui.terminal_integration import configure_enhanced_effects
            configure_enhanced_effects(
                terminal_renderer,
                corruption_sensitivity=0.8,
                effect_intensity=1.0,
                subliminal_frequency=0.1
            )
        
        story_manager = StoryManager(game_state, effect_manager)

        # Set up puzzle manager with terminal
        puzzle_manager.set_terminal(terminal_renderer)

        # Boot messages
        terminal_renderer.add_to_buffer("Cyberscape: Digital Dread - Booting...")
        terminal_renderer.add_to_buffer("Enhanced Terminal Renderer Activated.")
        terminal_renderer.add_to_buffer("System Initialized.")
        terminal_renderer.add_to_buffer("Waiting for user acknowledgement of disclaimer...")

        # Initialize command handler
        command_handler = MainTerminalHandler(
            effect_manager=effect_manager,
            file_system=file_system,
            puzzle_manager=puzzle_manager,
            story_manager=story_manager,
            terminal_renderer=terminal_renderer,
            llm_handler=llm_handler,
            world_manager=world_manager
        )

        # Set up LLM handler dependencies with knowledge graph integration
        llm_handler.set_dependencies(
            game_state_manager=game_state,
            effect_manager=effect_manager,
            terminal=terminal_renderer,
            knowledge_graph=knowledge_graph
        )

        # Enhanced diagnostics
        logger.info("Running diagnostics...")
        logger.info(f"GameState type: {type(game_state).__name__}")
        logger.info(f"EffectManager initialized: {effect_manager is not None}")
        logger.info(f"StoryManager initialized: {story_manager is not None}")
        logger.info(f"WorldManager initialized: {world_manager is not None}")
        logger.info(f"Audio Manager initialized: {audio_manager is not None}")
        logger.info(f"File System Handler initialized: {file_system is not None}")
        logger.info(f"LLM Handler initialized: {llm_handler is not None}")
        logger.info(f"Knowledge Graph initialized: {knowledge_graph is not None}")
        logger.info(f"Terminal Renderer initialized: {terminal_renderer is not None}")
        logger.info(f"Terminal Renderer type: {type(terminal_renderer).__name__}")
        
        # Check knowledge graph status
        if knowledge_graph:
            logger.info(f"Knowledge Graph entities: {len(knowledge_graph.nodes)}")
            logger.info(f"Knowledge Graph relationships: {len(knowledge_graph.edges)}")
            logger.info(f"Knowledge Graph narrative threads: {len(knowledge_graph.narrative_threads)}")
            logger.info(f"LLM-Knowledge Graph integration: {llm_handler.knowledge_graph is not None}")
        
        # Check enhanced terminal capabilities
        from src.ui.terminal_integration import get_renderer_capabilities, is_enhanced_renderer
        capabilities = get_renderer_capabilities(terminal_renderer)
        logger.info(f"Terminal Renderer is enhanced: {is_enhanced_renderer(terminal_renderer)}")
        enhanced_features = [name for name, available in capabilities.items() if available and 'enhanced' in name or 'effects' in name]
        logger.info(f"Available features: {', '.join(enhanced_features)}")
        
        logger.info(f"Command Handler initialized: {command_handler is not None}")
        logger.info(f"Persistence Manager initialized: {persistence_manager is not None}")
        logger.info(f"Puzzle Manager initialized: {puzzle_manager is not None}")
        logger.info("Diagnostics complete.")

        # Initialize and start the game
        game = Game(
            command_handler=command_handler,
            effect_manager=effect_manager,
            file_system=file_system,
            llm_handler=llm_handler,
            audio_manager=audio_manager,
            persistence_manager=persistence_manager,
            puzzle_manager=puzzle_manager,
            story_manager=story_manager,
            terminal_renderer=terminal_renderer,
            world_manager=world_manager,
            game_state=game_state
        )

        logger.info("Starting game...")
        game.run()

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Game shutdown complete")

if __name__ == "__main__":
    main()
