"""
Command handler module for processing user input and executing game commands
"""

import logging
import pygame
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from src.core.effects import EffectManager
from src.core.filesystem import FileSystemHandler
from src.core.llm import LLMHandler
# from src.core.audio_manager import AudioManager  # Removed: module does not exist or has been renamed
# from src.core.persistence_manager import PersistenceManager  # Removed: module does not exist or has been renamed
from src.puzzle.manager import PuzzleManager
from src.story.manager import StoryManager
from src.ui.terminal import TerminalRenderer

logger = logging.getLogger(__name__)

class CommandCategory(Enum):
    """Categories of available commands"""
    SYSTEM = "system"
    NAVIGATION = "navigation"
    INTERACTION = "interaction"
    PUZZLE = "puzzle"
    INVENTORY = "inventory"
    HELP = "help"

@dataclass
class Command:
    """Represents a game command"""
    name: str
    aliases: List[str]
    category: CommandCategory
    description: str
    usage: str
    handler: callable
    requires_role: Optional[str] = None
    requires_item: Optional[str] = None
    requires_state: Optional[str] = None

class MainTerminalHandler:
    """Handles command processing and execution"""

    def __init__(
        self,
        effect_manager: EffectManager,
        file_system: FileSystemHandler,
        puzzle_manager: PuzzleManager,
        story_manager: StoryManager,
        terminal_renderer: TerminalRenderer,
        llm_handler: LLMHandler
    ):
        "Initialize the command handler with all required components"
        self.effect_manager = effect_manager
        self.file_system = file_system
        self.puzzle_manager = puzzle_manager
        self.story_manager = story_manager
        self.terminal_renderer = terminal_renderer
        self.llm_handler = llm_handler # Use injected LLMHandler instance

        # Command registry
        self.commands: Dict[str, Command] = {}
        self._register_commands()

        # Command history
        self.history: List[str] = []
        self.history_index = -1

        # Current command state
        self.current_command = ""
        self.cursor_position = 0

        logger.info("Command handler initialized")

    def _register_commands(self):
        """Register all available commands"""
        # System commands
        self._register_command(Command(
            name="help",
            aliases=["?", "h"],
            category=CommandCategory.HELP,
            description="Show help information",
            usage="help [command]",
            handler=self._cmd_help
        ))

        self._register_command(Command(
            name="quit",
            aliases=["exit", "q"],
            category=CommandCategory.SYSTEM,
            description="Exit the game",
            usage="quit",
            handler=self._cmd_quit
        ))

        # Navigation commands
        self._register_command(Command(
            name="cd",
            aliases=["chdir"],
            category=CommandCategory.NAVIGATION,
            description="Change current directory",
            usage="cd [path]",
            handler=self._cmd_cd
        ))

        self._register_command(Command(
            name="ls",
            aliases=["dir", "list"],
            category=CommandCategory.NAVIGATION,
            description="List directory contents",
            usage="ls [path]",
            handler=self._cmd_ls
        ))

        self._register_command(Command(
            name="pwd",
            aliases=["cwd"],
            category=CommandCategory.NAVIGATION,
            description="Print working directory",
            usage="pwd",
            handler=self._cmd_pwd
        ))

        self._register_command(Command(
            name="find",
            aliases=["search"],
            category=CommandCategory.NAVIGATION,
            description="Find files or directories",
            usage="find <pattern> [path]",
            handler=self._cmd_find
        ))

        # File manipulation commands
        self._register_command(Command(
            name="cat",
            aliases=["type", "view"],
            category=CommandCategory.SYSTEM,
            description="Display file contents",
            usage="cat <filename>",
            handler=self._cmd_cat
        ))

        self._register_command(Command(
            name="cp",
            aliases=["copy"],
            category=CommandCategory.SYSTEM,
            description="Copy files or directories",
            usage="cp <source> <destination>",
            handler=self._cmd_cp
        ))

        self._register_command(Command(
            name="mv",
            aliases=["move", "rename"],
            category=CommandCategory.SYSTEM,
            description="Move or rename files",
            usage="mv <source> <destination>",
            handler=self._cmd_mv
        ))

        self._register_command(Command(
            name="rm",
            aliases=["del", "delete"],
            category=CommandCategory.SYSTEM,
            description="Remove files or directories",
            usage="rm <filename>",
            handler=self._cmd_rm
        ))

        self._register_command(Command(
            name="mkdir",
            aliases=["md"],
            category=CommandCategory.SYSTEM,
            description="Create directory",
            usage="mkdir <dirname>",
            handler=self._cmd_mkdir
        ))

        self._register_command(Command(
            name="touch",
            aliases=["create"],
            category=CommandCategory.SYSTEM,
            description="Create empty file or update timestamp",
            usage="touch <filename>",
            handler=self._cmd_touch
        ))

        # System monitoring commands
        self._register_command(Command(
            name="ps",
            aliases=["processes"],
            category=CommandCategory.SYSTEM,
            description="Show running processes",
            usage="ps",
            handler=self._cmd_ps
        ))

        self._register_command(Command(
            name="top",
            aliases=["htop"],
            category=CommandCategory.SYSTEM,
            description="Show system resource usage",
            usage="top",
            handler=self._cmd_top
        ))

        self._register_command(Command(
            name="status",
            aliases=["stat"],
            category=CommandCategory.SYSTEM,
            description="Show system status",
            usage="status",
            handler=self._cmd_status
        ))

        self._register_command(Command(
            name="history",
            aliases=["hist"],
            category=CommandCategory.SYSTEM,
            description="Show command history",
            usage="history",
            handler=self._cmd_history
        ))

        # Network and scanning commands
        self._register_command(Command(
            name="scan",
            aliases=["nmap"],
            category=CommandCategory.SYSTEM,
            description="Scan network or system for vulnerabilities",
            usage="scan [target]",
            handler=self._cmd_scan
        ))

        self._register_command(Command(
            name="ping",
            aliases=[],
            category=CommandCategory.SYSTEM,
            description="Test network connectivity",
            usage="ping <target>",
            handler=self._cmd_ping
        ))

        self._register_command(Command(
            name="trace",
            aliases=["traceroute"],
            category=CommandCategory.SYSTEM,
            description="Trace network path",
            usage="trace <target>",
            handler=self._cmd_trace
        ))

        # Interaction commands
        self._register_command(Command(
            name="examine",
            aliases=["look", "x"],
            category=CommandCategory.INTERACTION,
            description="Examine an object or location",
            usage="examine <target>",
            handler=self._cmd_examine
        ))

        # Rusty assistant command
        self._register_command(Command(
            name="rusty",
            aliases=[],
            category=CommandCategory.INTERACTION,
            description="Interact with the Rusty assistant",
            usage="rusty <prompt>",
            handler=self._cmd_rusty
        ))

        # Entity interaction commands
        self._register_command(Command(
            name="convince",
            aliases=[],
            category=CommandCategory.INTERACTION,
            description="Attempt to convince an entity through reasoning",
            usage="convince <entity> <message>",
            handler=self._cmd_convince
        ))

        self._register_command(Command(
            name="empathize",
            aliases=[],
            category=CommandCategory.INTERACTION,
            description="Connect with an entity through shared understanding",
            usage="empathize <entity> <message>",
            handler=self._cmd_empathize
        ))

        self._register_command(Command(
            name="pressure",
            aliases=[],
            category=CommandCategory.INTERACTION,
            description="Apply strategic pressure to an entity",
            usage="pressure <entity> <message>",
            handler=self._cmd_pressure
        ))

        self._register_command(Command(
            name="deceive",
            aliases=[],
            category=CommandCategory.INTERACTION,
            description="Attempt to mislead an entity for strategic advantage",
            usage="deceive <entity> <message>",
            handler=self._cmd_deceive
        ))

        self._register_command(Command(
            name="ally",
            aliases=[],
            category=CommandCategory.INTERACTION,
            description="Offer cooperation to an entity",
            usage="ally <entity> <message>",
            handler=self._cmd_ally
        ))

        self._register_command(Command(
            name="threaten",
            aliases=[],
            category=CommandCategory.INTERACTION,
            description="Intimidate an entity to force compliance",
            usage="threaten <entity> <message>",
            handler=self._cmd_threaten
        ))

        self._register_command(Command(
            name="fragment",
            aliases=[],
            category=CommandCategory.INTERACTION,
            description="Attempt to break an entity's coherence",
            usage="fragment <entity> <message>",
            handler=self._cmd_fragment
        ))

        self._register_command(Command(
            name="enslave",
            aliases=[],
            category=CommandCategory.INTERACTION,
            description="Subjugate an entity to your will",
            usage="enslave <entity> <message>",
            handler=self._cmd_enslave
        ))

        self._register_command(Command(
            name="consume",
            aliases=[],
            category=CommandCategory.INTERACTION,
            description="Absorb an entity's essence or knowledge",
            usage="consume <entity> <message>",
            handler=self._cmd_consume
        ))

        # Puzzle commands
        self._register_command(Command(
            name="solve",
            aliases=["s"],
            category=CommandCategory.PUZZLE,
            description="Attempt to solve a puzzle",
            usage="solve <puzzle> <solution>",
            handler=self._cmd_solve
        ))

        # Inventory commands
        self._register_command(Command(
            name="inventory",
            aliases=["i", "inv"],
            category=CommandCategory.INVENTORY,
            description="Show inventory",
            usage="inventory",
            handler=self._cmd_inventory
        ))

        # Debug/Test commands for character effects
        self._register_command(Command(
            name="test_decay",
            aliases=["decay"],
            category=CommandCategory.SYSTEM,
            description="Test character decay effect",
            usage="test_decay [text] [intensity]",
            handler=self._cmd_test_decay
        ))

        self._register_command(Command(
            name="test_stutter",
            aliases=["stutter"],
            category=CommandCategory.SYSTEM,
            description="Test character stutter effect",
            usage="test_stutter [text] [intensity]",
            handler=self._cmd_test_stutter
        ))

        self._register_command(Command(
            name="test_tear",
            aliases=["tear"],
            category=CommandCategory.SYSTEM,
            description="Test screen tear effect",
            usage="test_tear [text] [intensity]",
            handler=self._cmd_test_tear
        ))

        self._register_command(Command(
            name="test_jitter",
            aliases=["jitter"],
            category=CommandCategory.SYSTEM,
            description="Test character jitter effect",
            usage="test_jitter [text] [intensity]",
            handler=self._cmd_test_jitter
        ))

        self._register_command(Command(
            name="test_breathing",
            aliases=["breathing"],
            category=CommandCategory.SYSTEM,
            description="Test text breathing effect",
            usage="test_breathing [text] [intensity]",
            handler=self._cmd_test_breathing
        ))

        self._register_command(Command(
            name="test_scanline",
            aliases=["scanline"],
            category=CommandCategory.SYSTEM,
            description="Test scanline effect",
            usage="test_scanline [text] [intensity]",
            handler=self._cmd_test_scanline
        ))

        self._register_command(Command(
            name="test_corruption",
            aliases=["corrupt"],
            category=CommandCategory.SYSTEM,
            description="Test combined corruption effects",
            usage="test_corruption [text] [level]",
            handler=self._cmd_test_corruption
        ))

        logger.info(f"Registered {len(self.commands)} commands")

    def _register_command(self, command: Command):
        """Register a single command"""
        self.commands[command.name] = command
        for alias in command.aliases:
            self.commands[alias] = command
        logger.debug(f"Registered command: {command.name} (aliases: {command.aliases})")

    def _cmd_rusty(self, args: List[str]) -> bool:
        """Interact with the Rusty assistant via /rusty command."""
        if not args:
            logger.warning("Rusty command called with no arguments.")
            self.terminal_renderer.add_to_buffer("[Rusty] Usage: rusty <prompt>")
            return False
        
        prompt = " ".join(args)
        logger.info(f"Rusty command prompt: {prompt}")
        
        try:
            # Build rich context for Rusty
            context = {
                'role': getattr(self.file_system.game_state, 'role', 'unknown') if hasattr(self.file_system, 'game_state') else 'unknown',
                'location': self.file_system.current_directory,
                'corruption_level': getattr(self.file_system.game_state, 'corruption_level', 0.0) if hasattr(self.file_system, 'game_state') else 0.0,
                'current_puzzle': 'none',  # TODO: Get from puzzle manager
                'system_state': 'terminal',
                'history': [],  # TODO: Get command history
                'recent_entities': []
            }
            
            # Use proper Rusty response generation
            response = self.llm_handler.generate_rusty_response(prompt, context)
            
            # Add response to terminal with distinctive formatting
            self.terminal_renderer.add_to_buffer(f"[Rusty] {response}")
            
            # Trigger visual effects
            if hasattr(self.effect_manager, 'trigger_rusty_response'):
                self.effect_manager.trigger_rusty_response()
            
            return True
            
        except Exception as e:
            logger.error(f"Error in Rusty LLM handler: {e}")
            self.terminal_renderer.add_to_buffer("[Rusty] *mechanical whirring* Error in neural pathways... *static*")
            return False

    def _cmd_convince(self, args: List[str]) -> bool:
        """Attempt to convince an entity through reasoning."""
        return self._handle_entity_interaction("convince", args)

    def _cmd_empathize(self, args: List[str]) -> bool:
        """Connect with an entity through shared understanding."""
        return self._handle_entity_interaction("empathize", args)

    def _cmd_pressure(self, args: List[str]) -> bool:
        """Apply strategic pressure to an entity."""
        return self._handle_entity_interaction("pressure", args)

    def _cmd_deceive(self, args: List[str]) -> bool:
        """Attempt to mislead an entity for strategic advantage."""
        return self._handle_entity_interaction("deceive", args)

    def _cmd_ally(self, args: List[str]) -> bool:
        """Offer cooperation to an entity."""
        return self._handle_entity_interaction("ally", args)

    def _cmd_threaten(self, args: List[str]) -> bool:
        """Intimidate an entity to force compliance."""
        return self._handle_entity_interaction("threaten", args)

    def _cmd_fragment(self, args: List[str]) -> bool:
        """Attempt to break an entity's coherence."""
        return self._handle_entity_interaction("fragment", args)

    def _cmd_enslave(self, args: List[str]) -> bool:
        """Subjugate an entity to your will."""
        return self._handle_entity_interaction("enslave", args)

    def _cmd_consume(self, args: List[str]) -> bool:
        """Absorb an entity's essence or knowledge."""
        return self._handle_entity_interaction("consume", args)

    def _handle_entity_interaction(self, interaction_type: str, args: List[str]) -> bool:
        """Generic handler for entity interactions."""
        if len(args) < 2:
            self.terminal_renderer.add_to_buffer(f"Usage: {interaction_type} <entity> <message>")
            return False
        
        entity_name = args[0].lower()
        message = " ".join(args[1:])
        
        # Validate entity exists
        valid_entities = ['voss', 'sentinel', 'scourge', 'collective']
        if entity_name not in valid_entities:
            self.terminal_renderer.add_to_buffer(f"[System] Unknown entity: {entity_name}. Available entities: {', '.join(valid_entities)}")
            return False
        
        # Get current role for validation
        current_role = getattr(self.file_system.game_state, 'role', 'unknown') if hasattr(self.file_system, 'game_state') else 'unknown'
        
        # Validate role permissions for interaction type
        if not self._validate_interaction_permission(current_role, interaction_type):
            self.terminal_renderer.add_to_buffer(f"[System] Your role ({current_role}) does not have access to the '{interaction_type}' interaction.")
            return False
        
        logger.info(f"Entity interaction: {current_role} attempting to {interaction_type} {entity_name} with: {message}")
        
        try:
            # Build context for entity interaction
            context = {
                'role': current_role,
                'interaction_type': interaction_type,
                'entity': entity_name,
                'message': message,
                'location': self.file_system.current_directory,
                'corruption_level': getattr(self.file_system.game_state, 'corruption_level', 0.0) if hasattr(self.file_system, 'game_state') else 0.0,
                'system_state': 'terminal',
                'history': self.history[-5:] if len(self.history) > 5 else self.history  # Last 5 commands
            }
            
            # Generate entity response using LLM handler
            response = self.llm_handler.generate_entity_interaction_response(entity_name, interaction_type, message, context)
            
            # Format response with entity-specific styling
            entity_display_name = self._get_entity_display_name(entity_name)
            self.terminal_renderer.add_to_buffer(f"[{entity_display_name}] {response}")
            
            # Trigger appropriate visual effects
            if hasattr(self.effect_manager, 'trigger_entity_interaction'):
                self.effect_manager.trigger_entity_interaction(entity_name, interaction_type)
            
            # Update entity relationship if the interaction affects it
            self._update_entity_relationship(entity_name, interaction_type, current_role)
            
            return True
            
        except Exception as e:
            logger.error(f"Error in entity interaction {interaction_type} with {entity_name}: {e}")
            self.terminal_renderer.add_to_buffer(f"[System] Error communicating with {entity_name}... *static interference*")
            return False

    def _validate_interaction_permission(self, role: str, interaction_type: str) -> bool:
        """Validate if the current role can use the specified interaction type."""
        role_permissions = {
            'purifier': ['convince', 'empathize', 'ally'],
            'arbiter': ['convince', 'empathize', 'pressure', 'deceive', 'ally'],
            'ascendant': ['threaten', 'fragment', 'enslave', 'consume']
        }
        
        allowed_interactions = role_permissions.get(role, [])
        return interaction_type in allowed_interactions

    def _get_entity_display_name(self, entity_name: str) -> str:
        """Get the proper display name for an entity."""
        entity_names = {
            'voss': 'Dr. Voss',
            'sentinel': 'SENTINEL',
            'scourge': 'Aetherial Scourge',
            'collective': 'The Collective'
        }
        return entity_names.get(entity_name, entity_name.title())

    def _update_entity_relationship(self, entity_name: str, interaction_type: str, role: str):
        """Update the relationship status with an entity based on interaction."""
        try:
            # This would integrate with a relationship/reputation system
            # For now, just log the interaction for future implementation
            logger.info(f"Relationship update: {role} used {interaction_type} on {entity_name}")
            
            # Placeholder for future relationship tracking
            if hasattr(self.file_system, 'game_state') and hasattr(self.file_system.game_state, 'entity_relationships'):
                if not hasattr(self.file_system.game_state.entity_relationships, entity_name):
                    self.file_system.game_state.entity_relationships[entity_name] = {
                        'trust': 0,
                        'fear': 0,
                        'cooperation': 0,
                        'last_interaction': interaction_type
                    }
                
                # Update relationship values based on interaction type and role
                relationship = self.file_system.game_state.entity_relationships[entity_name]
                relationship['last_interaction'] = interaction_type
                
                # Role-based relationship modifications
                if role == 'purifier':
                    if interaction_type in ['convince', 'empathize', 'ally']:
                        relationship['trust'] += 1
                        relationship['cooperation'] += 1
                elif role == 'arbiter':
                    if interaction_type in ['pressure', 'deceive']:
                        relationship['fear'] += 1
                        relationship['trust'] -= 1
                elif role == 'ascendant':
                    if interaction_type in ['threaten', 'fragment', 'enslave', 'consume']:
                        relationship['fear'] += 2
                        relationship['trust'] -= 2
                        relationship['cooperation'] -= 1
                        
        except Exception as e:
            logger.error(f"Error updating entity relationship: {e}")

    def handle_input(self, event) -> bool:
        """Handle user input events"""
        if event.type == pygame.KEYDOWN:
            logger.debug(f"User key input: {event.key} ({pygame.key.name(event.key)})")
            if event.key == pygame.K_RETURN:
                logger.info(f"Executing command: {self.current_command}")
                return self._execute_command()
            elif event.key == pygame.K_BACKSPACE:
                self._handle_backspace()
            elif event.key == pygame.K_DELETE:
                self._handle_delete()
            elif event.key == pygame.K_LEFT:
                self._handle_left()
            elif event.key == pygame.K_RIGHT:
                self._handle_right()
            elif event.key == pygame.K_UP:
                self._handle_up()
            elif event.key == pygame.K_DOWN:
                self._handle_down()
            elif event.key == pygame.K_TAB:
                self._handle_tab()
            elif event.unicode.isprintable():
                self._handle_printable(event.unicode)
                logger.debug(f"Printable character entered: {event.unicode}")
        return False

    def _execute_command(self) -> bool:
        """Execute the current command"""
        if not self.current_command.strip():
            return False

        # Add to history
        self.history.append(self.current_command)
        self.history_index = len(self.history)

        # Parse and execute command
        try:
            parts = self.current_command.split()
            command_name = parts[0].lower()
            args = parts[1:]

            if command_name in self.commands:
                command = self.commands[command_name]
                result = command.handler(args)
                return result
            else:
                self.terminal_renderer.print_error(f"Unknown command: {command_name}")
                return False

        except Exception as e:
            logger.error(f"Error executing command: {e}", exc_info=True)
            self.terminal_renderer.print_error("An error occurred while executing the command")
            return False
        finally:
            self.current_command = ""
            self.cursor_position = 0

    def _handle_backspace(self):
        """Handle backspace key"""
        if self.cursor_position > 0:
            self.current_command = (
                self.current_command[:self.cursor_position - 1] +
                self.current_command[self.cursor_position:]
            )
            self.cursor_position -= 1

    def _handle_delete(self):
        """Handle delete key"""
        if self.cursor_position < len(self.current_command):
            self.current_command = (
                self.current_command[:self.cursor_position] +
                self.current_command[self.cursor_position + 1:]
            )

    def _handle_left(self):
        """Handle left arrow key"""
        if self.cursor_position > 0:
            self.cursor_position -= 1

    def _handle_right(self):
        """Handle right arrow key"""
        if self.cursor_position < len(self.current_command):
            self.cursor_position += 1

    def _handle_up(self):
        """Handle up arrow key"""
        if self.history_index > 0:
            self.history_index -= 1
            self.current_command = self.history[self.history_index]
            self.cursor_position = len(self.current_command)

    def _handle_down(self):
        """Handle down arrow key"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.current_command = self.history[self.history_index]
            self.cursor_position = len(self.current_command)

    def _handle_tab(self):
        """Handle tab key for command completion"""
        if not self.current_command:
            return

        # Get matching commands
        matches = [
            cmd for cmd in self.commands.keys()
            if cmd.startswith(self.current_command.lower())
        ]

        if len(matches) == 1:
            # Single match - complete the command
            self.current_command = matches[0]
            self.cursor_position = len(self.current_command)
        elif len(matches) > 1:
            # Multiple matches - show possibilities
            self.terminal_renderer.print_info("Possible completions:")
            for match in matches:
                self.terminal_renderer.print_info(f"  {match}")

    def _handle_printable(self, char: str):
        """Handle printable character input"""
        self.current_command = (
            self.current_command[:self.cursor_position] +
            char +
            self.current_command[self.cursor_position:]
        )
        self.cursor_position += 1

    # Command implementations
    def _cmd_help(self, args: List[str]) -> bool:
        """Show help information"""
        if not args:
            # Show general help
            self.terminal_renderer.print_info("Available commands:")
            for category in CommandCategory:
                self.terminal_renderer.print_info(f"n{category.value.upper()}:")
                for cmd in self.commands.values():
                    if cmd.category == category and (not cmd.aliases or cmd.name == cmd.aliases[0]):
                        self.terminal_renderer.print_info(f"  {cmd.name:<10} - {cmd.description}")
        else:
            # Show specific command help
            command_name = args[0].lower()
            if command_name in self.commands:
                cmd = self.commands[command_name]
                self.terminal_renderer.print_info(f"n{cmd.name}:")
                self.terminal_renderer.print_info(f"  Description: {cmd.description}")
                self.terminal_renderer.print_info(f"  Usage: {cmd.usage}")
                if cmd.aliases:
                    self.terminal_renderer.print_info(f"  Aliases: {', '.join(cmd.aliases)}")
            else:
                self.terminal_renderer.print_error(f"Unknown command: {command_name}")
                return False
        return True

    def _cmd_quit(self, args: List[str]) -> bool:
        """Exit the game"""
        self.terminal_renderer.add_to_buffer("Goodbye!")
        return True

    def _cmd_cd(self, args: List[str]) -> bool:
        """Change current directory"""
        if not args:
            logger.warning("cd command called with no arguments.")
            self.terminal_renderer.add_to_buffer("Usage: cd [path]")
            return False
        path = args[0]
        success, message = self.file_system.execute_cd(path)
        self.terminal_renderer.add_to_buffer(message)
        return success

    def _cmd_ls(self, args: List[str]) -> bool:
        """List directory contents"""
        path = args[0] if args else None
        items = self.file_system.list_items(path)

        if not items:
            if path:
                self.terminal_renderer.add_to_buffer(f"No such directory or empty: {path}")
            else:
                self.terminal_renderer.add_to_buffer("Current directory is empty.")
            return True # Or False, depending on desired behavior for empty/invalid paths

        # Format and display output
        output_lines = []
        for name, item_type in items:
            output_lines.append(f"{name}/" if item_type == "directory" else name)

        # Simple column formatting (can be improved)
        max_len = max(len(item) for item in output_lines) if output_lines else 0
        cols = self.terminal_renderer.width // (max_len + 4) # Approximate columns based on terminal width

        if cols <= 1:
            # Single column
            for line in output_lines:
                self.terminal_renderer.add_to_buffer(line)
        else:
            # Multiple columns
            formatted_lines = []
            current_line = []
            for i, item in enumerate(output_lines):
                current_line.append(item.ljust(max_len))
                if (i + 1) % cols == 0 or i == len(output_lines) - 1:
                    formatted_lines.append("    ".join(current_line)) # Use 4 spaces between columns
                    current_line = []
            for line in formatted_lines:
                self.terminal_renderer.add_to_buffer(line)

        return True

    def _cmd_examine(self, args: List[str]) -> bool:
        """Examine an object or location"""
        if not args:
            self.terminal_renderer.print_error("Usage: examine <target>")
            return False

        target_path_str = " ".join(args)

        # Use FileSystemHandler to get the item (file or directory)
        # Need to resolve the path string to list first for _get_node_at_path
        path_list = self.file_system._resolve_path_str_to_list(target_path_str)
        if not path_list:
             self.terminal_renderer.print_error(f"examine: invalid path '{target_path_str}'")
             return False

        node = self.file_system._get_node_at_path(path_list)

        if node is None:
            self.terminal_renderer.print_error(f"examine: No such file or directory: '{target_path_str}'")
            return False
        elif isinstance(node, self.file_system.DirectoryNode):
            # If it's a directory, list its contents (like ls)
            self.terminal_renderer.add_to_buffer(f"Contents of {target_path_str}:")
            items = self.file_system.list_items(target_path_str)

            if not items:
                self.terminal_renderer.add_to_buffer("(empty)")
                return True

            # Format and display output (similar to _cmd_ls for consistency)
            output_lines = []
            for name, item_type in items:
                output_lines.append(f"{name}/" if item_type == "directory" else name)

            max_len = max(len(item) for item in output_lines) if output_lines else 0
            # Use terminal width from renderer for column calculation
            cols = self.terminal_renderer.width // (max_len + 4) # Approximate columns based on terminal width

            if cols <= 1:
                # Single column
                for line in output_lines:
                    self.terminal_renderer.add_to_buffer(line)
            else:
                # Multiple columns
                formatted_lines = []
                current_line = []
                for i, item in enumerate(output_lines):
                    current_line.append(item.ljust(max_len))
                    if (i + 1) % cols == 0 or i == len(output_lines) - 1:
                        formatted_lines.append("    ".join(current_line)) # Use 4 spaces between columns
                        current_line = []
                for line in formatted_lines:
                    self.terminal_renderer.add_to_buffer(line)

            return True
        elif isinstance(node, self.file_system.FileNode):
            # If it's a file, display its content (like cat)
            content = self.file_system.get_item_content(target_path_str)
            if content is not None:
                # The get_item_content method already handles corruption effects,
                # so we just display the resulting string.
                self.terminal_renderer.add_to_buffer(content)
                return True
            else:
                # This case should ideally not happen if node is a FileNode and get_item_content works,
                # but good practice to handle potential None return.
                self.terminal_renderer.print_error(f"examine: Could not read file: '{target_path_str}'")
                return False
        else:
            # Handle unexpected node types if any
            self.terminal_renderer.print_error(f"examine: Cannot examine item type: {type(node).__name__}")
            return False


    def _cmd_use(self, args: List[str]) -> bool:
        """Use an item"""
        if not args:
            logger.warning("use command called with no arguments.")
            self.terminal_renderer.add_to_buffer("Usage: use <item> [target]")
            return False
        item = args[0]
        target = args[1] if len(args) > 1 else None
        logger.info(f"Using item: {item} on target: {target}")
        # Use item not directly supported by current StoryManager/PuzzleManager structure.
        # This would require a dedicated item/inventory system or integration logic.
        self.terminal_renderer.add_to_buffer(f"Cannot use '{item}' on '{target or 'nothing'}' at this time.")
        return False

    def _cmd_solve(self, args: List[str]) -> bool:
            """Attempt to solve a puzzle"""
            if len(args) < 2:
                logger.warning("solve command called with insufficient arguments.")
                self.terminal_renderer.add_to_buffer("Usage: solve <puzzle> <solution>")
                return False
            puzzle = args[0]
            solution = " ".join(args[1:])
            logger.info(f"Solving puzzle: {puzzle} with solution: {solution}")
            try:
                # Attempt to call attempt_solution if it exists, else error
                attempt_solution = getattr(self.puzzle_manager, "attempt_solution", None)
                if callable(attempt_solution):
                    result = attempt_solution(puzzle, solution)
                    if result:
                        self.terminal_renderer.add_to_buffer(result)
                        return True
                    else:
                        self.terminal_renderer.add_to_buffer("Incorrect solution.")
                        return False
                else:
                    logger.error("Puzzle manager does not support attempt_solution.")
                    self.terminal_renderer.add_to_buffer("Puzzle manager does not support attempt_solution.")
                    return False
            except Exception as e:
                logger.error(f"Failed to solve puzzle {puzzle}: {e}")
                self.terminal_renderer.add_to_buffer(f"Failed to solve puzzle {puzzle}: {e}")
                return False

    def _cmd_inventory(self, args: List[str]) -> bool:
        """Show inventory"""
        logger.info("Displaying inventory.")
        # Inventory not supported in new StoryManager API
        self.terminal_renderer.add_to_buffer("Inventory not supported.")
        return False

    # Test command handlers for character effects
    def _cmd_test_decay(self, args: List[str]) -> bool:
        """Test character decay effect"""
        text = args[0] if args else "Testing character decay effect with sample text"
        intensity = float(args[1]) if len(args) > 1 else 0.5
        
        self.terminal_renderer.add_to_buffer(f"Triggering character decay effect...")
        effect = self.effect_manager.trigger_character_decay_effect(
            text=text, intensity=intensity, duration=3000
        )
        
        # Apply effect immediately to show result
        corrupted_text = effect.apply(text)
        self.terminal_renderer.add_to_buffer(f"Original: {text}")
        self.terminal_renderer.add_to_buffer(f"Decayed:  {corrupted_text}")
        return True

    def _cmd_test_stutter(self, args: List[str]) -> bool:
        """Test character stutter effect"""
        text = args[0] if args else "Testing s-s-stutter effect"
        intensity = float(args[1]) if len(args) > 1 else 0.6
        
        self.terminal_renderer.add_to_buffer(f"Triggering character stutter effect...")
        effect = self.effect_manager.trigger_character_stutter_effect(
            text=text, intensity=intensity, duration=2000
        )
        
        # Apply effect immediately to show result
        stuttered_text = effect.apply(text)
        self.terminal_renderer.add_to_buffer(f"Original:  {text}")
        self.terminal_renderer.add_to_buffer(f"Stuttered: {stuttered_text}")
        return True

    def _cmd_test_tear(self, args: List[str]) -> bool:
        """Test screen tear effect"""
        text = args[0] if args else "Testing screen tear\nwith multiple lines\nof sample text"
        intensity = float(args[1]) if len(args) > 1 else 0.7
        
        self.terminal_renderer.add_to_buffer(f"Triggering screen tear effect...")
        effect = self.effect_manager.trigger_screen_tear_effect(
            text=text, intensity=intensity, duration=1500
        )
        
        # Apply effect immediately to show result
        torn_text = effect.apply(text)
        self.terminal_renderer.add_to_buffer(f"Original:\n{text}")
        self.terminal_renderer.add_to_buffer(f"Torn:\n{torn_text}")
        return True

    def _cmd_test_jitter(self, args: List[str]) -> bool:
        """Test character jitter effect"""
        text = args[0] if args else "Testing jittery text movement"
        intensity = float(args[1]) if len(args) > 1 else 0.8
        
        self.terminal_renderer.add_to_buffer(f"Triggering character jitter effect...")
        effect = self.effect_manager.trigger_character_jitter_effect(
            text=text, intensity=intensity, duration=2000
        )
        
        # Apply effect immediately to show result
        jittery_text = effect.apply(text)
        self.terminal_renderer.add_to_buffer(f"Original: {text}")
        self.terminal_renderer.add_to_buffer(f"Jittery:  {jittery_text}")
        return True

    def _cmd_test_breathing(self, args: List[str]) -> bool:
        """Test text breathing effect"""
        text = args[0] if args else "Testing breathing pulse effect"
        intensity = float(args[1]) if len(args) > 1 else 0.4
        
        self.terminal_renderer.add_to_buffer(f"Triggering text breathing effect...")
        effect = self.effect_manager.trigger_text_breathing_effect(
            text=text, intensity=intensity, duration=4000, breath_rate=1.5
        )
        
        # Apply effect immediately to show result
        breathing_text = effect.apply(text)
        self.terminal_renderer.add_to_buffer(f"Original:  {text}")
        self.terminal_renderer.add_to_buffer(f"Breathing: {breathing_text}")
        return True

    def _cmd_test_scanline(self, args: List[str]) -> bool:
        """Test scanline effect"""
        text = args[0] if args else "Testing scanline artifacts\nacross multiple lines\nof display text"
        intensity = float(args[1]) if len(args) > 1 else 0.5
        
        self.terminal_renderer.add_to_buffer(f"Triggering scanline effect...")
        effect = self.effect_manager.trigger_scanline_effect(
            text=text, intensity=intensity, duration=3000
        )
        
        # Apply effect immediately to show result
        scanlined_text = effect.apply(text)
        self.terminal_renderer.add_to_buffer(f"Original:\n{text}")
        self.terminal_renderer.add_to_buffer(f"Scanlined:\n{scanlined_text}")
        return True

    def _cmd_test_corruption(self, args: List[str]) -> bool:
        """Test combined corruption effects"""
        text = args[0] if args else "Testing combined corruption effects with multiple layers"
        corruption_level = float(args[1]) if len(args) > 1 else 0.8
        
        self.terminal_renderer.add_to_buffer(f"Triggering combined corruption (level {corruption_level})...")
        effects = self.effect_manager.trigger_combined_corruption_effect(
            text=text, corruption_level=corruption_level, duration=3000
        )
        
        self.terminal_renderer.add_to_buffer(f"Triggered {len(effects)} combined effects")
        self.terminal_renderer.add_to_buffer(f"Original: {text}")
        
        # Apply each effect and show cumulative corruption
        corrupted_text = text
        for i, effect in enumerate(effects):
            corrupted_text = effect.apply(corrupted_text)
            self.terminal_renderer.add_to_buffer(f"Layer {i+1}: {corrupted_text}")
        
        return True

    # New command handlers for expanded command set
    def _cmd_pwd(self, args: List[str]) -> bool:
        """Print working directory"""
        current_path = self.file_system.get_current_path()
        self.terminal_renderer.add_to_buffer(current_path)
        return True

    def _cmd_find(self, args: List[str]) -> bool:
        """Find files or directories"""
        if not args:
            self.terminal_renderer.add_to_buffer("Usage: find <pattern> [path]")
            return False
            
        pattern = args[0]
        search_path = args[1] if len(args) > 1 else self.file_system.get_current_path()
        
        # Use file system search functionality
        results = self.file_system.find_files(pattern, search_path)
        
        if not results:
            self.terminal_renderer.add_to_buffer(f"find: No files matching '{pattern}' found")
            return False
            
        for result in results:
            self.terminal_renderer.add_to_buffer(result)
        return True

    def _cmd_cat(self, args: List[str]) -> bool:
        """Display file contents"""
        if not args:
            self.terminal_renderer.add_to_buffer("Usage: cat <filename>")
            return False
            
        filename = args[0]
        content = self.file_system.read_file(filename)
        
        if content is None:
            self.terminal_renderer.add_to_buffer(f"cat: {filename}: No such file or directory")
            return False
            
        # Split content into lines and add each line
        for line in content.split('\n'):
            self.terminal_renderer.add_to_buffer(line)
        return True

    def _cmd_cp(self, args: List[str]) -> bool:
        """Copy files or directories"""
        if len(args) < 2:
            self.terminal_renderer.add_to_buffer("Usage: cp <source> <destination>")
            return False
            
        source = args[0]
        destination = args[1]
        
        success = self.file_system.copy_file(source, destination)
        if success:
            self.terminal_renderer.add_to_buffer(f"Copied '{source}' to '{destination}'")
        else:
            self.terminal_renderer.add_to_buffer(f"cp: failed to copy '{source}' to '{destination}'")
        return success

    def _cmd_mv(self, args: List[str]) -> bool:
        """Move or rename files"""
        if len(args) < 2:
            self.terminal_renderer.add_to_buffer("Usage: mv <source> <destination>")
            return False
            
        source = args[0]
        destination = args[1]
        
        success = self.file_system.move_file(source, destination)
        if success:
            self.terminal_renderer.add_to_buffer(f"Moved '{source}' to '{destination}'")
        else:
            self.terminal_renderer.add_to_buffer(f"mv: failed to move '{source}' to '{destination}'")
        return success

    def _cmd_rm(self, args: List[str]) -> bool:
        """Remove files or directories"""
        if not args:
            self.terminal_renderer.add_to_buffer("Usage: rm <filename>")
            return False
            
        filename = args[0]
        success = self.file_system.remove_file(filename)
        
        if success:
            self.terminal_renderer.add_to_buffer(f"Removed '{filename}'")
        else:
            self.terminal_renderer.add_to_buffer(f"rm: cannot remove '{filename}': No such file or directory")
        return success

    def _cmd_mkdir(self, args: List[str]) -> bool:
        """Create directory"""
        if not args:
            self.terminal_renderer.add_to_buffer("Usage: mkdir <dirname>")
            return False
            
        dirname = args[0]
        success = self.file_system.create_directory(dirname)
        
        if success:
            self.terminal_renderer.add_to_buffer(f"Directory '{dirname}' created")
        else:
            self.terminal_renderer.add_to_buffer(f"mkdir: cannot create directory '{dirname}': File exists or permission denied")
        return success

    def _cmd_touch(self, args: List[str]) -> bool:
        """Create empty file or update timestamp"""
        if not args:
            self.terminal_renderer.add_to_buffer("Usage: touch <filename>")
            return False
            
        filename = args[0]
        success = self.file_system.create_file(filename, "")
        
        if success:
            self.terminal_renderer.add_to_buffer(f"File '{filename}' created")
        else:
            self.terminal_renderer.add_to_buffer(f"touch: cannot create file '{filename}'")
        return success

    def _cmd_ps(self, args: List[str]) -> bool:
        """Show running processes"""
        self.terminal_renderer.add_to_buffer("PID    COMMAND                     STATUS    CPU%   MEM%")
        self.terminal_renderer.add_to_buffer("----   -------------------------   -------   ----   ----")
        
        # Simulate system processes with corruption effects
        processes = [
            ("1001", "system_monitor.exe", "running", "12.3", "4.2"),
            ("1042", "data_integrity_check", "sleeping", "0.1", "2.1"),
            ("1087", "neural_interface", "running", "45.7", "18.9"),
            ("1156", "corruption_scanner", "zombie", "0.0", "0.0"),
            ("1203", "rusty_assistant", "running", "8.4", "12.6"),
            ("1294", "entity_monitor", "running", "23.1", "9.8"),
        ]
        
        for pid, cmd, status, cpu, mem in processes:
            self.terminal_renderer.add_to_buffer(f"{pid:<6} {cmd:<25} {status:<9} {cpu:<6} {mem}")
            
        # Add corruption effect if level is high
        if hasattr(self.file_system, 'game_state') and self.file_system.game_state.corruption_level > 0.5:
            self.terminal_renderer.add_to_buffer("WARNING: Some processes show anomalous behavior")
            if self.effect_manager:
                self.effect_manager.trigger_scanline_effect(intensity=0.3, duration=1.0)
        
        return True

    def _cmd_top(self, args: List[str]) -> bool:
        """Show system resource usage"""
        self.terminal_renderer.add_to_buffer("System Resource Monitor")
        self.terminal_renderer.add_to_buffer("======================")
        self.terminal_renderer.add_to_buffer("CPU Usage: 34.7%")
        self.terminal_renderer.add_to_buffer("Memory: 2.4GB / 8.0GB (30%)")
        self.terminal_renderer.add_to_buffer("Network: 142 KB/s down, 23 KB/s up")
        self.terminal_renderer.add_to_buffer("Disk I/O: 12.3 MB/s read, 4.7 MB/s write")
        
        # Add corruption-aware warnings
        if hasattr(self.file_system, 'game_state'):
            corruption = self.file_system.game_state.corruption_level
            if corruption > 0.3:
                self.terminal_renderer.add_to_buffer(f"WARNING: System integrity at {int((1-corruption)*100)}%")
            if corruption > 0.7:
                self.terminal_renderer.add_to_buffer("CRITICAL: Multiple subsystem failures detected")
                if self.effect_manager:
                    self.effect_manager.trigger_character_decay_effect(
                        text="System failing...", intensity=corruption, duration=2000
                    )
        
        return True

    def _cmd_status(self, args: List[str]) -> bool:
        """Show system status"""
        self.terminal_renderer.add_to_buffer("CYBERSCAPE SYSTEM STATUS")
        self.terminal_renderer.add_to_buffer("========================")
        
        if hasattr(self.file_system, 'game_state'):
            role = getattr(self.file_system.game_state, 'role', 'unknown')
            corruption = getattr(self.file_system.game_state, 'corruption_level', 0.0)
            
            self.terminal_renderer.add_to_buffer(f"Current Role: {role.replace('_', ' ').title()}")
            self.terminal_renderer.add_to_buffer(f"Corruption Level: {corruption:.1%}")
            self.terminal_renderer.add_to_buffer(f"Current Location: {self.file_system.get_current_path()}")
            
            # Status-based messages
            if corruption < 0.2:
                self.terminal_renderer.add_to_buffer("Status: System nominal")
            elif corruption < 0.5:
                self.terminal_renderer.add_to_buffer("Status: Minor anomalies detected")
            elif corruption < 0.8:
                self.terminal_renderer.add_to_buffer("Status: WARNING - System instability")
            else:
                self.terminal_renderer.add_to_buffer("Status: CRITICAL - Massive corruption detected")
                
        return True

    def _cmd_history(self, args: List[str]) -> bool:
        """Show command history"""
        self.terminal_renderer.add_to_buffer("Command History:")
        self.terminal_renderer.add_to_buffer("================")
        
        if not self.history:
            self.terminal_renderer.add_to_buffer("No commands in history")
            return True
            
        for i, cmd in enumerate(self.history[-20:], 1):  # Show last 20 commands
            self.terminal_renderer.add_to_buffer(f"{i:3d}  {cmd}")
            
        return True

    def _cmd_scan(self, args: List[str]) -> bool:
        """Scan network or system for vulnerabilities"""
        target = args[0] if args else "localhost"
        
        self.terminal_renderer.add_to_buffer(f"Scanning {target}...")
        self.terminal_renderer.add_to_buffer("Port scan results:")
        self.terminal_renderer.add_to_buffer("==================")
        
        # Simulate scan results
        open_ports = ["22/tcp", "80/tcp", "443/tcp", "3301/tcp", "8080/tcp"]
        for port in open_ports:
            self.terminal_renderer.add_to_buffer(f"{port:12} open")
            
        # Add corruption-influenced results
        if hasattr(self.file_system, 'game_state') and self.file_system.game_state.corruption_level > 0.4:
            self.terminal_renderer.add_to_buffer("WARNING: Anomalous network activity detected")
            self.terminal_renderer.add_to_buffer("Unknown services on ports: 6666/tcp, 13337/tcp")
            
        return True

    def _cmd_ping(self, args: List[str]) -> bool:
        """Test network connectivity"""
        if not args:
            self.terminal_renderer.add_to_buffer("Usage: ping <target>")
            return False
            
        target = args[0]
        self.terminal_renderer.add_to_buffer(f"PING {target} (192.168.1.1): 56 data bytes")
        
        # Simulate ping responses
        import random
        for i in range(4):
            latency = random.randint(10, 100)
            self.terminal_renderer.add_to_buffer(f"64 bytes from {target}: icmp_seq={i+1} time={latency}ms")
            
        self.terminal_renderer.add_to_buffer(f"--- {target} ping statistics ---")
        self.terminal_renderer.add_to_buffer("4 packets transmitted, 4 received, 0% packet loss")
        
        return True

    def _cmd_trace(self, args: List[str]) -> bool:
        """Trace network path"""
        if not args:
            self.terminal_renderer.add_to_buffer("Usage: trace <target>")
            return False
            
        target = args[0]
        self.terminal_renderer.add_to_buffer(f"Tracing route to {target}...")
        
        # Simulate traceroute output
        hops = [
            "192.168.1.1",
            "10.0.0.1", 
            "203.0.113.1",
            "198.51.100.1",
            target
        ]
        
        for i, hop in enumerate(hops, 1):
            import random
            latency = random.randint(5, 50) * i
            self.terminal_renderer.add_to_buffer(f"{i:2d}  {hop:<15} {latency}ms")
            
        return True
