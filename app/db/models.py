from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, BigInteger, Boolean
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base


class FightContext(str, enum.Enum):
    """Fight context classification."""
    ZERG = "zerg"
    GUILD_RAID = "guild_raid"
    ROAM = "roam"
    UNKNOWN = "unknown"


class FightResult(str, enum.Enum):
    """Fight outcome."""
    VICTORY = "victory"
    DEFEAT = "defeat"
    DRAW = "draw"
    UNKNOWN = "unknown"


class Fight(Base):
    """Represents a single WvW fight/encounter."""
    __tablename__ = "fights"

    id = Column(Integer, primary_key=True, index=True)
    evtc_filename = Column(String, nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    start_time = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    
    context = Column(SQLEnum(FightContext), default=FightContext.UNKNOWN, nullable=False)
    result = Column(SQLEnum(FightResult), default=FightResult.UNKNOWN, nullable=False)
    
    ally_count = Column(Integer, default=0, nullable=False)
    enemy_count = Column(Integer, default=0, nullable=False)
    
    map_id = Column(Integer, nullable=True)
    ei_json_path = Column(String, nullable=True)
    dps_permalink = Column(String, nullable=True)
    dps_json_path = Column(String, nullable=True)
    
    player_stats = relationship("PlayerStats", back_populates="fight", cascade="all, delete-orphan")


class PlayerStats(Base):
    """Per-player statistics for a fight."""
    __tablename__ = "player_stats"

    id = Column(Integer, primary_key=True, index=True)
    fight_id = Column(Integer, ForeignKey("fights.id"), nullable=False)
    is_ally = Column(Boolean, default=True, nullable=False)
    
    character_name = Column(String, nullable=False)
    account_name = Column(String, nullable=True)
    profession = Column(String, nullable=True)
    elite_spec = Column(String, nullable=True)
    spec_name = Column(String, nullable=True)
    
    subgroup = Column(Integer, default=0, nullable=False)
    
    total_damage = Column(BigInteger, default=0, nullable=False)
    dps = Column(Float, default=0.0, nullable=False)
    
    downs = Column(Integer, default=0, nullable=False)
    kills = Column(Integer, default=0, nullable=False)
    deaths = Column(Integer, default=0, nullable=False)
    
    damage_taken = Column(BigInteger, default=0, nullable=False)
    
    cc_total = Column(BigInteger, default=0, nullable=False)
    strips_out = Column(BigInteger, default=0, nullable=False)
    strips_in = Column(BigInteger, default=0, nullable=False)
    cleanses = Column(BigInteger, default=0, nullable=False)
    
    healing_out = Column(BigInteger, default=0, nullable=False)
    barrier_out = Column(BigInteger, default=0, nullable=False)
    
    stability_uptime = Column(Float, default=0.0, nullable=False)
    quickness_uptime = Column(Float, default=0.0, nullable=False)
    alacrity_uptime = Column(Float, default=0.0, nullable=False)
    might_uptime = Column(Float, default=0.0, nullable=False)
    fury_uptime = Column(Float, default=0.0, nullable=False)
    protection_uptime = Column(Float, default=0.0, nullable=False)
    aegis_uptime = Column(Float, default=0.0, nullable=False)
    resistance_uptime = Column(Float, default=0.0, nullable=False)
    resolution_uptime = Column(Float, default=0.0, nullable=False)
    regeneration_uptime = Column(Float, default=0.0, nullable=False)
    vigor_uptime = Column(Float, default=0.0, nullable=False)
    superspeed_uptime = Column(Float, default=0.0, nullable=False)
    swiftness_uptime = Column(Float, default=0.0, nullable=False)
    stealth_uptime = Column(Float, default=0.0, nullable=False)
    
    # Outgoing boon production (milliseconds given to allies)
    stab_out_ms = Column(BigInteger, default=0, nullable=False)
    aegis_out_ms = Column(BigInteger, default=0, nullable=False)
    protection_out_ms = Column(BigInteger, default=0, nullable=False)
    quickness_out_ms = Column(BigInteger, default=0, nullable=False)
    alacrity_out_ms = Column(BigInteger, default=0, nullable=False)
    superspeed_out_ms = Column(BigInteger, default=0, nullable=False)
    resistance_out_ms = Column(BigInteger, default=0, nullable=False)
    might_out_stacks = Column(BigInteger, default=0, nullable=False)
    fury_out_ms = Column(BigInteger, default=0, nullable=False)
    regeneration_out_ms = Column(BigInteger, default=0, nullable=False)
    vigor_out_ms = Column(BigInteger, default=0, nullable=False)
    
    # Defensive granular stats (from defStats array)
    barrier_absorbed = Column(BigInteger, default=0, nullable=False)
    missed_count = Column(Integer, default=0, nullable=False)
    interrupted_count = Column(Integer, default=0, nullable=False)
    evaded_count = Column(Integer, default=0, nullable=False)
    blocked_count = Column(Integer, default=0, nullable=False)
    dodged_count = Column(Integer, default=0, nullable=False)
    downs_count = Column(Integer, default=0, nullable=False)
    downed_damage_taken = Column(BigInteger, default=0, nullable=False)
    dead_count = Column(Integer, default=0, nullable=False)
    
    # Support granular stats (from supportStats array)
    cleanses_other = Column(Integer, default=0, nullable=False)
    cleanses_self = Column(Integer, default=0, nullable=False)
    cleanses_time_other = Column(Float, default=0.0, nullable=False)
    cleanses_time_self = Column(Float, default=0.0, nullable=False)
    resurrects = Column(Integer, default=0, nullable=False)
    resurrect_time = Column(Float, default=0.0, nullable=False)
    stun_breaks = Column(Integer, default=0, nullable=False)
    stun_break_time = Column(Float, default=0.0, nullable=False)
    strips_time = Column(Float, default=0.0, nullable=False)
    
    # Gameplay stats (from gameplayStats array)
    time_wasted = Column(Float, default=0.0, nullable=False)
    time_saved = Column(Float, default=0.0, nullable=False)
    weapon_swaps = Column(Integer, default=0, nullable=False)
    stack_dist = Column(Float, default=0.0, nullable=False)
    dist_to_com = Column(Float, default=0.0, nullable=False)
    anim_percent = Column(Float, default=0.0, nullable=False)
    anim_no_auto_percent = Column(Float, default=0.0, nullable=False)
    
    # Active time tracking (for weighted averages)
    dead_duration_ms = Column(Float, default=0.0, nullable=False)
    dc_duration_ms = Column(Float, default=0.0, nullable=False)
    active_ms = Column(Float, default=0.0, nullable=False)
    presence_pct = Column(Float, default=0.0, nullable=False)
    
    detected_role = Column(String, nullable=True)
    
    fight = relationship("Fight", back_populates="player_stats")

    @staticmethod
    def _ms_to_seconds(value: int | float | None) -> float:
        return float(value or 0) / 1000.0

    @property
    def quickness_out_s(self) -> float:
        return self._ms_to_seconds(self.quickness_out_ms)

    @property
    def protection_out_s(self) -> float:
        return self._ms_to_seconds(self.protection_out_ms)

    @property
    def vigor_out_s(self) -> float:
        return self._ms_to_seconds(self.vigor_out_ms)

    @property
    def aegis_out_s(self) -> float:
        return self._ms_to_seconds(self.aegis_out_ms)

    @property
    def stability_out_s(self) -> float:
        return self._ms_to_seconds(self.stab_out_ms)

    @property
    def resistance_out_s(self) -> float:
        return self._ms_to_seconds(self.resistance_out_ms)

    @property
    def superspeed_out_s(self) -> float:
        return self._ms_to_seconds(self.superspeed_out_ms)

    @property
    def alacrity_out_s(self) -> float:
        return self._ms_to_seconds(self.alacrity_out_ms)

    @property
    def fury_out_s(self) -> float:
        return self._ms_to_seconds(self.fury_out_ms)

    @property
    def regeneration_out_s(self) -> float:
        return self._ms_to_seconds(self.regeneration_out_ms)

    @property
    def might_out_stack_seconds(self) -> float:
        return float(self.might_out_stacks or 0) / 1000.0
