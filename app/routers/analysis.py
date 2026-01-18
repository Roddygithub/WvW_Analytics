from collections import defaultdict

from fastapi import APIRouter, Request, UploadFile, File, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.services import logs_service
from app.services.dps_mapping import BOON_IDS

router = APIRouter(prefix="/analyze", tags=["analysis"])
templates = Jinja2Templates(directory="templates")

BOON_COLUMNS = [
    {"key": "might", "label": "Might", "uptime_attr": "might_uptime", "out_attr": "might_out_stacks"},
    {"key": "fury", "label": "Fury", "uptime_attr": "fury_uptime", "out_attr": "fury_out_ms"},
    {"key": "quickness", "label": "Quickness", "uptime_attr": "quickness_uptime", "out_attr": "quickness_out_ms"},
    {"key": "alacrity", "label": "Alacrity", "uptime_attr": "alacrity_uptime", "out_attr": "alacrity_out_ms"},
    {"key": "protection", "label": "Protection", "uptime_attr": "protection_uptime", "out_attr": "protection_out_ms"},
    {"key": "regeneration", "label": "Regeneration", "uptime_attr": "regeneration_uptime", "out_attr": "regeneration_out_ms"},
    {"key": "vigor", "label": "Vigor", "uptime_attr": "vigor_uptime", "out_attr": "vigor_out_ms"},
    {"key": "aegis", "label": "Aegis", "uptime_attr": "aegis_uptime", "out_attr": "aegis_out_ms"},
    {"key": "stability", "label": "Stability", "uptime_attr": "stability_uptime", "out_attr": "stab_out_ms"},
    {"key": "swiftness", "label": "Swiftness", "uptime_attr": "swiftness_uptime", "out_attr": None},
    {"key": "resistance", "label": "Resistance", "uptime_attr": "resistance_uptime", "out_attr": "resistance_out_ms"},
    {"key": "resolution", "label": "Resolution", "uptime_attr": "resolution_uptime", "out_attr": None},
    {"key": "superspeed", "label": "Superspeed", "uptime_attr": "superspeed_uptime", "out_attr": "superspeed_out_ms"},
    {"key": "stealth", "label": "Stealth", "uptime_attr": "stealth_uptime", "out_attr": None},
]

SQUAD_DEFAULT_BOONS = [
    "might",
    "fury",
    "quickness",
    "alacrity",
    "protection",
    "regeneration",
    "vigor",
    "aegis",
    "stability",
    "swiftness",
    "resistance",
    "resolution",
    "superspeed",
    "stealth",
]
ALLIED_NUMERIC_COLUMNS = [
    {"key": "dps", "label": "DPS", "attr": "dps"},
    {"key": "damage", "label": "Damage", "attr": "total_damage"},
    {"key": "downs", "label": "Downs", "attr": "downs"},
    {"key": "kills", "label": "Kills", "attr": "kills"},
    {"key": "deaths", "label": "Deaths", "attr": "deaths"},
    {"key": "damage_taken", "label": "Dmg Taken", "attr": "damage_taken"},
    {"key": "strips_out", "label": "Strips", "attr": "strips_out"},
    {"key": "cleanses", "label": "Cleanses", "attr": "cleanses"},
    {"key": "cc_total", "label": "CC", "attr": "cc_total"},
]

# Defensive stats columns
DEFENSIVE_COLUMNS = [
    {"key": "barrier_absorbed", "label": "Barrier", "attr": "barrier_absorbed"},
    {"key": "evaded_count", "label": "Evaded", "attr": "evaded_count"},
    {"key": "blocked_count", "label": "Blocked", "attr": "blocked_count"},
    {"key": "dodged_count", "label": "Dodged", "attr": "dodged_count"},
    {"key": "missed_count", "label": "Missed", "attr": "missed_count"},
    {"key": "interrupted_count", "label": "Interrupted", "attr": "interrupted_count"},
    {"key": "downs_count", "label": "Downed", "attr": "downs_count"},
    {"key": "downed_damage_taken", "label": "Downed Dmg", "attr": "downed_damage_taken"},
]

# Support stats columns
SUPPORT_COLUMNS = [
    {"key": "cleanses_other", "label": "Cleanses (Other)", "attr": "cleanses_other"},
    {"key": "cleanses_self", "label": "Cleanses (Self)", "attr": "cleanses_self"},
    {"key": "resurrects", "label": "Resurrects", "attr": "resurrects"},
    {"key": "resurrect_time", "label": "Res Time (s)", "attr": "resurrect_time"},
    {"key": "stun_breaks", "label": "Stun Breaks", "attr": "stun_breaks"},
    {"key": "healing_out", "label": "Healing", "attr": "healing_out"},
    {"key": "barrier_out", "label": "Barrier Out", "attr": "barrier_out"},
]

