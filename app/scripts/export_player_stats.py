"""
Export all PlayerStats to CSV for analysis.

Usage:
    python -m app.scripts.export_player_stats [output_file]
    
Example:
    python -m app.scripts.export_player_stats analysis/player_stats_all.csv
"""

import sys
import csv
from pathlib import Path

from app.db.base import SessionLocal, engine
from app.db.models import Base, PlayerStats


def export_player_stats(output_file: str):
    """
    Export all allied PlayerStats to CSV.
    
    Args:
        output_file: Path to output CSV file
    """
    db = SessionLocal()
    
    try:
        # Query all PlayerStats where account_name is not null (allies only)
        query = db.query(PlayerStats).filter(PlayerStats.account_name.isnot(None))
        total_count = query.count()
        
        print(f"📊 Exporting {total_count} allied player records...")
        
        # Create output directory if needed
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Define CSV columns
        columns = [
            "fight_id",
            "character_name",
            "account_name",
            "profession",
            "elite_spec",
            "subgroup",
            "dps",
            "total_damage",
            "downs",
            "kills",
            "deaths",
            "damage_taken",
            "quickness_uptime",
            "alacrity_uptime",
            "resistance_uptime",
            "might_uptime",
            "stability_uptime",
            "fury_uptime",
            "protection_uptime",
            "aegis_uptime",
            "strips_out",
            "cleanses",
            "cc_total",
            "healing_out",
            "barrier_out",
            "detected_role"
        ]
        
        # Write CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writeheader()
            
            for idx, player in enumerate(query, 1):
                if idx % 1000 == 0:
                    print(f"  Exported {idx}/{total_count} records...")
                
                row = {col: getattr(player, col, None) for col in columns}
                writer.writerow(row)
        
        print(f"✅ Export complete: {output_file}")
        print(f"   Total records: {total_count}")
        
    finally:
        db.close()


def main():
    """Main entry point for export script."""
    # Default output file
    default_output = "analysis/player_stats_all.csv"
    
    # Get output file from command line or use default
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
    else:
        output_file = default_output
        print(f"ℹ️  No output file specified, using default: {output_file}")
        print()
    
    export_player_stats(output_file)


if __name__ == "__main__":
    main()
