from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from collections import defaultdict
import re

from app.db.models import Fight, FightContext, FightResult, PlayerStats


# Buff IDs we surface in the UI (uptimes/outgoing)
BOON_IDS = {
    "might": 740,
    "fury": 725,
    "quickness": 1187,
    "alacrity": 30328,
    "protection": 717,
    "regeneration": 718,
    "vigor": 726,
    "aegis": 743,
    "stability": 1122,
    "swiftness": 719,
    "resistance": 26980,
    "resolution": 873,
    "superspeed": 5974,
    "stealth": 13017,
}


def _safe_get(data: Dict[str, Any], key: str, default: Any = 0) -> Any:
    return data.get(key, default)


def _parse_duration_ms(json_data: Dict[str, Any]) -> Optional[int]:
    """
    Extract fight duration in milliseconds from common EI/dps.report fields.
    """
    # Numeric fields in ms
    for key in ("fightDurationMS", "durationMS", "duration"):
        val = json_data.get(key)
        if isinstance(val, (int, float)) and val > 0:
            return int(val)

    def _parse_time_str(s: str) -> Optional[int]:
        s = s.strip()
        # Pattern 1: "1m 33s" or "01m33s"
        m = re.match(r"(?:(\d+)\s*m)?\s*(\d+)\s*s", s)
        if m:
            minutes = int(m.group(1) or 0)
            seconds = int(m.group(2))
            return (minutes * 60 + seconds) * 1000
        # Pattern 2: "MM:SS"
        m = re.match(r"(\d+):(\d{2})", s)
        if m:
            minutes = int(m.group(1))
            seconds = int(m.group(2))
            return (minutes * 60 + seconds) * 1000
        return None

    # String durations
    for key in ("fightDuration", "duration"):
        val = json_data.get(key)
        if isinstance(val, str):
            parsed = _parse_time_str(val)
            if parsed:
                return parsed

    # Fallback: if phases exist, take the longest duration field we can find
    phases = json_data.get("phases") or []
    duration_candidates: list[int] = []
    for phase in phases:
        for key in ("duration", "durationMS", "durationMs"):
            val = phase.get(key)
            if isinstance(val, (int, float)) and val > 0:
                duration_candidates.append(int(val))
            elif isinstance(val, str):
                parsed = _parse_time_str(val)
                if parsed:
                    duration_candidates.append(parsed)
    if duration_candidates:
        return max(duration_candidates)

    return None


def _flatten_entries(items: Any) -> list[Dict[str, Any]]:
    """
    EI may return per-phase arrays (list[list[dict]]); flatten to a single list of dict entries.
    """
    flat: list[Dict[str, Any]] = []
    for item in items or []:
        if isinstance(item, list):
            flat.extend(_flatten_entries(item))
        elif isinstance(item, dict):
            flat.append(item)
    return flat


def _first_non_zero_entry(entries: Any, keys: tuple[str, ...]) -> Dict[str, Any]:
    """
    Pick the first entry that has a non-zero value for any of the provided keys.
    If none, return the first entry or {}.
    """
    flat = _flatten_entries(entries)
    for entry in flat:
        for k in keys:
            v = entry.get(k)
            if isinstance(v, (int, float)) and v != 0:
                return entry
    return flat[0] if flat else {}


def _first_non_empty(sections: list[dict], keys: tuple[str, ...]) -> Dict[str, Any]:
    """
    Choose the first dict that contains any of the keys (even if zero),
    falling back to the first dict.
    """
    flat = _flatten_entries(sections)
    for entry in flat:
        if any(k in entry for k in keys):
            return entry
    return flat[0] if flat else {}


def _first_stats_entry(sections: list[dict], keys: tuple[str, ...]) -> Dict[str, Any]:
    """
    Choose the first stats dict that has a non-zero value for any of the given keys.
    Falls back to the first dict if none have non-zero data.
    """
    flat = _flatten_entries(sections)
    for entry in flat:
        for k in keys:
            v = entry.get(k)
            if isinstance(v, (int, float)) and v != 0:
                return entry
    return flat[0] if flat else {}


