"""add_digest_archive

Revision ID: 0022_add_digest_archive
Revises: 0019_add_replies_and_badges
Create Date: 2025-10-17
"""
from alembic import op
import sqlalchemy as sa

revision = "0022_add_digest_archive"
down_revision = "0019_add_replies_and_badges"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "digest_archive",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("month_label", sa.String(80), index=True),
        sa.Column("start_dt", sa.DateTime),
        sa.Column("end_dt", sa.DateTime),
        sa.Column("metrics_json", sa.JSON),
        sa.Column("recipients", sa.Text),
        sa.Column("html_snapshot", sa.Text),
        sa.Column("sent_at", sa.DateTime),
        sa.Column("created_by_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("created_via", sa.String(40), default="auto"),
        sa.Column("resent_at", sa.DateTime),
        sa.Column("resent_by_id", sa.Integer, sa.ForeignKey("users.id")),
    )

def downgrade():
    op.drop_table("digest_archive")