# Gameplay stats columns
GAMEPLAY_COLUMNS = [
    {"key": "weapon_swaps", "label": "Swaps", "attr": "weapon_swaps"},
    {"key": "anim_percent", "label": "Animation %", "attr": "anim_percent"},
    {"key": "stack_dist", "label": "Stack Dist", "attr": "stack_dist"},
    {"key": "dist_to_com", "label": "Dist to Com", "attr": "dist_to_com"},
    {"key": "presence_pct", "label": "Presence %", "attr": "presence_pct"},
]

BOON_GENERATION_COLUMNS = [
    {
        "key": "quickness_out",
        "label": "Quickness (%)",
        "attr": "quickness_out_ms",
    },
    {
        "key": "protection_out",
        "label": "Protection (%)",
        "attr": "protection_out_ms",
    },
    {
        "key": "vigor_out",
        "label": "Vigor (%)",
        "attr": "vigor_out_ms",
    },
    {
        "key": "aegis_out",
        "label": "Aegis (%)",
        "attr": "aegis_out_ms",
    },
    {
        "key": "stability_out",
        "label": "Stability (%)",
        "attr": "stab_out_ms",
    },
    {
        "key": "resistance_out",
        "label": "Resistance (%)",
        "attr": "resistance_out_ms",
    },
    {
        "key": "superspeed_out",
        "label": "Superspeed (%)",
        "attr": "superspeed_out_ms",
    },
    {
        "key": "alacrity_out",
        "label": "Alacrity (%)",
        "attr": "alacrity_out_ms",
    },
    {
        "key": "fury_out",
        "label": "Fury (%)",
        "attr": "fury_out_ms",
    },
    {
        "key": "regeneration_out",
        "label": "Regeneration (%)",
        "attr": "regeneration_out_ms",
    },
    {
        "key": "might_out",
        "label": "Might (avg stacks)",
        "attr": "might_out_stacks",
        "display_attr": "might_out_stack_seconds",
    },
]

ALLIED_SORT_COLUMNS = {col["key"]: col for col in ALLIED_NUMERIC_COLUMNS}
BOON_SORT_COLUMNS = {col["key"]: col for col in BOON_GENERATION_COLUMNS}
DEFAULT_ALLIED_SORT = "dps"
DEFAULT_ALLIED_DIR = "desc"
DEFAULT_BOON_SORT = "quickness_out"
DEFAULT_BOON_DIR = "desc"


@router.get("/", response_class=HTMLResponse)
async def analyze_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Analysis page with upload form and recent fights."""
    recent_fights = logs_service.get_recent_fights(db, limit=10)
    return templates.TemplateResponse(
        "analyze.html",
        {
            "request": request,
            "page": "analyze",
            "recent_fights": recent_fights
        }
    )


@router.post("/upload", response_class=HTMLResponse)
async def upload_log(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> HTMLResponse:
    """Upload and analyze a log file."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Uploading file: {file.filename}")
        file_path = await logs_service.save_upload_file(file)
        logger.info(f"File saved to: {file_path}")
        
        fight, error = await logs_service.process_log_file(file_path, db)
        
        if error:
            logger.error(f"Processing error: {error}")
            recent_fights = logs_service.get_recent_fights(db, limit=10)
            return templates.TemplateResponse(
                "analyze.html",
                {
                    "request": request,
                    "page": "analyze",
                    "upload_error": True,
                    "error_message": error,
                    "recent_fights": recent_fights
                },
                status_code=400
            )
        
        return RedirectResponse(
            url=f"/analyze/fight/{fight.id}",
            status_code=303
        )
        
    except Exception as e:
        logger.exception(f"Upload exception: {str(e)}")
        # Rollback the session if there was a transaction error
        try:
            db.rollback()
            recent_fights = logs_service.get_recent_fights(db, limit=10)
        except Exception:
            recent_fights = []
        
        return templates.TemplateResponse(
            "analyze.html",
            {
                "request": request,
                "page": "analyze",
                "upload_error": True,
                "error_message": f"Upload failed: {str(e)}",
                "recent_fights": recent_fights
            },
            status_code=500
        )


