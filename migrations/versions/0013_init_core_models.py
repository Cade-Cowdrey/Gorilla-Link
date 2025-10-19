"""Initialize all core models (posts, comments, messages, events, notifications) for Gorilla-Link / PittState-Connect"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# Revision identifiers
revision = "0013_init_core_models"
down_revision = "0012_seed_jobs_internships_demo"
branch_labels = None
depends_on = None


def upgrade():
    # --- POSTS ---
    op.create_table(
        "posts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("image_url", sa.String(255)),
        sa.Column("created_at", sa.DateTime, default=datetime.utcnow),
        sa.Column("updated_at", sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.Column("visibility", sa.String(50), default="public"),
        sa.Column("department_id", sa.Integer, sa.ForeignKey("departments.id")),
    )

    # --- COMMENTS ---
    op.create_table(
        "comments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("post_id", sa.Integer, sa.ForeignKey("posts.id", ondelete="CASCADE")),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, default=datetime.utcnow),
        sa.Column("updated_at", sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    )

    # --- MESSAGES ---
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("sender_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("receiver_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("is_read", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime, default=datetime.utcnow),
    )

    # --- EVENTS ---
    op.create_table(
        "events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("location", sa.String(150)),
        sa.Column("event_date", sa.DateTime, nullable=False),
        sa.Column("organizer_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("department_id", sa.Integer, sa.ForeignKey("departments.id")),
        sa.Column("created_at", sa.DateTime, default=datetime.utcnow),
        sa.Column("updated_at", sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    )

    # --- NOTIFICATIONS ---
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("message", sa.String(255), nullable=False),
        sa.Column("link", sa.String(255)),
        sa.Column("is_read", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime, default=datetime.utcnow),
    )

    # --- LIKES ---
    op.create_table(
        "likes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("post_id", sa.Integer, sa.ForeignKey("posts.id", ondelete="CASCADE")),
        sa.UniqueConstraint("user_id", "post_id", name="uq_user_post_like")
    )

    # --- REPLIES ---
    op.create_table(
        "replies",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("comment_id", sa.Integer, sa.ForeignKey("comments.id", ondelete="CASCADE")),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, default=datetime.utcnow),
    )

    # --- ENGAGEMENT LOGS (optional analytics linkage) ---
    op.create_table(
        "engagement_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("target_id", sa.Integer),
        sa.Column("target_type", sa.String(50)),
        sa.Column("created_at", sa.DateTime, default=datetime.utcnow),
    )

    print("✅ Core models initialized: posts, comments, messages, events, notifications, likes, replies, engagement_logs")


def downgrade():
    op.drop_table("engagement_logs")
    op.drop_table("replies")
    op.drop_table("likes")
    op.drop_table("notifications")
    op.drop_table("events")
    op.drop_table("messages")
    op.drop_table("comments")
    op.drop_table("posts")

    print("🧹 Core models dropped successfully.")
