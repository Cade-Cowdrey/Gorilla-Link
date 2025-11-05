"""Add Alumni, Job, Post, and DailyStats models

Revision ID: 0014_add_missing_models
Revises: 0026_split_user_name_into_first_last
Create Date: 2025-10-21 22:45:00.000000
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime


# Revision identifiers, used by Alembic.
revision = "0014_add_missing_models"
down_revision = "0026_split_user_name_into_first_last"
branch_labels = None
depends_on = None


def upgrade():
    # ---------------------------
    # Alumni table
    # ---------------------------
    op.create_table(
        "alumni",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("graduation_year", sa.String(length=10)),
        sa.Column("employer", sa.String(length=120)),
        sa.Column("position", sa.String(length=120)),
        sa.Column("location", sa.String(length=120)),
        sa.Column("achievements", sa.Text()),
        sa.Column("created_at", sa.DateTime(), default=datetime.utcnow),
    )

    # ---------------------------
    # Job table
    # ---------------------------
    op.create_table(
        "job",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=150)),
        sa.Column("company", sa.String(length=120)),
        sa.Column("description", sa.Text()),
        sa.Column("location", sa.String(length=120)),
        sa.Column("salary", sa.Float()),
        sa.Column("posted_date", sa.DateTime(), default=datetime.utcnow),
        sa.Column("deadline", sa.Date()),
        sa.Column("is_active", sa.Boolean(), default=True),
    )

    # ---------------------------
    # Post table
    # ---------------------------
    op.create_table(
        "post",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("content", sa.Text()),
        sa.Column("category", sa.String(length=80)),
        sa.Column("timestamp", sa.DateTime(), default=datetime.utcnow),
    )

    # ---------------------------
    # DailyStats table
    # ---------------------------
    op.create_table(
        "daily_stats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("date", sa.Date(), unique=True),
        sa.Column("active_users", sa.Integer(), default=0),
        sa.Column("new_users", sa.Integer(), default=0),
        sa.Column("scholarships_applied", sa.Integer(), default=0),
        sa.Column("jobs_posted", sa.Integer(), default=0),
    )


def downgrade():
    # Drop in reverse order
    op.drop_table("daily_stats")
    op.drop_table("post")
    op.drop_table("job")
    op.drop_table("alumni")
