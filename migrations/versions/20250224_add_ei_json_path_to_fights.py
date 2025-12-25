"""add ei_json_path to fights

Revision ID: 20250224_add_ei_json_path_to_fights
Revises: 20241224_add_regen_swiftness_stealth_columns
Create Date: 2025-02-24 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20250224_add_ei_json_path_to_fights"
down_revision = "20241224_add_regen_swiftness_stealth"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {col["name"] for col in inspector.get_columns("fights")}

    with op.batch_alter_table("fights") as batch_op:
        if "ei_json_path" not in columns:
            batch_op.add_column(sa.Column("ei_json_path", sa.String(), nullable=True))


def downgrade():
    with op.batch_alter_table("fights") as batch_op:
        batch_op.drop_column("ei_json_path")
