"""Add threaded reply model for posts."""

from alembic import op
import sqlalchemy as sa

revision = "0018_add_reply_model"
down_revision = "0017_seed_default_badges"
branch_labels = None
depends_on = None


def _table_exists(conn, name: str) -> bool:
    return name in sa.inspect(conn).get_table_names()


def upgrade():
    bind = op.get_bind()
    if not _table_exists(bind, "replies"):
        op.create_table(
            "replies",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("post_id", sa.Integer, sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")),
            sa.Column("parent_reply_id", sa.Integer, sa.ForeignKey("replies.id", ondelete="CASCADE")),
            sa.Column("content", sa.Text, nullable=False),
            sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Index("ix_replies_post_id_created_at", "post_id", "created_at"),
        )


def downgrade():
    bind = op.get_bind()
    if _table_exists(bind, "replies"):
        op.drop_table("replies")