@router.get("/fight/{fight_id}", response_class=HTMLResponse)
async def view_fight(
    request: Request,
    fight_id: int,
    allied_sort: str = Query(DEFAULT_ALLIED_SORT),
    allied_dir: str = Query(DEFAULT_ALLIED_DIR),
    boon_sort: str = Query(DEFAULT_BOON_SORT),
    boon_dir: str = Query(DEFAULT_BOON_DIR),
    show_boons: int = Query(0),
    db: Session = Depends(get_db)
) -> HTMLResponse:
    """View detailed fight analysis."""
    fight = logs_service.get_fight_by_id(db, fight_id)
    
    if not fight:
        return templates.TemplateResponse(
            "404.html",
            {"request": request},
            status_code=404
        )
    
    # Allies: explicit flag from EI mapping, exclude non-squad rows (subgroup <=0 or >=50)
    allied_players = [
        p for p in fight.player_stats
        if getattr(p, "is_ally", True) and 0 < int(getattr(p, "subgroup", 0) or 0) < 50
    ]
    show_boon_columns = bool(show_boons)

    fight_duration_ms = fight.duration_ms or 0

    # Squad boon uptimes per subgroup (weighted by active duration)
    def active_duration_ms(player) -> float:
        """Active duration = phase duration - deadDuration - dcDuration (clamped to 0)."""
        dead_ms = getattr(player, "dead_duration_ms", None)
        dc_ms = getattr(player, "dc_duration_ms", None)
        if dead_ms is None and dc_ms is None:
            presence = getattr(player, "presence", None) or getattr(player, "presence_pct", None)
            try:
                presence_val = float(presence) if presence is not None else None
            except (TypeError, ValueError):
                presence_val = None
            if presence_val is not None and presence_val > 0 and fight_duration_ms:
                return fight_duration_ms * (presence_val / 100.0)
            return float(fight_duration_ms or 0)
        dead_val = float(dead_ms or 0)
        dc_val = float(dc_ms or 0)
        return max(0.0, float(fight_duration_ms or 0) - dead_val - dc_val)

    group_totals: dict[int, dict] = defaultdict(lambda: {"active_ms": 0.0, "boon_ms": defaultdict(float)})
    squad_total = {"active_ms": 0.0, "boon_ms": defaultdict(float)}

    def buff_ms_from_states(player, buff_key: str, active_ms: float, phase_ms: float) -> float:
        """Prefer raw states (boonGraph) to compute buff active ms; fallback to % uptime."""
        buff_id = BOON_IDS.get(buff_key)
        states_map = getattr(player, "boon_states", {}) or {}
        states = states_map.get(buff_id) if buff_id is not None else None
        if states:
            states_sorted = sorted(states, key=lambda x: x[0])
            active = 0.0
            for (t, val), (t_next, _) in zip(states_sorted, states_sorted[1:]):
                if val and val > 0:
                    active += max(0.0, t_next - t)
            # Clamp to active duration
            if active_ms > 0:
                active = min(active, active_ms)
            return active
        # Fallback: use stored percentage
        value = getattr(player, f"{buff_key}_uptime", 0.0) or 0.0
        normalized_percent = min(100.0, max(0.0, float(value)))
        buff_ms = (normalized_percent / 100.0) * phase_ms
        if active_ms > 0:
            buff_ms = min(buff_ms, active_ms)
        return buff_ms

    for player in allied_players:
        subgroup = player.subgroup or 0
        group_entry = group_totals[subgroup]
        phase_ms = float(fight_duration_ms or 0)
        active_ms = active_duration_ms(player)
        if active_ms <= 0 and phase_ms > 0:
            active_ms = phase_ms
        group_entry["active_ms"] += active_ms
        # Exclude non-squad (subgroup 0) from "Squad Average" like EI
        if subgroup and subgroup > 0:
            squad_total["active_ms"] += active_ms

        for column in BOON_COLUMNS:
            buff_ms = buff_ms_from_states(player, column["key"], active_ms, phase_ms)
            group_entry["boon_ms"][column["key"]] += buff_ms
            if subgroup and subgroup > 0:
                squad_total["boon_ms"][column["key"]] += buff_ms

    def build_boon_row(label: str, data: dict, group_number: int | None = None) -> dict:
        boons = {}
        active_ms = data["active_ms"]
        for column in BOON_COLUMNS:
            if active_ms > 0:
                uptime_pct = (data["boon_ms"][column["key"]] / active_ms) * 100.0
                boons[column["key"]] = round(min(100.0, max(0.0, uptime_pct)), 1)
            else:
                boons[column["key"]] = 0.0
        # Count actual players contributing to this group
        player_count = len([p for p in allied_players if (p.subgroup or 0) == group_number]) if group_number is not None else 0
        return {
            "label": label,
            "group": group_number,
            "player_count": player_count,
            "boons": boons,
        }

    squad_boon_uptimes = []
    if squad_total["active_ms"] > 0:
        squad_boon_uptimes.append(build_boon_row("Squad Average", squad_total, None))
    else:
        # Ensure Squad Average always shows total player count even if active_ms=0
        squad_boon_uptimes.append({
            "label": "Squad Average",
            "group": None,
            "player_count": len(allied_players),
            "boons": {col["key"]: 0.0 for col in BOON_COLUMNS},
        })
    for group in sorted(group_totals.keys()):
        label = f"Group {group}" if group else "Group ?"
        squad_boon_uptimes.append(build_boon_row(label, group_totals[group], group))

    allied_sort_key = (allied_sort or DEFAULT_ALLIED_SORT).lower()
    if allied_sort_key not in ALLIED_SORT_COLUMNS:
        allied_sort_key = DEFAULT_ALLIED_SORT

    allied_sort_dir = allied_dir.lower()
    if allied_sort_dir not in {"asc", "desc"}:
        allied_sort_dir = DEFAULT_ALLIED_DIR

    def allied_value(player, column_key: str) -> float:
        column = ALLIED_SORT_COLUMNS[column_key]
        value = getattr(player, column["attr"], 0.0) or 0.0
        return float(value)

    allied_players_sorted = sorted(
        allied_players,
        key=lambda player: allied_value(player, allied_sort_key),
        reverse=(allied_sort_dir == "desc"),
    )

    def sort_link_for(column_key: str) -> dict:
        column_active = allied_sort_key == column_key
        next_dir = "asc" if column_active and allied_sort_dir == "desc" else "desc"
        url = request.url.include_query_params(
            allied_sort=column_key,
            allied_dir=next_dir,
            show_boons=int(show_boon_columns),
        )
        return {
            "url": str(url),
            "active": column_active,
            "direction": allied_sort_dir if column_active else "desc",
        }

    allied_sort_links = {
        column_key: sort_link_for(column_key) for column_key in ALLIED_SORT_COLUMNS.keys()
    }

    boon_sort_key = (boon_sort or DEFAULT_BOON_SORT).lower()
    if boon_sort_key not in BOON_SORT_COLUMNS:
        boon_sort_key = DEFAULT_BOON_SORT

    boon_sort_dir = boon_dir.lower()
    if boon_sort_dir not in {"asc", "desc"}:
        boon_sort_dir = DEFAULT_BOON_DIR

    def boon_value(player, column_key: str) -> float:
        column = BOON_SORT_COLUMNS[column_key]
        attr_name = column.get("display_attr") or column["attr"]
        value = getattr(player, attr_name, 0.0) or 0.0
        return float(value)

    boon_players_sorted = sorted(
        allied_players,
        key=lambda player: boon_value(player, boon_sort_key),
        reverse=(boon_sort_dir == "desc"),
    )

    def boon_sort_link_for(column_key: str) -> dict:
        column_active = boon_sort_key == column_key
        next_dir = "asc" if column_active and boon_sort_dir == "desc" else "desc"
        url = request.url.include_query_params(
            allied_sort=allied_sort_key,
            allied_dir=allied_sort_dir,
            boon_sort=column_key,
            boon_dir=next_dir,
            show_boons=int(show_boon_columns),
        )
        return {
            "url": str(url),
            "active": column_active,
            "direction": boon_sort_dir if column_active else "desc",
        }

    boon_sort_links = {
        column_key: boon_sort_link_for(column_key) for column_key in BOON_SORT_COLUMNS.keys()
    }

    toggle_on_url = request.url.include_query_params(
        show_boons=1,
        allied_sort=allied_sort_key,
        allied_dir=allied_sort_dir,
        boon_sort=boon_sort_key,
        boon_dir=boon_sort_dir,
    )
    toggle_off_url = request.url.include_query_params(
        show_boons=0,
        allied_sort=allied_sort_key,
        allied_dir=allied_sort_dir,
        boon_sort=boon_sort_key,
        boon_dir=boon_sort_dir,
    )

    squad_boon_columns = [
        column for column in BOON_COLUMNS if column["key"] in SQUAD_DEFAULT_BOONS
    ]

    return templates.TemplateResponse(
        "fight_detail.html",
        {
            "request": request,
            "page": "analyze",
            "fight": fight,
            "squad_boon_columns": squad_boon_columns,
            "squad_boon_uptimes": squad_boon_uptimes,
            "allied_players": allied_players_sorted,
            "allied_numeric_columns": ALLIED_NUMERIC_COLUMNS,
            "defensive_columns": DEFENSIVE_COLUMNS,
            "support_columns": SUPPORT_COLUMNS,
            "gameplay_columns": GAMEPLAY_COLUMNS,
            "allied_sort": allied_sort_key,
            "allied_sort_dir": allied_sort_dir,
            "allied_sort_links": allied_sort_links,
            "boon_generation_columns": BOON_GENERATION_COLUMNS,
            "boon_players": boon_players_sorted,
            "boon_sort": boon_sort_key,
            "boon_sort_dir": boon_sort_dir,
            "boon_sort_links": boon_sort_links,
            "show_boon_columns": show_boon_columns,
            "boon_toggle_on_url": str(toggle_on_url),
            "boon_toggle_off_url": str(toggle_off_url),
        }
    )