def _find_buff_entries(player: Dict[str, Any], keys: list[str], buff_id: int) -> list[Dict[str, Any]]:
    """
    Return buffData (or entry) for the given buff id, prioritizing earlier keys (e.g., Active variants first).
    """
    for key in keys:
        entries = _flatten_entries(player.get(key, []) or [])
        for entry in entries:
            if entry.get("id") == buff_id:
                data = entry.get("buffData")
                if isinstance(data, list) and data:
                    return data
                # Sometimes the data is directly on the entry (no buffData list)
                return [entry]
    return []


def _to_number(val, default=0):
    if isinstance(val, (int, float)):
        return val
    if isinstance(val, str):
        m = re.search(r"[-+]?\d*\.?\d+", val)
        if m:
            try:
                return float(m.group(0))
            except Exception:
                return default
    return default


def _to_int(val, default=0) -> int:
    try:
        if val is None:
            return default
        return int(val)
    except (TypeError, ValueError):
        try:
            return int(float(val))
        except Exception:
            return default


def _to_float(val, default=0.0) -> float:
    try:
        if val is None:
            return default
        return float(val)
    except (TypeError, ValueError):
        return default


def _states_ms(states):
    """
    Convert states array ([time_seconds, value]) to milliseconds.
    """
    out = []
    for entry in states or []:
        try:
            t, v = entry
            out.append([float(t) * 1000.0, v])
        except Exception:
            continue
    return out


def _col(arr: list, idx: int, col: int, default: Any = 0) -> Any:
    """
    Safe column accessor for phase arrays (defStats/supportStats/gameplayStats).
    """
    try:
        row = arr[idx]
        return row[col] if len(row) > col else default
    except Exception:
        return default


def _uptime_from_buff_data(
    player: Dict[str, Any],
    buff_id: int,
    duration_ms: Optional[int],
    subgroup_size: Optional[int] = None,
    subgroup_id: Optional[int] = None,
    subgroup_lookup: Optional[Dict[str, int]] = None,
    states_fallback: Optional[list[list[int]]] = None,
) -> float:
    """
    Extract uptime% for a given buff id.
    Prefer buffUptimesActive/buffUptimes; if missing, derive from boonGraph states (per-player).
    """
    entries = _find_buff_entries(player, ["buffUptimesActive", "buffUptimes"], buff_id)
    if entries:
        data = _first_non_zero_entry(entries, ("uptime", "duration", "active", "presence"))
        raw_uptime = data.get("uptime") or data.get("duration") or data.get("active") or 0.0
        try:
            uptime_val = float(raw_uptime)
        except (TypeError, ValueError):
            uptime_val = 0.0

        presence_pct = data.get("presence")

        # Derive presence/active duration using dead/dc durations
        defenses = (player.get("defenses") or [{}])[0] if isinstance(player.get("defenses"), list) else {}
        dead_duration_ms = _to_float(defenses.get("deadDuration"), 0)
        dc_duration_ms = _to_float(defenses.get("dcDuration"), 0)
        active_ms = max(0.0, (duration_ms or 0) - dead_duration_ms - dc_duration_ms)
        effective_duration_ms = active_ms if active_ms > 0 else (duration_ms or 0)

        if presence_pct is None and duration_ms:
            presence_pct = (active_ms / duration_ms * 100.0) if duration_ms else 0.0

        if 0 < uptime_val <= 105:
            return min(100.0, uptime_val)

        if presence_pct is not None:
            try:
                presence_val = float(presence_pct)
                if presence_val > 0:
                    return min(100.0, presence_val)
            except (TypeError, ValueError):
                pass

        if effective_duration_ms and effective_duration_ms > 0:
            states_entry = data.get("states") or []
            if not states_entry and isinstance(data.get("statesPerSource"), dict):
                combined = []
                for vals in data["statesPerSource"].values():
                    combined.extend(vals or [])
                states_entry = combined
            if not states_entry and states_fallback:
                states_entry = states_fallback

            def _uptime_from_states(states: list[list[int]]) -> Optional[float]:
                if not states:
                    return None
                states_sorted = sorted(states, key=lambda x: x[0])
                active_ms = 0.0
                for (t, val), (t_next, _) in zip(states_sorted, states_sorted[1:]):
                    if val and val > 0:
                        active_ms += max(0, t_next - t)
                if active_ms <= 0:
                    return None
                return min(100.0, (active_ms / effective_duration_ms) * 100.0)

            derived = _uptime_from_states(states_entry)
            if derived is not None and derived > 0:
                return derived

        if uptime_val and effective_duration_ms:
            fight_seconds = effective_duration_ms / 1000.0 if effective_duration_ms else 0.0
            if uptime_val <= fight_seconds + 5:
                return min(100.0, (uptime_val * 1000.0 / effective_duration_ms) * 100.0)

            if uptime_val > effective_duration_ms:
                return min(100.0, uptime_val)

            return min(100.0, (uptime_val / effective_duration_ms) * 100.0)

        return float(uptime_val)
    # No buff entries: fallback to boonGraph states if provided
    if states_fallback and duration_ms and duration_ms > 0:
        states_sorted = sorted(states_fallback, key=lambda x: x[0])
        active_ms = 0.0
        for (t, val), (t_next, _) in zip(states_sorted, states_sorted[1:]):
            if val and val > 0:
                active_ms += max(0, t_next - t)
        if active_ms > 0:
            return min(100.0, (active_ms / duration_ms) * 100.0)
    return 0.0


