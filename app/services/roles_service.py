"""
Role detection service for WvW Analytics.

Assigns primary roles to players based on their combat statistics.
"""

from typing import Tuple, List
from app.db.models import PlayerStats


# Role detection thresholds (5-score system based on OUTGOING boons)
# Now based on what players GIVE to others, not what they receive
# Thresholds will need tuning after re-import with outgoing metrics
# Last updated: 2024-12-23

# Normalization constants (convert milliseconds to comparable scores)
STAB_MS_NORM = 1000.0  # Divide stab_out_ms by this
BOON_MS_NORM = 1000.0  # Divide boon_out_ms by this
HEAL_NORM = 100.0  # Divide healing_out by this

# Healer thresholds
HEALER_MIN_HEAL = 50.0  # High heal_score (healing + barrier + cleanses weighted, normalized)
HEALER_MAX_DPS = 800  # Low DPS to ensure pure support builds
HEALER_MIN_CLEANSES = 100  # High cleanses (P90-P95)

# Stab Support thresholds
STAB_MIN_STAB = 30.0  # High stab_score (outgoing Stability + Aegis, normalized)
STAB_MIN_HEAL = 10.0  # Medium heal_score
STAB_MAX_HEAL = 80.0  # Not too high (to distinguish from pure Healer)
STAB_MIN_BOON = 10.0  # Non-zero boon_score

# Boon Support thresholds
BOON_MIN_BOON = 40.0  # High boon_score (outgoing Quickness/Resistance/etc., normalized)
BOON_MIN_HEAL = 5.0  # Some healing (can be small or large)
BOON_MAX_DPS = 1200  # Medium or low DPS

# Strip DPS thresholds
STRIP_MIN_STRIP = 50.0  # High strip_score
STRIP_MIN_DPS = 800  # Medium or high DPS
STRIP_MAX_HEAL = 30.0  # Modest heal_score

# Pure DPS thresholds
DPS_MIN_DPS = 1500  # Very high DPS (P90+)
DPS_MAX_HEAL = 20.0  # Low heal_score
DPS_MAX_BOON = 20.0  # Low boon_score
DPS_MAX_STAB = 15.0  # Low stab_score
DPS_MAX_STRIP = 30.0  # Low strip_score


def compute_scores(stats: PlayerStats) -> dict:
    """
    Compute 5 role scores from player stats based on OUTGOING boons.
    
    Now uses what the player GIVES to others (outgoing boons), not what they receive.
    
    Args:
        stats: PlayerStats instance with combat metrics
        
    Returns:
        Dictionary with stab_score, heal_score, boon_score, strip_score, dps_score
    """
    # Extract OUTGOING boon stats (what player gives to others)
    stab_out_ms = stats.stab_out_ms or 0
    aegis_out_ms = stats.aegis_out_ms or 0
    protection_out_ms = stats.protection_out_ms or 0
    quickness_out_ms = stats.quickness_out_ms or 0
    alacrity_out_ms = stats.alacrity_out_ms or 0
    resistance_out_ms = stats.resistance_out_ms or 0
    might_out_stacks = stats.might_out_stacks or 0
    fury_out_ms = stats.fury_out_ms or 0
    
    # Extract healing/support stats
    healing_out = stats.healing_out or 0
    barrier_out = stats.barrier_out or 0
    cleanses = stats.cleanses or 0
    
    # Extract combat stats
    strips = stats.strips_out or 0
    dps = stats.dps or 0
    
    # Compute stab_score: OUTGOING Stability + Aegis (+ optional Protection)
    # Normalized to comparable scale
    stab_score = (stab_out_ms / STAB_MS_NORM) + (aegis_out_ms / STAB_MS_NORM) + (protection_out_ms / STAB_MS_NORM * 0.3)
    
    # Compute heal_score: healing + barrier + cleanses weighted, normalized
    heal_score = (healing_out / HEAL_NORM) + (barrier_out / HEAL_NORM) + (cleanses * 0.5)
    
    # Compute boon_score: OUTGOING Quickness, Resistance, Alacrity, Might, Fury
    # Normalized to comparable scale
    boon_score = (
        (quickness_out_ms / BOON_MS_NORM) * 1.5 +  # Quickness is very important
        (resistance_out_ms / BOON_MS_NORM) * 1.0 +  # Resistance is key in WvW
        (alacrity_out_ms / BOON_MS_NORM) * 1.0 +
        (might_out_stacks / (BOON_MS_NORM * 10)) * 0.5 +  # Might is stacks*duration
        (fury_out_ms / BOON_MS_NORM) * 0.3
    )
    
    # Compute strip_score: direct strips
    strip_score = strips
    
    # Compute dps_score: direct DPS
    dps_score = dps
    
    return {
        "stab_score": stab_score,
        "heal_score": heal_score,
        "boon_score": boon_score,
        "strip_score": strip_score,
        "dps_score": dps_score
    }


