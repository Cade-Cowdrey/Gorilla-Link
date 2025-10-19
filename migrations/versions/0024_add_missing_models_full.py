"""Add missing models for Jobs, Connections, Events, DigestArchive, and EmailDigestLog"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime

# Revision identifiers, used by Alembic.
revision = "0024_add_missing_models_full"
down_revision = "0023_add_email_digests_logs"
branch_labels = None
depends_on = None


def upgrade():
    # ==========================================================
    # 🧩 CONNECTIONS TABLE
    # ==========================================================
    op.create_table(
        "connections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("connected_user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("status", sa.String(length=20), default="pending"),
        sa.Column("created_at", sa.DateTime(), default=datetime.utcnow),
    )

    # ==========================================================
    # 💼 JOBS TABLE
    # ==========================================================
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("company", sa.String(length=120)),
        sa.Column("location", sa.String(length=120)),
        sa.Column("job_type", sa.String(length=50)),
        sa.Column("description", sa.Text()),
        sa.Column("posted_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("posted_at", sa.DateTime(), default=datetime.utcnow),
        sa.Column("is_active", sa.Boolean(), default=True),
    )

    # ==========================================================
    # 🎟️ EVENTS TABLE
    # ==========================================================
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("location", sa.String(length=150)),
        sa.Column("event_date", sa.DateTime()),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(), default=datetime.utcnow),
    )

    # ==========================================================
    # 🗞️ DIGEST ARCHIVES TABLE
    # ==========================================================
    op.create_table(
        "digest_archives",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=200)),
        sa.Column("summary", sa.Text()),
        sa.Column("pdf_url", sa.String(length=255)),
        sa.Column("created_at", sa.DateTime(), default=datetime.utcnow),
    )

    # ==========================================================
    # ✉️ EMAIL DIGEST LOGS TABLE
    # ==========================================================
    op.create_table(
        "email_digest_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("recipient_email", sa.String(length=120)),
        sa.Column("subject", sa.String(length=255)),
        sa.Column("sent_at", sa.DateTime(), default=datetime.utcnow),
        sa.Column("status", sa.String(length=50), default="sent"),
    )


def downgrade():
    op.drop_table("email_digest_logs")
    op.drop_table("digest_archives")
    op.drop_table("events")
    op.drop_table("jobs")
    op.drop_table("connections")
