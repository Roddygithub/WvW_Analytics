"""
Bulk import script for processing multiple EVTC logs.

Usage:
    python -m app.scripts.bulk_import [directory_path]
    
Example:
    python -m app.scripts.bulk_import "/home/roddy/Téléchargements/WvW/WvW (1)"
"""

import sys
import os
from pathlib import Path
from typing import Optional
import hashlib

from sqlalchemy.orm import Session

from app.db.database import SessionLocal, engine
from app.db.models import Base, Fight
from app.services.logs_service import process_log_file


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of file to detect duplicates."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def is_already_imported(db: Session, filename: str) -> bool:
    """Check if a file with this name was already imported."""
    return db.query(Fight).filter(Fight.evtc_filename == filename).first() is not None


def bulk_import_logs(directory: str, db: Session) -> dict:
    """
    Import all EVTC logs from a directory recursively.
    
    Returns:
        dict with stats: processed, skipped, errors
    """
    stats = {
        "processed": 0,
        "skipped": 0,
        "errors": 0,
        "error_details": []
    }
    
    directory_path = Path(directory)
    if not directory_path.exists():
        print(f"❌ Directory not found: {directory}")
        return stats
    
    # Find all .evtc and .zevtc files recursively
    evtc_files = list(directory_path.rglob("*.evtc"))
    zevtc_files = list(directory_path.rglob("*.zevtc"))
    all_files = evtc_files + zevtc_files
    
    print(f"📁 Found {len(all_files)} log files in {directory}")
    print(f"   - {len(evtc_files)} .evtc files")
    print(f"   - {len(zevtc_files)} .zevtc files")
    print()
    
    for idx, file_path in enumerate(all_files, 1):
        filename = file_path.name
        
        # Check if already imported
        if is_already_imported(db, filename):
            print(f"[{idx}/{len(all_files)}] ⏭️  Skipped (already imported): {filename}")
            stats["skipped"] += 1
            continue
        
        print(f"[{idx}/{len(all_files)}] 🔄 Processing: {filename}")
        
        try:
            fight, error = process_log_file(file_path, db)
            
            if error:
                print(f"   ❌ Error: {error}")
                stats["errors"] += 1
                stats["error_details"].append({
                    "file": filename,
                    "error": error
                })
            else:
                print(f"   ✅ Imported Fight #{fight.id} ({fight.ally_count} allies, {fight.enemy_count} enemies)")
                stats["processed"] += 1
                
        except Exception as e:
            print(f"   ❌ Unexpected error: {str(e)}")
            stats["errors"] += 1
            stats["error_details"].append({
                "file": filename,
                "error": str(e)
            })
    
    return stats


def main():
    """Main entry point for bulk import script."""
    # Default directory
    default_dir = "/home/roddy/Téléchargements/WvW/WvW (1)"
    
    # Get directory from command line or use default
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = default_dir
        print(f"ℹ️  No directory specified, using default: {directory}")
        print()
    
    # Ensure database tables exist
    Base.metadata.create_all(bind=engine)
    
    # Create database session
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("🚀 WvW Analytics - Bulk Log Import")
        print("=" * 80)
        print()
        
        stats = bulk_import_logs(directory, db)
        
        print()
        print("=" * 80)
        print("📊 Import Summary")
        print("=" * 80)
        print(f"✅ Successfully processed: {stats['processed']}")
        print(f"⏭️  Skipped (duplicates):  {stats['skipped']}")
        print(f"❌ Errors:                {stats['errors']}")
        print()
        
        if stats["error_details"]:
            print("Error details:")
            for detail in stats["error_details"][:10]:  # Show first 10 errors
                print(f"  - {detail['file']}: {detail['error']}")
            if len(stats["error_details"]) > 10:
                print(f"  ... and {len(stats['error_details']) - 10} more errors")
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
