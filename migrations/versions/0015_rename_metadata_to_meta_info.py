"""Rename ActivityLog.metadata to meta_info

Revision ID: 0015_rename_metadata_to_meta_info
Revises: 0014
Create Date: 2025-10-16 22:33:00.000000
"""

from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = "0015_rename_metadata_to_meta_info"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade():
    # ✅ Check if table and column exist before altering (safe, idempotent)
    conn = op.get_bind()
    insp = sa.inspect(conn)
    if "activity_logs" in insp.get_table_names():
        cols = [c["name"] for c in insp.get_columns("activity_logs")]
        if "metadata" in cols:
            op.alter_column("activity_logs", "metadata", new_column_name="meta_info")
        elif "meta_info" not in cols:
            # If no column found at all (for first-time deployments)
            op.add_column("activity_logs", sa.Column("meta_info", sa.JSON(), nullable=True))


def downgrade():
    # ✅ Revert if needed (optional)
    conn = op.get_bind()
    insp = sa.inspect(conn)
    if "activity_logs" in insp.get_table_names():
        cols = [c["name"] for c in insp.get_columns("activity_logs")]
        if "meta_info" in cols:
            op.alter_column("activity_logs", "meta_info", new_column_name="metadata")
