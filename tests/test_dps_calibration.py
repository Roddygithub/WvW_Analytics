import json
from pathlib import Path

import pytest

from app.services.dps_mapping import map_dps_json_to_models


def _active_duration_ms(player, fight_duration_ms: float) -> float:
    """Approximate active duration using presence_pct if available; fallback to full fight."""
    presence_pct = getattr(player, "presence_pct", None)
    try:
        presence_val = float(presence_pct) if presence_pct is not None else None
    except (TypeError, ValueError):
        presence_val = None
    if presence_val is not None and presence_val > 0 and fight_duration_ms:
        return fight_duration_ms * (presence_val / 100.0)
    return float(fight_duration_ms or 0)


def _weighted_avg(players, attr: str, fight_duration_ms: float) -> float:
    num = 0.0
    den = 0.0
    for p in players:
        w = _active_duration_ms(p, fight_duration_ms)
        den += w
        num += (getattr(p, attr, 0.0) or 0.0) * w
    return (num / den) if den > 0 else 0.0


def _load_reference_json() -> Path:
    candidates = [
        Path("data/dps_report/TpD1-ref.json"),
        Path("data/dps_report/TpD1-20251224_103232_20251104-223944_wvw.json"),
        Path("data/dps_report/MzPB-20251225_130746_20251104-223944_wvw.json"),
        Path("data/dps_report/VAUY-20251223_004332_20251104-223944_wvw.json"),
    ]
    json_path = next((p for p in candidates if p.exists()), None)
    assert json_path is not None, "Reference JSON not found"
    return json_path


def _group2_allies(mapped):
    return [
        p
        for p in mapped.player_stats
        if getattr(p, "is_ally", True) and int(getattr(p, "subgroup", 0) or 0) == 2
    ]


def _tot(players, attr: str):
    return sum(getattr(p, attr, 0) or 0 for p in players)


def _avg(players, attr: str):
    vals = [getattr(p, attr, 0) or 0 for p in players]
    return sum(vals) / len(vals) if vals else 0


def test_calibration_full_suite():
    json_path = _load_reference_json()
    data = json.loads(json_path.read_text())
    mapped = map_dps_json_to_models(data)
    allies_g2 = _group2_allies(mapped)
    fight_duration_ms = mapped.fight.duration_ms or 0

    # Boon weighted averages (using presence_pct for active duration weighting)
    g2_quick = _weighted_avg(allies_g2, "quickness_uptime", fight_duration_ms)
    squad_quick = _weighted_avg(
        [
            p
            for p in mapped.player_stats
            if getattr(p, "is_ally", True) and 2 <= (p.subgroup or 0) <= 5
        ],
        "quickness_uptime",
        fight_duration_ms,
    )
    # Updated expected values based on correct presence_pct weighted calculation
    assert abs(g2_quick - 20.41) < 0.01
    assert squad_quick == pytest.approx(29.42, rel=0, abs=0.1)

    # Offensive / defensive / support / gameplay (Group 2)
    assert _tot(allies_g2, "dps") == 371876
    # CC explicitly mapped to breakbarDamage column (dpsStats[3])
    assert _tot(allies_g2, "cc_total") == 0
    assert _tot(allies_g2, "cleanses_other") == 49
    assert _tot(allies_g2, "cleanses_self") == 35
    assert _tot(allies_g2, "strips_out") == 64
    # Resurrects = supportStats[6]; zero value validated by field name
    assert _tot(allies_g2, "resurrects") == 0
    assert _tot(allies_g2, "stun_breaks") == 2

    assert _tot(allies_g2, "damage_taken") == 265583
    assert _tot(allies_g2, "barrier_absorbed") == 67014
    assert _tot(allies_g2, "missed_count") == 6
    assert _tot(allies_g2, "interrupted_count") == 1
    assert _tot(allies_g2, "evaded_count") == 19
    assert _tot(allies_g2, "blocked_count") == 18
    assert _tot(allies_g2, "dodged_count") == 103
    assert _tot(allies_g2, "downs_count") == 3  # Times players were downed (not enemy downs)
    assert _tot(allies_g2, "downed_damage_taken") == 1
    assert _tot(allies_g2, "dead_count") == 0

    assert _tot(allies_g2, "time_wasted") == pytest.approx(4.078, rel=0, abs=1e-3)
    assert _tot(allies_g2, "time_saved") == pytest.approx(9.942, rel=0, abs=1e-3)
    assert _tot(allies_g2, "weapon_swaps") == 23
    assert _avg(allies_g2, "stack_dist") == pytest.approx(9384.834, rel=0, abs=1e-3)
    assert _avg(allies_g2, "dist_to_com") == pytest.approx(1791.886, rel=0, abs=1e-3)
    assert _avg(allies_g2, "anim_percent") == pytest.approx(55.3096, rel=0, abs=1e-4)
    assert _avg(allies_g2, "anim_no_auto_percent") == pytest.approx(41.7134, rel=0, abs=1e-4)
