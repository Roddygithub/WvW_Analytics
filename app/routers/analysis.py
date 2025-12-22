from fastapi import APIRouter, Request, UploadFile, File, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.services import logs_service

router = APIRouter(prefix="/analyze", tags=["analysis"])
templates = Jinja2Templates(directory="templates")


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
        recent_fights = logs_service.get_recent_fights(db, limit=10)
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
    
    return templates.TemplateResponse(
        "fight_detail.html",
        {
            "request": request,
            "page": "analyze",
            "fight": fight
        }
    )
