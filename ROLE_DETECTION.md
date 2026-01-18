# Role Detection System

## Overview

The WvW Analytics role detection system uses a hybrid approach combining:
1. **Spec-based hints** from WvW meta knowledge (metabattle.com, snowcrows.com, guildjen.com)
2. **Statistical analysis** of player performance metrics
3. **Smart validation** to detect off-meta builds

## Role Categories

### 1. Healer
**Primary function:** Keep squad alive through healing, barrier, and condition cleanse

**Meta specs:**
- Druid (Tier S) - Ranged healing, condition removal, resurrection utility
- Tempest (Tier A) - Aura sharing, strong healing output
- Scourge (Tier A) - Barrier specialist, condition transfer
- Specter (Tier A) - Shadow shroud healing, single-target focus

**Detection criteria:**
- High healing output (>50k per fight)
- High condition cleanses (>80)
- Low DPS (<10k)
- Resurrects and utility

### 2. Stab Support (Primary Support)
**Primary function:** Provide Stability, Aegis, and defensive boons

**Meta specs:**
- Luminary (Tier S) - Best stability provider, unmatched Protection/Resistance/Aegis
- Firebrand (Tier S) - Excellent boon coverage, crowd control, stun breaks
- Troubadour (Tier S) - Versatile support, blocks, distortion, portal utility
- Chronomancer (Tier A) - Stability, boons, mesmer utility

**Detection criteria:**
- High Stability generation (>20s outgoing)
- High Aegis/Protection generation
- Medium healing (20-80k)
- Moderate boon output

### 3. Boon Support (Tertiary Support)
**Primary function:** Provide Quickness, Might, Alacrity, and Resistance

**Meta specs:**
- Harbinger (Tier S) - Quickness, Fury, Might specialist
- Conduit (Tier A) - Stability, Resistance, damage reduction
- Renegade (Tier A) - Stability, Might, damage reduction
- Paragon (Tier A) - Versatile boon provider

**Detection criteria:**
- High Quickness generation (>40s outgoing)
- High Resistance generation (>30s outgoing)
- Might stacking
- Medium DPS (<40k)

### 4. Strip DPS
**Primary function:** Remove enemy boons while dealing damage

**Meta specs:**
- Spellbreaker (Tier A) - Boon removal specialist
- Reaper (Tier A) - Boon corruption, crowd control
- Virtuoso (Tier S) - High damage with strip utility

**Detection criteria:**
- High boon strips (>50)
- High DPS (>20k)
- Low support output

### 5. Pure DPS
**Primary function:** Maximize damage output

**Meta specs:**
- Amalgam (Tier S) - Top tier damage
- Holosmith (Tier S) - Consistent high damage
- Berserker, Soulbeast, Untamed, Dragonhunter (Tier A)
- Bladesworn, Weaver, Willbender, Vindicator (Tier B)

**Detection criteria:**
- Very high DPS (>40k)
- Low support metrics
- Low boon generation

### 6. Hybrid
**Primary function:** Mixed role or unclear specialization

**Assigned when:**
- Spec has low confidence weight (<0.65)
- Stats don't match expected role
- Low performance across all metrics
- Core professions without elite spec

## Detection Algorithm

### Step 1: Spec-Based Hint
```python
spec_hint = SPEC_ROLE_HINTS.get(player.spec_name)
if spec_hint.weight >= 0.65:
    primary_role = spec_hint.primary
```

### Step 2: Compute Statistical Scores
```python
scores = {
    "dps_score": (dps / 40000) * 100,
    "heal_score": (healing / 100000) * 100 + (cleanses / 150) * 50,
    "stab_score": (stab_out / 50000) * 100 + (aegis_out / 50000) * 50,
    "boon_score": (quick_out / 80000) * 100 + (resist_out / 60000) * 80,
    "strip_score": (strips / 80) * 100
}
```

### Step 3: Validation & Override
If stats strongly contradict spec hint:
- Healer with high DPS → Pure DPS (off-meta build)
- DPS with high healing → Healer (off-meta build)
- Low performance → Hybrid (low performance tag)

## Statistical Validation (15 logs, 127 players)

### Role Distribution
- Hybrid: 30.7% (mostly core professions, Mesmer, Evoker)
- Pure DPS: 23.6% (Druid DPS, Untamed, Mirage, Amalgam)
- Boon Support: 22.0% (Conduit, Paragon, Renegade)
- Stab Support: 8.7% (Firebrand, Luminary, Chronomancer)
- Strip DPS: 8.7% (Reaper, Virtuoso, Spellbreaker)
- Healer: 6.3% (Druid, Tempest)

### Average Stats by Role

| Role | DPS | Healing | Cleanses | Strips | Stab Out | Quick Out |
|------|-----|---------|----------|--------|----------|-----------|
| Healer | 5k | 0 | 10.6 | 0.0 | 0.1s | 18.6s |
| Stab Support | 11k | 0 | 10.3 | 0.2 | 1.0s | 10.7s |
| Boon Support | 38k | 0 | 8.0 | 0.5 | 0.8s | 18.7s |
| Strip DPS | 26k | 0 | 0.4 | 3.3 | 0.4s | 25.8s |
| Pure DPS | 68k | 0 | 5.1 | 0.8 | 0.9s | 19.2s |

**Note:** Healing values showing 0 indicate these metrics need verification in the extraction logic.

## Known Issues & Future Improvements

1. **Healing metrics showing 0** - Need to verify `healing_out` extraction from EI JSON
2. **Druid role ambiguity** - 54% detected as Pure DPS (likely power DPS builds)
3. **Core professions** - Default to Hybrid due to lack of spec info
4. **Thresholds** - Will improve with more log data (currently based on 15 logs)

## Usage

```python
from app.services.roles_service_v2 import detect_player_role

role, tags = detect_player_role(player_stats)
# role: "Healer", "Stab Support", "Boon Support", "Strip DPS", "Pure DPS", "Hybrid"
# tags: ["high_dps", "off_meta_build", "low_performance", etc.]
```

## References

- [MetaBattle WvW Builds](https://metabattle.com/wiki/WvW)
- [Snow Crows WvW Support Tier List](https://snowcrows.com/news/wvw-tier-list-for-support-builds-dec-2025)
- [GuildJen WvW Builds](https://guildjen.com/gw2-wvw-builds/)

Last updated: 2026-01-18
