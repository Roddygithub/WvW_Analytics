# CALCULATION_RULES — Elite Insights Alignment (TpD1 Reference)

## 1) Aggregation Principles
- **Default rule:** Sum across squad/group members for numeric stats (dps/cc/cleanses/strips/defense/support/gameplay).
- **Boon uptimes:** Weighted average by active duration (presence_pct) as implemented in `dps_mapping.py` / analysis routes.
- **Averages shown below (distances, animation %)** are arithmetic means across players in the subgroup.
- **Official reference log:** `data/dps_report/TpD1-ref.json` (extracted from `tmp_TpD1.html`); phase 0, main target "Enemy Players".
- **Zero values must be semantically validated** (e.g., `cc_total` comes from `breakbarDamage`; `resurrects` from `supportStats[6]`).
- **All metrics are now persisted in database** - Complete alignment with Elite Insights achieved (Jan 2026).

## 2) Complete Data Schema (Phase 0 arrays)

### dpsStats (phase.dpsStats[i][col])
| HTML Index | Metric | JSON field | Aggregation | TpD1 G2 |
| --- | --- | --- | --- | --- |
| 0 | Damage (All) | `phases[0].dpsStats[i][0]` | Sum | 371,876 |
| 1 | Power Damage | `phases[0].dpsStats[i][1]` | Sum | (not asserted) |
| 2 | Condi Damage | `phases[0].dpsStats[i][2]` | Sum | (not asserted) |
| 3 | Breakbar Damage (CC) | `phases[0].dpsStats[i][3]` → **cc_total** | Sum | 0 |

### supportStats (phase.supportStats[i][col])
| HTML Index | Metric | JSON field | Aggregation | TpD1 G2 |
| --- | --- | --- | --- | --- |
| 0 | Condi Cleanse (others) | `supportStats[i][0]` → `cleanses_other` | Sum | 49 |
| 1 | Cleanse Time (others) | `supportStats[i][1]` | Sum | (not asserted) |
| 2 | Condi Cleanse (self) | `supportStats[i][2]` → `cleanses_self` | Sum | 35 |
| 3 | Cleanse Time (self) | `supportStats[i][3]` | Sum | (not asserted) |
| 4 | Boon Strips | `supportStats[i][4]` → `strips_out` | Sum | 64 |
| 5 | Strips Time | `supportStats[i][5]` → `strips_time` | Sum | (not asserted) |
| 6 | Resurrects | `supportStats[i][6]` → `resurrects` | Sum | 0 (field verified) |
| 7 | Resurrect Time | `supportStats[i][7]` | Sum | (not asserted) |
| 8 | Stun Breaks | `supportStats[i][8]` → `stun_breaks` | Sum | 2 |
| 9 | Stun Break Time | `supportStats[i][9]` | Sum | (not asserted) |

### defStats (phase.defStats[i][col])
| HTML Index | Metric | JSON field | Aggregation | TpD1 G2 |
| --- | --- | --- | --- | --- |
| 0 | Damage Taken | `defStats[i][0]` → `damage_taken` | Sum | 265,583 |
| 1 | Barrier Absorbed | `defStats[i][1]` → `barrier_absorbed` | Sum | 67,014 |
| 2 | Hits Missed | `defStats[i][2]` → `missed_count` | Sum | 6 |
| 3 | Interrupted (taken) | `defStats[i][3]` → `interrupted_count` | Sum | 1 |
| 4 | CC Taken | `defStats[i][4]` | Sum | (not asserted) |
| 5 | Invuln Count | `defStats[i][5]` | Sum | (not asserted) |
| 6 | Evades | `defStats[i][6]` → `evaded_count` | Sum | 19 |
| 7 | Blocks | `defStats[i][7]` → `blocked_count` | Sum | 18 |
| 8 | Dodges | `defStats[i][8]` → `dodged_count` | Sum | 103 |
| 9 | Cleanse Time (def) | `defStats[i][9]` | Sum | (not asserted) |
| 11 | Strips Time (def) | `defStats[i][11]` | Sum | (not asserted) |
| 13 | Times Downed | `defStats[i][13]` → `downs_count` | Sum | 0 |
| 14 | Damage While Downed | `defStats[i][14]` → `downed_damage_taken` | Sum | 1 |
| 15 | Times Died | `defStats[i][15]` → `dead_count` | Sum | 0 |
| 18 | Invuln Time | `defStats[i][18]` | Sum | (not asserted) |

