import os
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.db.models import Fight, FightContext, FightResult


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


async def save_upload_file(upload_file: UploadFile) -> Path:
    """Save uploaded file to disk."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{upload_file.filename}"
    file_path = UPLOAD_DIR / filename
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    return file_path


def validate_evtc_file(file_path: Path) -> tuple[bool, Optional[str]]:
    """
    Validate EVTC file format (placeholder).
    
    Returns:
        (is_valid, error_message)
    """
    if not file_path.exists():
        return False, "File does not exist"
    
    if file_path.suffix not in [".evtc", ".zevtc"]:
        return False, "Invalid file extension. Must be .evtc or .zevtc"
    
    if file_path.stat().st_size == 0:
        return False, "File is empty"
    
    if file_path.stat().st_size > 100 * 1024 * 1024:
        return False, "File too large (max 100MB)"
    
    return True, None


def is_wvw_log(file_path: Path) -> tuple[bool, Optional[str]]:
    """
    Check if log is WvW using EVTC parser.
    
    Returns:
        (is_wvw, error_message)
    """
    from app.parser.evtc_parser import EVTCParser, EVTCParseError
    
    try:
        parser = EVTCParser(file_path)
        parser.parse()
        
        if not parser.is_wvw_log():
            return False, "Not a WvW log (npcid != 1). PvE/PvP logs are not supported."
        
        return True, None
        
    except EVTCParseError as e:
        return False, f"EVTC parse error: {str(e)}"
    except Exception as e:
        return False, f"Failed to parse EVTC file: {str(e)}"


async def process_log_file(
    file_path: Path,
    db: Session
) -> tuple[Optional[Fight], Optional[str]]:
    """
    Process uploaded log file and extract basic metrics.
    
    Returns:
        (fight_record, error_message)
    """
    from app.parser.evtc_parser import EVTCParser, EVTCParseError
    
    is_valid, error = validate_evtc_file(file_path)
    if not is_valid:
        return None, error
    
    try:
        parser = EVTCParser(file_path)
        parser.parse()
        
        if not parser.is_wvw_log():
            return None, "Not a WvW log (npcid != 1). PvE/PvP logs are not supported."
        
        start_time = parser.get_combat_start_time()
        end_time = parser.get_combat_end_time()
        duration_ms = None
        if start_time is not None and end_time is not None:
            duration_ms = end_time - start_time
        
        map_id = parser.get_map_id()
        
        player_count = sum(1 for agent in parser.agents if agent.is_player)
        
        fight = Fight(
            evtc_filename=file_path.name,
            upload_timestamp=datetime.utcnow(),
            duration_ms=duration_ms,
            context=FightContext.UNKNOWN,
            result=FightResult.UNKNOWN,
            ally_count=player_count,
            enemy_count=0,
            map_id=map_id,
        )
        
        db.add(fight)
        db.commit()
        db.refresh(fight)
        
        return fight, None
        
    except EVTCParseError as e:
        return None, f"EVTC parse error: {str(e)}"
    except Exception as e:
        return None, f"Failed to process log file: {str(e)}"


def get_fight_by_id(db: Session, fight_id: int) -> Optional[Fight]:
    """Get fight by ID."""
    return db.query(Fight).filter(Fight.id == fight_id).first()


def get_recent_fights(db: Session, limit: int = 20) -> list[Fight]:
    """Get recent fights."""
    return (
        db.query(Fight)
        .order_by(Fight.upload_timestamp.desc())
        .limit(limit)
        .all()
    )
