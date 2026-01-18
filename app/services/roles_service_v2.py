"""
Enhanced role detection service for WvW Analytics.

Uses spec-based hints combined with statistical analysis to accurately detect player roles.
Based on GW2 WvW meta (January 2025) and real log data analysis.
"""

from typing import Tuple, List, Optional
from app.db.models import PlayerStats


# WvW Meta Role Mappings (January 2025)
# Based on metabattle.com, snowcrows.com, and guildjen.com tier lists
# Updated: 2026-01-18

SPEC_ROLE_HINTS = {
    # === TIER S: META BUILDS (Used in ~100% of groups) ===
    
    # Primary Supports - Stability Specialists
    "Luminary": {"primary": "Stab Support", "secondary": ["Boon Support"], "weight": 0.95},
    "Firebrand": {"primary": "Stab Support", "secondary": ["Boon Support"], "weight": 0.9},
    "Troubadour": {"primary": "Stab Support", "secondary": ["Boon Support"], "weight": 0.9},
    
    # Secondary Supports - Healers
    "Druid": {"primary": "Healer", "secondary": ["Boon Support"], "weight": 0.95},
    "Tempest": {"primary": "Healer", "secondary": ["Boon Support"], "weight": 0.85},
    
    # Tertiary Supports - Quickness/Might Providers
    "Harbinger": {"primary": "Boon Support", "secondary": ["Quickness"], "weight": 0.9},
    
    # Top Tier DPS
    "Amalgam": {"primary": "Pure DPS", "secondary": [], "weight": 0.9},
    "Holosmith": {"primary": "Pure DPS", "secondary": [], "weight": 0.85},
    "Virtuoso": {"primary": "Strip DPS", "secondary": ["Pure DPS"], "weight": 0.85},
    
    # === TIER A: GREAT BUILDS (Widely used) ===
    
    # Support Variants
    "Chronomancer": {"primary": "Stab Support", "secondary": ["Boon Support"], "weight": 0.8},
    "Paragon": {"primary": "Boon Support", "secondary": ["Healer"], "weight": 0.75},
    "Scourge": {"primary": "Healer", "secondary": ["Barrier Support"], "weight": 0.8},
    "Specter": {"primary": "Healer", "secondary": ["Boon Support"], "weight": 0.75},
    "Catalyst": {"primary": "Boon Support", "secondary": ["Healer"], "weight": 0.7},
    
    # Boon Providers
    "Renegade": {"primary": "Boon Support", "secondary": ["Stability"], "weight": 0.8},
    "Conduit": {"primary": "Boon Support", "secondary": ["Stability", "Resistance"], "weight": 0.8},
    
    # DPS with Utility
    "Spellbreaker": {"primary": "Strip DPS", "secondary": ["Pure DPS"], "weight": 0.85},
    "Reaper": {"primary": "Strip DPS", "secondary": ["Pure DPS"], "weight": 0.8},
    "Berserker": {"primary": "Pure DPS", "secondary": [], "weight": 0.75},
    "Soulbeast": {"primary": "Pure DPS", "secondary": [], "weight": 0.75},
    "Untamed": {"primary": "Pure DPS", "secondary": [], "weight": 0.75},
    "Dragonhunter": {"primary": "Pure DPS", "secondary": [], "weight": 0.7},
    
    # === TIER B: GOOD BUILDS (Moderate usage) ===
    
    # Hybrid Supports
    "Scrapper": {"primary": "Hybrid", "secondary": ["Boon Support", "Healer"], "weight": 0.65},
    "Evoker": {"primary": "Hybrid", "secondary": ["Boon Support"], "weight": 0.65},
    "Herald": {"primary": "Hybrid", "secondary": ["Boon Support"], "weight": 0.6},
    
    # DPS Variants
    "Ritualist": {"primary": "Pure DPS", "secondary": ["Boon Support"], "weight": 0.7},
    "Bladesworn": {"primary": "Pure DPS", "secondary": [], "weight": 0.75},
    "Weaver": {"primary": "Pure DPS", "secondary": [], "weight": 0.7},
    "Willbender": {"primary": "Pure DPS", "secondary": [], "weight": 0.7},
    "Vindicator": {"primary": "Pure DPS", "secondary": [], "weight": 0.7},
    "Daredevil": {"primary": "Pure DPS", "secondary": [], "weight": 0.7},
    "Deadeye": {"primary": "Pure DPS", "secondary": [], "weight": 0.65},
    "Mechanist": {"primary": "Pure DPS", "secondary": [], "weight": 0.65},
    "Mirage": {"primary": "Pure DPS", "secondary": [], "weight": 0.65},
    
    # === CORE PROFESSIONS (Fallback when spec unknown) ===
    "Guardian": {"primary": "Hybrid", "secondary": ["Stab Support"], "weight": 0.5},
    "Ranger": {"primary": "Hybrid", "secondary": ["Pure DPS"], "weight": 0.5},
    "Elementalist": {"primary": "Hybrid", "secondary": ["Pure DPS"], "weight": 0.5},
    "Mesmer": {"primary": "Hybrid", "secondary": ["Boon Support"], "weight": 0.5},
    "Necromancer": {"primary": "Hybrid", "secondary": ["Pure DPS"], "weight": 0.5},
    "Revenant": {"primary": "Hybrid", "secondary": ["Boon Support"], "weight": 0.5},
    "Warrior": {"primary": "Hybrid", "secondary": ["Pure DPS"], "weight": 0.5},
    "Engineer": {"primary": "Hybrid", "secondary": ["Pure DPS"], "weight": 0.5},
    "Thief": {"primary": "Hybrid", "secondary": ["Pure DPS"], "weight": 0.5},
}


