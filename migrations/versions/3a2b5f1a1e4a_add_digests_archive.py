"""add digest_archive table

Revision ID: 3a2b5f1a1e4a
Revises: 0010_seed_stats
Create Date: 2025-10-14 14:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "3a2b5f1a1e4a"
down_revision = "0010_seed_stats"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "digest_archives",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("to_email", sa.String(length=255), nullable=False),
        sa.Column("cc_email", sa.String(length=255)),
        sa.Column("summary_plain", sa.Text(), nullable=False),
        sa.Column("summary_html", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("pdf_bytes_len", sa.Integer()),
    )
    op.create_index("ix_digest_archives_created_at", "digest_archives", ["created_at"])


def downgrade():
    op.drop_index("ix_digest_archives_created_at", table_name="digest_archives")
    op.drop_table("digest_archives")
