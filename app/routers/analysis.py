from fastapi import APIRouter, Request, UploadFile, File, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.base import get_db

router = APIRouter(prefix="/analyze", tags=["analysis"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def analyze_page(request: Request) -> HTMLResponse:
    """Analysis page with upload form."""
    return templates.TemplateResponse(
        "analyze.html",
        {"request": request, "page": "analyze"}
    )


@router.post("/upload", response_class=HTMLResponse)
async def upload_log(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> HTMLResponse:
    """Upload and analyze a log file (placeholder)."""
    return templates.TemplateResponse(
        "analyze.html",
        {
            "request": request,
            "page": "analyze",
            "upload_success": True,
            "filename": file.filename,
            "message": "File uploaded successfully (parser not yet implemented)"
        }
    )


@router.get("/fight/{fight_id}", response_class=HTMLResponse)
async def view_fight(
    request: Request,
    fight_id: int,
    db: Session = Depends(get_db)
) -> HTMLResponse:
    """View detailed fight analysis (placeholder)."""
    return templates.TemplateResponse(
        "fight_detail.html",
        {
            "request": request,
            "page": "analyze",
            "fight_id": fight_id
        }
    )