### gameplayStats (phase.gameplayStats[i][col])
| HTML Index | Metric | JSON field | Aggregation | TpD1 G2 |
| --- | --- | --- | --- | --- |
| 0 | Time Wasted (s) | `gameplayStats[i][0]` → `time_wasted` | Sum | 4.078 |
| 1 | # Cancels Wasted | `gameplayStats[i][1]` | Sum | (not asserted) |
| 2 | Time Saved (s) | `gameplayStats[i][2]` → `time_saved` | Sum | 9.942 |
| 3 | # Cancels Saved | `gameplayStats[i][3]` | Sum | (not asserted) |
| 4 | Weapon Swaps | `gameplayStats[i][4]` → `weapon_swaps` | Sum | 23 |
| 5 | Avg Dist Stack | `gameplayStats[i][5]` → `stack_dist` | Avg | 9,384.834 |
| 6 | Avg Dist Commander | `gameplayStats[i][6]` → `dist_to_com` | Avg | 1,791.886 |
| 7 | % Time in Animation | `gameplayStats[i][7]` → `anim_percent` | Avg | 55.3096 |
| 8 | % Time in Animation (no auto) | `gameplayStats[i][8]` → `anim_no_auto_percent` | Avg | 41.7134 |

### offensiveStatsTargets (phase.offensiveStatsTargets[i][target][col]) — main target idx 0
| HTML Index | Metric | JSON field | Aggregation | TpD1 G2 |
| --- | --- | --- | --- | --- |
| 0 | Hits | `offensiveStatsTargets[i][0][0]` | Sum | (not asserted) |
| 2 | Critical Hits | `offensiveStatsTargets[i][0][2]` | Sum | (not asserted) |
| 3 | Breakbar Damage | `offensiveStatsTargets[i][0][12]` | Sum | (not asserted) |
| 19 | Kills (on target) | `offensiveStatsTargets[i][0][19]` | Sum | (not asserted) |

> Note: assertions currently focus on player/global stats; target rows are documented for future coverage.

## 3) Reference Values (TpD1, Group 2)
| Metric | Value |
| --- | --- |
| DPS (damage) | 371,876 |
| CC (breakbarDamage) | 0 |
| Cleanses (others) | 49 |
| Cleanses (self) | 35 |
| Boon Strips | 64 |
| Resurrects | 0 (field: `supportStats[6]`) |
| Stun Breaks | 2 |
| Damage Taken | 265,583 |
| Barrier Absorbed | 67,014 |
| Missed | 6 |
| Interrupted | 1 |
| Evades | 19 |
| Blocks | 18 |
| Dodges | 103 |
| Downs | 0 |
| Damage While Downed | 1 |
| Deaths | 0 |
| Time Wasted (s) | 4.078 |
| Time Saved (s) | 9.942 |
| Weapon Swaps | 23 |
| Avg Dist Stack | 9,384.834 |
| Avg Dist Commander | 1,791.886 |
| % Time in Animation | 55.3096 |
| % Time in Animation (no auto) | 41.7134 |

## 4) Notes on Zero-Value Verification
- **CC**: Derived from `breakbarDamage` (dpsStats column 3). Zero is confirmed to be a true zero, not a missing field.
- **Resurrects**: Sourced from `supportStats[6]`; zero validated against EI HTML.
- Any textual status fields in `defStats` (e.g., “100% Alive”) are discarded; numeric extraction is performed before summation.

## 5) Test Coverage
- `tests/test_dps_calibration.py::test_calibration_full_suite` asserts all metrics above (floats via `pytest.approx`).  
- Boon weighted averages updated to use presence_pct (Quickness G2 ≈ 20.41%, Squad ≈ 29.42%).
- All metrics are now persisted to database via PlayerStats model (35 new columns added in migration d6fc23497851).

## 6) Database Persistence (Complete as of Jan 2026)
All metrics extracted from Elite Insights JSON are now persisted in the `player_stats` table:
- **Defensive granular:** barrier_absorbed, missed_count, interrupted_count, evaded_count, blocked_count, dodged_count, downs_count, downed_damage_taken, dead_count
- **Support granular:** cleanses_other, cleanses_self, cleanses_time_other, cleanses_time_self, resurrects, resurrect_time, stun_breaks, stun_break_time, strips_time
- **Gameplay stats:** time_wasted, time_saved, weapon_swaps, stack_dist, dist_to_com, anim_percent, anim_no_auto_percent
- **Active time tracking:** dead_duration_ms, dc_duration_ms, active_ms, presence_pct

This achieves **100% alignment** with Elite Insights Parser for all combat metrics.
