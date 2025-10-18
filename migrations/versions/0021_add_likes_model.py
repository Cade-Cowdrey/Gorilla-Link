"""Add Like model for posts and integrate engagement tracking"""

from alembic import op
import sqlalchemy as sa

# Revision identifiers
revision = "0021_add_likes_model"
down_revision = "0020_add_post_engagement_columns"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "likes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "post_id", name="uq_user_post_like"),
    )


def downgrade():
    op.drop_table("likes")
