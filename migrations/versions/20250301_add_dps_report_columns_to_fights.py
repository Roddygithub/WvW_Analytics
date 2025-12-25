"""add dps.report columns to fights

Revision ID: 20250301_add_dps_report_columns_to_fights
Revises: 20250224_add_ei_json_path_to_fights
Create Date: 2025-03-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20250301_add_dps_report_columns_to_fights"
down_revision = "20250224_add_ei_json_path_to_fights"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {col["name"] for col in inspector.get_columns("fights")}

    with op.batch_alter_table("fights") as batch_op:
        if "dps_permalink" not in columns:
            batch_op.add_column(sa.Column("dps_permalink", sa.String(), nullable=True))
        if "dps_json_path" not in columns:
            batch_op.add_column(sa.Column("dps_json_path", sa.String(), nullable=True))


def downgrade():
    with op.batch_alter_table("fights") as batch_op:
        batch_op.drop_column("dps_permalink")
        batch_op.drop_column("dps_json_path")
