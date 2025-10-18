"""Add email digest logs table for tracking sent digests

Revision ID: 0023_add_email_digest_logs
Revises: 0019_add_replies_and_badges
Create Date: 2025-10-17 21:15:00.000000
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime

# Revision identifiers, used by Alembic.
revision = "0023_add_email_digest_logs"
down_revision = "0019_add_replies_and_badges"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "email_digest_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("digest_type", sa.String(120), nullable=False),  # student, alumni, faculty, analytics, etc.
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("recipients_count", sa.Integer, nullable=False, default=0),
        sa.Column("status", sa.String(50), nullable=False, default="pending"),  # success / failed
        sa.Column("details", sa.Text),
        sa.Column("created_at", sa.DateTime, default=datetime.utcnow, nullable=False),
    )

    op.create_index("ix_email_digest_logs_type", "email_digest_logs", ["digest_type"])
    op.create_index("ix_email_digest_logs_created_at", "email_digest_logs", ["created_at"])


def downgrade():
    op.drop_index("ix_email_digest_logs_created_at", table_name="email_digest_logs")
    op.drop_index("ix_email_digest_logs_type", table_name="email_digest_logs")
    op.drop_table("email_digest_logs")