def _out_ms_from_generations(player: Dict[str, Any], buff_id: int, duration_ms: Optional[int] = None) -> int:
    """
    Extract outgoing boon generation (milliseconds for duration boons, stack-ms for might).
    EI may populate `buffGenerations`/`buffGenerationsActive` (preferred) or place
    values directly in support stats; we aggregate them here.
    
    For might (740), EI returns stack-seconds which we convert to stack-milliseconds.
    For other boons, EI returns seconds which we convert to milliseconds.
    """
    # Preferred: explicit generations tables
    entries = _find_buff_entries(player, ["buffGenerations", "buffGenerationsActive"], buff_id)
    if not entries:
        # Fallback: use buffUptimes* generated fields per source
        entries = _find_buff_entries(player, ["buffUptimes", "buffUptimesActive"], buff_id)

    if not entries:
        return 0

    # Sum generation-esque fields across entries (usually one entry)
    total_seconds = 0.0
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        generated = entry.get("generation")
        if generated:
            total_seconds += float(generated)
            continue
        # EI may provide per-source dicts under "generated"/"overstacked"
        for key in ("generated", "overstacked", "wasted"):
            per_source = entry.get(key)
            if isinstance(per_source, dict):
                total_seconds += sum(float(v or 0.0) for v in per_source.values())
    
    # Convert seconds to milliseconds (for might this is stack-seconds to stack-ms)
    return int(total_seconds * 1000.0)


@dataclass
class MappedFight:
    fight: Fight
    player_stats: List[PlayerStats]