# Statistical thresholds based on real data analysis
# Updated from 10 logs analysis (will improve with more data)

class RoleThresholds:
    """Dynamic thresholds for role detection based on percentiles."""
    
    # DPS thresholds
    DPS_VERY_HIGH = 40000  # P90+ - Pure DPS
    DPS_HIGH = 20000       # P75+ - Strip DPS / Hybrid DPS
    DPS_MEDIUM = 10000     # P50+ - Support with some damage
    DPS_LOW = 5000         # P25+ - Pure support
    
    # Healing thresholds (per fight duration)
    HEAL_VERY_HIGH = 100000  # P90+ - Primary Healer
    HEAL_HIGH = 50000        # P75+ - Secondary Healer
    HEAL_MEDIUM = 20000      # P50+ - Hybrid with healing
    
    # Cleanse thresholds
    CLEANSE_VERY_HIGH = 150  # P90+ - Primary Healer
    CLEANSE_HIGH = 80        # P75+ - Support
    CLEANSE_MEDIUM = 30      # P50+ - Some support
    
    # Strip thresholds
    STRIP_VERY_HIGH = 80   # P90+ - Strip specialist
    STRIP_HIGH = 50        # P75+ - Strip DPS
    STRIP_MEDIUM = 20      # P50+ - Some strips
    
    # Boon generation thresholds (milliseconds)
    STAB_OUT_VERY_HIGH = 50000   # P90+ - Primary Stab Support
    STAB_OUT_HIGH = 20000        # P75+ - Secondary Stab
    STAB_OUT_MEDIUM = 5000       # P50+ - Some stab
    
    QUICK_OUT_VERY_HIGH = 80000  # P90+ - Quickness specialist
    QUICK_OUT_HIGH = 40000       # P75+ - Quickness provider
    QUICK_OUT_MEDIUM = 10000     # P50+ - Some quickness
    
    RESIST_OUT_VERY_HIGH = 60000  # P90+ - Resistance specialist
    RESIST_OUT_HIGH = 30000       # P75+ - Resistance provider
    RESIST_OUT_MEDIUM = 10000     # P50+ - Some resistance


def compute_role_scores(stats: PlayerStats) -> dict:
    """
    Compute normalized role scores from player statistics.
    
    Returns scores between 0-100 for each role category.
    """
    # Extract metrics
    dps = stats.dps or 0
    healing = stats.healing_out or 0
    barrier = stats.barrier_out or 0
    cleanses_other = stats.cleanses_other or 0
    cleanses_self = stats.cleanses_self or 0
    strips = stats.strips_out or 0
    
    # Boon generation (outgoing)
    stab_out = stats.stab_out_ms or 0
    quick_out = stats.quickness_out_ms or 0
    resist_out = stats.resistance_out_ms or 0
    alac_out = stats.alacrity_out_ms or 0
    prot_out = stats.protection_out_ms or 0
    aegis_out = stats.aegis_out_ms or 0
    might_out = stats.might_out_stacks or 0
    
    # Resurrects and stun breaks
    resurrects = stats.resurrects or 0
    stun_breaks = stats.stun_breaks or 0
    
    # Compute scores (0-100 scale)
    scores = {
        "dps_score": min(100, (dps / RoleThresholds.DPS_VERY_HIGH) * 100),
        "heal_score": min(100, ((healing + barrier) / RoleThresholds.HEAL_VERY_HIGH) * 100 + 
                         (cleanses_other / RoleThresholds.CLEANSE_VERY_HIGH) * 50 +
                         (resurrects * 5)),
        "stab_score": min(100, (stab_out / RoleThresholds.STAB_OUT_VERY_HIGH) * 100 +
                         (aegis_out / RoleThresholds.STAB_OUT_VERY_HIGH) * 50 +
                         (prot_out / RoleThresholds.STAB_OUT_VERY_HIGH) * 30),
        "boon_score": min(100, (quick_out / RoleThresholds.QUICK_OUT_VERY_HIGH) * 100 +
                         (resist_out / RoleThresholds.RESIST_OUT_VERY_HIGH) * 80 +
                         (alac_out / RoleThresholds.QUICK_OUT_VERY_HIGH) * 60 +
                         (might_out / 100000) * 40),
        "strip_score": min(100, (strips / RoleThresholds.STRIP_VERY_HIGH) * 100),
        "utility_score": min(100, (stun_breaks * 10) + (resurrects * 15) + (cleanses_self * 2))
    }
    
    return scores


