from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional
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
    "stealth": 130,
}


def _safe_get(data: Dict[str, Any], key: str, default: Any = 0) -> Any:
    return data.get(key, default)


def _parse_duration_ms(json_data: Dict[str, Any]) -> Optional[int]:
    """
    Extract fight duration in milliseconds from common EI/dps.report fields.
    """
    # Some EI exports include a numeric duration in ms
    for key in ("duration", "durationMS", "fightDurationMS"):
        val = json_data.get(key)
        if isinstance(val, (int, float)) and val > 0:
            return int(val)

    # EI string format like "1m 33s" or "02:15"
    fight_duration = json_data.get("fightDuration")
    if isinstance(fight_duration, str):
        # Pattern 1: "1m 33s"
        m = re.match(r"(?:(\d+)\s*m)?\s*(\d+)\s*s", fight_duration.strip())
        if m:
            minutes = int(m.group(1) or 0)
            seconds = int(m.group(2))
            return (minutes * 60 + seconds) * 1000
        # Pattern 2: "MM:SS"
        m = re.match(r"(\d+):(\d{2})", fight_duration.strip())
        if m:
            minutes = int(m.group(1))
            seconds = int(m.group(2))
            return (minutes * 60 + seconds) * 1000
    return None


def _find_buff_entries(player: Dict[str, Any], keys: list[str], buff_id: int) -> list[Dict[str, Any]]:
    for key in keys:
        for entry in player.get(key, []) or []:
            if entry.get("id") == buff_id:
                data = entry.get("buffData", [])
                if data:
                    return data
    return []


def _uptime_from_buff_data(player: Dict[str, Any], buff_id: int, duration_ms: Optional[int]) -> float:
    """
    Extract uptime% for a given buff id from EI player's buffUptimes.
    Falls back to buffUptimesActive (per phase) if needed.
    """
    entries = _find_buff_entries(player, ["buffUptimes", "buffUptimesActive"], buff_id)
    if entries:
        uptime_ms = float(entries[0].get("uptime", 0.0) or 0.0)
        if duration_ms and duration_ms > 0:
            return min(100.0, (uptime_ms / duration_ms) * 100.0)
        return uptime_ms
    return 0.0


def _out_ms_from_generations(player: Dict[str, Any], buff_id: int) -> int:
    """
    Extract outgoing boon generation (milliseconds) if present in EI buff generation tables.
    Falls back to buffGenerationsActive.
    """
    entries = _find_buff_entries(player, ["buffGenerations", "buffGenerationsActive"], buff_id)
    if entries:
        generated = entries[0].get("generation", 0)
        if generated:
            return int(generated)
    return 0


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

    def _build_player_stats(player: Dict[str, Any], is_ally: bool) -> PlayerStats:
        subgroup = int(player.get("group", 0))
        account = player.get("account", None)
        character = player.get("name", "Unknown")
        prof = player.get("profession")
        elite = player.get("eliteSpec", None)
        spec_name = f"{prof or ''}{' (' + elite + ')' if elite else ''}".strip()

        dps_all = player.get("dpsAll", [])
        support_all = player.get("supportAll", [])
        defense_all = player.get("defenseAll", [])

        stats_all = player.get("statsAll", [])

        dps_total = dps_all[0] if dps_all else (stats_all[0] if stats_all else {})
        support = support_all[0] if support_all else (stats_all[0] if stats_all else {})
        defense = defense_all[0] if defense_all else (stats_all[0] if stats_all else {})

        total_damage = int(_safe_get(dps_total, "damage", 0))
        dps = float(_safe_get(dps_total, "dps", 0.0))
        downs = int(_safe_get(defense, "downs", 0))
        deaths = int(_safe_get(defense, "dead", 0))
        kills = int(_safe_get(dps_total, "kills", 0))
        damage_taken = int(_safe_get(defense, "damageTaken", 0))
        cleanses = int(_safe_get(support, "condiCleanse", _safe_get(defense, "condiCleanse", 0)))
        strips_out = int(_safe_get(support, "boonStrips", _safe_get(defense, "boonStrips", 0)))
        cc_total = int(_safe_get(dps_total, "breakbarDamage", _safe_get(defense, "breakbarDamage", 0)))
        healing_out = int(_safe_get(support, "healing", 0))
        barrier_out = int(_safe_get(support, "barrier", 0))

        # Uptime percentages
        uptimes = {name: _uptime_from_buff_data(player, buff_id, duration_ms) for name, buff_id in BOON_IDS.items()}

        # Outgoing boon production (ms) if available
        outgoing_ms = {name: _out_ms_from_generations(player, buff_id) for name, buff_id in BOON_IDS.items()}

        # EI might uptime is percent; convert to average stacks (0-25)
        might_avg_stacks = (uptimes["might"] / 100.0) * 25.0 if uptimes["might"] else 0.0

        # For enemies, keep subgroup=0 to avoid showing in allied subgroup aggregation
        subgroup_value = subgroup if is_ally else 0
        account_value = account if is_ally else None

        return PlayerStats(
            fight_id=None,  # filled when persisted
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
            might_uptime=might_avg_stacks,
            stab_out_ms=outgoing_ms["stability"],
            aegis_out_ms=outgoing_ms["aegis"],
            protection_out_ms=outgoing_ms["protection"],
            quickness_out_ms=outgoing_ms["quickness"],
            alacrity_out_ms=outgoing_ms["alacrity"],
            resistance_out_ms=outgoing_ms["resistance"],
            might_out_stacks=outgoing_ms["might"],
            fury_out_ms=outgoing_ms["fury"],
            regeneration_out_ms=outgoing_ms["regeneration"],
            vigor_out_ms=outgoing_ms["vigor"],
            superspeed_out_ms=outgoing_ms["superspeed"],
        )

    # Allies
    for player in allies:
        ps = _build_player_stats(player, is_ally=True)
        player_stats.append(ps)

    # Enemies (optional in EI JSON)
    for player in enemies:
        ps = _build_player_stats(player, is_ally=False)
        player_stats.append(ps)

    fight.ally_count = len(allies)
    fight.enemy_count = len(enemies)

    return MappedFight(fight=fight, player_stats=player_stats)
