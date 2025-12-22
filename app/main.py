from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import logging

from app.db.base import init_db
from app.routers import home, analysis, meta

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="WvW Analytics",
    description="Professional WvW combat analytics for Guild Wars 2",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

app.include_router(home.router)
app.include_router(analysis.router)
app.include_router(meta.router)


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize database on startup."""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanup on shutdown."""
    logger.info("Shutting down WvW Analytics")


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> HTMLResponse:
    """Custom 404 page."""
    return templates.TemplateResponse(
        "404.html",
        {"request": request},
        status_code=404
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc: Exception) -> HTMLResponse:
    """Custom 500 page."""
    logger.error(f"Server error: {exc}")
    return templates.TemplateResponse(
        "500.html",
        {"request": request},
        status_code=500
    )
