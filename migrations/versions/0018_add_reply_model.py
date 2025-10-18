"""Add Reply model with nested replies for posts and messages

Revision ID: 0018_add_reply_model
Revises: 0017_seed_default_badges
Create Date: 2025-10-17
"""
from alembic import op
import sqlalchemy as sa

# Revision identifiers
revision = "0018_add_reply_model"
down_revision = "0017_seed_default_badges"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "replies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("post_id", sa.Integer(), sa.ForeignKey("posts.id"), nullable=True),
        sa.Column("message_id", sa.Integer(), sa.ForeignKey("messages.id"), nullable=True),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("replies.id"), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_replies_user_id", "replies", ["user_id"])
    op.create_index("ix_replies_post_id", "replies", ["post_id"])
    op.create_index("ix_replies_message_id", "replies", ["message_id"])
    op.create_index("ix_replies_parent_id", "replies", ["parent_id"])

def downgrade():
    op.drop_table("replies")
