from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models import Fight, PlayerStats, FightContext, FightResult


def get_meta_stats(db: Session, context: FightContext) -> dict:
    """
    Get META statistics for a specific context.
    
    Returns aggregated stats for fights in the given context.
    """
    fights = db.query(Fight).filter(Fight.context == context).all()
    
    total_fights = len(fights)
    total_wins = sum(1 for f in fights if f.result == FightResult.VICTORY)
    total_losses = sum(1 for f in fights if f.result == FightResult.DEFEAT)
    total_draws = sum(1 for f in fights if f.result == FightResult.DRAW)
    
    total_duration_ms = sum(f.duration_ms for f in fights if f.duration_ms)
    
    fight_ids = [f.id for f in fights]
    
    unique_players = 0
    if fight_ids:
        unique_players = (
            db.query(func.count(func.distinct(PlayerStats.character_name)))
            .filter(PlayerStats.fight_id.in_(fight_ids))
            .scalar()
        ) or 0
    
    top_specs = []
    spec_winrates = {}
    role_distribution = {}
    
    if fight_ids:
        spec_counts = (
            db.query(
                PlayerStats.elite_spec,
                func.count(PlayerStats.id).label('count')
            )
            .filter(PlayerStats.fight_id.in_(fight_ids))
            .filter(PlayerStats.elite_spec.isnot(None))
            .group_by(PlayerStats.elite_spec)
            .order_by(func.count(PlayerStats.id).desc())
            .limit(10)
            .all()
        )
        
        top_specs = [
            {"spec": spec, "count": count}
            for spec, count in spec_counts
        ]
        
        role_counts = (
            db.query(
                PlayerStats.detected_role,
                func.count(PlayerStats.id).label('count')
            )
            .filter(PlayerStats.fight_id.in_(fight_ids))
            .filter(PlayerStats.detected_role.isnot(None))
            .group_by(PlayerStats.detected_role)
            .all()
        )
        
        role_distribution = {
            role: count
            for role, count in role_counts
        }
    
    return {
        "context": context,
        "total_fights": total_fights,
        "total_wins": total_wins,
        "total_losses": total_losses,
        "total_draws": total_draws,
        "unique_players": unique_players,
        "total_duration_ms": total_duration_ms,
        "top_specs": top_specs,
        "spec_winrates": spec_winrates,
        "role_distribution": role_distribution,
    }


def get_all_contexts_summary(db: Session) -> dict:
    """Get summary stats for all contexts."""
    contexts = [FightContext.ZERG, FightContext.GUILD_RAID, FightContext.ROAM]
    
    summary = {}
    for context in contexts:
        stats = get_meta_stats(db, context)
        summary[context.value] = {
            "fights": stats["total_fights"],
            "wins": stats["total_wins"],
            "losses": stats["total_losses"],
        }
    
    return summary
