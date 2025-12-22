from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models import FightContext
from app.services import meta_service

router = APIRouter(prefix="/meta", tags=["meta"])
templates = Jinja2Templates(directory="templates")


@router.get("/zerg", response_class=HTMLResponse)
async def meta_zerg(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """META statistics for Zerg context."""
    stats = meta_service.get_meta_stats(db, FightContext.ZERG)
    return templates.TemplateResponse(
        "meta.html",
        {
            "request": request,
            "page": "meta",
            "context": FightContext.ZERG,
            "context_name": "Zerg",
            "stats": stats
        }
    )


@router.get("/guild_raid", response_class=HTMLResponse)
async def meta_guild_raid(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """META statistics for Guild Raid context."""
    stats = meta_service.get_meta_stats(db, FightContext.GUILD_RAID)
    return templates.TemplateResponse(
        "meta.html",
        {
            "request": request,
            "page": "meta",
            "context": FightContext.GUILD_RAID,
            "context_name": "Guild Raid",
            "stats": stats
        }
    )


@router.get("/roam", response_class=HTMLResponse)
async def meta_roam(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """META statistics for Roam context."""
    stats = meta_service.get_meta_stats(db, FightContext.ROAM)
    return templates.TemplateResponse(
        "meta.html",
        {
            "request": request,
            "page": "meta",
            "context": FightContext.ROAM,
            "context_name": "Roam",
            "stats": stats
        }
    )
