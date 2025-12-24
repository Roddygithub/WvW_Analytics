from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

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


def _uptime_from_buff_data(player: Dict[str, Any], buff_id: int) -> float:
    """
    Extract uptime% for a given buff id from EI player's buffUptimes.
    """
    for entry in player.get("buffUptimes", []):
        if entry.get("id") == buff_id:
            buff_data = entry.get("buffData", [])
            if buff_data:
                return float(buff_data[0].get("uptime", 0.0))
    return 0.0


def _out_ms_from_generations(player: Dict[str, Any], buff_id: int) -> int:
    """
    Extract outgoing boon generation (milliseconds) if present in EI buff generation tables.
    """
    # EI exposes buffGenerations? and boonsExtension? Structures vary; keep defensive defaults.
    for entry in player.get("buffGenerations", []):
        if entry.get("id") == buff_id:
            buff_data = entry.get("buffData", [])
            if buff_data:
                # EI reports uptime in seconds or percent in some modes; prefer duration if present
                generated = buff_data[0].get("generation", 0)
                if generated:
                    return int(generated)
    return 0


@dataclass
class MappedFight:
    fight: Fight
    player_stats: List[PlayerStats]


def map_ei_json_to_models(ei_json: Dict[str, Any]) -> MappedFight:
    """
    Map Elite Insights JSON into Fight + PlayerStats ORM models (unsaved).
    """
    duration_ms = int(ei_json.get("fightDuration", 0))
    result = FightResult.UNKNOWN
    if str(ei_json.get("success", "")).lower() in {"true", "1"}:
        result = FightResult.VICTORY
    fight = Fight(
        evtc_filename=ei_json.get("eiEncounterID", "unknown.evtc"),
        upload_timestamp=None,  # set by logs_service when persisting
        duration_ms=duration_ms,
        context=FightContext.UNKNOWN,
        result=result,
        ally_count=0,
        enemy_count=0,
        map_id=ei_json.get("mapID"),
    )

    player_stats: List[PlayerStats] = []
    players = ei_json.get("players", [])

    for player in players:
        subgroup = int(player.get("group", 0))
        account = player.get("account", None)
        character = player.get("name", "Unknown")
        prof = player.get("profession")
        elite = player.get("eliteSpec", None)
        spec_name = f"{prof or ''}{' (' + elite + ')' if elite else ''}".strip()

        dps_all = player.get("dpsAll", [])
        support_all = player.get("supportAll", [])
        defense_all = player.get("defenseAll", [])

        dps_total = dps_all[0] if dps_all else {}
        support = support_all[0] if support_all else {}
        defense = defense_all[0] if defense_all else {}

        total_damage = int(_safe_get(dps_total, "damage", 0))
        dps = float(_safe_get(dps_total, "dps", 0.0))
        downs = int(_safe_get(defense, "downs", 0))
        deaths = int(_safe_get(defense, "dead", 0))
        kills = int(_safe_get(dps_total, "kills", 0))
        damage_taken = int(_safe_get(defense, "damageTaken", 0))
        cleanses = int(_safe_get(support, "condiCleanse", 0))
        strips_out = int(_safe_get(support, "boonStrips", 0))
        cc_total = int(_safe_get(dps_total, "breakbarDamage", 0))
        healing_out = int(_safe_get(support, "healing", 0))
        barrier_out = int(_safe_get(support, "barrier", 0))

        # Uptime percentages
        uptimes = {name: _uptime_from_buff_data(player, buff_id) for name, buff_id in BOON_IDS.items()}

        # Outgoing boon production (ms) if available
        outgoing_ms = {name: _out_ms_from_generations(player, buff_id) for name, buff_id in BOON_IDS.items()}

        # EI might uptime is percent; convert to average stacks (0-25)
        might_avg_stacks = (uptimes["might"] / 100.0) * 25.0 if uptimes["might"] else 0.0

        ps = PlayerStats(
            fight_id=None,  # filled when persisted
            character_name=character,
            account_name=account,
            profession=str(prof) if prof is not None else None,
            elite_spec=str(elite) if elite is not None else None,
            spec_name=spec_name or None,
            subgroup=subgroup,
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
        player_stats.append(ps)

    fight.ally_count = len(player_stats)
    fight.enemy_count = 0

    return MappedFight(fight=fight, player_stats=player_stats)
