import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models import Fight, PlayerStats, FightContext, FightResult
from app.services import meta_service


def test_get_meta_stats_empty(db_session: Session):
    """Test META stats with no fights."""
    stats = meta_service.get_meta_stats(db_session, FightContext.ZERG)
    
    assert stats["total_fights"] == 0
    assert stats["total_wins"] == 0
    assert stats["total_losses"] == 0
    assert stats["unique_players"] == 0


def test_get_meta_stats_with_fights(db_session: Session):
    """Test META stats with some fights."""
    fight1 = Fight(
        evtc_filename="test1.evtc",
        upload_timestamp=datetime.utcnow(),
        context=FightContext.ZERG,
        result=FightResult.VICTORY,
        ally_count=50,
        enemy_count=45,
        duration_ms=300000
    )
    fight2 = Fight(
        evtc_filename="test2.evtc",
        upload_timestamp=datetime.utcnow(),
        context=FightContext.ZERG,
        result=FightResult.DEFEAT,
        ally_count=48,
        enemy_count=52,
        duration_ms=250000
    )
    fight3 = Fight(
        evtc_filename="test3.evtc",
        upload_timestamp=datetime.utcnow(),
        context=FightContext.GUILD_RAID,
        result=FightResult.VICTORY,
        ally_count=20,
        enemy_count=18,
        duration_ms=180000
    )
    
    db_session.add_all([fight1, fight2, fight3])
    db_session.commit()
    
    stats = meta_service.get_meta_stats(db_session, FightContext.ZERG)
    
    assert stats["total_fights"] == 2
    assert stats["total_wins"] == 1
    assert stats["total_losses"] == 1
    assert stats["total_draws"] == 0


def test_get_meta_stats_with_player_stats(db_session: Session):
    """Test META stats with player statistics."""
    fight = Fight(
        evtc_filename="test.evtc",
        upload_timestamp=datetime.utcnow(),
        context=FightContext.ZERG,
        result=FightResult.VICTORY,
        ally_count=10,
        enemy_count=8,
        duration_ms=200000
    )
    db_session.add(fight)
    db_session.commit()
    
    player1 = PlayerStats(
        fight_id=fight.id,
        character_name="Player One",
        elite_spec="Spellbreaker",
        detected_role="DPS"
    )
    player2 = PlayerStats(
        fight_id=fight.id,
        character_name="Player Two",
        elite_spec="Firebrand",
        detected_role="Support"
    )
    player3 = PlayerStats(
        fight_id=fight.id,
        character_name="Player Three",
        elite_spec="Spellbreaker",
        detected_role="DPS"
    )
    
    db_session.add_all([player1, player2, player3])
    db_session.commit()
    
    stats = meta_service.get_meta_stats(db_session, FightContext.ZERG)
    
    assert stats["unique_players"] == 3
    assert len(stats["top_specs"]) == 2
    assert stats["top_specs"][0]["spec"] == "Spellbreaker"
    assert stats["top_specs"][0]["count"] == 2
    assert "DPS" in stats["role_distribution"]
    assert stats["role_distribution"]["DPS"] == 2


def test_get_all_contexts_summary(db_session: Session):
    """Test summary across all contexts."""
    fight1 = Fight(
        evtc_filename="zerg.evtc",
        upload_timestamp=datetime.utcnow(),
        context=FightContext.ZERG,
        result=FightResult.VICTORY,
        ally_count=50,
        enemy_count=45
    )
    fight2 = Fight(
        evtc_filename="raid.evtc",
        upload_timestamp=datetime.utcnow(),
        context=FightContext.GUILD_RAID,
        result=FightResult.DEFEAT,
        ally_count=20,
        enemy_count=22
    )
    
    db_session.add_all([fight1, fight2])
    db_session.commit()
    
    summary = meta_service.get_all_contexts_summary(db_session)
    
    assert "zerg" in summary
    assert "guild_raid" in summary
    assert "roam" in summary
    assert summary["zerg"]["fights"] == 1
    assert summary["guild_raid"]["fights"] == 1
    assert summary["roam"]["fights"] == 0