def detect_player_role(stats: PlayerStats) -> Tuple[str, List[str]]:
    """
    Detect player role based on 5-score system.
    
    Args:
        stats: PlayerStats instance with combat metrics
        
    Returns:
        Tuple of (primary_role, role_tags)
        - primary_role: One of "Healer", "Stab Support", "Boon Support", "Strip DPS", "Pure DPS", "Hybrid"
        - role_tags: List of role indicators for future extensibility
    """
    role_tags = []
    
    # Compute 5 scores
    scores = compute_scores(stats)
    stab_score = scores["stab_score"]
    heal_score = scores["heal_score"]
    boon_score = scores["boon_score"]
    strip_score = scores["strip_score"]
    dps_score = scores["dps_score"]
    
    # Extract cleanses for Healer check
    cleanses = stats.cleanses or 0
    
    # Priority 1: Healer
    # Very high heal_score, low DPS, high cleanses
    if (heal_score >= HEALER_MIN_HEAL and 
        dps_score <= HEALER_MAX_DPS and 
        cleanses >= HEALER_MIN_CLEANSES):
        role_tags.extend(["healer", "support", "cleanse"])
        return "Healer", role_tags
    
    # Priority 2: Stab Support
    # High stab_score, medium heal_score, non-zero boon_score
    if (stab_score >= STAB_MIN_STAB and 
        heal_score >= STAB_MIN_HEAL and 
        heal_score <= STAB_MAX_HEAL and 
        boon_score >= STAB_MIN_BOON):
        role_tags.extend(["stab", "support", "stability", "aegis"])
        return "Stab Support", role_tags
    
    # Priority 3: Boon Support
    # High boon_score, some healing (can be small or large), medium/low DPS
    if (boon_score >= BOON_MIN_BOON and 
        heal_score >= BOON_MIN_HEAL and 
        dps_score <= BOON_MAX_DPS):
        role_tags.extend(["boon", "support"])
        if stats.quickness_uptime and stats.quickness_uptime >= 40:
            role_tags.append("quickness")
        if stats.resistance_uptime and stats.resistance_uptime >= 40:
            role_tags.append("resistance")
        if stats.alacrity_uptime and stats.alacrity_uptime >= 40:
            role_tags.append("alacrity")
        return "Boon Support", role_tags
    
    # Priority 4: Strip DPS
    # High strip_score, medium/high DPS, modest heal_score
    if (strip_score >= STRIP_MIN_STRIP and 
        dps_score >= STRIP_MIN_DPS and 
        heal_score <= STRIP_MAX_HEAL):
        role_tags.extend(["strip", "dps", "boonstrip"])
        return "Strip DPS", role_tags
    
    # Priority 5: Pure DPS
    # Very high DPS, all other scores low
    if (dps_score >= DPS_MIN_DPS and 
        heal_score <= DPS_MAX_HEAL and 
        boon_score <= DPS_MAX_BOON and 
        stab_score <= DPS_MAX_STAB and 
        strip_score <= DPS_MAX_STRIP):
        role_tags.append("pure_dps")
        return "Pure DPS", role_tags
    
    # Default: Hybrid
    # Mixed builds, unclear roles, or doesn't fit any category
    role_tags.append("hybrid")
    
    # Add specific tags for hybrid classification
    if dps_score >= DPS_MIN_DPS * 0.7:
        role_tags.append("high_dps")
    if heal_score >= HEALER_MIN_HEAL * 0.5:
        role_tags.append("healing")
    if boon_score >= BOON_MIN_BOON * 0.5:
        role_tags.append("boons")
    if stab_score >= STAB_MIN_STAB * 0.5:
        role_tags.append("stability")
    if strip_score >= STRIP_MIN_STRIP * 0.5:
        role_tags.append("strips")
    
    return "Hybrid", role_tags
