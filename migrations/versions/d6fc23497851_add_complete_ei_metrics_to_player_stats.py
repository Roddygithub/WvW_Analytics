"""add_complete_ei_metrics_to_player_stats

Revision ID: d6fc23497851
Revises: 20251224_add_is_ally
Create Date: 2026-01-18 09:17:25.104298

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd6fc23497851'
down_revision: Union[str, Sequence[str], None] = '20251224_add_is_ally'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add complete EI metrics to player_stats."""
    # Defensive granular stats
    op.add_column('player_stats', sa.Column('barrier_absorbed', sa.BigInteger(), nullable=False, server_default='0'))
    op.add_column('player_stats', sa.Column('missed_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('player_stats', sa.Column('interrupted_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('player_stats', sa.Column('evaded_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('player_stats', sa.Column('blocked_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('player_stats', sa.Column('dodged_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('player_stats', sa.Column('downs_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('player_stats', sa.Column('downed_damage_taken', sa.BigInteger(), nullable=False, server_default='0'))
    op.add_column('player_stats', sa.Column('dead_count', sa.Integer(), nullable=False, server_default='0'))
    
    # Support granular stats
    op.add_column('player_stats', sa.Column('cleanses_other', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('player_stats', sa.Column('cleanses_self', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('player_stats', sa.Column('cleanses_time_other', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('player_stats', sa.Column('cleanses_time_self', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('player_stats', sa.Column('resurrects', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('player_stats', sa.Column('resurrect_time', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('player_stats', sa.Column('stun_breaks', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('player_stats', sa.Column('stun_break_time', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('player_stats', sa.Column('strips_time', sa.Float(), nullable=False, server_default='0.0'))
    
    # Gameplay stats
    op.add_column('player_stats', sa.Column('time_wasted', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('player_stats', sa.Column('time_saved', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('player_stats', sa.Column('weapon_swaps', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('player_stats', sa.Column('stack_dist', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('player_stats', sa.Column('dist_to_com', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('player_stats', sa.Column('anim_percent', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('player_stats', sa.Column('anim_no_auto_percent', sa.Float(), nullable=False, server_default='0.0'))
    
    # Active time tracking
    op.add_column('player_stats', sa.Column('dead_duration_ms', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('player_stats', sa.Column('dc_duration_ms', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('player_stats', sa.Column('active_ms', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('player_stats', sa.Column('presence_pct', sa.Float(), nullable=False, server_default='0.0'))


def downgrade() -> None:
    """Downgrade schema - Remove complete EI metrics from player_stats."""
    # Active time tracking
    op.drop_column('player_stats', 'presence_pct')
    op.drop_column('player_stats', 'active_ms')
    op.drop_column('player_stats', 'dc_duration_ms')
    op.drop_column('player_stats', 'dead_duration_ms')
    
    # Gameplay stats
    op.drop_column('player_stats', 'anim_no_auto_percent')
    op.drop_column('player_stats', 'anim_percent')
    op.drop_column('player_stats', 'dist_to_com')
    op.drop_column('player_stats', 'stack_dist')
    op.drop_column('player_stats', 'weapon_swaps')
    op.drop_column('player_stats', 'time_saved')
    op.drop_column('player_stats', 'time_wasted')
    
    # Support granular stats
    op.drop_column('player_stats', 'strips_time')
    op.drop_column('player_stats', 'stun_break_time')
    op.drop_column('player_stats', 'stun_breaks')
    op.drop_column('player_stats', 'resurrect_time')
    op.drop_column('player_stats', 'resurrects')
    op.drop_column('player_stats', 'cleanses_time_self')
    op.drop_column('player_stats', 'cleanses_time_other')
    op.drop_column('player_stats', 'cleanses_self')
    op.drop_column('player_stats', 'cleanses_other')
    
    # Defensive granular stats
    op.drop_column('player_stats', 'dead_count')
    op.drop_column('player_stats', 'downed_damage_taken')
    op.drop_column('player_stats', 'downs_count')
    op.drop_column('player_stats', 'dodged_count')
    op.drop_column('player_stats', 'blocked_count')
    op.drop_column('player_stats', 'evaded_count')
    op.drop_column('player_stats', 'interrupted_count')
    op.drop_column('player_stats', 'missed_count')
    op.drop_column('player_stats', 'barrier_absorbed')
