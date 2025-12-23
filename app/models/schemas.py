from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.db.models import FightContext, FightResult


class PlayerStatsBase(BaseModel):
    """Base schema for player statistics."""
    character_name: str
    account_name: Optional[str] = None
    profession: Optional[str] = None
    elite_spec: Optional[str] = None
    subgroup: int = 0
    
    total_damage: int = 0
    dps: float = 0.0
    
    downs: int = 0
    kills: int = 0
    deaths: int = 0
    
    damage_taken: int = 0
    
    cc_total: int = 0
    strips_out: int = 0
    strips_in: int = 0
    cleanses: int = 0
    
    healing_out: int = 0
    barrier_out: int = 0
    
    stability_uptime: float = 0.0
    quickness_uptime: float = 0.0
    alacrity_uptime: float = 0.0
    might_uptime: float = 0.0
    fury_uptime: float = 0.0
    protection_uptime: float = 0.0
    aegis_uptime: float = 0.0
    resistance_uptime: float = 0.0
    resolution_uptime: float = 0.0
    vigor_uptime: float = 0.0
    superspeed_uptime: float = 0.0
    
    stab_out_ms: int = 0
    aegis_out_ms: int = 0
    protection_out_ms: int = 0
    quickness_out_ms: int = 0
    alacrity_out_ms: int = 0
    resistance_out_ms: int = 0
    might_out_stacks: int = 0
    fury_out_ms: int = 0
    regeneration_out_ms: int = 0
    vigor_out_ms: int = 0
    superspeed_out_ms: int = 0
    
    detected_role: Optional[str] = None


class PlayerStatsResponse(PlayerStatsBase):
    """Response schema for player statistics."""
    id: int
    fight_id: int
    
    class Config:
        from_attributes = True


class FightBase(BaseModel):
    """Base schema for fight data."""
    evtc_filename: str
    start_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    
    context: FightContext = FightContext.UNKNOWN
    result: FightResult = FightResult.UNKNOWN
    
    ally_count: int = 0
    enemy_count: int = 0
    
    map_id: Optional[int] = None


class FightResponse(FightBase):
    """Response schema for fight data."""
    id: int
    upload_timestamp: datetime
    player_stats: list[PlayerStatsResponse] = []
    
    class Config:
        from_attributes = True


class FightSummary(BaseModel):
    """Summary of a fight for list views."""
    id: int
    evtc_filename: str
    upload_timestamp: datetime
    duration_ms: Optional[int] = None
    context: FightContext
    result: FightResult
    ally_count: int
    enemy_count: int
    player_count: int = 0
    
    class Config:
        from_attributes = True


class MetaStats(BaseModel):
    """META statistics for a context."""
    context: FightContext
    total_fights: int = 0
    total_wins: int = 0
    total_losses: int = 0
    total_draws: int = 0
    unique_players: int = 0
    
    top_specs: list[dict[str, int]] = Field(default_factory=list)
    spec_winrates: dict[str, float] = Field(default_factory=dict)
    role_distribution: dict[str, int] = Field(default_factory=dict)


class UploadResponse(BaseModel):
    """Response after file upload."""
    success: bool
    message: str
    fight_id: Optional[int] = None
    error: Optional[str] = None
