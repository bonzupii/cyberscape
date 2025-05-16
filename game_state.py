# --- Game States ---
# Using strings for now, can be an Enum or more complex objects later
STATE_DISCLAIMER = "DISCLAIMER"
STATE_MAIN_TERMINAL = "MAIN_TERMINAL"
STATE_MINIGAME = "MINIGAME"
STATE_NARRATIVE_SCREEN = "NARRATIVE_SCREEN"
STATE_SAVE_MENU = "SAVE_MENU"
STATE_LLM_OUTPUT = "LLM_OUTPUT"
STATE_MSFCONSOLE = "MSFCONSOLE" # New state for msfconsole
STATE_ROLE_SELECTION = "ROLE_SELECTION" # New state for choosing a role
STATE_PUZZLE_ACTIVE = "PUZZLE_ACTIVE" # New state for when a puzzle is active
# Add more states as needed

# --- Player Roles ---
ROLE_NONE = None # Default before selection
ROLE_WHITE_HAT = "WHITE_HAT"
ROLE_GREY_HAT = "GREY_HAT"
ROLE_BLACK_HAT = "BLACK_HAT"

class GameStateManager:
    def __init__(self, initial_state=STATE_DISCLAIMER):
        self.current_state = initial_state
        self.previous_state = None # Stores the last state before a change
        self.player_role = ROLE_NONE # Stores the chosen player role
        self.player_attributes = {} # Stores role-specific attributes like background, skills, etc.

    def change_state(self, new_state):
        """Changes the current game state."""
        if self.current_state != new_state:
            self.previous_state = self.current_state
            self.current_state = new_state
            # print(f"Game state changed from {self.previous_state} to {self.current_state}") # For debugging
        # else:
            # print(f"Attempted to change to the same state: {new_state}") # For debugging

    def get_state(self):
        """Returns the current game state."""
        return self.current_state

    def is_state(self, state_to_check):
        """Checks if the current state matches the given state."""
        return self.current_state == state_to_check

    def set_player_role(self, role):
        """Sets the player's chosen role and initializes their attributes."""
        # Basic validation, can be expanded later if needed
        if role in [ROLE_WHITE_HAT, ROLE_GREY_HAT, ROLE_BLACK_HAT]:
            self.player_role = role
            self.initialize_player_attributes() # Initialize attributes based on role
            # print(f"Player role set to: {self.player_role}") # For debugging
            # print(f"Player attributes: {self.player_attributes}") # For debugging
        # else:
            # print(f"Attempted to set invalid role: {role}") # For debugging

    def initialize_player_attributes(self):
        """Initializes player attributes based on the current role."""
        self.player_attributes = {} # Reset attributes
        if self.player_role == ROLE_WHITE_HAT:
            self.player_attributes['background'] = "Former Aether Corp Security Specialist"
            self.player_attributes['motivation'] = "Redemption and Protection"
            self.player_attributes['initial_skill_focus'] = "System Integrity"
        elif self.player_role == ROLE_GREY_HAT:
            self.player_attributes['background'] = "Investigative Journalist / Info Broker"
            self.player_attributes['motivation'] = "Truth and Balance"
            self.player_attributes['initial_skill_focus'] = "Information Gathering"
        elif self.player_role == ROLE_BLACK_HAT:
            self.player_attributes['background'] = "Terminally Ill Programmer seeking Digital Transcendence"
            self.player_attributes['motivation'] = "Power and Evolution"
            self.player_attributes['initial_skill_focus'] = "Exploitation"
        # Add more attributes as needed

    def get_player_role(self):
        """Returns the player's chosen role."""
        return self.player_role

    def get_player_attribute(self, attribute_name):
        """Returns a specific player attribute, or None if not found."""
        return self.player_attributes.get(attribute_name)

# Global instance.
# Consider dependency injection or passing it around as the project grows.
game_state_manager = GameStateManager()