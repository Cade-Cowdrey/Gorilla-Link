"""init core models for gorilla-link / pittstate connect

Revision ID: 0013_init_core_models
Revises: 3a2b5f1a1e4a_add_digest_archive
Create Date: 2025-10-16
"""

from alembic import op
import sqlalchemy as sa

try:
    from sqlalchemy.dialects import postgresql
    JSONB = postgresql.JSONB
except Exception:
    JSONB = sa.JSON

revision = "0013_init_core_models"
down_revision = "3a2b5f1a1e4a_add_digest_archive"
branch_labels = None
depends_on = None


def upgrade():
    # departments
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_departments_slug", "departments", ["slug"], unique=True)
    op.create_index("ix_departments_name", "departments", ["name"], unique=True)
    op.create_index("ix_departments_created_at", "departments", ["created_at"])

    # careers
    op.create_table(
        "careers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("dept_id", sa.Integer, nullable=False),
        sa.Column("median_salary", sa.Integer),
        sa.Column("openings", sa.Integer, nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.ForeignKeyConstraint(["dept_id"], ["departments.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_careers_title", "careers", ["title"])
    op.create_index("ix_careers_dept_id", "careers", ["dept_id"])
    op.create_index("ix_careers_updated_at", "careers", ["updated_at"])
    op.create_index("ix_careers_dept_title", "careers", ["dept_id", "title"])

    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="student"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("last_login_at", sa.DateTime),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_is_active", "users", ["is_active"])
    op.create_index("ix_users_is_verified", "users", ["is_verified"])
    op.create_index("ix_users_created_at", "users", ["created_at"])
    op.create_index("ix_users_last_login_at", "users", ["last_login_at"])

    # profiles
    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, nullable=False),
        sa.Column("first_name", sa.String(80), nullable=False),
        sa.Column("last_name", sa.String(80), nullable=False),
        sa.Column("headline", sa.String(200)),
        sa.Column("bio", sa.Text()),
        sa.Column("department_id", sa.Integer),
        sa.Column("major", sa.String(120)),
        sa.Column("graduation_year", sa.Integer),
        sa.Column("linkedin_url", sa.String(255)),
        sa.Column("resume_url", sa.String(255)),
        sa.Column("location", sa.String(160)),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("user_id", name="uq_profiles_user"),
    )
    op.create_index("ix_profiles_user_id", "profiles", ["user_id"])
    op.create_index("ix_profiles_department_id", "profiles", ["department_id"])
    op.create_index("ix_profiles_first_name", "profiles", ["first_name"])
    op.create_index("ix_profiles_last_name", "profiles", ["last_name"])
    op.create_index("ix_profiles_major", "profiles", ["major"])
    op.create_index("ix_profiles_graduation_year", "profiles", ["graduation_year"])
    op.create_index("ix_profiles_created_at", "profiles", ["created_at"])
    op.create_index("ix_profiles_updated_at", "profiles", ["updated_at"])
    op.create_index("ix_profiles_name", "profiles", ["last_name", "first_name"])

    # connections
    op.create_table(
        "connections",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("requester_id", sa.Integer, nullable=False),
        sa.Column("addressee_id", sa.Integer, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("responded_at", sa.DateTime),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["addressee_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("requester_id", "addressee_id", name="uq_connection_pair"),
    )
    op.create_check_constraint("ck_no_self_connection", "connections", "requester_id <> addressee_id")
    op.create_index("ix_connections_requester_id", "connections", ["requester_id"])
    op.create_index("ix_connections_addressee_id", "connections", ["addressee_id"])
    op.create_index("ix_connections_pair", "connections", ["requester_id", "addressee_id"])
    op.create_index("ix_connections_status", "connections", ["status"])
    op.create_index("ix_connections_created_at", "connections", ["created_at"])

    # messages
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("sender_id", sa.Integer, nullable=False),
        sa.Column("receiver_id", sa.Integer, nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("read_at", sa.DateTime()),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["receiver_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_messages_sender_time", "messages", ["sender_id", "created_at"])
    op.create_index("ix_messages_receiver_time", "messages", ["receiver_id", "created_at"])

    # events
    op.create_table(
        "events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime()),
        sa.Column("location", sa.String(200)),
        sa.Column("created_by_id", sa.Integer()),
        sa.Column("capacity", sa.Integer()),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_events_slug", "events", ["slug"], unique=True)
    op.create_index("ix_events_title", "events", ["title"])
    op.create_index("ix_events_start_time", "events", ["start_time"])
    op.create_index("ix_events_end_time", "events", ["end_time"])
    op.create_index("ix_events_is_public", "events", ["is_public"])
    op.create_index("ix_events_created_at", "events", ["created_at"])

    # activity_logs
    op.create_table(
        "activity_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer()),
        sa.Column("action", sa.String(160), nullable=False),
        sa.Column("ip_address", sa.String(64)),
        sa.Column("user_agent", sa.String(255)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("metadata", JSONB),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_activity_user_time", "activity_logs", ["user_id", "created_at"])
    op.create_index("ix_activity_logs_action", "activity_logs", ["action"])
    op.create_index("ix_activity_logs_created_at", "activity_logs", ["created_at"])

    # feedback
    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer()),
        sa.Column("target_type", sa.String(40), nullable=False),
        sa.Column("target_id", sa.Integer()),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_check_constraint("ck_feedback_rating_range", "feedback", "rating BETWEEN 1 AND 5")
    op.create_index("ix_feedback_target", "feedback", ["target_type", "target_id"])
    op.create_index("ix_feedback_created_at", "feedback", ["created_at"])

    # audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("actor_user_id", sa.Integer()),
        sa.Column("action", sa.String(160), nullable=False),
        sa.Column("object_type", sa.String(120)),
        sa.Column("object_id", sa.Integer()),
        sa.Column("diff", JSONB),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_audit_object", "audit_logs", ["object_type", "object_id", "created_at"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade():
    for t in [
        "audit_logs",
        "feedback",
        "activity_logs",
        "events",
        "messages",
        "connections",
        "profiles",
        "users",
        "careers",
        "departments",
    ]:
        op.drop_table(t)
