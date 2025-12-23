"""
Recalculate roles for all existing PlayerStats using updated thresholds.

Usage:
    python -m app.scripts.recalculate_roles
"""

from app.db.base import SessionLocal
from app.db.models import PlayerStats
from app.services.roles_service import detect_player_role


def recalculate_all_roles():
    """
    Recalculate detected_role for all PlayerStats records.
    """
    db = SessionLocal()
    
    try:
        # Query all PlayerStats
        all_stats = db.query(PlayerStats).all()
        total = len(all_stats)
        
        print(f"📊 Recalculating roles for {total} player records...")
        print()

        if total == 0:
            print("ℹ️  No player stats to recalculate. Exiting.")
            return
        
        role_changes = {
            "unchanged": 0,
            "changed": 0
        }
        
        for idx, player_stat in enumerate(all_stats, 1):
            if idx % 5000 == 0:
                print(f"  Processed {idx}/{total} records...")
            
            old_role = player_stat.detected_role
            new_role, _ = detect_player_role(player_stat)
            
            if old_role != new_role:
                role_changes["changed"] += 1
            else:
                role_changes["unchanged"] += 1
            
            player_stat.detected_role = new_role
        
        # Commit all changes
        db.commit()
        
        print()
        print("=" * 80)
        print("✅ Role recalculation complete!")
        print("=" * 80)
        print(f"Total records:     {total}")
        print(f"Roles changed:     {role_changes['changed']} ({role_changes['changed']/total*100:.2f}%)")
        print(f"Roles unchanged:   {role_changes['unchanged']} ({role_changes['unchanged']/total*100:.2f}%)")
        print()
        
        # Show new distribution
        print("=" * 80)
        print("🎭 New Role Distribution")
        print("=" * 80)
        
        role_counts = {}
        for player_stat in all_stats:
            role = player_stat.detected_role or "Unknown"
            role_counts[role] = role_counts.get(role, 0) + 1
        
        for role in sorted(role_counts.keys(), key=lambda x: role_counts[x], reverse=True):
            count = role_counts[role]
            percentage = (count / total) * 100
            print(f"   {role:20s}: {count:6d} ({percentage:5.2f}%)")
        
    finally:
        db.close()


def main():
    """Main entry point."""
    print("=" * 80)
    print("🚀 WvW Analytics - Role Recalculation")
    print("=" * 80)
    print()
    
    recalculate_all_roles()


if __name__ == "__main__":
    main()
