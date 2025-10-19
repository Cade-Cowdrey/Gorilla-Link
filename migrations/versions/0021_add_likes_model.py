"""Add likes model and likes_count on posts."""

from alembic import op
import sqlalchemy as sa

revision = "0021_add_likes_model"
down_revision = "0020_add_post_engagement_columns"
branch_labels = None
depends_on = None


def _table_exists(conn, name: str) -> bool:
    return name in sa.inspect(conn).get_table_names()


def _has_column(conn, table: str, column: str) -> bool:
    insp = sa.inspect(conn)
    cols = [c["name"] for c in insp.get_columns(table)] if table in insp.get_table_names() else []
    return column in cols


def upgrade():
    bind = op.get_bind()

    if not _table_exists(bind, "likes"):
        op.create_table(
            "likes",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("post_id", sa.Integer, sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False),
            sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("user_id", "post_id", name="uq_like_user_post"),
            sa.Index("ix_likes_post_id", "post_id"),
        )

    if "posts" in sa.inspect(bind).get_table_names() and not _has_column(bind, "posts", "likes_count"):
        op.add_column("posts", sa.Column("likes_count", sa.Integer, server_default="0", nullable=False))


def downgrade():
    bind = op.get_bind()
    if _table_exists(bind, "likes"):
        op.drop_table("likes")
    if "posts" in sa.inspect(bind).get_table_names() and _has_column(bind, "posts", "likes_count"):
        op.drop_column("posts", "likes_count")
