import pytest
from commands_config import (
    ROLE_NONE,
    ROLE_WHITE_HAT,
    ROLE_GREY_HAT,
    ROLE_BLACK_HAT,
    COMMAND_ACCESS
)

def test_role_constants_defined():
    """Test that all role constants are defined and have correct values."""
    assert ROLE_NONE is None
    assert ROLE_WHITE_HAT == "WHITE_HAT"
    assert ROLE_GREY_HAT == "GREY_HAT"
    assert ROLE_BLACK_HAT == "BLACK_HAT"

def test_command_access_structure():
    """Test the basic structure of the COMMAND_ACCESS dictionary for each role."""
    roles = [ROLE_WHITE_HAT, ROLE_GREY_HAT, ROLE_BLACK_HAT]
    expected_keys = ["allowed_main", "allowed_msf", "help_text_main", "help_text_msf"]

    for role in roles:
        assert role in COMMAND_ACCESS, f"Role {role} not found in COMMAND_ACCESS"
        role_config = COMMAND_ACCESS[role]
        for key in expected_keys:
            assert key in role_config, f"Key '{key}' missing for role {role}"
        
        assert isinstance(role_config["allowed_main"], list), f"'allowed_main' should be a list for role {role}"
        assert isinstance(role_config["allowed_msf"], list), f"'allowed_msf' should be a list for role {role}"
        assert isinstance(role_config["help_text_main"], dict), f"'help_text_main' should be a dict for role {role}"
        assert isinstance(role_config["help_text_msf"], dict), f"'help_text_msf' should be a dict for role {role}"

def test_white_hat_specific_command_access():
    """Test specific command permissions for ROLE_WHITE_HAT."""
    config = COMMAND_ACCESS[ROLE_WHITE_HAT]
    
    # Allowed main commands
    assert "help" in config["allowed_main"]
    assert "ls" in config["allowed_main"]
    assert "msfconsole" in config["allowed_main"]
    
    # Disallowed main commands (for White Hat)
    assert "rm" not in config["allowed_main"]
    assert "mv" not in config["allowed_main"]
    
    # Allowed msf commands
    assert "help" in config["allowed_msf"]
    assert "search" in config["allowed_msf"]
    
    # Disallowed msf commands (for White Hat)
    assert "run" not in config["allowed_msf"]
    assert "exploit" not in config["allowed_msf"]

def test_grey_hat_specific_command_access():
    """Test specific command permissions for ROLE_GREY_HAT."""
    config = COMMAND_ACCESS[ROLE_GREY_HAT]
    
    # Allowed main commands (should include those White Hat has, plus more)
    assert "help" in config["allowed_main"]
    assert "ls" in config["allowed_main"]
    assert "rm" in config["allowed_main"] # Grey Hat can use rm
    assert "mv" in config["allowed_main"]  # Grey Hat can use mv
    assert "msfconsole" in config["allowed_main"]
    
    # Allowed msf commands (should include those White Hat has, plus more)
    assert "help" in config["allowed_msf"]
    assert "search" in config["allowed_msf"]
    assert "run" in config["allowed_msf"]    # Grey Hat can use run
    assert "exploit" in config["allowed_msf"] # Grey Hat can use exploit

def test_black_hat_specific_command_access():
    """Test specific command permissions for ROLE_BLACK_HAT.
    Currently same as Grey Hat, but test explicitly.
    """
    config = COMMAND_ACCESS[ROLE_BLACK_HAT]
    
    assert "rm" in config["allowed_main"]
    assert "mv" in config["allowed_main"]
    assert "run" in config["allowed_msf"]
    assert "exploit" in config["allowed_msf"]
    
    # Check a few common commands to ensure they are present
    assert "help" in config["allowed_main"]
    assert "ls" in config["allowed_main"]
    assert "help" in config["allowed_msf"]
    assert "search" in config["allowed_msf"]

def test_help_text_exists_for_allowed_commands():
    """Test that help text entries exist for all allowed commands for each role."""
    roles = [ROLE_WHITE_HAT, ROLE_GREY_HAT, ROLE_BLACK_HAT]

    for role in roles:
        role_config = COMMAND_ACCESS[role]
        
        # Check main commands help text
        for command in role_config["allowed_main"]:
            # Special case: 'exit' might be an alias and not have its own help entry if 'quit' covers it.
            # Or, if both are distinct, both should have help.
            # For this config, 'exit' is listed as an alias for 'quit' in help text.
            # The 'allowed_main' list contains both.
            # We expect help text for the primary command.
            if command == "exit" and "quit" in role_config["help_text_main"]:
                 # If 'quit' has help, 'exit' as an alias might not need its own separate entry
                 # if the help for 'quit' mentions 'exit'.
                 # However, the current structure has distinct help for 'exit' in White Hat.
                 # Let's assume for now each allowed command should have a help key.
                 pass # Allow specific handling if needed, for now, expect all.

            assert command in role_config["help_text_main"], \
                f"Help text missing for main command '{command}' in role {role}"
            assert isinstance(role_config["help_text_main"][command], str), \
                f"Help text for main command '{command}' in role {role} is not a string"

        # Check msf commands help text
        for command in role_config["allowed_msf"]:
            # Similar logic for aliases like 'exploit' for 'run'
            if command == "exploit" and "run" in role_config["help_text_msf"]:
                # If 'run' help covers 'exploit', this might be okay.
                # Current config has 'run / exploit' for both.
                pass

            assert command in role_config["help_text_msf"], \
                f"Help text missing for msf command '{command}' in role {role}"
            assert isinstance(role_config["help_text_msf"][command], str), \
                f"Help text for msf command '{command}' in role {role} is not a string"

def test_all_roles_present_in_command_access():
    """Ensure all defined roles (excluding ROLE_NONE) are keys in COMMAND_ACCESS."""
    defined_roles = {ROLE_WHITE_HAT, ROLE_GREY_HAT, ROLE_BLACK_HAT}
    configured_roles = set(COMMAND_ACCESS.keys())
    assert defined_roles == configured_roles, \
        f"Mismatch between defined roles and roles in COMMAND_ACCESS. Defined: {defined_roles}, Configured: {configured_roles}"

def test_msf_clear_command_universal_access():
    """Test that the 'clear' command is available in MSF console for all roles."""
    roles = [ROLE_WHITE_HAT, ROLE_GREY_HAT, ROLE_BLACK_HAT]
    clear_command = "clear"
    clear_help_text_expected_substring = "Clear the msfconsole screen"

    for role in roles:
        assert role in COMMAND_ACCESS, f"Role {role} not found in COMMAND_ACCESS for msf clear test"
        role_config = COMMAND_ACCESS[role]
        
        assert "allowed_msf" in role_config, f"'allowed_msf' key missing for role {role}"
        assert clear_command in role_config["allowed_msf"], \
            f"MSF command '{clear_command}' should be allowed for role {role}"
        
        assert "help_text_msf" in role_config, f"'help_text_msf' key missing for role {role}"
        assert clear_command in role_config["help_text_msf"], \
            f"Help text for MSF command '{clear_command}' missing for role {role}"
        assert clear_help_text_expected_substring in role_config["help_text_msf"][clear_command], \
            f"Help text for MSF '{clear_command}' for role {role} does not contain expected substring '{clear_help_text_expected_substring}'"