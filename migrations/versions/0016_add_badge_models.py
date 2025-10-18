"""Add CareerBadge and UserBadge models

Revision ID: 0016_add_badge_models
Revises: 0015_rename_metadata_to_meta_info
Create Date: 2025-10-17

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = "0016_add_badge_models"
down_revision = "0015_rename_metadata_to_meta_info"
branch_labels = None
depends_on = None


def upgrade():
    # --- CareerBadge table ---
    op.create_table(
        "career_badges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), unique=True, nullable=False),
        sa.Column("label", sa.String(length=120)),
        sa.Column("description", sa.Text()),
        sa.Column("icon", sa.String(length=200)),
        sa.Column("active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # --- UserBadge table ---
    op.create_table(
        "user_badges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("badge_id", sa.Integer(), sa.ForeignKey("career_badges.id")),
        sa.Column("awarded_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_index("ix_user_badges_user_id", "user_badges", ["user_id"])
    op.create_index("ix_user_badges_badge_id", "user_badges", ["badge_id"])


def downgrade():
    op.drop_index("ix_user_badges_badge_id", table_name="user_badges")
    op.drop_index("ix_user_badges_user_id", table_name="user_badges")
    op.drop_table("user_badges")
    op.drop_table("career_badges")
