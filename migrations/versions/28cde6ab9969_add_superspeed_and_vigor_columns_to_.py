"""Add superspeed and vigor columns to player_stats

Revision ID: 28cde6ab9969
Revises: 
Create Date: 2025-12-23 11:48:20.782191

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '28cde6ab9969'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    inspector = sa.inspect(op.get_bind())
    columns = {col["name"] for col in inspector.get_columns("player_stats")}

    with op.batch_alter_table("player_stats") as batch_op:
        if "vigor_uptime" not in columns:
            batch_op.add_column(
                sa.Column(
                    "vigor_uptime",
                    sa.Float(),
                    nullable=False,
                    server_default="0.0",
                )
            )
        if "superspeed_uptime" not in columns:
            batch_op.add_column(
                sa.Column(
                    "superspeed_uptime",
                    sa.Float(),
                    nullable=False,
                    server_default="0.0",
                )
            )
        if "vigor_out_ms" not in columns:
            batch_op.add_column(
                sa.Column(
                    "vigor_out_ms",
                    sa.BigInteger(),
                    nullable=False,
                    server_default="0",
                )
            )
        if "superspeed_out_ms" not in columns:
            batch_op.add_column(
                sa.Column(
                    "superspeed_out_ms",
                    sa.BigInteger(),
                    nullable=False,
                    server_default="0",
                )
            )

    with op.batch_alter_table("player_stats") as batch_op:
        if "vigor_uptime" not in columns:
            batch_op.alter_column("vigor_uptime", server_default=None)
        if "superspeed_uptime" not in columns:
            batch_op.alter_column("superspeed_uptime", server_default=None)
        if "vigor_out_ms" not in columns:
            batch_op.alter_column("vigor_out_ms", server_default=None)
        if "superspeed_out_ms" not in columns:
            batch_op.alter_column("superspeed_out_ms", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("player_stats") as batch_op:
        batch_op.drop_column("superspeed_out_ms")
        batch_op.drop_column("vigor_out_ms")
        batch_op.drop_column("superspeed_uptime")
        batch_op.drop_column("vigor_uptime")
