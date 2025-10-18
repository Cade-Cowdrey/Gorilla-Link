"""add missing models for groups/stories/badges/achievements/feedback/audit/analytics/rsvps/dms

Revision ID: 0014_add_missing_models
Revises: 0013_init_core_models
Create Date: 2025-10-16
"""
from alembic import op
import sqlalchemy as sa

try:
    from sqlalchemy.dialects import postgresql
    JSONB = postgresql.JSONB
except Exception:
    JSONB = sa.JSON

revision = "0014_add_missing_models"
down_revision = "0013_init_core_models"
branch_labels = None
depends_on = None


def upgrade():
    # stories
    op.create_table(
        "stories",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("body", sa.Text()),
        sa.Column("author_id", sa.Integer),
        sa.Column("department_id", sa.Integer),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("published", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index("ix_stories_title", "stories", ["title"])
    op.create_index("ix_stories_published", "stories", ["published"])
    op.create_index("ix_stories_created_at", "stories", ["created_at"])

    # achievements & badges
    op.create_table(
        "achievements",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_achievements_code", "achievements", ["code"], unique=True)

    op.create_table(
        "user_achievements",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, nullable=False),
        sa.Column("achievement_id", sa.Integer, nullable=False),
        sa.Column("awarded_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),
    )
    op.create_index("ix_user_achievements_user", "user_achievements", ["user_id"])
    op.create_index("ix_user_achievements_ach", "user_achievements", ["achievement_id"])
    op.create_index("ix_user_achievements_awarded_at", "user_achievements", ["awarded_at"])

    op.create_table(
        "career_badges",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("label", sa.String(120), nullable=False),
        sa.Column("description", sa.Text()),
    )
    op.create_index("ix_career_badges_slug", "career_badges", ["slug"], unique=True)

    op.create_table(
        "user_badges",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, nullable=False),
        sa.Column("badge_id", sa.Integer, nullable=False),
        sa.Column("granted_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),
    )
    op.create_index("ix_user_badges_user", "user_badges", ["user_id"])
    op.create_index("ix_user_badges_badge", "user_badges", ["badge_id"])

    # event RSVPs
    op.create_table(
        "event_attendees",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("event_id", sa.Integer, nullable=False),
        sa.Column("user_id", sa.Integer, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="going"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("event_id", "user_id", name="uq_event_user"),
    )
    op.create_index("ix_event_attendees_event_status", "event_attendees", ["event_id", "status"])

    # groups
    op.create_table(
        "groups",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(140), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("created_by_id", sa.Integer),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_groups_name", "groups", ["name"], unique=True)
    op.create_index("ix_groups_created_at", "groups", ["created_at"])

    op.create_table(
        "group_members",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("group_id", sa.Integer, nullable=False),
        sa.Column("user_id", sa.Integer, nullable=False),
        sa.Column("role", sa.String(40), nullable=False, server_default="member"),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("group_id", "user_id", name="uq_group_user"),
    )
    op.create_index("ix_group_members_group_id", "group_members", ["group_id"])
    op.create_index("ix_group_members_user_id", "group_members", ["user_id"])
    op.create_index("ix_group_members_role", "group_members", ["role"])
    op.create_index("ix_group_members_joined_at", "group_members", ["joined_at"])

    op.create_table(
        "group_messages",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("group_id", sa.Integer, nullable=False),
        sa.Column("sender_id", sa.Integer, nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_group_messages_group_time", "group_messages", ["group_id", "created_at"])

    # analytics (dept/year)
    op.create_table(
        "analytics_records",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("department_id", sa.Integer, nullable=False),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("placements", sa.Integer, nullable=False, server_default="0"),
        sa.Column("avg_salary", sa.Integer),
        sa.Column("engagement_rate", sa.Float()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("department_id", "year", name="uq_analytics_dept_year"),
    )
    op.create_index("ix_analytics_dept_year", "analytics_records", ["department_id", "year"])
    op.create_index("ix_analytics_created_at", "analytics_records", ["created_at"])
    op.create_index("ix_analytics_updated_at", "analytics_records", ["updated_at"])


def downgrade():
    for name in [
        "analytics_records",
        "group_messages",
        "group_members",
        "groups",
        "event_attendees",
        "user_badges",
        "career_badges",
        "user_achievements",
        "achievements",
        "stories",
    ]:
        op.drop_table(name)