def map_dps_json_to_models(json_data: Dict[str, Any]) -> MappedFight:
    """
    Map dps.report EI JSON into Fight + PlayerStats ORM models (unsaved).
    """
    duration_ms = _parse_duration_ms(json_data)
    result = FightResult.UNKNOWN
    if str(json_data.get("success", "")).lower() in {"true", "1"}:
        result = FightResult.VICTORY
    elif str(json_data.get("success", "")).lower() in {"false", "0"}:
        result = FightResult.DEFEAT

    fight = Fight(
        evtc_filename=json_data.get("eiEncounterID", "unknown.evtc"),
        upload_timestamp=None,  # set by logs_service when persisting
        duration_ms=duration_ms,
        context=FightContext.UNKNOWN,
        result=result,
        ally_count=0,
        enemy_count=0,
        map_id=json_data.get("mapID"),
    )

    player_stats: List[PlayerStats] = []
    allies = json_data.get("players", []) or []
    enemies = json_data.get("enemyPlayers", []) or []

    # Pre-compute subgroup sizes and lookup for allies (used for generation->pct fallback on some boons)
    ally_subgroup_sizes: Dict[int, int] = defaultdict(int)
    ally_subgroup_lookup: Dict[str, int] = {}
    for pl in allies:
        g = int(pl.get("group", 0))
        if g > 0:
            ally_subgroup_sizes[g] += 1
        name = pl.get("name")
        if name:
            ally_subgroup_lookup[name] = g if g > 0 else 0

    phase0 = (json_data.get("phases") or [{}])[0] if isinstance(json_data.get("phases"), list) else {}
    phase_dps = phase0.get("dpsStats") or []
    phase_def = phase0.get("defStats") or []
    phase_sup = phase0.get("supportStats") or []
    phase_gp = phase0.get("gameplayStats") or []

    def _build_player_stats(player: Dict[str, Any], is_ally: bool, idx: int) -> PlayerStats:
        character = player.get("name", "Unknown")
        account = player.get("account", None)
        subgroup = int(player.get("group", 0))
        prof = player.get("profession", None)
        elite = player.get("eliteSpec", None)
        spec_name = f"{prof or ''}{' (' + elite + ')' if elite else ''}".strip()

        boon_graph_states = {}
        details = player.get("details") or {}
        if isinstance(details, dict):
            bg = details.get("boonGraph") or []
            if isinstance(bg, list):
                for entry in bg:
                    # Some EI exports wrap boonGraph as a list of dicts inside a single list item
                    iter_entries = entry if isinstance(entry, list) else [entry]
                    for sub in iter_entries:
                        if isinstance(sub, dict) and "id" in sub:
                            states = sub.get("states") or []
                            boon_graph_states[int(sub["id"])] = _states_ms(states)

        dps_all = player.get("dpsAll", []) or []
        support_all = player.get("supportAll", []) or []
        defense_all = player.get("defenseAll", []) or []
        stats_all = player.get("statsAll", []) or []

        # EI sometimes uses "support"/"defenses" arrays (preferred) instead of supportAll/defenseAll
        support_pref = player.get("support", []) or []
        defense_pref = player.get("defenses", []) or []

        dps_total = _first_stats_entry(dps_all or stats_all, ("damage", "dps", "breakbarDamage", "kills"))
        support = _first_stats_entry(
            support_pref or support_all or stats_all,
            ("condiCleanse", "boonStrips", "healing", "barrier", "boonStripsTime", "resurrects", "stunBreak"),
        )
        defense = _first_stats_entry(
            defense_pref or defense_all or stats_all,
            (
                "downs",
                "dead",
                "damageTaken",
                "condiCleanse",
                "boonStrips",
                "breakbarDamage",
                "boonStripsTime",
                "damageBarrier",
                "deadDuration",
                "dcDuration",
            ),
        )
        combat_stats = _first_stats_entry(
            stats_all,
            (
                "evaded",
                "blocked",
                "missed",
                "interrupts",
                "dodgeCount",
                "downed",
                "killed",
            ),
        )
        gameplay = _first_stats_entry(
            stats_all,
            (
                "timeWasted",
                "timeSaved",
                "swapCount",
                "stackDist",
                "distToCom",
                "skillCastUptime",
                "skillCastUptimeNoAA",
            ),
        )

        total_damage = int(_col(phase_dps, idx, 0, _safe_get(dps_total, "damage", 0)))
        dps = float(total_damage)
        # Downs = enemy players downed by this player (from statsAll.downed)
        downs = int(_safe_get(combat_stats, "downed", 0))
        # Kills = enemy players killed by this player (from statsAll.killed)
        kills = int(_safe_get(combat_stats, "killed", 0))
        # Deaths = times this player died (from defenses.deadCount)
        deaths = int(_safe_get(defense, "deadCount", _safe_get(defense, "dead", 0)))
        damage_taken = int(_col(phase_def, idx, 0, _safe_get(defense, "damageTaken", 0)))
        cleanses = int(_safe_get(support, "condiCleanse", _safe_get(defense, "condiCleanse", 0)))
        strips_out = int(_safe_get(support, "boonStrips", _safe_get(defense, "boonStrips", 0)))
        cc_total = int(_col(phase_dps, idx, 3, _safe_get(defense, "breakbarDamage", 0)))
        healing_out = int(_safe_get(support, "healing", 0))
        barrier_out = int(_safe_get(support, "barrier", 0))

        # Defensive/support granular stats (EI arrays: defStats/supportStats)
        barrier_absorbed = int(_col(phase_def, idx, 1, _safe_get(defense, "damageBarrier", 0)))
        missed_count = int(_col(phase_def, idx, 2, _safe_get(defense, "missedCount", _safe_get(combat_stats, "missed", 0))))
        interrupted_count = int(_col(phase_def, idx, 3, _safe_get(defense, "interruptedCount", _safe_get(combat_stats, "interrupts", 0))))
        evaded_count = int(_col(phase_def, idx, 6, _safe_get(defense, "evadedCount", _safe_get(combat_stats, "evaded", 0))))
        blocked_count = int(_col(phase_def, idx, 7, _safe_get(defense, "blockedCount", _safe_get(combat_stats, "blocked", 0))))
        dodged_count = int(_col(phase_def, idx, 8, _safe_get(defense, "dodgeCount", _safe_get(combat_stats, "dodgeCount", 0))))
        downs_count = int(_to_number(_col(phase_def, idx, 13, _safe_get(defense, "downCount", _safe_get(combat_stats, "downed", 0))), 0))
        downed_damage_taken = int(_col(phase_def, idx, 14, _safe_get(defense, "downedDamageTaken", 0)))
        # defStats[15] contains text like "100% Alive", use defense dict instead
        dead_count = int(_safe_get(defense, "deadCount", _safe_get(defense, "dead", 0)))

        cleanses_other = int(_col(phase_sup, idx, 0, _safe_get(support, "condiCleanse", 0)))
        cleanses_self = int(_col(phase_sup, idx, 2, _safe_get(support, "condiCleanseSelf", 0)))
        strips_out = int(_col(phase_sup, idx, 4, _safe_get(support, "boonStrips", _safe_get(defense, "boonStrips", 0))))
        strips_time = float(_col(phase_sup, idx, 5, _safe_get(support, "boonStripsTime", _safe_get(defense, "boonStripsTime", 0.0))) or 0.0)
        cleanses_time = float(_col(phase_sup, idx, 1, _safe_get(support, "condiCleanseTime", _safe_get(defense, "conditionCleansesTime", 0.0))) or 0.0)
        cleanses_time_self = float(_col(phase_sup, idx, 3, _safe_get(support, "condiCleanseTimeSelf", 0.0)) or 0.0)
        resurrects = int(_col(phase_sup, idx, 6, _safe_get(support, "resurrects", 0)))
        resurrect_time = float(_col(phase_sup, idx, 7, _safe_get(support, "resurrectTime", 0.0)) or 0.0)
        stun_breaks = int(_col(phase_sup, idx, 8, _safe_get(support, "stunBreak", 0)))
        stun_break_time = float(_col(phase_sup, idx, 9, _safe_get(support, "removedStunDuration", 0.0)) or 0.0)
        strips_out_time = strips_time
        cleanses_time_other = cleanses_time

        # Gameplay stats
        time_wasted = float(_col(phase_gp, idx, 0, _safe_get(gameplay, "timeWasted", _safe_get(gameplay, "wasted", 0.0))) or 0.0)
        time_saved = float(_col(phase_gp, idx, 2, _safe_get(gameplay, "timeSaved", _safe_get(gameplay, "saved", 0.0))) or 0.0)
        weapon_swaps = int(_col(phase_gp, idx, 4, _safe_get(gameplay, "swapCount", 0)))
        stack_dist = float(_col(phase_gp, idx, 5, _safe_get(gameplay, "stackDist", 0.0)) or 0.0)
        dist_to_com = float(_col(phase_gp, idx, 6, _safe_get(gameplay, "distToCom", 0.0)) or 0.0)
        anim_percent = float(_col(phase_gp, idx, 7, _safe_get(gameplay, "skillCastUptime", 0.0)) or 0.0)
        anim_no_auto_percent = float(_col(phase_gp, idx, 8, _safe_get(gameplay, "skillCastUptimeNoAA", 0.0)) or 0.0)

        # Dead/DC durations for active time approximation
        dead_duration_ms = _to_float(_col(phase_def, idx, 16, _safe_get(defense, "deadDuration", 0)))
        dc_duration_ms = _to_float(_col(phase_def, idx, 18, _safe_get(defense, "dcDuration", 0)))
        active_ms = max(0.0, duration_ms - dead_duration_ms - dc_duration_ms)

        # Uptime percentages
        subgroup_size = ally_subgroup_sizes.get(subgroup) if is_ally and subgroup > 0 else None
        uptimes = {}
        for name, buff_id in BOON_IDS.items():
            uptimes[name] = _uptime_from_buff_data(
                player,
                buff_id,
                duration_ms,
                subgroup_size=subgroup_size,
                subgroup_id=subgroup if is_ally else None,
                subgroup_lookup=ally_subgroup_lookup if is_ally else None,
                states_fallback=boon_graph_states.get(buff_id),
            )

        # Outgoing boon production (ms) if available
        outgoing_ms = {
            name: _out_ms_from_generations(player, buff_id, duration_ms)
            for name, buff_id in BOON_IDS.items()
        }

        # For enemies, keep subgroup=0 to avoid showing in allied subgroup aggregation
        subgroup_value = subgroup if is_ally else 0
        account_value = account if is_ally else None

        ps = PlayerStats(
            fight=fight,
            is_ally=is_ally,
            character_name=character,
            account_name=account_value,
            profession=str(prof) if prof is not None else None,
            elite_spec=str(elite) if elite is not None else None,
            spec_name=spec_name or None,
            subgroup=subgroup_value,
            total_damage=total_damage,
            dps=dps,
            downs=downs,
            kills=kills,
            deaths=deaths,
            damage_taken=damage_taken,
            cc_total=cc_total,
            strips_out=strips_out,
            strips_in=0,
            cleanses=cleanses,
            healing_out=healing_out,
            barrier_out=barrier_out,
            # Boon uptimes
            stability_uptime=uptimes["stability"],
            quickness_uptime=uptimes["quickness"],
            aegis_uptime=uptimes["aegis"],
            protection_uptime=uptimes["protection"],
            fury_uptime=uptimes["fury"],
            resistance_uptime=uptimes["resistance"],
            alacrity_uptime=uptimes["alacrity"],
            vigor_uptime=uptimes["vigor"],
            superspeed_uptime=uptimes["superspeed"],
            regeneration_uptime=uptimes["regeneration"],
            swiftness_uptime=uptimes["swiftness"],
            stealth_uptime=uptimes["stealth"],
            resolution_uptime=uptimes["resolution"],
            might_uptime=uptimes["might"],
            # Boon generation (outgoing)
            stab_out_ms=outgoing_ms["stability"],
            aegis_out_ms=outgoing_ms["aegis"],
            protection_out_ms=outgoing_ms["protection"],
            quickness_out_ms=outgoing_ms["quickness"],
            alacrity_out_ms=outgoing_ms["alacrity"],
            superspeed_out_ms=outgoing_ms["superspeed"],
            resistance_out_ms=outgoing_ms["resistance"],
            might_out_stacks=outgoing_ms["might"],
            fury_out_ms=outgoing_ms["fury"],
            regeneration_out_ms=outgoing_ms["regeneration"],
            vigor_out_ms=outgoing_ms["vigor"],
            # Defensive granular stats
            barrier_absorbed=barrier_absorbed,
            missed_count=missed_count,
            interrupted_count=interrupted_count,
            evaded_count=evaded_count,
            blocked_count=blocked_count,
            dodged_count=dodged_count,
            downs_count=downs_count,
            downed_damage_taken=downed_damage_taken,
            dead_count=dead_count,
            # Support granular stats
            cleanses_other=cleanses_other,
            cleanses_self=cleanses_self,
            cleanses_time_other=cleanses_time_other,
            cleanses_time_self=cleanses_time_self,
            resurrects=resurrects,
            resurrect_time=resurrect_time,
            stun_breaks=stun_breaks,
            stun_break_time=stun_break_time,
            strips_time=strips_out_time,
            # Gameplay stats
            time_wasted=time_wasted,
            time_saved=time_saved,
            weapon_swaps=weapon_swaps,
            stack_dist=stack_dist,
            dist_to_com=dist_to_com,
            anim_percent=anim_percent,
            anim_no_auto_percent=anim_no_auto_percent,
            # Active time tracking
            dead_duration_ms=dead_duration_ms,
            dc_duration_ms=dc_duration_ms,
            active_ms=active_ms,
            presence_pct=(active_ms / duration_ms * 100.0) if duration_ms else 0.0,
        )

        # Attach non-persisted fields for runtime use (boon graph states for debugging)
        ps.boon_states = boon_graph_states

        return ps
    # Allies
    for idx, player in enumerate(allies):
        ps = _build_player_stats(player, is_ally=True, idx=idx)
        player_stats.append(ps)

    # Enemies (optional in EI JSON)
    for idx, player in enumerate(enemies):
        ps = _build_player_stats(player, is_ally=False, idx=idx)
        player_stats.append(ps)

    fight.ally_count = len(allies)
    fight.enemy_count = len(enemies)

    return MappedFight(fight=fight, player_stats=player_stats)
