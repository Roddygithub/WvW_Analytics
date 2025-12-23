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
BOON_COLUMN_MAP = {col["key"]: col for col in BOON_COLUMNS}
DEFAULT_BOON_SORT = "quickness"


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
    boon_sort: str = Query(DEFAULT_BOON_SORT),
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
    
    boon_sort_key = (boon_sort or DEFAULT_BOON_SORT).lower()
    if boon_sort_key not in BOON_COLUMN_MAP:
        boon_sort_key = DEFAULT_BOON_SORT

    allied_players = [p for p in fight.player_stats if p.account_name]

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

    # Boon generation ranking
    def outgoing_value(player, column_key: str) -> float:
        column = BOON_COLUMN_MAP[column_key]
        return getattr(player, column["out_attr"], 0.0) or 0.0

    players_sorted = sorted(
        allied_players,
        key=lambda player: outgoing_value(player, boon_sort_key),
        reverse=True
    )

    boon_generation_rows = []
    for player in players_sorted:
        boons = {}
        total = 0.0
        for column in BOON_COLUMNS:
            seconds = outgoing_value(player, column["key"]) / 1000.0
            boons[column["key"]] = seconds
            total += seconds
        boon_generation_rows.append(
            {
                "character_name": player.character_name,
                "account_name": player.account_name,
                "spec_name": player.spec_name or player.profession or "Unknown",
                "role": player.detected_role or "Unknown",
                "subgroup": player.subgroup or 0,
                "boons": boons,
                "total": total,
            }
        )

    boon_sort_links = {
        column["key"]: f"{request.url.path}?boon_sort={column['key']}"
        for column in BOON_COLUMNS
    }

    return templates.TemplateResponse(
        "fight_detail.html",
        {
            "request": request,
            "page": "analyze",
            "fight": fight,
            "boon_columns": BOON_COLUMNS,
            "squad_boon_uptimes": squad_boon_uptimes,
            "boon_generation_rows": boon_generation_rows,
            "boon_sort": boon_sort_key,
            "boon_sort_links": boon_sort_links,
        }
    )
