"""add is_ally flag to player_stats

Revision ID: 20251224_add_is_ally
Revises: 20250301_add_dps_report_columns_to_fights
Create Date: 2025-12-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20251224_add_is_ally"
down_revision: Union[str, Sequence[str], None] = "20250301_add_dps_report_columns_to_fights"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_ally boolean column if missing."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("player_stats")}

    with op.batch_alter_table("player_stats") as batch_op:
        if "is_ally" not in columns:
            batch_op.add_column(sa.Column("is_ally", sa.Boolean(), nullable=False, server_default=sa.true()))

    # Backfill existing rows to True (all historic entries treated as allies)
    if "is_ally" not in columns:
        op.execute("UPDATE player_stats SET is_ally = TRUE WHERE is_ally IS NULL")

    # Drop default after backfill for cleanliness
    with op.batch_alter_table("player_stats") as batch_op:
        if "is_ally" not in columns:
            batch_op.alter_column("is_ally", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("player_stats") as batch_op:
        batch_op.drop_column("is_ally")
