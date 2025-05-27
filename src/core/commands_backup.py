"""
Command handler module for processing user input and executing game commands
"""

import logging
import pygame
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import os
import random

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
        llm_handler: LLMHandler,
        world_manager=None
    ):
        """Initialize the command handler with all required components"""
        self.effect_manager = effect_manager
        self.file_system = file_system
        self.puzzle_manager = puzzle_manager
        self.story_manager = story_manager
        self.terminal_renderer = terminal_renderer
        self.llm_handler = llm_handler  # Use injected LLMHandler instance
        self.world_manager = world_manager

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

        # Role-specific commands - Purifier
        self._register_command(Command(
            name="purify",
            aliases=["cleanse", "clean"],
            category=CommandCategory.SYSTEM,
            description="Purify corrupted files or systems",
            usage="purify <target>",
            handler=self._cmd_purify,
            requires_role="purifier"
        ))

        self._register_command(Command(
            name="quarantine",
            aliases=["isolate"],
            category=CommandCategory.SYSTEM,
            description="Quarantine infected files or processes",
            usage="quarantine <target>",
            handler=self._cmd_quarantine,
            requires_role="purifier"
        ))

        self._register_command(Command(
            name="integrity",
            aliases=["verify", "check"],
            category=CommandCategory.SYSTEM,
            description="Check system integrity and corruption levels",
            usage="integrity [target]",
            handler=self._cmd_integrity,
            requires_role="purifier"
        ))

        # Role-specific commands - Arbiter
        self._register_command(Command(
            name="analyze",
            aliases=["assess", "evaluate"],
            category=CommandCategory.SYSTEM,
            description="Analyze system vulnerabilities and data",
            usage="analyze <target>",
            handler=self._cmd_analyze,
            requires_role="arbiter"
        ))

        self._register_command(Command(
            name="negotiate",
            aliases=["bargain", "deal"],
            category=CommandCategory.INTERACTION,
            description="Negotiate with entities for information or access",
            usage="negotiate <entity> <terms>",
            handler=self._cmd_negotiate,
            requires_role="arbiter"
        ))

        self._register_command(Command(
            name="exploit",
            aliases=["use", "execute"],
            category=CommandCategory.SYSTEM,
            description="Execute exploits against vulnerabilities",
            usage="exploit <vulnerability> [options]",
            handler=self._cmd_exploit,
            requires_role="arbiter"
        ))

        # Role-specific commands - Ascendant
        self._register_command(Command(
            name="corrupt",
            aliases=["infect", "taint"],
            category=CommandCategory.SYSTEM,
            description="Deliberately corrupt systems or data",
            usage="corrupt <target> [level]",
            handler=self._cmd_corrupt,
            requires_role="ascendant"
        ))

        self._register_command(Command(
            name="absorb",
            aliases=["consume", "assimilate"],
            category=CommandCategory.INTERACTION,
            description="Absorb entity knowledge or power",
            usage="absorb <entity>",
            handler=self._cmd_absorb,
            requires_role="ascendant"
        ))

        self._register_command(Command(
            name="manipulate",
            aliases=["control", "override"],
            category=CommandCategory.SYSTEM,
            description="Manipulate system processes or entity behavior",
            usage="manipulate <target> <action>",
            handler=self._cmd_manipulate,
            requires_role="ascendant"
        ))

        # Advanced system commands
        self._register_command(Command(
            name="decrypt",
            aliases=["unlock", "decode"],
            category=CommandCategory.SYSTEM,
            description="Decrypt encrypted files with provided key",
            usage="decrypt <file> <key>",
            handler=self._cmd_decrypt
        ))

        self._register_command(Command(
            name="encode",
            aliases=["encrypt", "secure"],
            category=CommandCategory.SYSTEM,
            description="Encrypt files or data",
            usage="encode <file> [key]",
            handler=self._cmd_encode
        ))

        self._register_command(Command(
            name="monitor",
            aliases=["watch", "observe"],
            category=CommandCategory.SYSTEM,
            description="Monitor system processes and corruption",
            usage="monitor [duration]",
            handler=self._cmd_monitor
        ))

        self._register_command(Command(
            name="recover",
            aliases=["restore", "repair"],
            category=CommandCategory.SYSTEM,
            description="Attempt to recover corrupted data",
            usage="recover <target>",
            handler=self._cmd_recover
        ))

        # Puzzle and investigation commands
        self._register_command(Command(
            name="solve",
            aliases=["answer", "complete"],
            category=CommandCategory.PUZZLE,
            description="Attempt to solve active puzzle",
            usage="solve <answer>",
            handler=self._cmd_solve_puzzle
        ))

        self._register_command(Command(
            name="hint",
            aliases=["clue", "help_puzzle"],
            category=CommandCategory.PUZZLE,
            description="Get a hint for the current puzzle",
            usage="hint",
            handler=self._cmd_puzzle_hint
        ))

        self._register_command(Command(
            name="investigate",
            aliases=["inspect", "research"],
            category=CommandCategory.INTERACTION,
            description="Investigate objects, files, or entities",
            usage="investigate <target>",
            handler=self._cmd_investigate
        ))

        # System intrusion and hacking commands
        self._register_command(Command(
            name="backdoor",
            aliases=["access", "breach"],
            category=CommandCategory.SYSTEM,
            description="Create or use backdoor access",
            usage="backdoor <target> [method]",
            handler=self._cmd_backdoor
        ))

        self._register_command(Command(
            name="stealth",
            aliases=["hide", "ghost"],
            category=CommandCategory.SYSTEM,
            description="Enable stealth mode to avoid detection",
            usage="stealth [on|off]",
            handler=self._cmd_stealth
        ))

        # Enhanced file operations
        self._register_command(Command(
            name="search",
            aliases=["find", "locate"],
            category=CommandCategory.NAVIGATION,
            description="Search for files, directories, or content",
            usage="search <pattern> [location]",
            handler=self._cmd_search
        ))

        self._register_command(Command(
            name="compile",
            aliases=["build", "make"],
            category=CommandCategory.SYSTEM,
            description="Compile code or assemble tools",
            usage="compile <source> [options]",
            handler=self._cmd_compile
        ))

        # Network and communication
        self._register_command(Command(
            name="connect",
            aliases=["link", "join"],
            category=CommandCategory.SYSTEM,
            description="Establish connection to remote system",
            usage="connect <target> [port]",
            handler=self._cmd_connect
        ))

        # World Navigation Commands
        self._register_command(Command(
            name="layer_info",
            aliases=["layer", "current_layer"],
            category=CommandCategory.NAVIGATION,
            description="Display information about the current network layer",
            usage="layer_info",
            handler=self._cmd_layer_info
        ))

        self._register_command(Command(
            name="explore",
            aliases=["explore_location", "search_area"],
            category=CommandCategory.NAVIGATION,
            description="Explore the current location for hidden content",
            usage="explore [thorough|focused|general]",
            handler=self._cmd_explore
        ))

        self._register_command(Command(
            name="navigate",
            aliases=["go", "move"],
            category=CommandCategory.NAVIGATION,
            description="Navigate to a specific location",
            usage="navigate <location_id>",
            handler=self._cmd_navigate
        ))

        self._register_command(Command(
            name="scan_layer",
            aliases=["layer_scan", "scan_network"],
            category=CommandCategory.NAVIGATION,
            description="Scan the current layer for accessible locations",
            usage="scan_layer",
            handler=self._cmd_scan_layer
        ))

        self._register_command(Command(
            name="layer_transition",
            aliases=["ascend", "descend", "change_layer"],
            category=CommandCategory.NAVIGATION,
            description="Attempt to transition to a different network layer",
            usage="layer_transition <layer_name>",
            handler=self._cmd_layer_transition
        ))

        self._register_command(Command(
            name="world_status",
            aliases=["world_info", "progression"],
            category=CommandCategory.NAVIGATION,
            description="Display world exploration progress and status",
            usage="world_status",
            handler=self._cmd_world_status
        ))

        self._register_command(Command(
            name="location_actions",
            aliases=["actions", "available_actions"],
            category=CommandCategory.NAVIGATION,
            description="Show available actions at the current location",
            usage="location_actions",
            handler=self._cmd_location_actions
        ))

        self._register_command(Command(
            name="traverse",
            aliases=["cross", "bridge"],
            category=CommandCategory.NAVIGATION,
            description="Traverse between connected locations or layers",
            usage="traverse <path_id>",
            handler=self._cmd_traverse
        ))

        # ... existing command registrations continue ...
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

    # New role-specific command implementations
    def _cmd_purify(self, args: List[str]) -> bool:
        """Purify corrupted files or systems (Purifier role)"""
        if not args:
            self.terminal_renderer.add_to_buffer("Usage: purify <target>")
            return False
            
        target = args[0]
        
        # Check if file exists
        if self.file_system.file_exists(target):
            # Get corruption level
            file_info = self.file_system.get_file_info(target)
            if file_info and file_info.get('is_corrupted', False):
                corruption_level = file_info.get('corruption_level', 0.0)
                
                # Purification process
                self.terminal_renderer.add_to_buffer(f"Initiating purification of {target}...")
                self.terminal_renderer.add_to_buffer(f"Corruption level detected: {corruption_level*100:.1f}%")
                
                # Apply purification effect
                success_chance = 0.8 - (corruption_level * 0.3)  # Higher corruption = lower success
                
                if random.random() < success_chance:
                    # Successful purification
                    self.file_system.uncorrupt_file(target)
                    self.terminal_renderer.add_to_buffer(f"✓ Purification successful! {target} has been cleansed.")
                    self.effect_manager.trigger_purification_effect()
                else:
                    # Partial purification
                    new_corruption = max(0.0, corruption_level - 0.3)
                    self.file_system.corrupt_file(target, new_corruption)
                    self.terminal_renderer.add_to_buffer(f"⚠ Partial purification. Corruption reduced to {new_corruption*100:.1f}%")
            else:
                self.terminal_renderer.add_to_buffer(f"{target} is already pure.")
        else:
            self.terminal_renderer.add_to_buffer(f"Target not found: {target}")
            
        return True
    
    def _cmd_quarantine(self, args: List[str]) -> bool:
        """Quarantine infected files (Purifier role)"""
        if not args:
            self.terminal_renderer.add_to_buffer("Usage: quarantine <target>")
            return False
            
        target = args[0]
        
        if self.file_system.file_exists(target):
            # Move to quarantine directory
            quarantine_path = f"/system/quarantine/{os.path.basename(target)}"
            
            if self.file_system.move_file(target, quarantine_path):
                self.terminal_renderer.add_to_buffer(f"✓ {target} quarantined successfully.")
                self.terminal_renderer.add_to_buffer(f"Location: {quarantine_path}")
            else:
                self.terminal_renderer.add_to_buffer(f"✗ Failed to quarantine {target}")
        else:
            self.terminal_renderer.add_to_buffer(f"Target not found: {target}")
            
        return True
    
    def _cmd_integrity(self, args: List[str]) -> bool:
        """Check system integrity (Purifier role)"""
        target = args[0] if args else "/"
        
        self.terminal_renderer.add_to_buffer("SYSTEM INTEGRITY SCAN")
        self.terminal_renderer.add_to_buffer("=" * 30)
        
        # Get filesystem statistics
        stats = self.file_system.get_system_info()
        
        corruption_percentage = stats.get('corruption_percentage', 0)
        total_files = stats.get('total_files', 0)
        corrupted_files = stats.get('corrupted_files', 0)
        
        self.terminal_renderer.add_to_buffer(f"Total files scanned: {total_files}")
        self.terminal_renderer.add_to_buffer(f"Corrupted files found: {corrupted_files}")
        self.terminal_renderer.add_to_buffer(f"Corruption level: {corruption_percentage:.1f}%")
        
        if corruption_percentage < 10:
            self.terminal_renderer.add_to_buffer("Status: ✓ SYSTEM CLEAN")
        elif corruption_percentage < 30:
            self.terminal_renderer.add_to_buffer("Status: ⚠ MINOR CORRUPTION")
        elif corruption_percentage < 60:
            self.terminal_renderer.add_to_buffer("Status: ⚠ MODERATE CORRUPTION")
        else:
            self.terminal_renderer.add_to_buffer("Status: ✗ CRITICAL CORRUPTION")
            
        return True
    
    def _cmd_analyze(self, args: List[str]) -> bool:
        """Analyze system vulnerabilities (Arbiter role)"""
        if not args:
            self.terminal_renderer.add_to_buffer("Usage: analyze <target>")
            return False
            
        target = args[0]
        
        self.terminal_renderer.add_to_buffer(f"VULNERABILITY ANALYSIS: {target}")
        self.terminal_renderer.add_to_buffer("=" * 40)
        
        # Simulate vulnerability scanning
        vulnerabilities = [
            "Buffer overflow in input handler",
            "Privilege escalation vector detected",
            "Unencrypted data transmission",
            "Weak authentication mechanism",
            "SQL injection vulnerability",
            "Cross-site scripting potential"
        ]
        
        found_vulns = random.sample(vulnerabilities, random.randint(1, 4))
        
        for i, vuln in enumerate(found_vulns, 1):
            severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
            self.terminal_renderer.add_to_buffer(f"{i}. {vuln} - {severity}")
        
        self.terminal_renderer.add_to_buffer(f"\nTotal vulnerabilities found: {len(found_vulns)}")
        self.terminal_renderer.add_to_buffer("Recommendation: Immediate patching required")
        
        return True
    
    def _cmd_negotiate(self, args: List[str]) -> bool:
        """Negotiate with entities (Arbiter role)"""
        if len(args) < 2:
            self.terminal_renderer.add_to_buffer("Usage: negotiate <entity> <terms>")
            return False
            
        entity = args[0]
        terms = ' '.join(args[1:])
        
        self.terminal_renderer.add_to_buffer(f"Initiating negotiation with {entity}...")
        self.terminal_renderer.add_to_buffer(f"Terms proposed: {terms}")
        
        # Simulate negotiation based on player's history and entity type
        success_chance = random.uniform(0.3, 0.8)
        
        if random.random() < success_chance:
            self.terminal_renderer.add_to_buffer(f"✓ {entity} accepts your terms.")
            self.terminal_renderer.add_to_buffer("Negotiation successful. Information access granted.")
        else:
            self.terminal_renderer.add_to_buffer(f"✗ {entity} rejects your proposal.")
            self.terminal_renderer.add_to_buffer("Counter-offer required or alternative approach needed.")
            
        return True
    
    def _cmd_exploit(self, args: List[str]) -> bool:
        """Execute exploits (Arbiter role)"""
        if not args:
            self.terminal_renderer.add_to_buffer("Usage: exploit <vulnerability> [options]")
            return False
            
        vulnerability = args[0]
        options = args[1:] if len(args) > 1 else []
        
        self.terminal_renderer.add_to_buffer(f"Executing exploit: {vulnerability}")
        
        # Simulate exploit execution
        exploit_types = {
            "buffer_overflow": "Buffer overflow exploit executed",
            "privilege_escalation": "Privilege escalation successful",
            "sql_injection": "SQL injection payload delivered",
            "xss": "Cross-site scripting exploit active"
        }
        
        if vulnerability.lower() in exploit_types:
            self.terminal_renderer.add_to_buffer(exploit_types[vulnerability.lower()])
            self.terminal_renderer.add_to_buffer("✓ Exploit successful - Access gained")
        else:
            self.terminal_renderer.add_to_buffer(f"Unknown vulnerability: {vulnerability}")
            self.terminal_renderer.add_to_buffer("✗ Exploit failed")
            
        return True
    
    def _cmd_corrupt(self, args: List[str]) -> bool:
        """Deliberately corrupt systems (Ascendant role)"""
        if not args:
            self.terminal_renderer.add_to_buffer("Usage: corrupt <target> [level]")
            return False
            
        target = args[0]
        corruption_level = float(args[1]) if len(args) > 1 else 0.5
        corruption_level = max(0.0, min(1.0, corruption_level))  # Clamp between 0-1
        
        if self.file_system.file_exists(target):
            self.terminal_renderer.add_to_buffer(f"Initiating corruption of {target}...")
            self.terminal_renderer.add_to_buffer(f"Corruption level: {corruption_level*100:.1f}%")
            
            self.file_system.corrupt_file(target, corruption_level)
            
            self.terminal_renderer.add_to_buffer(f"✓ Corruption successful")
            self.terminal_renderer.add_to_buffer("The shadows spread through the data...")
            
            # Trigger corruption visual effects
            self.effect_manager.increase_corruption(corruption_level * 0.1)
        else:
            self.terminal_renderer.add_to_buffer(f"Target not found: {target}")
            
        return True
    
    def _cmd_absorb(self, args: List[str]) -> bool:
        """Absorb entity knowledge (Ascendant role)"""
        if not args:
            self.terminal_renderer.add_to_buffer("Usage: absorb <entity>")
            return False
            
        entity = args[0]
        
        self.terminal_renderer.add_to_buffer(f"Attempting to absorb essence of {entity}...")
        self.terminal_renderer.add_to_buffer("Reality bends as knowledge flows...")
        
        # Simulate absorption with corruption side effects
        absorption_success = random.random() < 0.7
        
        if absorption_success:
            self.terminal_renderer.add_to_buffer(f"✓ Absorption complete. {entity}'s knowledge is now yours.")
            self.terminal_renderer.add_to_buffer("New capabilities unlocked...")
            
            # Increase corruption as side effect
            self.effect_manager.increase_corruption(0.1)
        else:
            self.terminal_renderer.add_to_buffer(f"✗ Absorption failed. {entity} resists.")
            self.terminal_renderer.add_to_buffer("The entity's essence slips away...")
            
        return True
    
    def _cmd_manipulate(self, args: List[str]) -> bool:
        """Manipulate systems or entities (Ascendant role)"""
        if len(args) < 2:
            self.terminal_renderer.add_to_buffer("Usage: manipulate <target> <action>")
            return False
            
        target = args[0]
        action = ' '.join(args[1:])
        
        self.terminal_renderer.add_to_buffer(f"Manipulating {target}: {action}")
        self.terminal_renderer.add_to_buffer("Exerting influence through digital channels...")
        
        # Simulate manipulation with varying success
        manipulation_power = random.uniform(0.4, 0.9)
        
        if manipulation_power > 0.6:
            self.terminal_renderer.add_to_buffer(f"✓ Manipulation successful")
            self.terminal_renderer.add_to_buffer(f"{target} responds to your influence")
        else:
            self.terminal_renderer.add_to_buffer(f"⚠ Partial success")
            self.terminal_renderer.add_to_buffer(f"{target} shows resistance")
            
        return True

    # Advanced system command implementations
    
    def _cmd_decrypt(self, args: List[str]) -> bool:
        """Decrypt encrypted files"""
        if len(args) < 2:
            self.terminal_renderer.add_to_buffer("Usage: decrypt <file> <key>")
            return False
            
        file_path = args[0]
        key = args[1]
        
        if not self.file_system.file_exists(file_path):
            self.terminal_renderer.add_to_buffer(f"File not found: {file_path}")
            return False
            
        content = self.file_system.read_file(file_path)
        
        if not content.startswith("ENCRYPTED_FILE"):
            self.terminal_renderer.add_to_buffer(f"{file_path} is not an encrypted file")
            return False
            
        # Extract key hint and verify
        lines = content.split('\n')
        key_hint_line = next((line for line in lines if line.startswith("KEY_HINT:")), None)
        
        if key_hint_line:
            key_hint = key_hint_line.split(":", 1)[1].strip()
            expected_pattern = f"{key[:2]}***{key[-2:]}" if len(key) >= 4 else "***"
            
            if key_hint == expected_pattern:
                # Decrypt content (reverse the simple encryption)
                encrypted_content = '\n'.join(lines[4:])  # Skip header
                decrypted = self._decrypt_content(encrypted_content, key)
                
                # Save decrypted version
                decrypted_path = file_path.replace('.enc', '').replace('encrypted_', '')
                self.file_system.create_file(decrypted_path, decrypted)
                
                self.terminal_renderer.add_to_buffer(f"✓ Decryption successful")
                self.terminal_renderer.add_to_buffer(f"Decrypted file saved as: {decrypted_path}")
            else:
                self.terminal_renderer.add_to_buffer("✗ Invalid decryption key")
        else:
            self.terminal_renderer.add_to_buffer("✗ Corrupted encryption metadata")
            
        return True
    
    def _decrypt_content(self, encrypted_content: str, key: str) -> str:
        """Decrypt content using the provided key"""
        key_sum = sum(ord(c) for c in key) % 26
        decrypted_chars = []
        
        for char in encrypted_content:
            if char.isalpha():
                base = ord('A') if char.isupper() else ord('a')
                shifted = ((ord(char) - base - key_sum) % 26) + base
                decrypted_chars.append(chr(shifted))
            else:
                decrypted_chars.append(char)
        
        return ''.join(decrypted_chars)
    
    def _cmd_encode(self, args: List[str]) -> bool:
        """Encrypt files or data"""
        if not args:
            self.terminal_renderer.add_to_buffer("Usage: encode <file> [key]")
            return False
            
        file_path = args[0]
        key = args[1] if len(args) > 1 else f"key_{random.randint(1000, 9999)}"
        
        if not self.file_system.file_exists(file_path):
            self.terminal_renderer.add_to_buffer(f"File not found: {file_path}")
            return False
            
        content = self.file_system.read_file(file_path)
        encrypted_path = f"encrypted_{os.path.basename(file_path)}"
        
        encryption_key = self.file_system.create_encrypted_file(encrypted_path, content, key)
        
        self.terminal_renderer.add_to_buffer(f"✓ File encrypted successfully")
        self.terminal_renderer.add_to_buffer(f"Encrypted file: {encrypted_path}")
        self.terminal_renderer.add_to_buffer(f"Encryption key: {encryption_key}")
        
        return True
    
    def _cmd_monitor(self, args: List[str]) -> bool:
        """Monitor system processes and corruption"""
        duration = int(args[0]) if args and args[0].isdigit() else 10
        
        self.terminal_renderer.add_to_buffer(f"Starting system monitor (duration: {duration}s)")
        self.terminal_renderer.add_to_buffer("=" * 40)
        
        # Simulate real-time monitoring
        for i in range(min(duration, 5)):  # Limit to 5 iterations for demo
            stats = self.file_system.get_system_info()
            corruption = stats.get('corruption_percentage', 0)
            
            self.terminal_renderer.add_to_buffer(f"[{i+1:02d}] Corruption: {corruption:.1f}% | "
                                               f"Files: {stats.get('total_files', 0)} | "
                                               f"Locked: {stats.get('locked_files', 0)}")
            
            if corruption > 50:
                self.terminal_renderer.add_to_buffer("⚠ WARNING: High corruption detected!")
                
        self.terminal_renderer.add_to_buffer("Monitoring complete.")
        return True
    
    def _cmd_recover(self, args: List[str]) -> bool:
        """Attempt to recover corrupted data"""
        if not args:
            self.terminal_renderer.add_to_buffer("Usage: recover <target>")
            return False
            
        target = args[0]
        
        if not self.file_system.file_exists(target):
            self.terminal_renderer.add_to_buffer(f"Target not found: {target}")
            return False
            
        file_info = self.file_system.get_file_info(target)
        
        if not file_info.get('is_corrupted', False):
            self.terminal_renderer.add_to_buffer(f"{target} is not corrupted")
            return True
            
        corruption_level = file_info.get('corruption_level', 0)
        
        self.terminal_renderer.add_to_buffer(f"Attempting recovery of {target}...")
        self.terminal_renderer.add_to_buffer(f"Current corruption: {corruption_level*100:.1f}%")
        
        # Recovery success depends on corruption level
        recovery_chance = 1.0 - corruption_level
        
        if random.random() < recovery_chance:
            # Successful recovery
            reduced_corruption = max(0.0, corruption_level - 0.5)
            if reduced_corruption > 0:
                self.file_system.corrupt_file(target, reduced_corruption)
                self.terminal_renderer.add_to_buffer(f"✓ Partial recovery successful")
                self.terminal_renderer.add_to_buffer(f"Corruption reduced to {reduced_corruption*100:.1f}%")
            else:
                # Full recovery
                content = self.file_system.read_file(target)
                # Remove corruption markers from content
                clean_content = self._clean_corrupted_content(content)
                self.file_system.create_file(target, clean_content)
                self.terminal_renderer.add_to_buffer(f"✓ Full recovery successful")
        else:
            self.terminal_renderer.add_to_buffer(f"✗ Recovery failed - corruption too severe")
            
        return True
    
    def _clean_corrupted_content(self, content: str) -> str:
        """Remove corruption markers from content"""
        # Remove corruption prefixes and restore readable text
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove corruption markers
            cleaned_line = line
            corruption_markers = ["[CORRUPTED]", "[ERROR]", "[LOST]", "[NULL]", "[DATA LOST - RECOVERY IMPOSSIBLE]"]
            
            for marker in corruption_markers:
                cleaned_line = cleaned_line.replace(marker, "").strip()
            
            # Only add non-empty lines
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
                
        return '\n'.join(cleaned_lines)
    
    def _cmd_solve_puzzle(self, args: List[str]) -> bool:
        """Attempt to solve active puzzle"""
        if not args:
            self.terminal_renderer.add_to_buffer("Usage: solve <answer>")
            return False
            
        answer = ' '.join(args)
        
        # Check if there's an active puzzle
        if not self.puzzle_manager.has_active_puzzle():
            self.terminal_renderer.add_to_buffer("No active puzzle to solve")
            return False
            
        success, message = self.puzzle_manager.attempt_solution(answer)
        
        self.terminal_renderer.add_to_buffer(message)
        
        if success:
            self.terminal_renderer.add_to_buffer("✓ Puzzle solved successfully!")
            # Trigger puzzle completion effects
            self.effect_manager.trigger_success_effect()
        else:
            self.terminal_renderer.add_to_buffer("✗ Incorrect answer. Try again.")
            
        return True
    
    def _cmd_puzzle_hint(self, args: List[str]) -> bool:
        """Get a hint for the current puzzle"""
        if not self.puzzle_manager.has_active_puzzle():
            self.terminal_renderer.add_to_buffer("No active puzzle for hints")
            return False
            
        hint = self.puzzle_manager.get_hint()
        
        if hint:
            self.terminal_renderer.add_to_buffer(f"Hint: {hint}")
        else:
            self.terminal_renderer.add_to_buffer("No more hints available for this puzzle")
            
        return True
    
    def _cmd_investigate(self, args: List[str]) -> bool:
        """Investigate objects, files, or entities"""
        if not args:
            self.terminal_renderer.add_to_buffer("Usage: investigate <target>")
            return False
            
        target = args[0]
        
        self.terminal_renderer.add_to_buffer(f"INVESTIGATION REPORT: {target}")
        self.terminal_renderer.add_to_buffer("=" * 30)
        
        # Check if target is a file
        if self.file_system.file_exists(target):
            file_info = self.file_system.get_file_info(target)
            
            self.terminal_renderer.add_to_buffer(f"Type: File")
            self.terminal_renderer.add_to_buffer(f"Size: {file_info.get('size', 0)} bytes")
            self.terminal_renderer.add_to_buffer(f"Permissions: {file_info.get('permissions', 'unknown')}")
            self.terminal_renderer.add_to_buffer(f"Created: {file_info.get('created_at', 'unknown')}")
            self.terminal_renderer.add_to_buffer(f"Modified: {file_info.get('modified_at', 'unknown')}")
            
            if file_info.get('is_corrupted', False):
                corruption_level = file_info.get('corruption_level', 0)
                self.terminal_renderer.add_to_buffer(f"⚠ CORRUPTION DETECTED: {corruption_level*100:.1f}%")
                
            # Check for hidden content or metadata
            content = self.file_system.read_file(target)
            if "ENCRYPTED" in content:
                self.terminal_renderer.add_to_buffer("🔒 File contains encrypted data")
            if any(marker in content for marker in ["[CLASSIFIED]", "[REDACTED]", "[SECURE]"]):
                self.terminal_renderer.add_to_buffer("🔐 File contains classified information")
                
        else:
            # Investigate entity or system component
            investigation_results = [
                f"No physical file found for '{target}'",
                "Searching entity database...",
                "Checking system processes...",
                "Analyzing network connections..."
            ]
            
            for result in investigation_results:
                self.terminal_renderer.add_to_buffer(result)
                
            # Simulate finding information about entities
            if target.lower() in ["rusty", "voss", "scourge", "sentinel"]:
                self.terminal_renderer.add_to_buffer(f"Entity profile found: {target}")
                self.terminal_renderer.add_to_buffer("Classification: Digital Consciousness")
                self.terminal_renderer.add_to_buffer("Status: Active")
            else:
                self.terminal_renderer.add_to_buffer("No additional information found")
                
        return True

    # World Navigation Command Handlers
    
    def _cmd_layer_info(self, args: List[str]) -> bool:
        """Display information about the current network layer."""
        if not self.world_manager:
            self.terminal_renderer.add_to_buffer("Error: World manager not available")
            return False
        
        try:
            layer_info = self.world_manager.get_current_layer_info()
            
            self.terminal_renderer.add_to_buffer(f"=== {layer_info['name']} ===")
            self.terminal_renderer.add_to_buffer(f"Description: {layer_info['description']}")
            self.terminal_renderer.add_to_buffer(f"Security Level: {layer_info['security_level']}")
            self.terminal_renderer.add_to_buffer(f"Corruption Level: {layer_info['corruption_level']:.1%}")
            
            if layer_info['available_commands']:
                self.terminal_renderer.add_to_buffer(f"Available Commands: {', '.join(layer_info['available_commands'])}")
            
            if layer_info['accessible_locations']:
                self.terminal_renderer.add_to_buffer("\nAccessible Locations:")
                for location in layer_info['accessible_locations']:
                    status = "🟢 Visited" if location['visited'] else "🔍 Unexplored"
                    progress = f"({location['discovery_progress']:.1%} discovered)"
                    self.terminal_renderer.add_to_buffer(f"  {location['id']}: {location['name']} {status} {progress}")
            
            return True
        except Exception as e:
            self.terminal_renderer.add_to_buffer(f"Error retrieving layer information: {e}")
            return False

    def _cmd_explore(self, args: List[str]) -> bool:
        """Explore the current location for hidden content."""
        if not self.world_manager:
            self.terminal_renderer.add_to_buffer("Error: World manager not available")
            return False
        
        exploration_type = args[0] if args else "general"
        if exploration_type not in ["general", "thorough", "focused"]:
            self.terminal_renderer.add_to_buffer("Usage: explore [general|thorough|focused]")
            return False
        
        try:
            result = self.world_manager.explore_location(exploration_type)
            
            if not result['success']:
                self.terminal_renderer.add_to_buffer(result['message'])
                return False
            
            self.terminal_renderer.add_to_buffer(f"Exploration ({exploration_type}) complete.")
            self.terminal_renderer.add_to_buffer(f"Discovery Progress: {result['discovery_progress']:.1%}")
            
            if result['revealed_content']:
                self.terminal_renderer.add_to_buffer("\n🔍 New content discovered:")
                for content in result['revealed_content']:
                    self.terminal_renderer.add_to_buffer(f"  [{content['type'].upper()}] {content['content']}")
            
            if result['corruption_encountered']:
                self.terminal_renderer.add_to_buffer("\n⚠️  High corruption levels detected during exploration")
            
            return True
        except Exception as e:
            self.terminal_renderer.add_to_buffer(f"Error during exploration: {e}")
            return False

    def _cmd_navigate(self, args: List[str]) -> bool:
        """Navigate to a specific location."""
        if not self.world_manager:
            self.terminal_renderer.add_to_buffer("Error: World manager not available")
            return False
        
        if not args:
            self.terminal_renderer.add_to_buffer("Usage: navigate <location_id>")
            return False
        
        location_id = args[0]
        
        try:
            result = self.world_manager.move_to_location(location_id)
            
            if not result['success']:
                self.terminal_renderer.add_to_buffer(f"Navigation failed: {result['message']}")
                return False
            
            location = result['location']
            self.terminal_renderer.add_to_buffer(f"=== Arrived at {location['name']} ===")
            self.terminal_renderer.add_to_buffer(location['description'])
            
            if location['entities_present']:
                self.terminal_renderer.add_to_buffer(f"\n🤖 Entities detected: {', '.join(location['entities_present'])}")
            
            if location['corruption_level'] > 0.3:
                self.terminal_renderer.add_to_buffer(f"\n⚠️  Corruption level: {location['corruption_level']:.1%}")
            
            if location['available_actions']:
                self.terminal_renderer.add_to_buffer(f"\nAvailable actions: {', '.join(location['available_actions'])}")
            
            return True
        except Exception as e:
            self.terminal_renderer.add_to_buffer(f"Error during navigation: {e}")
            return False

    def _cmd_scan_layer(self, args: List[str]) -> bool:
        """Scan the current layer for accessible locations."""
        if not self.world_manager:
            self.terminal_renderer.add_to_buffer("Error: World manager not available")
            return False
        
        try:
            layer_info = self.world_manager.get_current_layer_info()
            
            self.terminal_renderer.add_to_buffer(f"Scanning {layer_info['name']}...")
            self.terminal_renderer.add_to_buffer("=" * 40)
            
            locations = layer_info['accessible_locations']
            if not locations:
                self.terminal_renderer.add_to_buffer("No accessible locations found in current layer")
                return True
            
            for location in locations:
                status_icon = "🟢" if location['visited'] else "🔍"
                corruption_info = f"[{location['corruption_level']:.1%} corrupted]" if location['corruption_level'] > 0.1 else ""
                
                self.terminal_renderer.add_to_buffer(
                    f"{status_icon} {location['id']}: {location['name']} "
                    f"({location['discovery_progress']:.1%} discovered) {corruption_info}"
                )
                
                if location['entities_present']:
                    self.terminal_renderer.add_to_buffer(f"    🤖 Entities: {', '.join(location['entities_present'])}")
                
                if location['available_actions']:
                    self.terminal_renderer.add_to_buffer(f"    ⚡ Actions: {', '.join(location['available_actions'])}")
            
            return True
        except Exception as e:
            self.terminal_renderer.add_to_buffer(f"Error during layer scan: {e}")
            return False

    def _cmd_layer_transition(self, args: List[str]) -> bool:
        """Transition between network layers."""
        if not self.world_manager:
            self.terminal_renderer.add_to_buffer("Error: World manager not available")
            return False
        
        if not args:
            self.terminal_renderer.add_to_buffer("Usage: layer_transition <target_layer>")
            self.terminal_renderer.add_to_buffer("Available layers: surface, deep_web, dark_net, core")
            return False
        
        target_layer = args[0].lower()
        
        try:
            result = self.world_manager.attempt_layer_transition(target_layer)
            
            if not result['success']:
                self.terminal_renderer.add_to_buffer(f"Layer transition failed: {result['message']}")
                if result.get('requirements'):
                    self.terminal_renderer.add_to_buffer("Requirements not met:")
                    for req in result['requirements']:
                        self.terminal_renderer.add_to_buffer(f"  - {req}")
                return False
            
            new_layer = result['new_layer']
            self.terminal_renderer.add_to_buffer(f"=== Layer Transition Successful ===")
            self.terminal_renderer.add_to_buffer(f"Now entering: {new_layer['name']}")
            self.terminal_renderer.add_to_buffer(f"Security Level: {new_layer['security_level']}")
            self.terminal_renderer.add_to_buffer(f"Description: {new_layer['description']}")
            
            if new_layer['corruption_level'] > 0.5:
                self.terminal_renderer.add_to_buffer(f"⚠️  WARNING: High corruption detected ({new_layer['corruption_level']:.1%})")
            
            if result.get('warnings'):
                for warning in result['warnings']:
                    self.terminal_renderer.add_to_buffer(f"⚠️  {warning}")
            
            return True
        except Exception as e:
            self.terminal_renderer.add_to_buffer(f"Error during layer transition: {e}")
            return False

    def _cmd_world_status(self, args: List[str]) -> bool:
        """Display exploration progress and world state."""
        if not self.world_manager:
            self.terminal_renderer.add_to_buffer("Error: World manager not available")
            return False
        
        try:
            world_state = self.world_manager.get_world_state()
            progression = self.world_manager.get_layer_progression_summary()
            
            self.terminal_renderer.add_to_buffer("=== WORLD STATUS ===")
            self.terminal_renderer.add_to_buffer(f"Current Layer: {world_state['current_layer']['name']}")
            self.terminal_renderer.add_to_buffer(f"Current Location: {world_state['current_location']['name']}")
            self.terminal_renderer.add_to_buffer(f"Overall Progress: {world_state['overall_progress']:.1%}")
            
            self.terminal_renderer.add_to_buffer("\n=== LAYER PROGRESSION ===")
            for layer_name, layer_data in progression.items():
                status_icon = "🔓" if layer_data['unlocked'] else "🔒"
                progress = f"{layer_data['exploration_progress']:.1%}"
                locations_found = f"{layer_data['locations_discovered']}/{layer_data['total_locations']}"
                
                self.terminal_renderer.add_to_buffer(
                    f"{status_icon} {layer_name.upper()}: {progress} explored "
                    f"({locations_found} locations)"
                )
                
                if layer_data['major_discoveries']:
                    for discovery in layer_data['major_discoveries']:
                        self.terminal_renderer.add_to_buffer(f"    ✓ {discovery}")
            
            if world_state['active_objectives']:
                self.terminal_renderer.add_to_buffer("\n=== ACTIVE OBJECTIVES ===")
                for objective in world_state['active_objectives']:
                    self.terminal_renderer.add_to_buffer(f"• {objective}")
            
            return True
        except Exception as e:
            self.terminal_renderer.add_to_buffer(f"Error retrieving world status: {e}")
            return False

    def _cmd_location_actions(self, args: List[str]) -> bool:
        """Show available actions at the current location."""
        if not self.world_manager:
            self.terminal_renderer.add_to_buffer("Error: World manager not available")
            return False
        
        try:
            layer_info = self.world_manager.get_current_layer_info()
            current_location = None
            
            # Find current location
            for location in layer_info['accessible_locations']:
                if location.get('is_current', False):
                    current_location = location
                    break
            
            if not current_location:
                self.terminal_renderer.add_to_buffer("Current location information not available")
                return False
            
            self.terminal_renderer.add_to_buffer(f"=== {current_location['name']} - Available Actions ===")
            
            if not current_location['available_actions']:
                self.terminal_renderer.add_to_buffer("No special actions available at this location")
                return True
            
            for action in current_location['available_actions']:
                self.terminal_renderer.add_to_buffer(f"⚡ {action}")
                
                # Provide usage hints for common actions
                if action == "hack_system":
                    self.terminal_renderer.add_to_buffer("    Usage: hack <target_system>")
                elif action == "decrypt_file":
                    self.terminal_renderer.add_to_buffer("    Usage: decrypt <filename>")
                elif action == "access_terminal":
                    self.terminal_renderer.add_to_buffer("    Usage: access terminal")
                elif action == "scan_network":
                    self.terminal_renderer.add_to_buffer("    Usage: netscan")
                elif action == "interact_entity":
                    self.terminal_renderer.add_to_buffer("    Usage: talk <entity_name>")
            
            if current_location['entities_present']:
                self.terminal_renderer.add_to_buffer(f"\n🤖 Entities present: {', '.join(current_location['entities_present'])}")
            
            if current_location['corruption_level'] > 0.2:
                self.terminal_renderer.add_to_buffer(f"\n⚠️  Location corruption: {current_location['corruption_level']:.1%}")
            
            return True
        except Exception as e:
            self.terminal_renderer.add_to_buffer(f"Error retrieving location actions: {e}")
            return False

    def _cmd_traverse(self, args: List[str]) -> bool:
        """Navigate between connected locations."""
        if not self.world_manager:
            self.terminal_renderer.add_to_buffer("Error: World manager not available")
            return False
        
        if not args:
            # Show available connections from current location
            try:
                layer_info = self.world_manager.get_current_layer_info()
                current_location = None
                
                for location in layer_info['accessible_locations']:
                    if location.get('is_current', False):
                        current_location = location
                        break
                
                if not current_location:
                    self.terminal_renderer.add_to_buffer("Current location information not available")
                    return False
                
                self.terminal_renderer.add_to_buffer(f"=== Connections from {current_location['name']} ===")
                
                if current_location.get('connected_locations'):
                    for connection in current_location['connected_locations']:
                        status = "🟢 Available" if connection['accessible'] else "🔒 Locked"
                        self.terminal_renderer.add_to_buffer(f"{status} {connection['id']}: {connection['name']}")
                        
                        if not connection['accessible'] and connection.get('requirements'):
                            self.terminal_renderer.add_to_buffer(f"    Requirements: {', '.join(connection['requirements'])}")
                else:
                    self.terminal_renderer.add_to_buffer("No direct connections available")
                    self.terminal_renderer.add_to_buffer("Use 'navigate <location_id>' to move to any accessible location")
                
                return True
            except Exception as e:
                self.terminal_renderer.add_to_buffer(f"Error retrieving connections: {e}")
                return False
        
        # Navigate to specified connected location
        target_location = args[0]
        
        try:
            # Use the navigate command functionality for traversal
            return self._cmd_navigate([target_location])
        except Exception as e:
            self.terminal_renderer.add_to_buffer(f"Error during traversal: {e}")
            return False
