"""
Role detection service for WvW Analytics.

Assigns primary roles to players based on their combat statistics.
"""

from typing import Tuple, List
from app.db.models import PlayerStats


# Role detection thresholds (5-score system)
# Based on percentile analysis of 1603 WvW logs (111k+ player records)
# Last updated: 2024-12-22

# Healer thresholds
HEALER_MIN_HEAL = 5000.0  # High heal_score (healing + barrier + cleanses weighted)
HEALER_MAX_DPS = 800  # Low DPS to ensure pure support builds
HEALER_MIN_CLEANSES = 100  # High cleanses (P90-P95)

# Stab Support thresholds
STAB_MIN_STAB = 40.0  # High stab_score (Stability + Aegis weighted)
STAB_MIN_HEAL = 1000.0  # Medium heal_score
STAB_MAX_HEAL = 8000.0  # Not too high (to distinguish from pure Healer)
STAB_MIN_BOON = 20.0  # Non-zero boon_score

# Boon Support thresholds
BOON_MIN_BOON = 50.0  # High boon_score (Quickness/Resistance/etc.)
BOON_MIN_HEAL = 500.0  # Some healing (can be small or large, e.g. Paragon)
BOON_MAX_DPS = 1200  # Medium or low DPS

# Strip DPS thresholds
STRIP_MIN_STRIP = 50.0  # High strip_score
STRIP_MIN_DPS = 800  # Medium or high DPS
STRIP_MAX_HEAL = 3000.0  # Modest heal_score

# Pure DPS thresholds
DPS_MIN_DPS = 1500  # Very high DPS (P90+)
DPS_MAX_HEAL = 2000.0  # Low heal_score
DPS_MAX_BOON = 30.0  # Low boon_score
DPS_MAX_STAB = 20.0  # Low stab_score
DPS_MAX_STRIP = 30.0  # Low strip_score


def compute_scores(stats: PlayerStats) -> dict:
    """
    Compute 5 role scores from player stats.
    
    Args:
        stats: PlayerStats instance with combat metrics
        
    Returns:
        Dictionary with stab_score, heal_score, boon_score, strip_score, dps_score
    """
    # Extract raw stats
    stability = stats.stability_uptime or 0
    aegis = stats.aegis_uptime or 0
    protection = stats.protection_uptime or 0
    healing_out = stats.healing_out or 0
    barrier_out = stats.barrier_out or 0
    cleanses = stats.cleanses or 0
    quickness = stats.quickness_uptime or 0
    alacrity = stats.alacrity_uptime or 0
    resistance = stats.resistance_uptime or 0
    might = stats.might_uptime or 0
    fury = stats.fury_uptime or 0
    strips = stats.strips_out or 0
    dps = stats.dps or 0
    
    # Compute stab_score: Stability + Aegis (+ optional Protection)
    stab_score = stability + aegis + (protection * 0.3)
    
    # Compute heal_score: healing + barrier + cleanses weighted
    heal_score = healing_out + barrier_out + (cleanses * 30)
    
    # Compute boon_score: Quickness, Resistance, Alacrity, Might, Fury
    boon_score = quickness + resistance + alacrity + (might * 0.5) + (fury * 0.3)
    
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
