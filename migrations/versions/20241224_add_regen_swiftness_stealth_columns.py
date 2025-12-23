"""Add regeneration, swiftness, and stealth uptime columns to player_stats

Revision ID: 20241224_add_regen_swiftness_stealth
Revises: 28cde6ab9969
Create Date: 2025-12-24 00:04:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20241224_add_regen_swiftness_stealth"
down_revision: Union[str, Sequence[str], None] = "28cde6ab9969"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {col["name"] for col in inspector.get_columns("player_stats")}

    with op.batch_alter_table("player_stats") as batch_op:
        if "regeneration_uptime" not in columns:
            batch_op.add_column(
                sa.Column(
                    "regeneration_uptime",
                    sa.Float(),
                    nullable=False,
                    server_default="0.0",
                )
            )
        if "swiftness_uptime" not in columns:
            batch_op.add_column(
                sa.Column(
                    "swiftness_uptime",
                    sa.Float(),
                    nullable=False,
                    server_default="0.0",
                )
            )
        if "stealth_uptime" not in columns:
            batch_op.add_column(
                sa.Column(
                    "stealth_uptime",
                    sa.Float(),
                    nullable=False,
                    server_default="0.0",
                )
            )

    with op.batch_alter_table("player_stats") as batch_op:
        if "regeneration_uptime" not in columns:
            batch_op.alter_column("regeneration_uptime", server_default=None)
        if "swiftness_uptime" not in columns:
            batch_op.alter_column("swiftness_uptime", server_default=None)
        if "stealth_uptime" not in columns:
            batch_op.alter_column("stealth_uptime", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("player_stats") as batch_op:
        batch_op.drop_column("stealth_uptime")
        batch_op.drop_column("swiftness_uptime")
        batch_op.drop_column("regeneration_uptime")
