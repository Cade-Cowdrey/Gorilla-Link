"""Add replies and badges models"""

from alembic import op
import sqlalchemy as sa

# Revision identifiers
revision = "0019_add_replies_and_badges"
down_revision = "0018_add_replies_badges"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "replies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("post_id", sa.Integer(), sa.ForeignKey("posts.id")),
        sa.Column("message_id", sa.Integer(), sa.ForeignKey("messages.id")),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("replies.id")),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "career_badges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("icon", sa.String(length=255)),
        sa.Column("category", sa.String(length=120)),
        sa.Column("created_at", sa.DateTime()),
    )

    op.create_table(
        "user_badges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("badge_id", sa.Integer(), sa.ForeignKey("career_badges.id")),
        sa.Column("earned_at", sa.DateTime()),
    )


def downgrade():
    op.drop_table("user_badges")
    op.drop_table("career_badges")
    op.drop_table("replies")
