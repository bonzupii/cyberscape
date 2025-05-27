"""Tests for src/story/manager.py"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from dataclasses import asdict

from src.story.manager import Character, StoryManager
from src.core.state import GameStateManager
from src.core.effects import EffectManager
from src.core.llm import LLMHandler


class TestCharacter:
    """Test cases for Character class."""

    @pytest.fixture
    def sample_character(self):
        """Create a sample character for testing."""
        return Character(
            name="Dr. Sarah Chen",
            role="Security Analyst",
            personality={"cautious": 0.8, "analytical": 0.9, "trusting": 0.3},
            knowledge={"project_eternal": "classified research project", "scourge": "digital entity"},
            trust_level=0.5,
            corruption_level=0.1,
            last_interaction=datetime.now(),
            interaction_history=[("Hello", "Hello there.")]
        )

    def test_character_initialization(self, sample_character):
        """Test Character initialization."""
        assert sample_character.name == "Dr. Sarah Chen"
        assert sample_character.role == "Security Analyst"
        assert sample_character.personality["cautious"] == 0.8
        assert sample_character.trust_level == 0.5
        assert len(sample_character.interaction_history) == 1

    def test_character_generate_response_with_llm(self, sample_character):
        """Test character response generation with LLM."""
        with patch('src.story.manager.LLMHandler') as mock_llm_class:
            mock_llm = Mock()
            mock_llm.generate_response.return_value = "I understand your concern."
            mock_llm_class.return_value = mock_llm
            
            response = sample_character.generate_response("What do you know?", "Investigator")
            assert isinstance(response, str)
            assert len(response) > 0

    def test_character_generate_response_fallback(self, sample_character):
        """Test character response generation fallback."""
        with patch('src.story.manager.LLMHandler', side_effect=Exception("LLM Error")):
            response = sample_character.generate_response("Hello", "Player")
            assert response.startswith("I'm not sure how to respond")

    def test_character_update_trust_level(self, sample_character):
        """Test updating character trust level."""
        original_trust = sample_character.trust_level
        sample_character.trust_level = min(1.0, original_trust + 0.1)
        assert sample_character.trust_level == 0.6

    def test_character_add_interaction(self, sample_character):
        """Test adding interaction to history."""
        original_count = len(sample_character.interaction_history)
        sample_character.interaction_history.append(("New input", "New response"))
        assert len(sample_character.interaction_history) == original_count + 1


class TestStoryManager:
    """Test cases for StoryManager class."""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all dependencies for StoryManager."""
        mock_state = Mock(spec=GameStateManager)
        mock_state.get_state.return_value = {
            "story_flags": {},
            "character_states": {},
            "corruption_level": 0.1,
            "player_role": "Investigator"
        }
        
        mock_effects = Mock(spec=EffectManager)
        mock_llm = Mock(spec=LLMHandler)
        mock_llm.generate_response.return_value = "Generated story content"
        
        return mock_state, mock_effects, mock_llm

    @pytest.fixture
    def story_manager(self, mock_dependencies):
        """Create StoryManager instance for testing."""
        state_manager, effect_manager, llm_handler = mock_dependencies
        return StoryManager(state_manager, effect_manager, llm_handler)

    def test_story_manager_initialization(self, story_manager):
        """Test StoryManager initialization."""
        assert story_manager.state_manager is not None
        assert story_manager.effect_manager is not None
        assert story_manager.llm_handler is not None
        assert isinstance(story_manager.characters, dict)
        assert isinstance(story_manager.story_flags, dict)
        assert isinstance(story_manager.current_scene, str)

    def test_initialize_characters(self, story_manager):
        """Test character initialization."""
        story_manager.initialize_characters()
        assert len(story_manager.characters) > 0
        
        # Check if specific characters exist
        character_names = [char.name for char in story_manager.characters.values()]
        expected_characters = ["Dr. Sarah Chen", "Marcus Kane", "ARIA"]
        for expected in expected_characters:
            assert any(expected in name for name in character_names)

    def test_get_character_existing(self, story_manager):
        """Test getting existing character."""
        story_manager.initialize_characters()
        char_id = list(story_manager.characters.keys())[0]
        character = story_manager.get_character(char_id)
        assert character is not None
        assert isinstance(character, Character)

    def test_get_character_nonexistent(self, story_manager):
        """Test getting non-existent character."""
        character = story_manager.get_character("nonexistent")
        assert character is None

    def test_interact_with_character_success(self, story_manager):
        """Test successful character interaction."""
        story_manager.initialize_characters()
        char_id = list(story_manager.characters.keys())[0]
        
        with patch.object(story_manager.characters[char_id], 'generate_response', return_value="Test response"):
            response = story_manager.interact_with_character(char_id, "Hello")
            assert response == "Test response"

    def test_interact_with_character_not_found(self, story_manager):
        """Test interaction with non-existent character."""
        response = story_manager.interact_with_character("nonexistent", "Hello")
        assert "Character not found" in response

    def test_get_random_log_entry(self, story_manager):
        """Test getting random log entry."""
        log_entry = story_manager.get_random_log_entry()
        assert isinstance(log_entry, str)
        assert len(log_entry) > 0

    def test_get_random_log_entry_category(self, story_manager):
        """Test getting random log entry from specific category."""
        log_entry = story_manager.get_random_log_entry("voss")
        assert isinstance(log_entry, str)
        assert len(log_entry) > 0

    def test_get_corruption_event(self, story_manager):
        """Test getting corruption event."""
        event = story_manager.get_corruption_event(0.5)
        assert isinstance(event, str)
        assert len(event) > 0

    def test_get_scourge_manifestation(self, story_manager):
        """Test getting scourge manifestation."""
        manifestation = story_manager.get_scourge_manifestation(0.7)
        assert isinstance(manifestation, str)
        assert len(manifestation) > 0

    def test_advance_story_with_flag(self, story_manager):
        """Test advancing story and setting flag."""
        story_manager.advance_story("test_event")
        assert story_manager.story_flags.get("test_event") is True

    def test_check_story_flag_exists(self, story_manager):
        """Test checking existing story flag."""
        story_manager.story_flags["test_flag"] = True
        assert story_manager.check_story_flag("test_flag") is True

    def test_check_story_flag_not_exists(self, story_manager):
        """Test checking non-existent story flag."""
        assert story_manager.check_story_flag("nonexistent") is False

    def test_generate_dynamic_content_success(self, story_manager):
        """Test successful dynamic content generation."""
        with patch.object(story_manager.llm_handler, 'generate_response', return_value="Dynamic content"):
            content = story_manager.generate_dynamic_content("test_prompt", "narrative")
            assert content == "Dynamic content"

    def test_generate_dynamic_content_fallback(self, story_manager):
        """Test dynamic content generation with fallback."""
        with patch.object(story_manager.llm_handler, 'generate_response', side_effect=Exception("LLM Error")):
            content = story_manager.generate_dynamic_content("test_prompt", "narrative")
            assert "Unable to generate" in content

    def test_update_character_relationships(self, story_manager):
        """Test updating character relationships."""
        story_manager.initialize_characters()
        char_id = list(story_manager.characters.keys())[0]
        original_trust = story_manager.characters[char_id].trust_level
        
        story_manager.update_character_relationships(char_id, "positive")
        assert story_manager.characters[char_id].trust_level > original_trust

    def test_update_character_relationships_negative(self, story_manager):
        """Test negative character relationship update."""
        story_manager.initialize_characters()
        char_id = list(story_manager.characters.keys())[0]
        original_trust = story_manager.characters[char_id].trust_level
        
        story_manager.update_character_relationships(char_id, "negative")
        assert story_manager.characters[char_id].trust_level < original_trust

    def test_get_current_scene_description(self, story_manager):
        """Test getting current scene description."""
        description = story_manager.get_current_scene_description()
        assert isinstance(description, str)
        assert len(description) > 0

    def test_set_scene(self, story_manager):
        """Test setting current scene."""
        new_scene = "laboratory"
        story_manager.set_scene(new_scene)
        assert story_manager.current_scene == new_scene

    def test_get_available_interactions(self, story_manager):
        """Test getting available interactions."""
        story_manager.initialize_characters()
        interactions = story_manager.get_available_interactions()
        assert isinstance(interactions, list)
        assert len(interactions) > 0

    def test_save_story_state(self, story_manager):
        """Test saving story state."""
        story_manager.story_flags["test"] = True
        state = story_manager.save_story_state()
        assert isinstance(state, dict)
        assert "story_flags" in state
        assert "characters" in state
        assert state["story_flags"]["test"] is True

    def test_load_story_state(self, story_manager):
        """Test loading story state."""
        mock_state = {
            "story_flags": {"loaded_flag": True},
            "characters": {},
            "current_scene": "loaded_scene"
        }
        story_manager.load_story_state(mock_state)
        assert story_manager.story_flags["loaded_flag"] is True
        assert story_manager.current_scene == "loaded_scene"

    def test_load_story_state_invalid(self, story_manager):
        """Test loading invalid story state."""
        with patch('logging.Logger.warning') as mock_warning:
            story_manager.load_story_state({"invalid": "state"})
            mock_warning.assert_called()

    def test_get_character_corruption_levels(self, story_manager):
        """Test getting character corruption levels."""
        story_manager.initialize_characters()
        corruption_levels = story_manager.get_character_corruption_levels()
        assert isinstance(corruption_levels, dict)
        assert len(corruption_levels) > 0

    def test_trigger_story_event(self, story_manager):
        """Test triggering story event."""
        with patch.object(story_manager.effect_manager, 'apply_effect') as mock_effect:
            result = story_manager.trigger_story_event("test_event")
            assert isinstance(result, str)
            mock_effect.assert_called()

    def test_get_contextual_hint(self, story_manager):
        """Test getting contextual hint."""
        hint = story_manager.get_contextual_hint("player_location")
        assert isinstance(hint, str)
        assert len(hint) > 0

    def test_corruption_influence_on_story(self, story_manager):
        """Test corruption influence on story."""
        # Test with high corruption
        story_manager.state_manager.get_state.return_value = {
            "corruption_level": 0.8,
            "story_flags": {},
            "character_states": {},
            "player_role": "Investigator"
        }
        content = story_manager.generate_dynamic_content("test", "narrative")
        assert isinstance(content, str)

    def test_character_state_persistence(self, story_manager):
        """Test character state persistence across interactions."""
        story_manager.initialize_characters()
        char_id = list(story_manager.characters.keys())[0]
        
        # First interaction
        story_manager.interact_with_character(char_id, "Hello")
        interaction_count = len(story_manager.characters[char_id].interaction_history)
        
        # Second interaction
        story_manager.interact_with_character(char_id, "How are you?")
        assert len(story_manager.characters[char_id].interaction_history) == interaction_count + 1