def detect_player_role_v2(stats: PlayerStats) -> Tuple[str, List[str]]:
    """
    Enhanced role detection using spec hints + statistical analysis.
    
    Args:
        stats: PlayerStats instance with combat metrics
        
    Returns:
        Tuple of (primary_role, role_tags)
    """
    role_tags = []
    spec_name = stats.spec_name or stats.profession
    
    # Step 1: Check spec-based hint
    spec_hint = SPEC_ROLE_HINTS.get(spec_name)
    
    # Step 2: Compute statistical scores
    scores = compute_role_scores(stats)
    
    # Step 3: Determine role with weighted decision
    if spec_hint and spec_hint["weight"] >= 0.65:
        # Strong spec hint - use it as primary guidance
        primary_role = spec_hint["primary"]
        role_tags.extend(spec_hint["secondary"])
        
        # But verify with scores (override if stats strongly contradict)
        # This catches off-meta builds or players not playing their role
        if primary_role == "Healer":
            if scores["heal_score"] < 15 and scores["dps_score"] > 50:
                primary_role = "Pure DPS"
                role_tags = ["off_meta_build"]
            elif scores["heal_score"] < 15 and scores["boon_score"] > 40:
                primary_role = "Boon Support"
                role_tags = ["off_meta_build"]
        elif primary_role == "Stab Support":
            if scores["stab_score"] < 15 and scores["dps_score"] > 50:
                primary_role = "Pure DPS"
                role_tags = ["off_meta_build"]
            elif scores["stab_score"] < 15 and scores["heal_score"] > 50:
                primary_role = "Healer"
                role_tags = ["off_meta_build"]
        elif primary_role == "Boon Support":
            if scores["boon_score"] < 15 and scores["dps_score"] > 50:
                primary_role = "Pure DPS"
                role_tags = ["off_meta_build"]
            elif scores["boon_score"] < 15 and scores["heal_score"] > 50:
                primary_role = "Healer"
                role_tags = ["off_meta_build"]
        elif primary_role == "Pure DPS":
            if scores["dps_score"] < 20:
                # Low DPS - check if playing support instead
                if scores["heal_score"] > 40:
                    primary_role = "Healer"
                    role_tags = ["off_meta_build"]
                elif scores["stab_score"] > 40:
                    primary_role = "Stab Support"
                    role_tags = ["off_meta_build"]
                elif scores["boon_score"] > 40:
                    primary_role = "Boon Support"
                    role_tags = ["off_meta_build"]
                else:
                    primary_role = "Hybrid"
                    role_tags = ["low_performance"]
    else:
        # Weak or no spec hint - use pure statistical detection
        primary_role = _detect_role_from_scores(scores, stats)
        role_tags = _generate_role_tags(scores, stats)
    
    # Add performance tags
    if scores["dps_score"] >= 80:
        role_tags.append("high_dps")
    if scores["heal_score"] >= 80:
        role_tags.append("high_healing")
    if scores["stab_score"] >= 80:
        role_tags.append("high_stability")
    if scores["boon_score"] >= 80:
        role_tags.append("high_boons")
    if scores["strip_score"] >= 80:
        role_tags.append("high_strips")
    
    return primary_role, role_tags


def _detect_role_from_scores(scores: dict, stats: PlayerStats) -> str:
    """Detect role purely from statistical scores."""
    
    # Priority 1: Healer (high healing, low DPS)
    if scores["heal_score"] >= 60 and scores["dps_score"] < 40:
        return "Healer"
    
    # Priority 2: Stab Support (high stability, medium healing)
    if scores["stab_score"] >= 50 and scores["heal_score"] >= 20:
        return "Stab Support"
    
    # Priority 3: Boon Support (high boons, low-medium DPS)
    if scores["boon_score"] >= 50 and scores["dps_score"] < 60:
        return "Boon Support"
    
    # Priority 4: Strip DPS (high strips, high DPS)
    if scores["strip_score"] >= 40 and scores["dps_score"] >= 40:
        return "Strip DPS"
    
    # Priority 5: Pure DPS (very high DPS, low everything else)
    if scores["dps_score"] >= 60 and all(scores[k] < 30 for k in ["heal_score", "stab_score", "boon_score"]):
        return "Pure DPS"
    
    # Default: Hybrid
    return "Hybrid"


def _generate_role_tags(scores: dict, stats: PlayerStats) -> List[str]:
    """Generate descriptive tags based on scores."""
    tags = []
    
    if scores["dps_score"] >= 40:
        tags.append("dps")
    if scores["heal_score"] >= 30:
        tags.append("healing")
    if scores["stab_score"] >= 30:
        tags.append("stability")
    if scores["boon_score"] >= 30:
        tags.append("boons")
    if scores["strip_score"] >= 30:
        tags.append("strips")
    if scores["utility_score"] >= 40:
        tags.append("utility")
    
    return tags


# Backward compatibility wrapper
def detect_player_role(stats: PlayerStats) -> Tuple[str, List[str]]:
    """Wrapper for backward compatibility."""
    return detect_player_role_v2(stats)
