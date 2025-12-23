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
    with op.batch_alter_table("player_stats") as batch_op:
        batch_op.add_column(
            sa.Column(
                "vigor_uptime",
                sa.Float(),
                nullable=False,
                server_default="0.0",
            )
        )
        batch_op.add_column(
            sa.Column(
                "superspeed_uptime",
                sa.Float(),
                nullable=False,
                server_default="0.0",
            )
        )
        batch_op.add_column(
            sa.Column(
                "vigor_out_ms",
                sa.BigInteger(),
                nullable=False,
                server_default="0",
            )
        )
        batch_op.add_column(
            sa.Column(
                "superspeed_out_ms",
                sa.BigInteger(),
                nullable=False,
                server_default="0",
            )
        )

    # Drop the server defaults now that existing rows are populated.
    with op.batch_alter_table("player_stats") as batch_op:
        batch_op.alter_column("vigor_uptime", server_default=None)
        batch_op.alter_column("superspeed_uptime", server_default=None)
        batch_op.alter_column("vigor_out_ms", server_default=None)
        batch_op.alter_column("superspeed_out_ms", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("player_stats") as batch_op:
        batch_op.drop_column("superspeed_out_ms")
        batch_op.drop_column("vigor_out_ms")
        batch_op.drop_column("superspeed_uptime")
        batch_op.drop_column("vigor_uptime")
