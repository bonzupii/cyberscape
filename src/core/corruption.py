"""Comprehensive corruption system for Cyberscape: Digital Dread.

This module implements visual, audio, and narrative corruption effects
that respond to player actions and game state.
"""

import logging
import time
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CorruptionSource:
    """Represents a source of corruption in the system."""
    id: str
    rate: float
    description: str
    start_time: float = field(default_factory=time.time)
    zone_specific: bool = False
    target_zone: Optional[str] = None


class CorruptionSystem:
    """Comprehensive corruption system with visual, audio, and narrative effects."""
    
    def __init__(self, effect_manager=None, audio_manager=None):
        self.effect_manager = effect_manager
        self.audio_manager = audio_manager
        self.corruption_level = 0.0  # 0.0 to 1.0
        self.corruption_zones = {}  # Zone-specific corruption levels
        self.corruption_history = []  # Track corruption events
        self.corruption_sources: Set[CorruptionSource] = set()
        self.resistance_factors = {}  # Corruption resistance by role/item
        
        # Corruption thresholds for different effects
        self.thresholds = {
            'visual_glitch': 0.1,
            'audio_distortion': 0.2,
            'text_corruption': 0.3,
            'ui_breakdown': 0.5,
            'narrative_corruption': 0.6,
            'entity_awareness': 0.7,
            'fourth_wall_break': 0.8,
            'system_failure': 0.9
        }
        
        # Zone-specific corruption data
        self.zone_corruption_data = {
            'quarantine_zone': {
                'base_level': 0.3,
                'growth_rate': 0.05,
                'effects': ['glitch_text', 'scanlines', 'whispers']
            },
            'corporate_shell': {
                'base_level': 0.1,
                'growth_rate': 0.02,
                'effects': ['data_loss', 'security_alerts', 'system_logs']
            },
            'development_sphere': {
                'base_level': 0.4,
                'growth_rate': 0.08,
                'effects': ['code_corruption', 'debug_errors', 'phantom_voices']
            },
            'neural_network': {
                'base_level': 0.6,
                'growth_rate': 0.12,
                'effects': ['thought_intrusion', 'memory_loss', 'identity_crisis']
            },
            'the_core': {
                'base_level': 0.8,
                'growth_rate': 0.15,
                'effects': ['reality_breakdown', 'entity_manifestation', 'system_takeover']
            }
        }
        
        logger.info("Corruption system initialized")
    
    def update_corruption(self, delta_time: float, current_zone: str = None):
        """Update corruption levels based on time and environment."""
        # Base corruption growth
        base_growth = 0.001 * delta_time  # Very slow base growth
        
        # Zone-specific corruption
        if current_zone and current_zone in self.zone_corruption_data:
            zone_data = self.zone_corruption_data[current_zone]
            zone_growth = zone_data['growth_rate'] * delta_time
            self.corruption_level += zone_growth
            
            # Update zone-specific corruption
            if current_zone not in self.corruption_zones:
                self.corruption_zones[current_zone] = zone_data['base_level']
            else:
                self.corruption_zones[current_zone] += zone_growth
        
        # Apply corruption from active sources
        for source in self.corruption_sources:
            if source.zone_specific and source.target_zone:
                if source.target_zone not in self.corruption_zones:
                    self.corruption_zones[source.target_zone] = 0.0
                self.corruption_zones[source.target_zone] += source.rate * delta_time
            else:
                self.corruption_level += source.rate * delta_time
        
        # Apply resistance factors
        total_resistance = sum(self.resistance_factors.values())
        if total_resistance > 0:
            resistance_reduction = min(0.5, total_resistance * 0.1)
            self.corruption_level *= (1.0 - resistance_reduction)
        
        # Clamp corruption level
        self.corruption_level = max(0.0, min(1.0, self.corruption_level))
        
        # Trigger threshold effects
        self._check_corruption_thresholds()
    
    def _check_corruption_thresholds(self):
        """Check and trigger effects when corruption thresholds are crossed."""
        for effect_name, threshold in self.thresholds.items():
            if self.corruption_level >= threshold:
                self._trigger_corruption_effect(effect_name)
    
    def _trigger_corruption_effect(self, effect_name: str):
        """Trigger specific corruption effects."""
        if effect_name == 'visual_glitch':
            self._apply_visual_corruption()
        elif effect_name == 'audio_distortion':
            self._apply_audio_corruption()
        elif effect_name == 'text_corruption':
            self._apply_text_corruption()
        elif effect_name == 'ui_breakdown':
            self._apply_ui_corruption()
        elif effect_name == 'narrative_corruption':
            self._apply_narrative_corruption()
        elif effect_name == 'entity_awareness':
            self._apply_entity_awareness()
        elif effect_name == 'fourth_wall_break':
            self._apply_fourth_wall_break()
        elif effect_name == 'system_failure':
            self._apply_system_failure()
    
    def _apply_visual_corruption(self):
        """Apply visual corruption effects."""
        if self.effect_manager:
            # This would integrate with the effect manager
            logger.debug(f"Applying visual corruption at level {self.corruption_level}")
    
    def _apply_audio_corruption(self):
        """Apply audio corruption effects."""
        if self.audio_manager:
            # Distorted system sounds
            distortion_level = self.corruption_level * 0.7
            logger.debug(f"Applying audio corruption with distortion {distortion_level}")
    
    def _apply_text_corruption(self):
        """Apply text corruption effects."""
        if self.effect_manager:
            logger.debug(f"Applying text corruption at level {self.corruption_level}")
    
    def _apply_ui_corruption(self):
        """Apply UI breakdown effects."""
        if self.effect_manager:
            logger.debug(f"Applying UI corruption at level {self.corruption_level}")
    
    def _apply_narrative_corruption(self):
        """Apply narrative corruption effects."""
        logger.debug("Applying narrative corruption")
    
    def _apply_entity_awareness(self):
        """Apply entity awareness effects."""
        logger.debug("Entities becoming aware of player presence")
    
    def _apply_fourth_wall_break(self):
        """Apply fourth wall breaking effects."""
        logger.debug("Fourth wall breaking initiated")
    
    def _apply_system_failure(self):
        """Apply critical system failure effects."""
        logger.debug("Critical system failure effects triggered")
    
    def add_corruption_source(self, source_id: str, rate: float, description: str = "", 
                            zone_specific: bool = False, target_zone: str = None):
        """Add a source of ongoing corruption."""
        source = CorruptionSource(
            id=source_id,
            rate=rate,
            description=description,
            zone_specific=zone_specific,
            target_zone=target_zone
        )
        self.corruption_sources.add(source)
        logger.info(f"Added corruption source: {source_id} (rate: {rate})")
    
    def remove_corruption_source(self, source_id: str):
        """Remove a corruption source."""
        self.corruption_sources = {s for s in self.corruption_sources if s.id != source_id}
        logger.info(f"Removed corruption source: {source_id}")
    
    def add_resistance_factor(self, factor_id: str, resistance: float):
        """Add a corruption resistance factor."""
        self.resistance_factors[factor_id] = resistance
        logger.info(f"Added corruption resistance: {factor_id} ({resistance})")
    
    def get_corruption_status(self) -> dict:
        """Get detailed corruption status."""
        active_effects = []
        for effect_name, threshold in self.thresholds.items():
            if self.corruption_level >= threshold:
                active_effects.append(effect_name)
        
        return {
            'global_level': self.corruption_level,
            'zone_levels': self.corruption_zones.copy(),
            'active_effects': active_effects,
            'sources': len(self.corruption_sources),
            'resistance': sum(self.resistance_factors.values()),
            'next_threshold': self._get_next_threshold()
        }
    
    def _get_next_threshold(self) -> Optional[Tuple[str, float]]:
        """Get the next corruption threshold."""
        for effect_name, threshold in sorted(self.thresholds.items(), key=lambda x: x[1]):
            if self.corruption_level < threshold:
                return (effect_name, threshold)
        return None
    
    def purify_corruption(self, amount: float, zone: str = None):
        """Reduce corruption levels (Purifier ability)."""
        if zone and zone in self.corruption_zones:
            self.corruption_zones[zone] = max(0.0, self.corruption_zones[zone] - amount)
        else:
            self.corruption_level = max(0.0, self.corruption_level - amount)
        
        logger.info(f"Purified corruption: {amount} (zone: {zone or 'global'})")
    
    def corrupt_intentionally(self, amount: float, zone: str = None):
        """Intentionally increase corruption (Ascendant ability)."""
        if zone and zone in self.zone_corruption_data:
            if zone not in self.corruption_zones:
                self.corruption_zones[zone] = self.zone_corruption_data[zone]['base_level']
            self.corruption_zones[zone] = min(1.0, self.corruption_zones[zone] + amount)
        else:
            self.corruption_level = min(1.0, self.corruption_level + amount)
        
        logger.info(f"Increased corruption: {amount} (zone: {zone or 'global'})")
