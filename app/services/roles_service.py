"""
Role detection service for WvW Analytics.

Assigns primary roles to players based on their combat statistics.
"""

from typing import Tuple, List
from app.db.models import PlayerStats


# Role detection thresholds (tuneable constants)
# These values can be adjusted based on real-world data analysis

# Healer/Support thresholds
HEALER_MIN_CLEANSES = 200
HEALER_MAX_DPS = 800

# Boon Support thresholds
BOON_MIN_UPTIME = 40  # % for quickness or alacrity
BOON_MAX_DPS = 1500

# Stripper thresholds
STRIPPER_MIN_STRIPS = 100
STRIPPER_MAX_CLEANSES = 100
STRIPPER_STRIP_TO_CLEANSE_RATIO = 2.0

# DPS thresholds
DPS_MIN_DPS = 1500
DPS_MAX_CLEANSES = 100
DPS_MAX_STRIPS = 50
DPS_MAX_BOON_UPTIME = 30  # % for quickness and alacrity


def detect_player_role(stats: PlayerStats) -> Tuple[str, List[str]]:
    """
    Detect player role based on combat statistics.
    
    Args:
        stats: PlayerStats instance with combat metrics
        
    Returns:
        Tuple of (primary_role, role_tags)
        - primary_role: One of "DPS", "Boon Support", "Healer/Support", "Stripper", "Hybrid"
        - role_tags: List of role indicators for future extensibility
    """
    role_tags = []
    
    # Extract relevant stats
    dps = stats.dps or 0
    cleanses = stats.cleanses or 0
    strips = stats.strips_out or 0
    quickness = stats.quickness_uptime or 0
    alacrity = stats.alacrity_uptime or 0
    resistance = stats.resistance_uptime or 0
    
    # Check for Healer/Support role
    # High cleanses, low damage - focused on keeping group alive
    if cleanses >= HEALER_MIN_CLEANSES and dps < HEALER_MAX_DPS:
        role_tags.extend(["healer", "support", "cleanse"])
        return "Healer/Support", role_tags
    
    # Check for Boon Support role
    # High boon uptime, moderate/low damage - typical FB/chrono/scrapper builds
    # In WvW: Quickness, Alacrity (rare), or Resistance are key support boons
    if (quickness >= BOON_MIN_UPTIME or alacrity >= BOON_MIN_UPTIME or resistance >= BOON_MIN_UPTIME) and dps < BOON_MAX_DPS:
        role_tags.extend(["boon", "support"])
        if quickness >= BOON_MIN_UPTIME:
            role_tags.append("quickness")
        if alacrity >= BOON_MIN_UPTIME:
            role_tags.append("alacrity")
        if resistance >= BOON_MIN_UPTIME:
            role_tags.append("resistance")
        return "Boon Support", role_tags
    
    # Check for Stripper role
    # High strips, relatively lower cleanses - typical Spellbreaker, Scourge, some Scrapper
    if strips >= STRIPPER_MIN_STRIPS and (strips > STRIPPER_STRIP_TO_CLEANSE_RATIO * cleanses or cleanses < STRIPPER_MAX_CLEANSES):
        role_tags.extend(["stripper", "boonstrip"])
        return "Stripper", role_tags
    
    # Check for DPS role
    # High damage, low support activity - pure damage dealers
    # Note: We don't check boon uptimes here since players receive boons, not give them
    if (dps >= DPS_MIN_DPS and 
        cleanses < DPS_MAX_CLEANSES and 
        strips < DPS_MAX_STRIPS):
        role_tags.append("dps")
        return "DPS", role_tags
    
    # Default to Hybrid for mixed/unclear builds
    # Could be boon DPS, off-support, weird builds, etc.
    role_tags.append("hybrid")
    
    # Add specific tags for hybrid classification
    if dps >= DPS_MIN_DPS:
        role_tags.append("high_dps")
    if cleanses >= HEALER_MIN_CLEANSES // 2:
        role_tags.append("cleanses")
    if strips >= STRIPPER_MIN_STRIPS // 2:
        role_tags.append("strips")
    if quickness >= BOON_MIN_UPTIME // 2 or alacrity >= BOON_MIN_UPTIME // 2 or resistance >= BOON_MIN_UPTIME // 2:
        role_tags.append("boons")
    
    return "Hybrid", role_tags
