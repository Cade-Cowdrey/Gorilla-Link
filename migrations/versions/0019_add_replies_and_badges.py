"""Add reply_count to posts and quality-of-life fields to badges."""

from alembic import op
import sqlalchemy as sa

revision = "0019_add_replies_and_badges"
down_revision = "0018_add_reply_model"
branch_labels = None
depends_on = None


def _has_column(conn, table: str, column: str) -> bool:
    insp = sa.inspect(conn)
    cols = [c["name"] for c in insp.get_columns(table)] if table in insp.get_table_names() else []
    return column in cols


def upgrade():
    bind = op.get_bind()

    if "posts" in sa.inspect(bind).get_table_names() and not _has_column(bind, "posts", "reply_count"):
        op.add_column("posts", sa.Column("reply_count", sa.Integer, server_default="0", nullable=False))

    # badges.slug (+ unique) and badges.is_active (if missing)
    if "badges" in sa.inspect(bind).get_table_names():
        if not _has_column(bind, "badges", "slug"):
            op.add_column("badges", sa.Column("slug", sa.String(120), unique=True))
        if not _has_column(bind, "badges", "is_active"):
            op.add_column("badges", sa.Column("is_active", sa.Boolean, server_default=sa.text("true")))


def downgrade():
    bind = op.get_bind()

    if "posts" in sa.inspect(bind).get_table_names() and _has_column(bind, "posts", "reply_count"):
        op.drop_column("posts", "reply_count")

    if "badges" in sa.inspect(bind).get_table_names():
        if _has_column(bind, "badges", "is_active"):
            op.drop_column("badges", "is_active")
        if _has_column(bind, "badges", "slug"):
            op.drop_column("badges", "slug")
