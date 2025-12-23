from collections import defaultdict

from fastapi import APIRouter, Request, UploadFile, File, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.services import logs_service

router = APIRouter(prefix="/analyze", tags=["analysis"])
templates = Jinja2Templates(directory="templates")

BOON_COLUMNS = [
    {"key": "quickness", "label": "Quickness", "uptime_attr": "quickness_uptime", "out_attr": "quickness_out_ms"},
    {"key": "protection", "label": "Protection", "uptime_attr": "protection_uptime", "out_attr": "protection_out_ms"},
    {"key": "vigor", "label": "Vigor", "uptime_attr": "vigor_uptime", "out_attr": "vigor_out_ms"},
    {"key": "aegis", "label": "Aegis", "uptime_attr": "aegis_uptime", "out_attr": "aegis_out_ms"},
    {"key": "stability", "label": "Stability", "uptime_attr": "stability_uptime", "out_attr": "stab_out_ms"},
    {"key": "resistance", "label": "Resistance", "uptime_attr": "resistance_uptime", "out_attr": "resistance_out_ms"},
    {"key": "superspeed", "label": "Superspeed", "uptime_attr": "superspeed_uptime", "out_attr": "superspeed_out_ms"},
]
ALLIED_NUMERIC_COLUMNS = [
    {"key": "dps", "label": "DPS", "attr": "dps"},
    {"key": "damage", "label": "Damage", "attr": "total_damage"},
    {"key": "downs", "label": "Downs", "attr": "downs"},
    {"key": "kills", "label": "Kills", "attr": "kills"},
    {"key": "deaths", "label": "Deaths", "attr": "deaths"},
    {"key": "damage_taken", "label": "Dmg Taken", "attr": "damage_taken"},
    {"key": "quickness_uptime", "label": "Quick %", "attr": "quickness_uptime"},
    {"key": "alacrity_uptime", "label": "Alac %", "attr": "alacrity_uptime"},
    {"key": "might_uptime", "label": "Might", "attr": "might_uptime"},
    {"key": "strips_out", "label": "Strips", "attr": "strips_out"},
    {"key": "cleanses", "label": "Cleanses", "attr": "cleanses"},
    {"key": "cc_total", "label": "CC", "attr": "cc_total"},
]

ALLIED_BOON_COLUMNS = [
    {"key": "quickness_out", "label": "Quickness (s)", "attr": "quickness_out_ms", "divisor": 1000},
    {"key": "protection_out", "label": "Protection (s)", "attr": "protection_out_ms", "divisor": 1000},
    {"key": "vigor_out", "label": "Vigor (s)", "attr": "vigor_out_ms", "divisor": 1000},
    {"key": "aegis_out", "label": "Aegis (s)", "attr": "aegis_out_ms", "divisor": 1000},
    {"key": "stability_out", "label": "Stability (s)", "attr": "stab_out_ms", "divisor": 1000},
    {"key": "resistance_out", "label": "Resistance (s)", "attr": "resistance_out_ms", "divisor": 1000},
    {"key": "superspeed_out", "label": "Superspeed (s)", "attr": "superspeed_out_ms", "divisor": 1000},
]

ALLIED_SORT_COLUMNS = {
    col["key"]: col for col in [*ALLIED_NUMERIC_COLUMNS, *ALLIED_BOON_COLUMNS]
}
DEFAULT_ALLIED_SORT = "dps"
DEFAULT_ALLIED_DIR = "desc"


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
    
    allied_players = [p for p in fight.player_stats if p.account_name]
    show_boon_columns = bool(show_boons)

    # Squad boon uptimes per subgroup
    group_totals: dict[int, dict] = defaultdict(lambda: {"count": 0, "boon_sums": defaultdict(float)})
    squad_total = {"count": 0, "boon_sums": defaultdict(float)}

    for player in allied_players:
        subgroup = player.subgroup or 0
        group_entry = group_totals[subgroup]
        group_entry["count"] += 1
        squad_total["count"] += 1

        for column in BOON_COLUMNS:
            value = getattr(player, column["uptime_attr"], 0.0) or 0.0
            group_entry["boon_sums"][column["key"]] += value
            squad_total["boon_sums"][column["key"]] += value

    def build_boon_row(label: str, data: dict, group_number: int | None = None) -> dict:
        boons = {}
        count = data["count"]
        for column in BOON_COLUMNS:
            avg_value = (data["boon_sums"][column["key"]] / count) if count else 0.0
            boons[column["key"]] = round(avg_value, 1)
        return {
            "label": label,
            "group": group_number,
            "player_count": count,
            "boons": boons,
        }

    squad_boon_uptimes = []
    if squad_total["count"] > 0:
        squad_boon_uptimes.append(build_boon_row("Squad Average", squad_total))
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

    boon_toggle_url = request.url.include_query_params(
        show_boons=int(not show_boon_columns),
        allied_sort=allied_sort_key,
        allied_dir=allied_sort_dir,
    )

    return templates.TemplateResponse(
        "fight_detail.html",
        {
            "request": request,
            "page": "analyze",
            "fight": fight,
            "boon_columns": BOON_COLUMNS,
            "squad_boon_uptimes": squad_boon_uptimes,
            "allied_players": allied_players_sorted,
            "allied_numeric_columns": ALLIED_NUMERIC_COLUMNS,
            "allied_boon_columns": ALLIED_BOON_COLUMNS,
            "allied_sort": allied_sort_key,
            "allied_sort_dir": allied_sort_dir,
            "allied_sort_links": allied_sort_links,
            "show_boon_columns": show_boon_columns,
            "boon_toggle_url": str(boon_toggle_url),
        }
    )
